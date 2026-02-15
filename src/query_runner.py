# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Main query runner module for paginated query execution with 4-file output.

Standalone tool for running queries against the database and capturing results.
Uses load_config(environment) and EDW_PASSWORD env var for connection.

Usage:
    uv run python -m src.query_runner --sql-file <file> --query-type schema_info --slug <name> --environment dev
"""

import math
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyodbc

from .execute_pipeline import get_connection_string, load_config
from .file_writer import write_all_files
from .logger import QueryLogger
from .query_types import QUERY_TIMEOUTS, ExitStatus, QueryMetadata, QueryType
from .resumption import generate_resumption_template
from .retry import retry_on_transient_error
from .slug_generator import create_slug, extract_slug_from_sql


class QueryRunner:
    """Main query execution class."""

    BATCH_SIZE = 1000  # Fixed batch size for predictable memory usage

    def __init__(self, environment: str = "dev"):
        """Initialize query runner with environment config."""
        self.config = load_config(environment)
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)

    @retry_on_transient_error(max_retries=3, base_delay=1.0, backoff_factor=5.0)
    def get_connection(self) -> pyodbc.Connection:
        """Get database connection."""
        conn_str = get_connection_string(self.config)
        return pyodbc.connect(conn_str, autocommit=True)

    def extract_sort_columns(self, sql: str) -> list[str]:
        """Extract ORDER BY columns from SQL query."""
        match = re.search(r"\bORDER\s+BY\s+(.+?)(?:\s+OFFSET|\s+FETCH|;|$)", sql, re.IGNORECASE | re.DOTALL)

        if not match:
            return []

        order_clause = match.group(1)
        columns = []
        for part in order_clause.split(","):
            col = re.sub(r"\s+(ASC|DESC)\s*$", "", part.strip(), flags=re.IGNORECASE)
            col = col.strip("[]")
            if "." in col:
                col = col.split(".")[-1].strip("[]")
            columns.append(col)

        return columns

    def get_row_count_estimate(self, conn: pyodbc.Connection, sql: str, table_name: str | None = None) -> int:
        """Get row count estimate from sys.dm_db_partition_stats (fast).

        Falls back to COUNT(*) if DMV query fails.
        """
        cursor = conn.cursor()

        if not table_name:
            table_match = re.search(r"\bFROM\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)", sql, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(2) or table_match.group(1)

        if table_name:
            try:
                dmv_query = f"""
                SELECT SUM(p.rows) AS row_count
                FROM sys.tables t
                INNER JOIN sys.indexes i ON t.object_id = i.object_id
                INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                WHERE t.name = '{table_name}'
                AND i.index_id <= 1
                GROUP BY t.name
                """
                cursor.execute(dmv_query)
                result = cursor.fetchone()
                if result and result[0]:
                    print(f"  Row count estimate (DMV): {result[0]:,}", file=sys.stderr)
                    return int(result[0])
            except Exception as e:
                print(f"  Warning: DMV query failed ({e}), falling back to COUNT(*)", file=sys.stderr)

        try:
            clean_sql = sql.strip().rstrip(";")
            count_query = f"SELECT COUNT(*) FROM ({clean_sql}) AS count_subquery"
            cursor.execute(count_query)
            result = cursor.fetchone()
            count = int(result[0]) if result else 0
            print(f"  Row count (COUNT(*)): {count:,}", file=sys.stderr)
            return count
        except Exception as e:
            print(f"  Warning: COUNT(*) failed ({e}), assuming unknown row count", file=sys.stderr)
            return 0

    def execute_query(
        self,
        sql: str,
        query_type: QueryType,
        slug: str | None = None,
        has_phi: bool = True,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute SQL query and generate 4 output files."""
        start_time = time.time()

        if arguments is None:
            arguments = {}

        now = datetime.now(UTC)
        timestamp_iso = now.strftime("%Y%m%dT%H%M%SZ")
        timestamp_readable = now.isoformat()

        if slug is None:
            slug = extract_slug_from_sql(sql) or "query"
        else:
            slug = create_slug(slug)

        files = {
            "sql": self.output_dir / f"{timestamp_iso}_query_{slug}.sql",
            "results": self.output_dir / f"{timestamp_iso}_results_{slug}.jsonl",
            "log": self.output_dir / f"{timestamp_iso}_log_{slug}.jsonl",
            "config": self.output_dir / f"{timestamp_iso}_config_{slug}.json",
        }

        sort_columns = self.extract_sort_columns(sql)
        if not sort_columns:
            print("  Warning: No ORDER BY clause found. Resumption not supported.", file=sys.stderr)

        logger = QueryLogger(start_time=start_time)

        conn = None
        cursor = None
        exit_status: ExitStatus = "success"
        row_count = 0
        actual_batches = 0
        expected_batches = 0
        mb_total = 0.0
        last_processed_value: dict[str, str] = {}
        all_rows: list[dict[str, Any]] = []

        try:
            print(f"[1/5] Connecting to {self.config['server']}...", file=sys.stderr)
            conn = self.get_connection()
            cursor = conn.cursor()

            print("[2/5] Estimating row count...", file=sys.stderr)
            estimated_rows = self.get_row_count_estimate(conn, sql)
            expected_batches = math.ceil(estimated_rows / self.BATCH_SIZE) if estimated_rows > 0 else 0

            logger.log_start(estimated_rows, expected_batches)

            stmt_timeout = QUERY_TIMEOUTS.get(query_type, 7200)
            conn.timeout = stmt_timeout
            print(f"[3/5] Executing query (timeout: {stmt_timeout}s)...", file=sys.stderr)
            cursor.execute(sql)

            def flush_messages() -> None:
                if hasattr(cursor, "messages") and cursor.messages:
                    for msg in cursor.messages:
                        msg_text = msg[1] if len(msg) > 1 else str(msg)
                        print(msg_text, file=sys.stderr)
                    cursor.messages.clear()

            flush_messages()

            column_names = [desc[0] for desc in cursor.description] if cursor.description else []

            if not column_names:
                print("  Success: Execution complete (no result set).", file=sys.stderr)
            else:
                print(f"[4/5] Fetching results (batch size: {self.BATCH_SIZE})...", file=sys.stderr)
                cursor.arraysize = self.BATCH_SIZE

                logger.start_timer_thread()

                batch_num = 0
                while True:
                    batch = cursor.fetchmany(self.BATCH_SIZE)
                    if not batch:
                        break

                    batch_num += 1
                    batch_rows = []

                    for row in batch:
                        row_dict = {col: val for col, val in zip(column_names, row, strict=False)}
                        batch_rows.append(row_dict)
                        row_count += 1

                        if sort_columns:
                            last_processed_value = {col: str(row_dict.get(col, "")) for col in sort_columns}

                    all_rows.extend(batch_rows)

                    batch_bytes = sum(len(str(val)) if val is not None else 0 for row in batch_rows for val in row.values())
                    mb_batch = batch_bytes / (1024 * 1024)
                    mb_total += mb_batch

                    progress_pct = (batch_num / expected_batches * 100) if expected_batches > 0 else 0
                    actual_batches = batch_num

                    resumption_template = None
                    if sort_columns and last_processed_value:
                        resumption_template = generate_resumption_template(sql, sort_columns, last_processed_value)

                    logger.log_batch(
                        batch=batch_num,
                        rows_processed=row_count,
                        progress_pct=progress_pct,
                        mb_batch=mb_batch,
                        mb_total=mb_total,
                        last_processed_value=last_processed_value,
                        resumption_template=resumption_template,
                    )

                    print(
                        f"  Batch {batch_num}: {row_count:,} rows, {progress_pct:.1f}% complete, {mb_total:.2f} MB",
                        file=sys.stderr,
                    )

            while cursor.nextset():
                flush_messages()
            flush_messages()

            cursor.close()
            conn.close()

            print("[5/5] Writing output files...", file=sys.stderr)

        except Exception as e:
            exit_status = "error"
            logger.log_error(e)
            error_msg = f"  Error: {e}"
            print(error_msg, file=sys.stderr)
            print(error_msg)
            raise

        finally:
            logger.stop_timer_thread()

            runtime_seconds = time.time() - start_time
            logger.log_end(exit_status)
            log_entries = logger.get_log_entries()

            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            pyodbc_version = pyodbc.version
            driver_version = "ODBC Driver 18"

            mb_per_batch = mb_total / actual_batches if actual_batches > 0 else 0.0

            metadata = QueryMetadata(
                tool_type="query_runner",
                query_type=query_type,
                execution_timestamp=timestamp_readable,
                timestamp_iso8601=timestamp_iso,
                slug=slug,
                runtime_seconds=round(runtime_seconds, 2),
                row_count=row_count,
                exit_status=exit_status,
                connection_params={
                    "server": self.config["server"],
                    "database": self.config["database"],
                    "port": self.config.get("port", 1433),
                    "driver": "ODBC Driver 18 for SQL Server",
                    "timeout": self.config.get("timeout", 7200),
                    "username": "[REDACTED]",
                    "password": "[REDACTED]",
                },
                batch_size=self.BATCH_SIZE,
                expected_batches=expected_batches,
                actual_batches=actual_batches,
                mb_per_batch=round(mb_per_batch, 3),
                mb_total=round(mb_total, 3),
                sort_columns=sort_columns,
                last_processed_value=last_processed_value,
                has_phi=has_phi,
                python_version=python_version,
                pyodbc_version=pyodbc_version,
                driver_version=driver_version,
                arguments=arguments,
            )

            write_all_files(
                files=files,
                metadata=metadata,
                sql=sql,
                rows=all_rows,
                log_entries=log_entries,
                config=self.config,
            )

            print(f"Query completed: {exit_status}", file=sys.stderr)
            print(f"  Runtime: {runtime_seconds:.2f}s", file=sys.stderr)
            print(f"  Rows: {row_count:,}", file=sys.stderr)
            print("  Files created:", file=sys.stderr)
            for file_type, file_path in files.items():
                print(f"    {file_type}: {file_path}", file=sys.stderr)

        return {"files": files, "metadata": metadata, "exit_status": exit_status}


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Execute SQL query against database with paginated output")
    parser.add_argument("--sql", help="SQL query text")
    parser.add_argument("--sql-file", help="Path to SQL file")
    parser.add_argument(
        "--query-type",
        required=True,
        choices=["schema_info", "exploratory", "large_query"],
        help="Query type (determines timeout expectations)",
    )
    parser.add_argument("--slug", help="Filename slug (auto-generated if omitted)")
    parser.add_argument(
        "--environment",
        "-e",
        default="dev",
        choices=("dev", "qa", "prod"),
        help="Target environment (default: dev)",
    )
    parser.add_argument(
        "--has-phi",
        action="store_true",
        default=True,
        help="Query accesses PHI data (default: True)",
    )

    args = parser.parse_args()

    if args.sql:
        sql = args.sql
    elif args.sql_file:
        with open(args.sql_file, encoding="utf-8") as f:
            sql = f.read()
    else:
        print("Error: Must provide --sql or --sql-file", file=sys.stderr)
        sys.exit(2)

    runner = QueryRunner(args.environment)
    try:
        runner.execute_query(
            sql=sql,
            query_type=args.query_type,
            slug=args.slug,
            has_phi=args.has_phi,
            arguments=vars(args),
        )
        sys.exit(0)
    except Exception as e:
        print(f"Query execution failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
