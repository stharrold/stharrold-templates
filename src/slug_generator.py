# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Slug generation following git workflow branch naming convention."""

import re


def create_slug(description: str) -> str:
    """Generate slug from description (same as git workflow branch naming).

    Algorithm:
    1. Convert to lowercase
    2. Remove special characters (keep alphanumeric and hyphens)
    3. Replace whitespace/underscores with hyphens
    4. Strip leading/trailing hyphens
    5. Truncate to 50 characters

    Examples:
        "Get Patient Demographics" -> "get-patient-demographics"
        "TOP 1000 Active Patients" -> "top-1000-active-patients"
    """
    if not description:
        return "query"

    slug = description.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")

    return slug[:50] if slug else "query"


def extract_slug_from_sql(sql: str) -> str | None:
    """Extract slug from SQL comment or table name.

    Priority:
    1. SQL comment: -- Query: Get Patient Demographics
    2. Table name: SELECT ... FROM Patients ...
    """
    comment_match = re.search(r"--\s*Query:\s*(.+?)(\n|$)", sql, re.IGNORECASE)
    if comment_match:
        return create_slug(comment_match.group(1))

    table_match = re.search(r"\bFROM\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)", sql, re.IGNORECASE)
    if table_match:
        table_name = table_match.group(2) or table_match.group(1)
        return create_slug(table_name)

    return None
