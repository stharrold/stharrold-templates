# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""SQL utilities shared across pipeline, deployer, and validator."""

import re


def split_sql_batches(sql_content: str) -> list[str]:
    """Split SQL content into batches by GO statements.

    Args:
        sql_content: Raw SQL file content.

    Returns:
        List of non-empty, stripped SQL batches.
    """
    return [
        batch.strip()
        for batch in re.split(
            r"^\s*GO\s*$", sql_content, flags=re.MULTILINE | re.IGNORECASE
        )
        if batch.strip()
    ]
