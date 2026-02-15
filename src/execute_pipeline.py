# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Pipeline Orchestrator - executes stored procedures in dependency order.

Produces auditable JSONL logs with YAML frontmatter.
Full pipeline execution mode with optional resumption.

Usage:
    uv run python -m src.execute_pipeline                    # Default: dev
    uv run python -m src.execute_pipeline --environment dev  # Explicit dev
    uv run python -m src.execute_pipeline --environment qa   # QA environment
    uv run python -m src.execute_pipeline --environment prod # Production
"""

import argparse
import json
import os
import sys
import tempfile
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyodbc
import yaml

from src.config_validator import validate_config_file
from src.query_types import ConfigDict
from src.resumption import filter_steps_for_resumption
from src.retry import retry_on_transient_error
from src.sql_utils import split_sql_batches

VALID_ENVIRONMENTS = ("dev", "qa", "prod")

# TODO: Customize -- set to your database password environment variable name
EDW_PASSWORD_ENV_VAR = "EDW_PASSWORD"


def load_config(environment: str = "dev") -> ConfigDict:
    """Load configuration from config.{environment}.json.

    Args:
        environment: One of 'dev', 'qa', 'prod'. Defaults to 'dev'.

    Returns:
        Configuration dictionary with server, database, username, etc.

    Raises:
        ValueError: If environment is not valid.
        FileNotFoundError: If config file does not exist.
    """
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError(f"Invalid environment '{environment}'. Must be one of: {', '.join(VALID_ENVIRONMENTS)}")

    config_path = Path(__file__).parent.parent / "config" / f"config.{environment}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}. Expected one of: config/config.dev.json, config/config.qa.json, config/config.prod.json")

    with open(config_path) as f:
        config: ConfigDict = json.load(f)

    validate_config_file(config)
    return config


def get_connection_string(config: ConfigDict) -> str:
    """Build connection string using password from environment.

    Expects secrets_run.py to have already injected the password
    environment variable before this function is called.
    """
    username = config["username"]
    password = os.environ[EDW_PASSWORD_ENV_VAR]  # TODO: Customize env var name above

    return config["connection_template"].format(
        server=config["server"],
        database=config["database"],
        username=username,
        password=password,
        timeout=config.get("timeout", 7200),
    )


@retry_on_transient_error(max_retries=3, base_delay=1.0, backoff_factor=5.0)
def connect_with_retry(conn_str: str) -> pyodbc.Connection:
    """Connect to database with retry on transient errors."""
    return pyodbc.connect(conn_str)


@retry_on_transient_error(max_retries=3, base_delay=1.0, backoff_factor=5.0)
def execute_batch_with_retry(cursor: pyodbc.Cursor, batch: str) -> None:
    """Execute a SQL batch with retry on transient errors."""
    cursor.execute(batch)


class PipelineRunner:
    """Encapsulates mutable pipeline state for a single execution run."""

    def __init__(self) -> None:
        self.current_step_number: int | None = None
        self.current_step_name: str | None = None
        self.log_entries: list[dict[str, Any]] = []

    def capture_cursor_messages(self, cursor: pyodbc.Cursor) -> None:
        """Capture SQL Server PRINT statements from cursor.messages."""
        if not cursor.messages:
            return

        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        for _message_class, message_text in cursor.messages:
            text = message_text.strip() if message_text else ""
            if not text:
                continue

            # Strip ODBC driver prefix (e.g. "[Microsoft][ODBC Driver 18 ...][SQL Server]")
            marker = "[SQL Server]"
            idx = text.find(marker)
            if idx >= 0:
                text = text[idx + len(marker) :].strip()

            if not text:
                continue

            # Try to parse as JSON (from PRINT statements in stored procedures)
            try:
                sql_output = json.loads(text)
                log_entry = {
                    "timestamp": now,
                    "event_type": "sql_print",
                    "step_number": self.current_step_number,
                    "step_name": self.current_step_name,
                    "sql_output": sql_output,
                }
            except json.JSONDecodeError:
                log_entry = {
                    "timestamp": now,
                    "event_type": "sql_message",
                    "step_number": self.current_step_number,
                    "step_name": self.current_step_name,
                    "message": text,
                }

            self.log_entries.append(log_entry)

        cursor.messages.clear()

    def execute_stored_procedure(
        self,
        connection: pyodbc.Connection,
        step_number: int,
        step_name: str,
        stored_procedure: str,
        sql_file: Path | None = None,
    ) -> dict[str, Any]:
        """Execute SQL file directly (not as stored procedure)."""
        self.current_step_number = step_number
        self.current_step_name = step_name

        start_time = datetime.now(UTC)

        # Log step start
        log_entry = {
            "timestamp": start_time.isoformat().replace("+00:00", "Z"),
            "event_type": "step_start",
            "step_number": step_number,
            "step_name": step_name,
            "sql_file": str(sql_file) if sql_file else None,
        }
        self.log_entries.append(log_entry)

        try:
            # Read SQL file and execute
            if sql_file and sql_file.exists():
                with open(sql_file, encoding="utf-8") as f:
                    sql_script = f.read()

                batches = split_sql_batches(sql_script)

                # Set autocommit mode for DDL operations
                connection.autocommit = True
                cursor = connection.cursor()
                total_rows_affected = 0

                for batch in batches:
                    if batch.strip():
                        execute_batch_with_retry(cursor, batch)
                        # Capture PRINT messages before consuming result sets
                        self.capture_cursor_messages(cursor)
                        # Consume all result sets
                        while cursor.nextset():
                            self.capture_cursor_messages(cursor)
                        if cursor.rowcount != -1:
                            total_rows_affected += cursor.rowcount

                # Restore autocommit = False
                connection.autocommit = False
            else:
                raise FileNotFoundError(f"SQL file not found: {sql_file}")

            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            # Log step complete
            log_entry = {
                "timestamp": end_time.isoformat().replace("+00:00", "Z"),
                "event_type": "step_complete",
                "step_number": step_number,
                "step_name": step_name,
                "sql_file": str(sql_file),
                "duration_seconds": round(duration, 3),
                "rows_affected": total_rows_affected,
                "status": "success",
            }
            self.log_entries.append(log_entry)

            return {"status": "success", "duration_seconds": duration}

        except pyodbc.Error as e:
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            # Log error (only catch database errors; let code bugs propagate)
            log_entry = {
                "timestamp": end_time.isoformat().replace("+00:00", "Z"),
                "event_type": "error",
                "step_number": step_number,
                "step_name": step_name,
                "sql_file": str(sql_file) if sql_file else None,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "duration_seconds": round(duration, 3),
                "status": "failed",
            }
            self.log_entries.append(log_entry)

            return {"status": "failed", "error": str(e)}

    def run(self, environment: str, resume_from_step: int | None = None) -> None:
        """Execute full pipeline."""
        execution_start = datetime.now(UTC)
        timestamp_iso8601 = execution_start.strftime("%Y%m%dT%H%M%SZ")

        execution_mode = "resumed" if resume_from_step else "full_pipeline"

        print(f"[ENV] Targeting environment: {environment.upper()}", file=sys.stderr)
        if resume_from_step:
            print(f"[ENV] Resuming from step {resume_from_step}", file=sys.stderr)

        # Load pipeline configuration
        pipeline_config = load_pipeline_config()
        pipeline_name = pipeline_config["pipeline_name"]
        total_steps = pipeline_config["total_steps"]

        # Initialize log
        self.log_entries = []
        self.log_entries.append(
            {
                "timestamp": execution_start.isoformat().replace("+00:00", "Z"),
                "event_type": "pipeline_start",
                "pipeline_name": pipeline_name,
                "environment": environment,
                "total_steps": total_steps,
                "execution_mode": execution_mode,
                "resume_from_step": resume_from_step,
            }
        )

        # Load config for specified environment
        config = load_config(environment)
        conn_str = get_connection_string(config)

        print(f"[ENV] Server: {config['server']}", file=sys.stderr)

        # Connect to database
        connection = connect_with_retry(conn_str)

        successful_steps = 0
        failed_steps = 0
        step_durations: list[float] = []

        try:
            # Load pipeline steps from config
            project_root = Path(__file__).parent.parent
            steps = pipeline_config["steps"]

            # Apply resumption filter if requested
            if resume_from_step is not None:
                steps = filter_steps_for_resumption(steps, resume_from_step)

            steps_total = len(steps)

            # Execute each step
            for step_idx, step_config in enumerate(steps):
                step_number = step_config["step_number"]
                step_name = step_config["step_name"]
                step_type = step_config["type"]

                print(f"[{step_number}/{total_steps}] {step_name}...", file=sys.stderr)

                # Handle SQL steps
                if step_type == "sql":
                    stored_procedure = step_config["stored_procedure"]
                    sql_file_path = project_root / step_config["sql_file"]
                    result = self.execute_stored_procedure(connection, step_number, step_name, stored_procedure, sql_file_path)
                else:
                    raise ValueError(f"Unknown step type: {step_type}")

                if result["status"] == "success":
                    successful_steps += 1
                    step_dur = result["duration_seconds"]
                    step_durations.append(step_dur)

                    # Calculate ETA
                    remaining = steps_total - (step_idx + 1)
                    if remaining > 0 and step_durations:
                        avg_dur = sum(step_durations) / len(step_durations)
                        eta_min = (avg_dur * remaining) / 60.0
                        print(
                            f"  [OK] Complete ({step_dur:.1f}s) | ETA: ~{eta_min:.1f}min ({remaining} steps remaining)",
                            file=sys.stderr,
                        )
                    else:
                        print(f"  [OK] Complete ({step_dur:.1f}s)", file=sys.stderr)
                else:
                    failed_steps += 1
                    print(f"  [FAILED] {result.get('error', 'Unknown error')}", file=sys.stderr)
                    break  # Stop on first failure (full pipeline mode)

            # Run smoke tests if no step failures
            smoke_tests = pipeline_config.get("smoke_tests", [])
            if failed_steps == 0 and smoke_tests:
                print(f"\n[SMOKE] Running {len(smoke_tests)} smoke tests...", file=sys.stderr)
                smoke_results = execute_smoke_tests(connection, smoke_tests)

                smoke_failures = [r for r in smoke_results if not r["passed"]]
                if smoke_failures:
                    failed_steps += len(smoke_failures)
                    print(f"[SMOKE] {len(smoke_failures)} smoke test(s) failed", file=sys.stderr)

                self.log_entries.append(
                    {
                        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "event_type": "smoke_tests",
                        "results": smoke_results,
                        "passed": len(smoke_failures) == 0,
                    }
                )

        except Exception as e:
            print(f"Pipeline error: {e}", file=sys.stderr)
            traceback.print_exc()
            failed_steps += 1

        finally:
            connection.close()

            execution_end = datetime.now(UTC)
            total_duration = (execution_end - execution_start).total_seconds()

            print(f"\n[TIME] Total elapsed: {total_duration / 60.0:.1f}min", file=sys.stderr)

            # Determine exit status
            exit_status = "success" if failed_steps == 0 else "error"

            # Log pipeline complete
            self.log_entries.append(
                {
                    "timestamp": execution_end.isoformat().replace("+00:00", "Z"),
                    "event_type": "pipeline_complete",
                    "pipeline_name": pipeline_name,
                    "total_steps": total_steps,
                    "successful_steps": successful_steps,
                    "failed_steps": failed_steps,
                    "total_duration_seconds": round(total_duration, 3),
                    "exit_status": exit_status,
                }
            )

            # Build metadata for YAML frontmatter
            metadata = {
                "pipeline_name": pipeline_name,
                "environment": environment,
                "execution_timestamp": execution_start.isoformat().replace("+00:00", "Z"),
                "timestamp_iso8601": timestamp_iso8601,
                "runtime_seconds": round(total_duration, 3),
                "exit_status": exit_status,
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "failed_steps": failed_steps,
                "connection_params": {
                    "server": config["server"],
                    "database": config["database"],
                    "username": "[REDACTED]",
                    "password": "[REDACTED]",
                    "timeout": config["timeout"],
                },
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "pyodbc_version": pyodbc.version,
                "has_phi": True,
                "execution_mode": execution_mode,
                "resume_from_step": resume_from_step,
            }

            # Write log file
            output_dir = Path(__file__).parent.parent / "outputs"
            output_dir.mkdir(exist_ok=True)

            # TODO: Customize -- update pipeline slug in log filename
            log_path = output_dir / f"{timestamp_iso8601}_pipeline_{environment}.jsonl"
            write_log_file(metadata, log_path, self.log_entries)

            print(f"\n[OK] Log written to: {log_path}", file=sys.stderr)

            if failed_steps > 0:
                sys.exit(1)


def write_log_file(metadata: dict[str, Any], output_path: Path, log_entries: list[dict[str, Any]]) -> None:
    """Write JSONL log file with YAML frontmatter."""
    # Write to temp file first (atomic write pattern)
    temp_fd, temp_path = tempfile.mkstemp(dir=output_path.parent, suffix=".tmp")

    try:
        with open(temp_fd, "w", encoding="utf-8") as f:
            # Write YAML frontmatter
            f.write("---\n")
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
            f.write("---\n")

            # Write JSONL entries
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

        # Atomic rename
        Path(temp_path).replace(output_path)

    except Exception:
        # Clean up temp file on error
        Path(temp_path).unlink(missing_ok=True)
        raise


def execute_smoke_tests(connection: pyodbc.Connection, smoke_tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run smoke tests (row count checks) against pipeline views.

    Args:
        connection: Active database connection.
        smoke_tests: List of smoke test configs from pipeline_config.json.

    Returns:
        List of result dicts with name, expected, actual, passed.
    """
    results: list[dict[str, Any]] = []

    for test in smoke_tests:
        name = test["name"]
        schema = test["schema"]
        table = test["table"]
        min_rows = test["min_rows"]

        try:
            cursor = connection.cursor()
            sql = test.get("sql", f"SELECT COUNT(*) FROM [{schema}].[{table}]")
            cursor.execute(sql)
            row = cursor.fetchone()
            actual = row[0] if row else 0

            passed = actual >= min_rows
            results.append(
                {
                    "name": name,
                    "table": f"[{schema}].[{table}]",
                    "min_rows": min_rows,
                    "actual_rows": actual,
                    "passed": passed,
                }
            )

            status = "[OK]" if passed else "[FAIL]"
            print(
                f"  {status} {name}: {actual:,} rows (min: {min_rows:,})",
                file=sys.stderr,
            )

        except Exception as e:
            results.append(
                {
                    "name": name,
                    "table": f"[{schema}].[{table}]",
                    "min_rows": min_rows,
                    "actual_rows": -1,
                    "passed": False,
                    "error": str(e),
                    "sql": sql,
                }
            )
            print(f"  [FAIL] {name}: {e} (sql: {sql})", file=sys.stderr)

    return results


def load_pipeline_config() -> dict[str, Any]:
    """Load pipeline configuration from pipeline_config.json.

    Returns:
        Dictionary containing pipeline_name, total_steps, and list of step configs.
    """
    config_path = Path(__file__).parent.parent / "pipeline_config.json"
    with open(config_path) as f:
        result: dict[str, Any] = json.load(f)
        return result


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Execute pipeline against specified environment.")
    parser.add_argument("--environment", "-e", type=str, choices=VALID_ENVIRONMENTS, default="dev", help="Target environment: dev (default), qa, or prod")
    parser.add_argument("--resume-from-step", type=int, default=None, help="Resume pipeline from this step number (inclusive)")
    return parser.parse_args()


def main() -> None:
    """Execute full pipeline."""
    args = parse_args()
    runner = PipelineRunner()
    runner.run(args.environment, args.resume_from_step)


if __name__ == "__main__":
    main()
