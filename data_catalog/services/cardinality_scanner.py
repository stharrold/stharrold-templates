# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Cardinality scanner for column frequency analysis.

Scans column cardinality at progressive sample levels and stores top-N
value frequencies per column. Used for FK candidate identification and
data profiling.
"""
from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from data_catalog.db.models import Asset, ColumnCardinalityHistory, ColumnValueFrequency
from data_catalog.db.repositories import AssetRepository
from data_catalog.services.sql_dialect import SQLDialect

logger = logging.getLogger(__name__)

FREQ_BATCH_SIZE = 50  # Max columns per UNPIVOT query


class CardinalityScanner:
    """Scans and stores column cardinality at progressive sample levels.

    Uses dialect-generated SQL for all source database queries.
    Supports batched UNPIVOT for wide tables and per-column fallback
    when UNPIVOT returns no data.
    """

    def __init__(
        self,
        db: Session,
        source_cursor: Any,
        dialect: SQLDialect,
        sample_pool=None,
    ):
        self.db = db
        self.cursor = source_cursor
        self.dialect = dialect
        self.repo = AssetRepository(db)
        self._sample_pool = sample_pool

    def _create_temp_table(
        self,
        schema: str,
        table: str,
        sample_pct: float,
        seed_col: str,
        suffix: str = "",
    ) -> str:
        """Create a sample temp table, delegating to pool or dialect."""
        if self._sample_pool is not None:
            return self._sample_pool.get_sample(sample_pct)

        temp_name = f"#card_{suffix}_{int(time.time())}"
        old_autocommit = self.cursor.connection.autocommit
        try:
            self.cursor.connection.autocommit = True
            sql = self.dialect.create_sample_table(
                temp_name, schema, table, seed_col, sample_pct
            )
            old_timeout = self.dialect.set_timeout(self.cursor, 600)
            try:
                t0 = time.time()
                self.cursor.execute(sql)
                elapsed = time.time() - t0
            finally:
                self.dialect.set_timeout(self.cursor, old_timeout)
            self.dialect.drain_cursor(self.cursor)

            # Count rows for logging
            old_timeout = self.dialect.set_timeout(self.cursor, 300)
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {temp_name}")
                row_count = self.cursor.fetchone()[0]
            finally:
                self.dialect.set_timeout(self.cursor, old_timeout)
            self.dialect.drain_cursor(self.cursor)

            logger.info(
                f"  Temp table {temp_name} ready: "
                f"{row_count:,} rows in {elapsed:.1f}s"
            )
        finally:
            self.cursor.connection.autocommit = old_autocommit
        return temp_name

    def _drop_temp_table(self, temp_name: str | None) -> None:
        """Drop temp table. No-op when pool manages lifecycle."""
        if not temp_name or self._sample_pool is not None:
            return
        try:
            old_autocommit = self.cursor.connection.autocommit
            try:
                self.cursor.connection.autocommit = True
                self.cursor.execute(self.dialect.drop_temp_table(temp_name))
                self.dialect.drain_cursor(self.cursor)
            finally:
                self.cursor.connection.autocommit = old_autocommit
        except Exception:
            pass

    def _get_fk_candidate_columns(
        self, asset: Asset
    ) -> list[dict[str, Any]]:
        """Get columns suitable for frequency scanning.

        Filters to columns with selectivity between 0.01% and 100%
        (excludes constants and unique-per-row columns).
        """
        columns = (asset.schema_metadata or {}).get("columns", [])
        if not columns:
            return []

        # If cardinality data exists, filter by selectivity
        cardinality = self.db.query(ColumnCardinalityHistory).filter(
            ColumnCardinalityHistory.table_schema == asset.table_schema,
            ColumnCardinalityHistory.table_name == asset.table_name,
        ).all()

        if not cardinality:
            return columns  # No cardinality data, return all

        card_map = {c.column_name: c for c in cardinality}
        candidates = []
        for col in columns:
            card = card_map.get(col["name"])
            if not card:
                candidates.append(col)
                continue
            # Use best available selectivity
            sel = None
            for attr in [
                "selectivity_at_10pct",
                "selectivity_at_1pct",
                "selectivity_at_100pct",
            ]:
                val = getattr(card, attr, None)
                if val is not None:
                    sel = float(val)
                    break
            if sel is None or (0.01 <= sel <= 100):
                candidates.append(col)
        return candidates

    def scan_frequencies(
        self,
        asset: Asset,
        schema: str,
        table: str,
        sample_pct: float = 10.0,
        top_n: int = 100,
        seed_col: str | None = None,
        progress_callback: Callable | None = None,
    ) -> dict[str, Any]:
        """Scan value frequencies for all FK-candidate columns.

        Uses batched UNPIVOT (dialect.unpivot_frequency_query) with
        FREQ_BATCH_SIZE columns per batch. Falls back to per-column
        GROUP BY when UNPIVOT returns 0 rows.

        Returns:
            Dict with columns_scanned, frequencies stored, errors.
        """
        candidates = self._get_fk_candidate_columns(asset)
        if not candidates:
            return {"columns_scanned": 0, "error": "No candidate columns"}

        col_names = [c["name"] for c in candidates]

        # Create or reuse sample temp table
        if not seed_col and col_names:
            seed_col = col_names[0]
        temp_name = self._create_temp_table(
            schema, table, sample_pct, seed_col or col_names[0]
        )

        all_freqs: dict[str, list] = {c: [] for c in col_names}
        errors = []

        try:
            # Batched UNPIVOT scan
            for batch_start in range(0, len(col_names), FREQ_BATCH_SIZE):
                batch_cols = col_names[batch_start:batch_start + FREQ_BATCH_SIZE]
                try:
                    sql = self.dialect.unpivot_frequency_query(
                        temp_name, batch_cols, top_n
                    )
                    old_timeout = self.dialect.set_timeout(self.cursor, 300)
                    try:
                        self.cursor.execute(sql)
                        rows = self.cursor.fetchall()
                    finally:
                        self.dialect.set_timeout(self.cursor, old_timeout)

                    for row in rows:
                        col_name, value, freq = row[0], row[1], row[2]
                        if col_name in all_freqs:
                            all_freqs[col_name].append((value, freq))
                except Exception as e:
                    logger.warning(f"  UNPIVOT batch failed: {e}")
                    errors.append(str(e))

            # Per-column fallback for columns with 0 UNPIVOT rows
            empty_cols = [c for c in col_names if not all_freqs[c]]
            if empty_cols:
                logger.info(
                    f"  Per-column fallback for {len(empty_cols)} columns"
                )
                for col in empty_cols:
                    try:
                        sql = self.dialect.frequency_query(
                            temp_name, col, top_n
                        )
                        old_timeout = self.dialect.set_timeout(self.cursor, 300)
                        try:
                            self.cursor.execute(sql)
                            rows = self.cursor.fetchall()
                        finally:
                            self.dialect.set_timeout(self.cursor, old_timeout)

                        for row in rows:
                            all_freqs[col].append((row[0], row[1]))
                    except Exception as e:
                        logger.warning(f"  Per-column scan failed for {col}: {e}")
                        errors.append(f"{col}: {e}")

            # Store frequencies
            stored = 0
            for col_name, freqs in all_freqs.items():
                if not freqs:
                    # Store sentinel for all-NULL columns
                    freq_record = ColumnValueFrequency(
                        id=str(uuid4()),
                        table_schema=schema,
                        table_name=table,
                        column_name=col_name,
                        rank=0,
                        value=None,
                        frequency=0,
                        sample_pct=sample_pct,
                    )
                    self.db.add(freq_record)
                    stored += 1
                    continue

                for rank, (value, freq) in enumerate(freqs, 1):
                    freq_record = ColumnValueFrequency(
                        id=str(uuid4()),
                        table_schema=schema,
                        table_name=table,
                        column_name=col_name,
                        rank=rank,
                        value=str(value) if value is not None else None,
                        frequency=int(freq),
                        sample_pct=sample_pct,
                    )
                    self.db.add(freq_record)
                    stored += 1

            self.db.commit()

        finally:
            self._drop_temp_table(temp_name)

        return {
            "columns_scanned": len(col_names),
            "frequencies_stored": stored,
            "errors": errors,
        }

    def scan_view(
        self,
        qualified_name: str,
        progress_callback: Callable[[str, dict], None] | None = None,
    ) -> dict[str, Any]:
        """Scan all columns for a single asset."""
        asset = self.repo.find_by_qualified_name(qualified_name)
        if not asset:
            return {"error": f"Asset not found: {qualified_name}"}

        match = re.match(r"\[([^\]]+)\]\.\[([^\]]+)\]", qualified_name)
        if not match:
            return {"error": f"Invalid qualified name: {qualified_name}"}

        schema, table = match.group(1), match.group(2)
        return self.scan_frequencies(asset, schema, table)

    def scan_schema(
        self,
        schema_pattern: str,
        progress_callback: Callable[[str, dict], None] | None = None,
    ) -> dict[str, Any]:
        """Scan all assets in a schema pattern."""
        assets = self.repo.find_by_schema_pattern(schema_pattern)
        if not assets:
            return {"error": f"No assets found for: {schema_pattern}"}

        results = []
        for i, asset in enumerate(assets, 1):
            if progress_callback:
                progress_callback("asset", {
                    "asset": asset.qualified_name,
                    "current": i,
                    "total": len(assets),
                })
            result = self.scan_view(asset.qualified_name, progress_callback)
            results.append(result)

        return {
            "schema_pattern": schema_pattern,
            "assets_scanned": len(results),
            "total_columns": sum(
                r.get("columns_scanned", 0) for r in results
            ),
            "errors": [
                e for r in results
                for e in (
                    r.get("errors", []) + ([r["error"]] if "error" in r else [])
                )
            ],
        }
