# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Shared sample pool for reusing temp tables across pipeline phases.

Lazy-creating, per-asset temp table cache. Each sampling level (0.1%,
1%, 10%, etc.) is materialized once on first request, then reused by
all consumers (PK discovery, cardinality scan, frequency scan).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from data_catalog.services.sql_dialect import SQLDialect
from data_catalog.utils.sql_safety import validate_identifier

logger = logging.getLogger(__name__)


def select_seed_column(
    cursor: Any,
    dialect: SQLDialect,
    schema: str,
    table: str,
    columns: list[str],
) -> str:
    """Select a high-cardinality column for sampling.

    Uses a small sample to find the column with the most distinct values.
    """
    validate_identifier(schema)
    validate_identifier(table)
    try:
        test_cols = columns[:30]
        sql = dialect.seed_column_query(schema, table, test_cols)
        old_timeout = dialect.set_timeout(cursor, 300)
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
        finally:
            dialect.set_timeout(cursor, old_timeout)

        best_col, best_card = columns[0], 0
        for i, col in enumerate(test_cols):
            card = row[i] if row[i] is not None else 0
            if card > best_card:
                best_card = card
                best_col = col

        logger.info(f"  Pool seed column: {best_col} ({best_card} unique)")
        return best_col
    except Exception as e:
        logger.warning(f"  Pool seed selection failed: {e}")
        return columns[0]


class SamplePool:
    """Lazy-creating, per-asset temp table cache.

    Each sampling level is materialized once on first request, then
    reused by all consumers. Delegates SQL generation to the dialect.

    Args:
        cursor: Database cursor for source queries.
        dialect: SQL dialect for query generation.
        schema: Schema name.
        table: Table name.
        seed_col: Column for deterministic sampling.
    """

    def __init__(
        self,
        cursor: Any,
        dialect: SQLDialect,
        schema: str,
        table: str,
        seed_col: str,
    ) -> None:
        validate_identifier(schema)
        validate_identifier(table)
        validate_identifier(seed_col)
        self._cursor = cursor
        self._dialect = dialect
        self._schema = schema
        self._table = table
        self._seed_col = seed_col
        self._pool: dict[float, str] = {}
        self._row_counts: dict[float, int] = {}
        self._ts = int(time.time())

    @property
    def seed_col(self) -> str:
        return self._seed_col

    def get_sample(self, pct: float) -> str:
        """Get (or create) a temp table for the given sampling percentage."""
        key = 100.0 if pct >= 100 else pct

        if key in self._pool:
            logger.info(
                f"  Reusing temp {self._pool[key]} for {key}% "
                f"({self._row_counts.get(key, '?'):,} rows)"
            )
            return self._pool[key]

        # Materialize
        pct_tag = str(key).replace(".", "x")
        temp_name = f"#pool_{pct_tag}_{self._ts}"

        sql = self._dialect.create_sample_table(
            temp_name, self._schema, self._table, self._seed_col, key,
        )

        old_timeout = self._dialect.set_timeout(self._cursor, 600)
        try:
            t0 = time.time()
            self._cursor.execute(sql)
            ctas_elapsed = time.time() - t0
        finally:
            self._dialect.set_timeout(self._cursor, old_timeout)

        # Row count
        count_sql = f"SELECT COUNT(*) FROM {temp_name}"
        old_timeout = self._dialect.set_timeout(self._cursor, 300)
        try:
            self._cursor.execute(count_sql)
            row_count = self._cursor.fetchone()[0]
        finally:
            self._dialect.set_timeout(self._cursor, old_timeout)

        self._dialect.drain_cursor(self._cursor)

        logger.info(
            f"  Pool temp {temp_name} ready: "
            f"{row_count:,} rows in {ctas_elapsed:.1f}s"
        )

        self._pool[key] = temp_name
        self._row_counts[key] = row_count
        return temp_name

    def get_row_count(self, pct: float) -> int:
        key = 100.0 if pct >= 100 else pct
        return self._row_counts[key]

    def drop_all(self) -> None:
        """Drop all temp tables owned by this pool."""
        for pct, temp_name in list(self._pool.items()):
            try:
                self._cursor.execute(self._dialect.drop_temp_table(temp_name))
                self._dialect.drain_cursor(self._cursor)
            except Exception:
                pass
        self._pool.clear()
        self._row_counts.clear()
