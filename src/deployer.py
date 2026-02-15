# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""SQL Deployment module for handling scripts with GO separators.

Standalone tool for deploying individual SQL files to the database.
Uses load_config(environment) and EDW_PASSWORD env var for connection.

Usage:
    uv run python -m src.deployer sql/v1/example_view.sql --environment dev
"""

import argparse
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyodbc

from .execute_pipeline import get_connection_string, load_config
from .file_writer import write_log_jsonl
from .query_types import DeployMetadata, ExitStatus
from .retry import retry_on_transient_error
from .sql_utils import split_sql_batches


class Deployer:
    """Handles deployment of SQL scripts containing GO separators."""

    def __init__(self, environment: str = "dev"):
        """Initialize deployer with environment config."""
        self.config = load_config(environment)
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)

    @retry_on_transient_error(max_retries=3, base_delay=1.0, backoff_factor=5.0)
    def get_connection(self) -> pyodbc.Connection:
        """Get database connection."""
        conn_str = get_connection_string(self.config)
        return pyodbc.connect(conn_str, autocommit=True)

    @staticmethod
    def parse_batches(sql_content: str) -> list[str]:
        """Split SQL content by GO separators."""
        return split_sql_batches(sql_content)

    def deploy_file(self, file_path: str, arguments: dict[str, Any] | None = None) -> None:
        """Read and execute a SQL file batch by batch."""
        start_time = time.time()
        print(f"Deploying {file_path}...")

        if arguments is None:
            arguments = {}

        log_entries: list[dict[str, Any]] = []
        exit_status: ExitStatus = "success"
        batches_processed = 0
        batch_count = 0

        path_obj = Path(file_path)
        slug = path_obj.stem
        timestamp_iso = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            batches = self.parse_batches(content)
            batch_count = len(batches)
            print(f"Found {batch_count} batches.")

            conn = self.get_connection()
            cursor = conn.cursor()

            def flush_messages(cursor: pyodbc.Cursor) -> list[str]:
                """Flush SQL Server PRINT/RAISERROR messages from cursor."""
                messages: list[str] = []
                if hasattr(cursor, "messages") and cursor.messages:
                    for msg in cursor.messages:
                        msg_text = msg[1] if len(msg) > 1 else str(msg)
                        messages.append(msg_text)
                        print(msg_text, file=sys.stderr)
                    cursor.messages.clear()
                return messages

            for i, batch in enumerate(batches, 1):
                print(f"  Executing batch {i}/{batch_count}...", end='', flush=True)
                batch_start = time.time()
                try:
                    cursor.execute(batch)
                    flush_messages(cursor)

                    while cursor.nextset():
                        flush_messages(cursor)
                    flush_messages(cursor)

                    duration = time.time() - batch_start
                    print(" Done.")

                    log_entries.append({
                        "batch": i,
                        "status": "success",
                        "duration_seconds": round(duration, 3),
                        "sql_snippet": batch[:100] + "..." if len(batch) > 100 else batch
                    })
                    batches_processed += 1

                except pyodbc.Error as e:
                    print(f"\nError in batch {i}:")
                    print(e)
                    log_entries.append({
                        "batch": i,
                        "status": "error",
                        "error": str(e),
                        "sql_snippet": batch[:100]
                    })
                    exit_status = "error"
                    raise

            conn.close()
            print(f"Successfully deployed {file_path}")

        except Exception as e:
            exit_status = "error"
            error_msg = f"\nDeployment Error: {e}"
            print(error_msg, file=sys.stderr)
            print(error_msg)
            log_entries.append({"error": str(e)})

        finally:
            runtime = time.time() - start_time

            metadata = DeployMetadata(
                tool_type="deployer",
                execution_timestamp=datetime.now(UTC).isoformat(),
                timestamp_iso8601=timestamp_iso,
                slug=slug,
                runtime_seconds=round(runtime, 2),
                exit_status=exit_status,
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                file_path=file_path,
                batch_count=batch_count,
                batches_processed=batches_processed,
                connection_params={
                    "server": self.config.get("server"),
                    "database": self.config.get("database"),
                    "driver": "ODBC Driver 18 for SQL Server",
                },
                driver_version="ODBC Driver 18",
                pyodbc_version=pyodbc.version,
                arguments=arguments,
            )

            log_path = self.output_dir / f"{timestamp_iso}_deploy_log_{slug}.jsonl"
            try:
                write_log_jsonl(log_path, metadata, log_entries)
                print(f"  Log written to: {log_path}")
            except Exception as e:
                exit_status = "error"
                print(f"Failed to write log: {e}", file=sys.stderr)

            if exit_status == "error":
                sys.exit(1)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Deploy SQL scripts with GO separators")
    parser.add_argument("file", help="Path to SQL file to deploy")
    parser.add_argument(
        "--environment", "-e",
        default="dev",
        choices=("dev", "qa", "prod"),
        help="Target environment (default: dev)",
    )

    args = parser.parse_args()

    deployer = Deployer(args.environment)
    deployer.deploy_file(args.file, arguments=vars(args))


if __name__ == "__main__":
    main()
