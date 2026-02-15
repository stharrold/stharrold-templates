# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Resumption logic for both row-level queries and step-level pipelines.

Row-level: Generate WHERE-clause resumption templates for failed queries.
Step-level: Filter pipeline steps for resumption from a given step number.
"""

from __future__ import annotations

import re
from typing import Any

# Valid SQL column name: starts with letter/underscore, contains only alphanumerics/underscores
VALID_COLUMN_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# ---------------------------------------------------------------------------
# Row-level resumption
# ---------------------------------------------------------------------------


def generate_resumption_template(
    sql: str, sort_columns: list[str], last_values: dict[str, Any]
) -> str:
    """Generate resumption SQL template with WHERE clause.

    Creates a new SQL query that will resume from where the previous query
    left off, based on the ORDER BY columns and their last processed values.

    Examples:
        Single column ORDER BY:
            WHERE PatientID > '12345'

        Multi-column ORDER BY:
            WHERE EncounterDate > '2025-11-18'
               OR (EncounterDate = '2025-11-18' AND PatientID > '12345')
    """
    if not sort_columns or not last_values:
        return sql

    for col in sort_columns:
        _validate_column_name(col)

    where_conditions = []

    if len(sort_columns) == 1:
        col = sort_columns[0]
        value = last_values.get(col, "")
        quoted_value = _quote_value(value)
        where_conditions.append(f"{col} > {quoted_value}")

    else:
        for i, col in enumerate(sort_columns):
            value = last_values.get(col, "")
            quoted_value = _quote_value(value)

            if i == 0:
                where_conditions.append(f"{col} > {quoted_value}")
            else:
                and_conditions = []
                for prev_idx in range(i):
                    prev_col = sort_columns[prev_idx]
                    prev_value = last_values.get(prev_col, "")
                    prev_quoted = _quote_value(prev_value)
                    and_conditions.append(f"{prev_col} = {prev_quoted}")

                and_conditions.append(f"{col} > {quoted_value}")
                where_conditions.append(f"({' AND '.join(and_conditions)})")

    where_clause = " OR ".join(where_conditions)
    return _insert_where_clause(sql, where_clause)


def _validate_column_name(name: str) -> None:
    """Validate that a column name is safe for SQL interpolation."""
    if not VALID_COLUMN_PATTERN.match(name):
        raise ValueError(
            f"Invalid column name '{name}': must contain only letters, digits, and underscores, "
            f"and must start with a letter or underscore"
        )


def _quote_value(value: Any) -> str:
    """Quote a value appropriately for SQL."""
    if value is None:
        return "NULL"
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"


def _insert_where_clause(sql: str, where_clause: str) -> str:
    """Insert WHERE clause into SQL query."""
    from_match = re.search(r"\bFROM\b", sql, re.IGNORECASE)
    order_by_match = re.search(r"\bORDER\s+BY\b", sql, re.IGNORECASE)

    if not from_match or not order_by_match:
        return sql

    from_pos = from_match.start()
    order_by_pos = order_by_match.start()

    middle_section = sql[from_pos:order_by_pos]
    existing_where = re.search(r"\bWHERE\b", middle_section, re.IGNORECASE)

    if existing_where:
        new_sql = sql[:order_by_pos].rstrip() + f"\n  AND ({where_clause})\n" + sql[order_by_pos:]
    else:
        new_sql = sql[:order_by_pos].rstrip() + f"\nWHERE {where_clause}\n" + sql[order_by_pos:]

    return new_sql


def extract_resumption_info(log_entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract resumption information from log entries.

    Returns the last batch's resumption template and values.
    """
    for entry in reversed(log_entries):
        if entry.get("type") == "batch":
            return {
                "last_processed_value": entry.get("last_processed_value", {}),
                "resumption_template": entry.get("resumption_template", ""),
                "batch": entry.get("batch", 0),
                "rows_processed": entry.get("rows_processed", 0),
            }

    return {"last_processed_value": {}, "resumption_template": "", "batch": 0, "rows_processed": 0}


# ---------------------------------------------------------------------------
# Step-level pipeline resumption
# ---------------------------------------------------------------------------


def filter_steps_for_resumption(
    steps: list[dict[str, Any]], resume_from_step: int
) -> list[dict[str, Any]]:
    """Filter pipeline steps to resume from a given step number.

    Args:
        steps: Full list of pipeline step configurations.
        resume_from_step: Step number to resume from (inclusive).

    Returns:
        Filtered list of steps starting from resume_from_step.

    Raises:
        ValueError: If resume_from_step is not a valid step number.
    """
    step_numbers = [s["step_number"] for s in steps]
    if resume_from_step not in step_numbers:
        raise ValueError(
            f"Invalid resume step {resume_from_step}. "
            f"Valid steps: {step_numbers}"
        )

    return [s for s in steps if s["step_number"] >= resume_from_step]


def get_last_completed_step(log_entries: list[dict[str, Any]]) -> int | None:
    """Get the last successfully completed step number from log entries.

    Scans log entries for step_complete events and returns the highest
    step number with status=success.
    """
    last_step: int | None = None

    for entry in log_entries:
        if (
            entry.get("event_type") == "step_complete"
            and entry.get("status") == "success"
        ):
            step_num = entry.get("step_number")
            if step_num is not None:
                if last_step is None or step_num > last_step:
                    last_step = step_num

    return last_step
