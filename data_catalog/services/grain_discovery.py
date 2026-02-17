# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Grain discovery service for primary key detection.

Discovers primary keys (grain) in database tables/views using:
- Manual overrides from configuration file
- Pattern-based detection (fast, for common naming conventions)
- Progressive 7-step scanning (thorough, for large tables)
- Iterative accumulation fallback (for extract-partitioned tables)
- Functional dependency minimization (removes FD-redundant columns)

The service delegates all SQL generation to a ``SQLDialect`` instance,
making it portable across database engines.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from data_catalog.db.repositories import AssetRepository
from data_catalog.models.data_model import GrainResult
from data_catalog.services.sql_dialect import SQLDialect
from data_catalog.utils.sql_safety import validate_identifier, validate_qualified_name

logger = logging.getLogger(__name__)

# Threshold for using progressive scanning vs pattern-only
PROGRESSIVE_SCAN_THRESHOLD = 10_000_000  # 10 million rows


class GrainDiscoveryService:
    """Service for discovering and managing grain (primary keys).

    Provides:
    - Automatic grain discovery using pattern-based detection
    - Progressive scanning for large tables
    - Iterative accumulation for extract-partitioned tables
    - Manual override support from configuration
    - Catalog synchronization for persisting results
    - FD minimization for composite PKs
    """

    DEFAULT_CONFIG_PATH = Path("config/primary_keys_config.json")
    DEFAULT_SAMPLE_SIZE = 10000
    UNIQUENESS_THRESHOLD = 99.99

    def __init__(
        self,
        db_session: Session,
        source_cursor: Any,
        dialect: SQLDialect | None = None,
        config_path: Path | None = None,
        sample_pool=None,
    ) -> None:
        """Initialize the grain discovery service.

        Args:
            db_session: SQLAlchemy session for catalog database.
            source_cursor: Database cursor for source queries.
            dialect: SQL dialect for query generation.
            config_path: Path to primary_keys_config.json.
            sample_pool: Optional SamplePool for shared temp tables.
        """
        self.db = db_session
        self.cursor = source_cursor
        self.dialect = dialect
        self.repo = AssetRepository(db_session)
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: dict[str, Any] | None = None
        self._sample_pool = sample_pool

    @property
    def config(self) -> dict[str, Any]:
        """Lazy-load configuration."""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> dict[str, Any]:
        """Load primary keys configuration file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {"primary_keys": {}, "no_natural_pk": []}

    def _save_config(self) -> None:
        """Save configuration back to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def _is_no_natural_pk(self, qualified_name: str) -> bool:
        """Check if asset is designated as having no natural PK."""
        return qualified_name in self.config.get("no_natural_pk", [])

    def _get_config_pk(self, qualified_name: str) -> list[str] | None:
        """Get PK from configuration if available."""
        pk_config = self.config.get("primary_keys", {}).get(qualified_name)
        if pk_config:
            return pk_config.get("columns", [])
        return None

    def _parse_qualified_name(self, qualified_name: str) -> tuple[str, str]:
        """Parse [Schema].[Table] into (schema, table)."""
        match = re.match(r"\[([^\]]+)\]\.\[([^\]]+)\]", qualified_name)
        if not match:
            raise ValueError(f"Invalid qualified name: {qualified_name}")
        return match.group(1), match.group(2)

    def _get_asset_columns(self, qualified_name: str) -> list[dict]:
        """Get columns from asset metadata or source database."""
        asset = self.repo.find_by_qualified_name(qualified_name)
        if asset and asset.schema_metadata:
            columns = asset.schema_metadata.get("columns", [])
            if columns:
                return columns

        # Fall back to source DB query
        if self.cursor and self.dialect:
            schema, table = self._parse_qualified_name(qualified_name)
            sql = self.dialect.column_metadata_query(schema, table)
            self.cursor.execute(sql)
            return [
                {"name": row[0], "data_type": row[1], "ordinal_position": row[2]}
                for row in self.cursor.fetchall()
            ]
        return []

    def _get_row_count(self, schema: str, table: str) -> int | None:
        """Get row count from source database."""
        if not self.cursor or not self.dialect:
            return None
        try:
            sql = self.dialect.row_count_query(schema, table)
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.warning(f"Row count failed for [{schema}].[{table}]: {e}")
            return None

    def _test_uniqueness(
        self,
        schema: str,
        table: str,
        columns: list[str],
        sample_pct: float = 1.0,
    ) -> float:
        """Test selectivity of a column combination on source database.

        Returns selectivity percentage (100.0 = unique).
        """
        if not self.cursor or not self.dialect:
            return 0.0

        # Use sample pool if available, otherwise query source directly
        source = f"[{schema}].[{table}]"
        if self._sample_pool:
            source = self._sample_pool.get_sample(sample_pct)

        sql = self.dialect.count_distinct(source, columns=[], composites=[columns])
        try:
            old_timeout = self.dialect.set_timeout(self.cursor, 600)
            try:
                self.cursor.execute(sql)
                row = self.cursor.fetchone()
            finally:
                self.dialect.set_timeout(self.cursor, old_timeout)

            if not row:
                return 0.0

            total = row[0]  # _row_count
            distinct = row[1]  # comp_0
            if total == 0:
                return 0.0
            return (distinct / total) * 100.0
        except Exception as e:
            logger.warning(f"Uniqueness test failed: {e}")
            return 0.0

    def _pattern_based_discovery(
        self, qualified_name: str, columns: list[dict]
    ) -> GrainResult | None:
        """Try pattern-based PK detection.

        Looks for common naming patterns:
        - Single column ending in 'ID' or 'Key'
        - Table name + 'ID' pattern
        - Known composite key patterns
        """
        col_names = [c["name"] for c in columns]

        # Pattern 1: Single column named exactly <TableName>ID
        schema, table = self._parse_qualified_name(qualified_name)
        for suffix in ["ID", "Id", "_ID", "_id", "Key", "_Key"]:
            candidate = table + suffix
            if candidate in col_names:
                return GrainResult(
                    qualified_name=qualified_name,
                    grain=[candidate],
                    method="pattern",
                    pattern_used="table_name_id",
                    source="auto",
                )

        # Pattern 2: Single column ending in ID that's unique
        id_cols = [c for c in col_names if c.upper().endswith("ID")]
        if len(id_cols) == 1:
            return GrainResult(
                qualified_name=qualified_name,
                grain=[id_cols[0]],
                method="pattern",
                pattern_used="single_id_column",
                source="auto",
            )

        return None

    def _fd_minimize_pk(
        self, schema: str, table: str, pk_columns: list[str]
    ) -> tuple[list[str], list[str]]:
        """Functional dependency minimization of composite PK.

        Tests each PK column for FD-redundancy: if GROUP BY other PK
        columns yields COUNT(DISTINCT col) = 1 for every group, the
        column is functionally determined by the others.

        Returns:
            (minimal_pk, removed_columns)
        """
        if len(pk_columns) <= 1 or not self.cursor or not self.dialect:
            return pk_columns, []

        removed = []
        remaining = list(pk_columns)

        for col in pk_columns:
            others = [c for c in remaining if c != col]
            if not others:
                continue

            validate_identifier(col)
            for o in others:
                validate_identifier(o)

            group_cols = ", ".join(f"[{c}]" for c in others)
            source = f"[{schema}].[{table}]"
            if self._sample_pool:
                source = self._sample_pool.get_sample(1.0)

            sql = (
                f"SELECT MAX(cnt) FROM ("
                f"  SELECT COUNT(DISTINCT [{col}]) AS cnt"
                f"  FROM {source}"
                f"  GROUP BY {group_cols}"
                f") AS fd_check"
            )

            try:
                old_timeout = self.dialect.set_timeout(self.cursor, 600)
                try:
                    self.cursor.execute(sql)
                    row = self.cursor.fetchone()
                finally:
                    self.dialect.set_timeout(self.cursor, old_timeout)

                if row and row[0] == 1:
                    # Column is FD-redundant
                    removed.append(col)
                    remaining.remove(col)
                    logger.info(f"  FD: [{col}] is redundant (determined by {others})")
            except Exception as e:
                logger.warning(f"  FD check failed for [{col}]: {e}")

        return remaining, removed

    def discover_grain(
        self,
        qualified_name: str,
        sample_size: int | None = None,
    ) -> GrainResult:
        """Discover the primary key (grain) for an asset.

        Discovery order:
        1. Check config for no_natural_pk designation
        2. Check config for manual PK override
        3. Try pattern-based detection
        4. Use progressive scanning (for large tables)
        5. Fall back to iterative accumulation

        Args:
            qualified_name: Asset name in [Schema].[Table] format.
            sample_size: Sample size for pattern-based detection.

        Returns:
            GrainResult with discovered grain or explanation.
        """
        # Step 1: Check no_natural_pk
        if self._is_no_natural_pk(qualified_name):
            return GrainResult(
                qualified_name=qualified_name,
                grain=None,
                method="no-pk",
                source="config",
            )

        # Step 2: Check config override
        config_pk = self._get_config_pk(qualified_name)
        if config_pk:
            return GrainResult(
                qualified_name=qualified_name,
                grain=config_pk,
                method="config",
                source="primary_keys_config",
            )

        # Step 3: Get columns
        columns = self._get_asset_columns(qualified_name)
        if not columns:
            return GrainResult(
                qualified_name=qualified_name,
                grain=None,
                method="error",
                source="No columns found",
                error="No columns available for grain discovery",
            )

        # Step 4: Pattern-based
        pattern_result = self._pattern_based_discovery(qualified_name, columns)
        if pattern_result:
            # Validate pattern result against source DB
            schema, table = self._parse_qualified_name(qualified_name)
            if self.cursor and self.dialect:
                selectivity = self._test_uniqueness(
                    schema, table, pattern_result.grain, sample_pct=1.0
                )
                if selectivity >= self.UNIQUENESS_THRESHOLD:
                    return pattern_result
                logger.info(
                    f"  Pattern candidate {pattern_result.grain} "
                    f"selectivity={selectivity:.2f}%, not unique"
                )
            else:
                # No source DB to validate, return pattern result
                return pattern_result

        # Step 5: Progressive scanning (requires source DB)
        if self.cursor and self.dialect:
            schema, table = self._parse_qualified_name(qualified_name)
            row_count = self._get_row_count(schema, table)

            if row_count and row_count > 0:
                from data_catalog.services.pk_discovery.scanner import (
                    ProgressiveScanner,
                )

                scanner = ProgressiveScanner(
                    self.cursor,
                    self.dialect,
                    sample_pool=self._sample_pool,
                )
                scan_result = scanner.scan(schema, table, columns)

                if scan_result and scan_result.primary_key:
                    pk_cols = scan_result.primary_key

                    # FD minimization for composite PKs
                    pk_minimal = None
                    fd_removed = None
                    if len(pk_cols) > 1:
                        pk_minimal, fd_removed = self._fd_minimize_pk(
                            schema, table, pk_cols
                        )
                        if not fd_removed:
                            pk_minimal = None
                            fd_removed = None

                    return GrainResult(
                        qualified_name=qualified_name,
                        grain=pk_cols,
                        method="progressive-scan",
                        source="auto",
                        pk_minimal=pk_minimal,
                        fd_removed=fd_removed,
                    )

        # Step 6: No PK found
        return GrainResult(
            qualified_name=qualified_name,
            grain=None,
            method="exhausted",
            source="All discovery methods tried",
        )

    def discover_all(
        self,
        schema_filter: str | None = None,
        skip_discovered: bool = False,
        sample_size: int | None = None,
    ) -> list[GrainResult]:
        """Discover grain for all assets matching a filter.

        Args:
            schema_filter: Schema pattern to filter assets.
            skip_discovered: Skip assets that already have grain.
            sample_size: Sample size for pattern detection.

        Returns:
            List of GrainResult for each asset.
        """
        if schema_filter:
            assets = self.repo.find_by_schema_pattern(schema_filter)
        else:
            assets = self.repo.find_all()

        results = []
        for i, asset in enumerate(assets, 1):
            if skip_discovered:
                gs = (asset.schema_metadata or {}).get("grain_status")
                if gs in ("confirmed", "no_natural_pk"):
                    continue

            logger.info(
                f"[{i}/{len(assets)}] Discovering grain for "
                f"{asset.qualified_name}..."
            )
            result = self.discover_grain(
                asset.qualified_name, sample_size=sample_size
            )
            results.append(result)

            # Sync to catalog
            self.sync_to_catalog(asset.qualified_name, result)

        return results

    def sync_to_catalog(
        self, qualified_name: str, result: GrainResult
    ) -> None:
        """Persist grain discovery result to the catalog database.

        Updates Asset.schema_metadata with grain_status, primary_key,
        pk_minimal, and fd_removed fields.
        """
        asset = self.repo.find_by_qualified_name(qualified_name)
        if not asset:
            return

        meta = asset.schema_metadata or {}

        if result.grain:
            meta["grain_status"] = "confirmed"
            meta["primary_key"] = result.grain
            meta["pk_discovery"] = {
                "method": result.method,
                "pattern_used": result.pattern_used,
                "discovered_at": datetime.now(UTC).isoformat(),
            }
            if result.pk_minimal:
                meta["pk_minimal"] = result.pk_minimal
                meta["fd_removed"] = result.fd_removed
        elif result.method == "no-pk":
            meta["grain_status"] = "no_natural_pk"
        else:
            meta["grain_status"] = "no_natural_pk"

        asset.schema_metadata = meta
        flag_modified(asset, "schema_metadata")
        self.db.commit()

    def generate_report(
        self,
        schema_filter: str | None = None,
        output_format: str = "text",
    ) -> str:
        """Generate a grain discovery status report.

        Args:
            schema_filter: Optional schema pattern filter.
            output_format: 'text' or 'json'.

        Returns:
            Formatted report string.
        """
        if schema_filter:
            assets = self.repo.find_by_schema_pattern(schema_filter)
        else:
            assets = self.repo.find_all()

        confirmed = 0
        no_pk = 0
        unknown = 0

        for asset in assets:
            gs = (asset.schema_metadata or {}).get("grain_status")
            if gs == "confirmed":
                confirmed += 1
            elif gs == "no_natural_pk":
                no_pk += 1
            else:
                unknown += 1

        total = len(assets)

        if output_format == "json":
            import json as json_mod

            return json_mod.dumps({
                "total": total,
                "confirmed": confirmed,
                "no_natural_pk": no_pk,
                "unknown": unknown,
                "coverage_pct": round(
                    (confirmed + no_pk) / total * 100, 1
                ) if total else 0,
            }, indent=2)

        lines = [
            "Grain Discovery Report",
            "=" * 40,
            f"Total assets:    {total}",
            f"PK confirmed:    {confirmed}",
            f"No natural PK:   {no_pk}",
            f"Unknown:         {unknown}",
            f"Coverage:        {(confirmed + no_pk) / total * 100:.1f}%"
            if total else "Coverage: N/A",
        ]
        return "\n".join(lines)

    def mark_no_natural_pk(
        self, qualified_name: str, source: str, confirmed_by: str
    ) -> GrainResult:
        """Mark an asset as having no natural primary key."""
        no_pk_list = self.config.setdefault("no_natural_pk", [])
        if qualified_name not in no_pk_list:
            no_pk_list.append(qualified_name)
            self._save_config()

        result = GrainResult(
            qualified_name=qualified_name,
            grain=None,
            method="no-pk",
            source=source,
        )
        self.sync_to_catalog(qualified_name, result)
        return result

    def apply_manual_override(
        self,
        qualified_name: str,
        columns: list[str],
        source: str,
        confirmed_by: str,
    ) -> GrainResult:
        """Apply a manual PK override for an asset."""
        pk_config = self.config.setdefault("primary_keys", {})
        pk_config[qualified_name] = {
            "columns": columns,
            "source": source,
            "confirmed_by": confirmed_by,
            "confirmed_date": datetime.now(UTC).strftime("%Y-%m-%d"),
        }
        self._save_config()

        result = GrainResult(
            qualified_name=qualified_name,
            grain=columns,
            method="manual",
            source=source,
        )
        self.sync_to_catalog(qualified_name, result)
        return result
