# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Grain discovery service for primary key detection.

Discovers primary keys (grain) in database tables/views using:
- Manual overrides from configuration file
- Pattern-based detection (fast, for common naming conventions)
- Progressive 7-step scanning (thorough, for large tables)
- Varying column chase (for near-unique candidates with dupe groups)
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

# Column types to skip in PK candidate testing
_SKIP_TYPES = frozenset({
    "xml", "image", "text", "ntext", "geography", "geometry",
    "varbinary", "binary", "hierarchyid", "sql_variant",
})

# Column name patterns to skip
_SKIP_NAME_PATTERNS = [
    re.compile(r"^__\$"),            # CDC columns
    re.compile(r"ArchiveDTS$"),      # Archive timestamps
    re.compile(r"^rowguid$", re.IGNORECASE),
]


def _should_test_column(name: str, data_type: str) -> bool:
    """Check if a column should be tested as PK candidate."""
    dt = data_type.lower().split("(")[0].strip()
    if dt in _SKIP_TYPES:
        return False
    for pat in _SKIP_NAME_PATTERNS:
        if pat.search(name):
            return False
    return True


class GrainDiscoveryService:
    """Service for discovering and managing grain (primary keys).

    Provides:
    - Automatic grain discovery using pattern-based detection
    - Progressive scanning for large tables
    - Varying column chase for near-unique candidates
    - Iterative accumulation for extract-partitioned tables
    - Manual override support from configuration
    - Catalog synchronization for persisting results
    - FD minimization for composite PKs
    """

    DEFAULT_CONFIG_PATH = Path("config/primary_keys_config.json")
    DEFAULT_SAMPLE_SIZE = 10000
    UNIQUENESS_THRESHOLD = 99.99

    # -- Varying Column Chase (VCC) constants --
    _VCC_MAX_DUPE_GROUPS = 20         # Fetch rows from this many duplicate groups
    _VCC_VARIATION_THRESHOLD = 0.30   # Column must vary in >30% of dupe groups
    _VCC_UNIQUENESS_THRESHOLD = 0.9999  # Composite must achieve this selectivity
    _VCC_MAX_COMPOSITE_TESTS = 10     # Cap composite tests to limit query cost

    # -- Iterative Accumulation (IA) constants --
    _IA_MAX_DEPTH = 10
    _IA_BATCH_SIZE = 5
    _IA_UNIQUENESS_THRESHOLD = 0.9999
    _IA_PLATEAU_LIMIT = 3
    _IA_SELECTIVITY_BATCH = 25

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
                    status="confirmed",
                    primary_key=[candidate],
                    method="pattern",
                    metadata={"pattern_used": "table_name_id"},
                )

        # Pattern 2: Single column ending in ID that's unique
        id_cols = [c for c in col_names if c.upper().endswith("ID")]
        if len(id_cols) == 1:
            return GrainResult(
                qualified_name=qualified_name,
                status="confirmed",
                primary_key=[id_cols[0]],
                method="pattern",
                metadata={"pattern_used": "single_id_column"},
            )

        return None

    def _fd_minimize_pk(
        self,
        schema: str,
        table: str,
        pk_columns: list[str],
        *,
        temp_table: str | None = None,
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
            if temp_table:
                source = temp_table
            elif self._sample_pool:
                source = self._sample_pool.get_sample(1.0)
            else:
                source = f"[{schema}].[{table}]"

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

    # ------------------------------------------------------------------
    # Main discovery flow
    # ------------------------------------------------------------------

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
        4. Use progressive scanning
        5. Varying column chase (from progressive scan best candidate)
        6. Iterative accumulation (includes VCC escalation from plateau)

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
                status="no_natural_pk",
                method="no-pk",
            )

        # Step 2: Check config override
        config_pk = self._get_config_pk(qualified_name)
        if config_pk:
            return GrainResult(
                qualified_name=qualified_name,
                status="confirmed",
                primary_key=config_pk,
                method="config",
            )

        # Step 3: Get columns
        columns = self._get_asset_columns(qualified_name)
        if not columns:
            return GrainResult(
                qualified_name=qualified_name,
                status="error",
                method="error",
                metadata={"error": "No columns available for grain discovery"},
            )

        # Step 4: Pattern-based
        pattern_result = self._pattern_based_discovery(qualified_name, columns)
        if pattern_result:
            # Validate pattern result against source DB
            schema, table = self._parse_qualified_name(qualified_name)
            if self.cursor and self.dialect:
                selectivity = self._test_uniqueness(
                    schema, table, pattern_result.primary_key, sample_pct=1.0
                )
                if selectivity >= self.UNIQUENESS_THRESHOLD:
                    return pattern_result
                logger.info(
                    f"  Pattern candidate {pattern_result.primary_key} "
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
                        status="confirmed",
                        primary_key=pk_cols,
                        pk_minimal=pk_minimal,
                        fd_removed=fd_removed,
                        method="progressive-scan",
                    )

                # Step 5b: VCC from progressive scan best candidate
                if scan_result and scan_result.step_history:
                    last_step = scan_result.step_history[-1]
                    best_cand = last_step.best_candidate
                    best_sel = last_step.best_selectivity
                    if best_cand and best_sel:
                        chase_result = self._varying_column_chase(
                            qualified_name, best_cand, best_sel,
                            columns, row_count,
                        )
                        if chase_result:
                            return chase_result

                # Step 6: Iterative accumulation (includes VCC escalation)
                ia_result = self._iterative_accumulation(
                    qualified_name, columns, row_count,
                )
                if ia_result:
                    return ia_result

        # Step 7: No PK found
        return GrainResult(
            qualified_name=qualified_name,
            status="unknown",
            method="exhausted",
        )

    # ------------------------------------------------------------------
    # Varying Column Chase (VCC)
    # ------------------------------------------------------------------

    def _varying_column_chase(
        self,
        qualified_name: str,
        best_candidate: str,
        best_selectivity: float,
        columns: list[dict],
        row_count: int | None,
        *,
        temp_table: str | None = None,
    ) -> GrainResult | None:
        """Analyze duplicate groups to find discriminating columns.

        When a near-unique candidate exists, samples its duplicate groups
        to find columns that vary within them, then tests refined
        composites (candidate + varying_col).

        Args:
            qualified_name: [Schema].[Table] format.
            best_candidate: Best candidate (e.g. "ColA + ColB").
            best_selectivity: Selectivity of the best candidate (0.0-1.0).
            columns: Column metadata from source database.
            row_count: Pre-fetched row count (or None).
            temp_table: Optional pre-existing temp table to reuse.

        Returns:
            GrainResult if a PK is found, None otherwise.
        """
        if not self.cursor or not self.dialect:
            return None

        logger.info(
            f"Varying column chase for {qualified_name}: "
            f"candidate={best_candidate} selectivity={best_selectivity:.2%}"
        )
        start_time = time.time()

        schema, table = self._parse_qualified_name(qualified_name)

        # Step 1: Parse candidate — split "ColA + ColB" into ["ColA", "ColB"]
        candidate_cols = [c.strip() for c in best_candidate.split(" + ")]
        candidate_set = set(candidate_cols)

        # Step 2: Get testable columns (all except candidate, filtered)
        testable_cols: list[str] = []
        for c in columns:
            if c["name"] in candidate_set:
                continue
            if not _should_test_column(c["name"], c.get("data_type", "")):
                continue
            try:
                validate_identifier(c["name"])
                testable_cols.append(c["name"])
            except Exception:
                continue

        if not testable_cols:
            logger.info("  VCC: no testable non-candidate columns")
            return None

        # Step 3: Get or create sample (reuse caller's temp table if provided)
        created_temp = False
        if temp_table is None:
            if self._sample_pool:
                try:
                    temp_table = self._sample_pool.get_sample(1)
                except Exception as e:
                    logger.warning(f"  VCC: pool sample failed: {e}")

            if temp_table is None:
                temp_table = self._ia_create_temp_sample(
                    schema, table,
                    sample_pct=1 if (row_count and row_count > 100_000) else 100,
                )
                if temp_table is None:
                    return None
                created_temp = True

        try:
            # Step 4: Fetch dupe rows from top N duplicate groups
            safe_cand_cols = ", ".join(
                f"[{validate_identifier(c)}]" for c in candidate_cols
            )
            # NULL-safe join: (s.col = dk.col OR (s.col IS NULL AND dk.col IS NULL))
            join_conditions = " AND ".join(
                f"(s.[{validate_identifier(c)}] = dk.[{validate_identifier(c)}]"
                f" OR (s.[{validate_identifier(c)}] IS NULL"
                f" AND dk.[{validate_identifier(c)}] IS NULL))"
                for c in candidate_cols
            )

            # NOTE: SELECT TOP is SQL Server syntax; adapt for other dialects
            dupe_sql = (
                f"WITH DupeKeys AS (\n"
                f"    SELECT TOP {self._VCC_MAX_DUPE_GROUPS} {safe_cand_cols}\n"
                f"    FROM {temp_table}\n"
                f"    GROUP BY {safe_cand_cols}\n"
                f"    HAVING COUNT(*) > 1\n"
                f"    ORDER BY COUNT(*) DESC\n"
                f")\n"
                f"SELECT s.*\n"
                f"FROM {temp_table} s\n"
                f"INNER JOIN DupeKeys dk ON {join_conditions}"
            )

            try:
                old_timeout = self.dialect.set_timeout(self.cursor, 600)
                try:
                    self.cursor.execute(dupe_sql)
                    dupe_rows = self.cursor.fetchall()
                    col_names = [desc[0] for desc in self.cursor.description]
                finally:
                    self.dialect.set_timeout(self.cursor, old_timeout)
            except Exception as e:
                logger.warning(f"  VCC: dupe query failed: {e}")
                return None

            if not dupe_rows:
                logger.info("  VCC: no duplicate groups found in sample")
                return None

            logger.info(
                f"  VCC: fetched {len(dupe_rows)} rows from duplicate groups"
            )

            # Step 5: Identify varying columns (Python analysis)
            col_idx_map = {name: i for i, name in enumerate(col_names)}
            cand_indices = [
                col_idx_map[c] for c in candidate_cols if c in col_idx_map
            ]

            groups: dict[tuple, list] = {}
            for row in dupe_rows:
                key = tuple(row[i] for i in cand_indices)
                groups.setdefault(key, []).append(row)

            num_groups = len(groups)
            if num_groups == 0:
                return None

            testable_in_result = [c for c in testable_cols if c in col_idx_map]
            variation_counts: dict[str, int] = {}
            for col in testable_in_result:
                cidx = col_idx_map[col]
                varying_groups = 0
                for group_rows in groups.values():
                    values = {r[cidx] for r in group_rows}
                    if len(values) > 1:
                        varying_groups += 1
                variation_counts[col] = varying_groups

            # Filter columns that vary in >30% of dupe groups
            varying_cols = [
                (col, count / num_groups)
                for col, count in variation_counts.items()
                if count / num_groups > self._VCC_VARIATION_THRESHOLD
            ]
            varying_cols.sort(key=lambda x: x[1], reverse=True)

            if not varying_cols:
                logger.info(
                    f"  VCC: no columns vary in "
                    f">{self._VCC_VARIATION_THRESHOLD:.0%} "
                    f"of {num_groups} dupe groups"
                )
                return None

            logger.info(
                f"  VCC: {len(varying_cols)} varying columns: "
                + ", ".join(f"{c}({f:.0%})" for c, f in varying_cols[:5])
            )

            # Step 6: Test refined composites
            composites_to_test: list[list[str]] = []

            # Each varying column individually: (candidate + varying_col)
            for col, _frac in varying_cols:
                composites_to_test.append(candidate_cols + [col])
                if len(composites_to_test) >= self._VCC_MAX_COMPOSITE_TESTS:
                    break

            # Top-2 varying columns together
            if (
                len(varying_cols) >= 2
                and len(composites_to_test) < self._VCC_MAX_COMPOSITE_TESTS
            ):
                composites_to_test.append(
                    candidate_cols + [varying_cols[0][0], varying_cols[1][0]]
                )

            # Use dialect.count_distinct for composite testing
            test_sql = self.dialect.count_distinct(
                temp_table, columns=[], composites=composites_to_test,
            )

            try:
                old_timeout = self.dialect.set_timeout(self.cursor, 600)
                try:
                    self.cursor.execute(test_sql)
                    test_row = self.cursor.fetchone()
                finally:
                    self.dialect.set_timeout(self.cursor, old_timeout)
            except Exception as e:
                logger.warning(f"  VCC: composite test query failed: {e}")
                return None

            if not test_row:
                return None

            sample_count = int(test_row[0]) if test_row[0] is not None else 0
            if sample_count == 0:
                return None

            # Step 7: Check for PK
            for idx, composite in enumerate(composites_to_test):
                distinct = (
                    int(test_row[idx + 1])
                    if test_row[idx + 1] is not None
                    else 0
                )
                selectivity = distinct / sample_count

                if selectivity >= self._VCC_UNIQUENESS_THRESHOLD:
                    # FD minimization
                    pk_minimal, fd_removed_list = self._fd_minimize_pk(
                        schema, table, composite, temp_table=temp_table,
                    )
                    pk_min = pk_minimal if fd_removed_list else None
                    fd_rem = fd_removed_list if fd_removed_list else None

                    duration = time.time() - start_time
                    logger.info(
                        f"  VCC found PK: {composite} "
                        f"(selectivity {selectivity:.4%}) in {duration:.1f}s"
                    )

                    return GrainResult(
                        qualified_name=qualified_name,
                        status="confirmed",
                        primary_key=composite,
                        pk_minimal=pk_min,
                        fd_removed=fd_rem,
                        method="varying-column-chase",
                        confidence=selectivity,
                        metadata={
                            "original_candidate": best_candidate,
                            "original_selectivity": best_selectivity,
                            "discriminating_column": [
                                c for c in composite if c not in candidate_set
                            ],
                            "dupe_groups_analyzed": num_groups,
                            "varying_columns": [c for c, _ in varying_cols],
                            "duration_seconds": round(duration, 1),
                        },
                    )

            duration = time.time() - start_time
            logger.info(
                f"  VCC: no PK found after testing "
                f"{len(composites_to_test)} composites in {duration:.1f}s"
            )
            return None

        finally:
            if created_temp:
                self._ia_drop_temp_sample(temp_table)

    # ------------------------------------------------------------------
    # Iterative Accumulation (IA)
    # ------------------------------------------------------------------

    def _ia_create_temp_sample(
        self,
        schema: str,
        table: str,
        *,
        sample_pct: int = 1,
        seed_col: str | None = None,
    ) -> str | None:
        """Create a temp table with a sample for iterative accumulation.

        Delegates to sample pool if available, otherwise creates via dialect.

        Returns:
            Temp table name, or None if creation failed.
        """
        if self._sample_pool:
            try:
                return self._sample_pool.get_sample(sample_pct)
            except Exception as e:
                logger.warning(f"  Pool sample creation failed: {e}")
                return None

        if not self.cursor or not self.dialect:
            return None

        if not seed_col:
            seed_col = self._ia_select_seed_column(schema, table)

        validate_identifier(schema)
        validate_identifier(table)
        temp_name = f"#ia_sample_{int(time.time())}"

        sql = self.dialect.create_sample_table(
            temp_name, schema, table, seed_col, float(sample_pct),
        )

        try:
            old_timeout = self.dialect.set_timeout(self.cursor, 600)
            try:
                logger.info(f"  Creating IA temp sample ({sample_pct}%)...")
                t0 = time.time()
                self.cursor.execute(sql)
                elapsed = time.time() - t0
            finally:
                self.dialect.set_timeout(self.cursor, old_timeout)

            # Row count
            old_timeout = self.dialect.set_timeout(self.cursor, 300)
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {temp_name}")
                row_count = self.cursor.fetchone()[0]
            finally:
                self.dialect.set_timeout(self.cursor, old_timeout)

            self.dialect.drain_cursor(self.cursor)
            logger.info(
                f"  IA temp sample ready: {row_count:,} rows in {elapsed:.1f}s"
            )
            return temp_name
        except Exception as e:
            logger.warning(f"  IA temp table creation failed: {e}")
            return None

    def _ia_drop_temp_sample(self, temp_name: str | None) -> None:
        """Drop an IA temp table. No-op when pool manages temp tables."""
        if not temp_name:
            return
        if self._sample_pool:
            return  # Pool owns the temp table lifecycle
        if not self.cursor or not self.dialect:
            return
        try:
            sql = self.dialect.drop_temp_table(temp_name)
            self.cursor.execute(sql)
            self.dialect.drain_cursor(self.cursor)
        except Exception:
            pass

    def _ia_select_seed_column(
        self, schema: str, table: str,
    ) -> str:
        """Select a high-cardinality column for sampling."""
        if not self.cursor or not self.dialect:
            return "1"  # Fallback: use constant (full scan)

        # Get columns first
        columns = self._get_asset_columns(
            f"[{schema}].[{table}]"
        )
        col_names = [c["name"] for c in columns if c.get("name")][:30]
        if not col_names:
            return "1"

        try:
            sql = self.dialect.seed_column_query(schema, table, col_names)
            old_timeout = self.dialect.set_timeout(self.cursor, 300)
            try:
                self.cursor.execute(sql)
                row = self.cursor.fetchone()
            finally:
                self.dialect.set_timeout(self.cursor, old_timeout)

            best_col, best_card = col_names[0], 0
            for i, col in enumerate(col_names):
                card = row[i] if row[i] is not None else 0
                if card > best_card:
                    best_card = card
                    best_col = col

            logger.debug(f"  Seed column: {best_col} ({best_card} unique)")
            return best_col
        except Exception as e:
            logger.warning(f"  Seed selection failed: {e}")
            return col_names[0]

    def _ia_measure_all_selectivities(
        self,
        schema: str,
        table: str,
        columns: list[str],
        *,
        temp_table: str | None = None,
    ) -> dict[str, float]:
        """Measure per-column selectivity, batching to avoid SQL nesting limits.

        Uses temp_table if available, otherwise queries source directly.
        """
        if not self.cursor or not self.dialect:
            return {}

        source = temp_table or f"[{schema}].[{table}]"

        selectivities: dict[str, float] = {}
        sample_row_count: int | None = None

        for batch_start in range(0, len(columns), self._IA_SELECTIVITY_BATCH):
            batch_cols = columns[
                batch_start : batch_start + self._IA_SELECTIVITY_BATCH
            ]

            # Use dialect.count_distinct with individual columns
            sql = self.dialect.count_distinct(
                source, columns=batch_cols, composites=None,
            )

            try:
                old_timeout = self.dialect.set_timeout(self.cursor, 600)
                try:
                    self.cursor.execute(sql)
                    row = self.cursor.fetchone()
                finally:
                    self.dialect.set_timeout(self.cursor, old_timeout)
            except Exception as e:
                logger.warning(
                    f"  Selectivity measurement failed (batch {batch_start}): {e}"
                )
                return selectivities

            if not row:
                return selectivities

            row_count = int(row[0]) if row[0] is not None else 0
            if row_count == 0:
                return {}

            if sample_row_count is None:
                sample_row_count = row_count

            for idx, col in enumerate(batch_cols):
                distinct = int(row[idx + 1]) if row[idx + 1] is not None else 0
                selectivities[col] = distinct / row_count

        n_batches = (
            (len(columns) + self._IA_SELECTIVITY_BATCH - 1)
            // self._IA_SELECTIVITY_BATCH
        )
        logger.info(
            f"  Measured selectivities for {len(selectivities)} columns "
            f"({sample_row_count:,} sample rows, {n_batches} batch(es))"
        )
        return selectivities

    def _ia_try_accumulation_batched(
        self,
        sorted_cols: list[str],
        ordering: str,
        *,
        temp_table: str,
    ) -> list[str] | None:
        """Try iterative accumulation with batched SQL queries.

        Accumulates columns one at a time into a composite key, testing
        cumulative selectivity at each depth. Returns the composite PK
        columns if uniqueness threshold is reached, None otherwise.

        Sets ``self._ia_best_plateau`` when a plateau is detected,
        enabling VCC escalation in the orchestrator.
        """
        if not self.cursor or not self.dialect:
            return None

        max_depth = min(self._IA_MAX_DEPTH, len(sorted_cols))
        accumulated: list[str] = []
        prev_selectivity = 0.0
        plateau_count = 0

        col_idx = 0
        while col_idx < max_depth:
            batch_end = min(col_idx + self._IA_BATCH_SIZE, max_depth)
            batch_cols = sorted_cols[col_idx:batch_end]

            # Build composite tests: accumulated + each prefix of batch
            batch_composites: list[list[str]] = []
            for i in range(len(batch_cols)):
                accumulated_plus = accumulated + batch_cols[: i + 1]
                batch_composites.append(accumulated_plus)

            sql = self.dialect.count_distinct(
                temp_table, columns=[], composites=batch_composites,
            )

            try:
                old_timeout = self.dialect.set_timeout(self.cursor, 600)
                try:
                    self.cursor.execute(sql)
                    row = self.cursor.fetchone()
                finally:
                    self.dialect.set_timeout(self.cursor, old_timeout)
            except Exception as e:
                logger.warning(
                    f"  Accumulation query failed ({ordering} batch "
                    f"{col_idx + 1}-{batch_end}): {e}"
                )
                return None

            if not row:
                return None

            row_count = int(row[0]) if row[0] is not None else 0
            if row_count == 0:
                return None

            for i in range(len(batch_cols)):
                depth = col_idx + i + 1
                distinct = (
                    int(row[i + 1]) if row[i + 1] is not None else 0
                )
                selectivity = distinct / row_count

                logger.debug(
                    f"  {ordering} depth {depth}: "
                    f"{', '.join(batch_composites[i])} -> "
                    f"{selectivity:.4%} ({distinct:,}/{row_count:,})"
                )

                if selectivity >= self._IA_UNIQUENESS_THRESHOLD:
                    pk_cols = batch_composites[i]
                    logger.info(
                        f"  {ordering} PK found at depth {depth}: "
                        f"{pk_cols} ({selectivity:.4%})"
                    )
                    return pk_cols

                improvement = selectivity - prev_selectivity
                threshold = 0.001 if selectivity >= 0.90 else 0.01
                if improvement < threshold:
                    plateau_count += 1
                else:
                    plateau_count = 0

                if plateau_count >= self._IA_PLATEAU_LIMIT:
                    logger.info(
                        f"  {ordering} plateau after depth {depth} "
                        f"({selectivity:.4%}), stopping"
                    )
                    # Track best plateau for VCC escalation
                    composite = batch_composites[i]
                    if (
                        self._ia_best_plateau is None
                        or selectivity > self._ia_best_plateau[1]
                    ):
                        self._ia_best_plateau = (composite, selectivity)
                    return None

                prev_selectivity = selectivity

            accumulated = batch_composites[-1]
            col_idx = batch_end

        return None

    def _ia_minimize_pk(
        self,
        pk_cols: list[str],
        *,
        temp_table: str,
    ) -> list[str]:
        """Leave-one-out minimization of an iterative-accumulation PK.

        Tries removing each column and checks if the remaining composite
        still achieves uniqueness. Repeats until no column can be removed.
        """
        if len(pk_cols) <= 1 or not self.cursor or not self.dialect:
            return pk_cols

        current = list(pk_cols)
        while len(current) > 1:
            candidates: list[list[str]] = []
            composites: list[list[str]] = []
            for i in range(len(current)):
                subset = current[:i] + current[i + 1 :]
                candidates.append(subset)
                composites.append(subset)

            sql = self.dialect.count_distinct(
                temp_table, columns=[], composites=composites,
            )

            try:
                old_timeout = self.dialect.set_timeout(self.cursor, 600)
                try:
                    self.cursor.execute(sql)
                    row = self.cursor.fetchone()
                finally:
                    self.dialect.set_timeout(self.cursor, old_timeout)
            except Exception as e:
                logger.warning(f"  Minimization query failed: {e}")
                return current

            if not row:
                return current

            row_count = int(row[0]) if row[0] is not None else 0
            if row_count == 0:
                return current

            dropped = False
            for i in range(len(current)):
                distinct = (
                    int(row[i + 1]) if row[i + 1] is not None else 0
                )
                selectivity = distinct / row_count
                if selectivity >= self._IA_UNIQUENESS_THRESHOLD:
                    dropped_col = current[i]
                    current = candidates[i]
                    logger.info(
                        f"  Minimization: dropped [{dropped_col}], "
                        f"{len(current)} cols remain ({selectivity:.4%})"
                    )
                    dropped = True
                    break

            if not dropped:
                break

        return current

    def _iterative_accumulation(
        self,
        qualified_name: str,
        columns: list[dict],
        row_count: int | None,
    ) -> GrainResult | None:
        """Fallback PK discovery using iterative column accumulation.

        Accumulates columns one at a time into a composite key, testing
        cumulative selectivity at each depth. Tries highest-selectivity-first
        (top-down) then lowest-selectivity-first (bottom-up).

        When both orderings plateau without finding a PK, escalates to
        VCC using the best plateau composite as the candidate.
        """
        if not self.cursor or not self.dialect:
            return None

        logger.info(f"Trying iterative accumulation for {qualified_name}")
        start_time = time.time()

        # Track best plateau composite across orderings for VCC escalation
        self._ia_best_plateau: tuple[list[str], float] | None = None

        schema, table = self._parse_qualified_name(qualified_name)

        # Get testable columns
        testable: list[str] = []
        for c in columns:
            if not _should_test_column(c["name"], c.get("data_type", "")):
                continue
            try:
                validate_identifier(c["name"])
                testable.append(c["name"])
            except Exception:
                continue

        if not testable:
            return None

        # Create materialized temp sample
        sample_pct = 1 if (row_count and row_count > 100_000) else 100
        temp_table = self._ia_create_temp_sample(
            schema, table, sample_pct=sample_pct,
        )
        if not temp_table:
            return None

        try:
            # Measure per-column selectivities
            selectivities = self._ia_measure_all_selectivities(
                schema, table, testable, temp_table=temp_table,
            )
            if not selectivities:
                return None

            # Filter out zero-selectivity columns
            nonzero = {k: v for k, v in selectivities.items() if v > 0}
            if not nonzero:
                return None

            # Top-down: highest selectivity first
            top_down = sorted(
                nonzero.keys(), key=lambda c: nonzero[c], reverse=True,
            )
            result = self._ia_try_accumulation_batched(
                top_down, "top-down", temp_table=temp_table,
            )
            if result:
                result = self._ia_minimize_pk(result, temp_table=temp_table)
                pk_minimal, fd_removed = self._fd_minimize_pk(
                    schema, table, result, temp_table=temp_table,
                )
                fd_rem = fd_removed if fd_removed else None
                pk_min = pk_minimal if fd_removed else None
                duration = time.time() - start_time
                logger.info(
                    f"Iterative accumulation (top-down) found PK: "
                    f"{result} in {duration:.1f}s"
                )
                return GrainResult(
                    qualified_name=qualified_name,
                    status="confirmed",
                    primary_key=result,
                    pk_minimal=pk_min,
                    fd_removed=fd_rem,
                    method="iterative-accumulation",
                    confidence=0.9999,
                    metadata={
                        "ordering": "top-down",
                        "duration_seconds": round(duration, 1),
                        "sample_pct": sample_pct,
                    },
                )

            # Bottom-up: lowest selectivity first
            bottom_up = sorted(
                nonzero.keys(), key=lambda c: nonzero[c],
            )
            result = self._ia_try_accumulation_batched(
                bottom_up, "bottom-up", temp_table=temp_table,
            )
            if result:
                result = self._ia_minimize_pk(result, temp_table=temp_table)
                pk_minimal, fd_removed = self._fd_minimize_pk(
                    schema, table, result, temp_table=temp_table,
                )
                fd_rem = fd_removed if fd_removed else None
                pk_min = pk_minimal if fd_removed else None
                duration = time.time() - start_time
                logger.info(
                    f"Iterative accumulation (bottom-up) found PK: "
                    f"{result} in {duration:.1f}s"
                )
                return GrainResult(
                    qualified_name=qualified_name,
                    status="confirmed",
                    primary_key=result,
                    pk_minimal=pk_min,
                    fd_removed=fd_rem,
                    method="iterative-accumulation",
                    confidence=0.9999,
                    metadata={
                        "ordering": "bottom-up",
                        "duration_seconds": round(duration, 1),
                        "sample_pct": sample_pct,
                    },
                )

            # VCC escalation: if IA plateaued with a near-unique composite,
            # try varying column chase to find the discriminating column.
            if self._ia_best_plateau is not None:
                plateau_cols, plateau_sel = self._ia_best_plateau
                logger.info(
                    f"  IA plateau escalation to VCC: "
                    f"{' + '.join(plateau_cols)} ({plateau_sel:.4%})"
                )
                candidate_str = " + ".join(plateau_cols)
                chase_result = self._varying_column_chase(
                    qualified_name, candidate_str, plateau_sel,
                    columns, row_count,
                    temp_table=temp_table,
                )
                if chase_result:
                    chase_result.metadata["source"] = (
                        f"IA plateau -> varying column chase "
                        f"(plateau at {plateau_sel:.4%})"
                    )
                    return chase_result

            duration = time.time() - start_time
            logger.info(
                f"Iterative accumulation found no PK for "
                f"{qualified_name} after {duration:.1f}s"
            )
            return None
        finally:
            self._ia_drop_temp_sample(temp_table)

    # ------------------------------------------------------------------
    # Bulk discovery and catalog sync
    # ------------------------------------------------------------------

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

        if result.primary_key:
            meta["grain_status"] = "confirmed"
            meta["primary_key"] = result.primary_key
            meta["pk_discovery"] = {
                "method": result.method,
                "discovered_at": datetime.now(UTC).isoformat(),
            }
            if result.metadata.get("pattern_used"):
                meta["pk_discovery"]["pattern_used"] = result.metadata[
                    "pattern_used"
                ]
            if result.pk_minimal:
                meta["pk_minimal"] = result.pk_minimal
                meta["fd_removed"] = result.fd_removed
        elif result.status == "no_natural_pk":
            meta["grain_status"] = "no_natural_pk"
        else:
            meta["grain_status"] = result.status

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
            status="no_natural_pk",
            method="no-pk",
            metadata={"source": source, "confirmed_by": confirmed_by},
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
            status="confirmed",
            primary_key=columns,
            method="manual",
            metadata={"source": source, "confirmed_by": confirmed_by},
        )
        self.sync_to_catalog(qualified_name, result)
        return result
