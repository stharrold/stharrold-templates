# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""SQL safety utilities for preventing injection in dynamic SQL.

Source database queries use f-string interpolation for schema/table/column
names (most databases don't support parameterized identifiers). This module
validates those identifiers before interpolation.
"""

import re

# Valid identifier: letters, digits, underscores, spaces, parentheses
_IDENTIFIER_RE = re.compile(r"^[\w ()]+$")

# Qualified name: [Schema].[Table] or Schema.Table
_QUALIFIED_RE = re.compile(r"^\[?[\w ]+\]?\.\[?[\w ]+\]?$")


class UnsafeIdentifierError(ValueError):
    """Raised when a SQL identifier contains suspicious characters."""

    pass


def validate_identifier(name: str) -> str:
    """Validate a single SQL identifier (schema, table, or column name).

    Returns the validated identifier (unchanged).

    Raises:
        UnsafeIdentifierError: If the identifier contains invalid characters.
    """
    if not name or not _IDENTIFIER_RE.match(name):
        raise UnsafeIdentifierError(
            f"Unsafe SQL identifier: {name!r}. "
            "Only letters, digits, underscores, spaces, and parentheses "
            "are allowed."
        )
    return name


def validate_qualified_name(qualified_name: str) -> str:
    """Validate a qualified [Schema].[Table] name.

    Returns the validated qualified name (unchanged).

    Raises:
        UnsafeIdentifierError: If the name doesn't match expected pattern.
    """
    if not qualified_name or not _QUALIFIED_RE.match(qualified_name):
        raise UnsafeIdentifierError(
            f"Unsafe qualified name: {qualified_name!r}. "
            "Expected format: [Schema].[Table] or Schema.Table"
        )
    return qualified_name


def bracket_identifier(name: str) -> str:
    """Validate and bracket a SQL identifier, e.g. ``[MyTable]``."""
    validate_identifier(name)
    return f"[{name}]"


def bracket_qualified(schema: str, table: str) -> str:
    """Validate and bracket a schema.table pair, e.g. ``[dbo].[MyTable]``."""
    validate_identifier(schema)
    validate_identifier(table)
    return f"[{schema}].[{table}]"
