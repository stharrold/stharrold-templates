# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Progressive Scanner for PK Discovery.

Orchestrates the 7-step progressive scanning algorithm:
    Step 1: 0.1% rows, 100% columns - Initial screening
    Step 2: 0.3% rows, 30% columns - First elimination
    Step 3: 1% rows, 10% columns - Composite testing begins
    Step 4: 3% rows, 3% columns - Escalation checkpoint
    Step 5: 10% rows, 1% columns - Final candidates
    Step 6: 30% rows, 0.3% columns - Near-validation
    Step 7: 100% rows, 0.1% columns - Full validation
"""

from __future__ import annotations

import logging
import math
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from data_catalog.services.sql_dialect import SQLDialect
from data_catalog.services.pk_discovery.decision import DecisionEngine
from data_catalog.services.pk_discovery.models import (
    ColumnCandidate,
    CompositeCandidate,
    ScanResult,
    ScanStep,
    StepResult,
)

logger = logging.getLogger(__name__)

# Default step configuration (inverse progression)
DEFAULT_STEP_CONFIG = [
    {"step": 1, "row_pct": 0.1, "col_pct": 100.0, "timeout": 60},
    {"step": 2, "row_pct": 0.3, "col_pct": 30.0, "timeout": 120},
    {"step": 3, "row_pct": 1.0, "col_pct": 10.0, "timeout": 180},
    {"step": 4, "row_pct": 3.0, "col_pct": 3.0, "timeout": 300},
    {"step": 5, "row_pct": 10.0, "col_pct": 1.0, "timeout": 300},
    {"step": 6, "row_pct": 30.0, "col_pct": 0.3, "timeout": 300},
    {"step": 7, "row_pct": 100.0, "col_pct": 0.1, "timeout": 600},
]

# PK naming patterns for priority ranking
PK_PATTERNS = [
    (re.compile(r"^.*_ID$", re.IGNORECASE), 1),
    (re.compile(r"^.*_KEY$", re.IGNORECASE), 1),
    (re.compile(r"^.*_SK$", re.IGNORECASE), 1),
    (re.compile(r"^.*_SID$", re.IGNORECASE), 1),
    (re.compile(r"^ID$", re.IGNORECASE), 2),
    (re.compile(r"^KEY$", re.IGNORECASE), 2),
    (re.compile(r"^.*_CODE$", re.IGNORECASE), 3),
    (re.compile(r"^.*_NUM$", re.IGNORECASE), 3),
    (re.compile(r"^.*_NUMBER$", re.IGNORECASE), 3),
]

# Data types that cannot be PK candidates
EXCLUDED_TYPES = {
    "text", "ntext", "image", "xml", "geography", "geometry",
    "hierarchyid", "sql_variant", "timestamp", "rowversion",
}

# Maximum COUNT DISTINCT expressions per query (prevents nesting-depth errors)
CARDINALITY_BATCH_SIZE = 50


class ProgressiveScanner:
    """Orchestrates the 7-step progressive PK discovery algorithm.

    Args:
        cursor: Database cursor for source queries.
        dialect: SQL dialect for query generation.
        step_config: Optional custom step configuration.
        sample_pool: Optional SamplePool for shared temp tables.
    """

    def __init__(
        self,
        cursor: Any,
        dialect: SQLDialect,
        step_config: list[dict[str, Any]] | None = None,
        sample_pool: Any = None,
    ) -> None:
        self.cursor = cursor
        self.dialect = dialect
        self.decision_engine = DecisionEngine()
        self._sample_pool = sample_pool
        self._current_temp: str | None = None
        self._logger = logging.getLogger(f"{__name__}.ProgressiveScanner")

        config = step_config or DEFAULT_STEP_CONFIG
        self.steps = [
            ScanStep(
                step_number=c["step"],
                row_sample_pct=c["row_pct"],
                col_subset_pct=c["col_pct"],
                timeout_seconds=c.get("timeout", 300),
            )
            for c in config
        ]

    def scan(
        self,
        view_name: str,
        progress_callback: Callable[[StepResult], None] | None = None,
    ) -> ScanResult:
        """Execute progressive scan on a table/view.

        Args:
            view_name: Fully qualified name ``[Schema].[Table]``.
            progress_callback: Optional callback for step progress.

        Returns:
            ScanResult with discovery outcome.
        """
        start_time = datetime.now(UTC)
        schema, table = self._parse_view_name(view_name)

        self._logger.info(f"Starting progressive scan for [{schema}].[{table}]")

        # Get metadata
        total_rows = self._get_row_count(schema, table)
        columns_meta = self._get_column_inventory(schema, table)
        total_cols = len(columns_meta)
        self._logger.info(f"  {total_rows:,} rows, {total_cols} columns")

        # Select seed column for sampling
        all_col_names = [c["name"] for c in columns_meta]
        if self._sample_pool is not None:
            seed_col = self._sample_pool.seed_col
        else:
            seed_col = self._select_seed_column(schema, table, all_col_names)

        # Calculate step parameters
        for step in self.steps:
            step.row_count = max(1, math.ceil(total_rows * step.row_sample_pct / 100))
            step.col_count = max(1, math.ceil(total_cols * step.col_subset_pct / 100))

        # Initialize candidates (exclude non-PK-able types)
        candidates = [
            ColumnCandidate(
                column_name=col["name"],
                data_type=col["type"],
                ordinal_position=col["ordinal"],
                pk_priority=self._get_pk_priority(col["name"]),
            )
            for col in columns_meta
            if col["type"].lower() not in EXCLUDED_TYPES
        ]
        candidates.sort(key=lambda c: (c.pk_priority, c.ordinal_position))

        composites: list[CompositeCandidate] = []
        step_history: list[StepResult] = []
        step_timings: dict[int, float] = {}

        # Execute steps
        for step in self.steps:
            step_start = time.time()

            active_candidates = [c for c in candidates if not c.is_eliminated()]
            step_cols = active_candidates[: step.col_count]
            if not step_cols:
                self._logger.warning(f"Step {step.step_number}: No candidates")
                break

            # Generate composites at Step 3+
            if step.step_number >= 3:
                max_cols = 3 if step.step_number >= 4 else 2
                new_composites = self.decision_engine.generate_composites(
                    active_candidates, step, max_cols
                )
                composites.extend(new_composites)

            # Create sample temp table
            temp_table = self._create_step_sample(schema, table, step, seed_col)

            # Execute cardinality query (batched if needed)
            col_names = [c.column_name for c in step_cols]
            comp_cols = [comp.columns for comp in composites]

            try:
                results = self._execute_batched_query(
                    temp_table or f"[{schema}].[{table}]",
                    col_names,
                    comp_cols,
                )
            except Exception as e:
                self._logger.error(f"Step {step.step_number} query failed: {e}")
                self._cleanup_temp(temp_table)
                return self._create_result(
                    view_name, total_rows, total_cols, "error",
                    None, 0.0, start_time, 0, 0, 0, {}, [],
                    escalation_reason=str(e),
                )
            finally:
                self._cleanup_temp(temp_table)

            # Parse results
            row_count = results.get("_row_count", 0)
            selectivities = {
                k: v / row_count if row_count else 0.0
                for k, v in results.items()
                if k != "_row_count"
            }

            # Make decision
            decision = self.decision_engine.decide(
                step, candidates, composites, selectivities, row_count
            )

            step_duration = time.time() - step_start
            step_timings[step.step_number] = step_duration

            step_result = StepResult(
                step_number=step.step_number,
                row_sample=row_count,
                columns_tested=col_names,
                sample_rows=row_count,
                cardinalities={k: v for k, v in results.items() if k != "_row_count"},
                selectivities=selectivities,
                candidates_promoted=[
                    c.column_name for c in decision.promoted_candidates
                ],
                candidates_eliminated=decision.eliminated_candidates,
                best_candidate=decision.best_candidate,
                best_selectivity=decision.best_selectivity,
                duration_seconds=step_duration,
            )
            step_history.append(step_result)
            if progress_callback:
                progress_callback(step_result)

            self._logger.info(
                f"Step {step.step_number}: {row_count:,} rows, "
                f"best={decision.best_candidate} "
                f"({decision.best_selectivity:.1%} sel), "
                f"{step_duration:.1f}s"
            )

            # Early termination: stable high selectivity
            if len(step_history) >= 2 and decision.best_selectivity is not None:
                recent = [
                    s.best_selectivity for s in step_history[-3:]
                    if s.best_selectivity is not None
                ]
                if len(recent) >= 2:
                    current, prev = recent[-1], recent[-2]
                    stability = max(recent) - min(recent)

                    if current >= 0.95 and stability <= 0.02 and step.step_number >= 4:
                        pk_cols = self._parse_candidate(decision.best_candidate)
                        return self._create_result(
                            view_name, total_rows, total_cols, "confirmed",
                            pk_cols, current, start_time,
                            step.step_number, len(candidates), len(composites),
                            step_timings, step_history,
                        )

                    if step.step_number >= 4 and current < 0.85 and current <= prev:
                        return self._create_result(
                            view_name, total_rows, total_cols, "escalated",
                            None, 0.0, start_time,
                            step.step_number, len(candidates), len(composites),
                            step_timings, step_history,
                            escalation_reason=(
                                f"Selectivity {current:.1%} declining below 85%"
                            ),
                        )

            if decision.pk_found:
                return self._create_result(
                    view_name, total_rows, total_cols, "confirmed",
                    decision.pk_columns, 1.0, start_time,
                    step.step_number, len(candidates), len(composites),
                    step_timings, step_history,
                )

            if decision.skip_to_validation and step.step_number >= 3:
                pk_cols = self._parse_candidate(decision.best_candidate)
                return self._create_result(
                    view_name, total_rows, total_cols, "confirmed",
                    pk_cols, decision.best_selectivity or 0.99, start_time,
                    step.step_number, len(candidates), len(composites),
                    step_timings, step_history,
                )

            if decision.escalate:
                return self._create_result(
                    view_name, total_rows, total_cols, "escalated",
                    None, 0.0, start_time,
                    step.step_number, len(candidates), len(composites),
                    step_timings, step_history,
                    escalation_reason=decision.escalation_reason,
                )

            candidates = decision.promoted_candidates + [
                c for c in candidates if c.is_eliminated()
            ]
            composites = decision.promoted_composites

        # Use best from last step
        best = step_history[-1].best_candidate if step_history else None
        if best:
            pk_cols = self._parse_candidate(best)
            return self._create_result(
                view_name, total_rows, total_cols, "confirmed",
                pk_cols, step_history[-1].best_selectivity or 0.0, start_time,
                len(self.steps), len(candidates), len(composites),
                step_timings, step_history,
            )

        return self._create_result(
            view_name, total_rows, total_cols, "escalated",
            None, 0.0, start_time,
            len(self.steps), len(candidates), len(composites),
            step_timings, step_history,
            escalation_reason="No viable candidate after all steps",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_view_name(self, view_name: str) -> tuple[str, str]:
        parts = view_name.replace("[", "").replace("]", "").split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid view name format: {view_name}")
        return parts[0], parts[1]

    def _parse_candidate(self, name: str | None) -> list[str] | None:
        if not name:
            return None
        return name.split(" + ") if " + " in name else [name]

    def _get_row_count(self, schema: str, table: str) -> int:
        sql = self.dialect.row_count_query(schema, table)
        old_timeout = self.dialect.set_timeout(self.cursor, 300)
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
        finally:
            self.dialect.set_timeout(self.cursor, old_timeout)
        return int(row[0]) if row and row[0] else 0

    def _get_column_inventory(self, schema: str, table: str) -> list[dict]:
        sql = self.dialect.column_metadata_query(schema, table)
        self.cursor.execute(sql)
        return [
            {"name": r[0], "type": r[1], "ordinal": r[2]}
            for r in self.cursor.fetchall()
        ]

    def _get_pk_priority(self, column_name: str) -> int:
        for pattern, priority in PK_PATTERNS:
            if pattern.match(column_name):
                return priority
        return 5

    def _select_seed_column(
        self, schema: str, table: str, columns: list[str]
    ) -> str:
        try:
            test_cols = columns[:30]
            sql = self.dialect.seed_column_query(schema, table, test_cols)
            old_timeout = self.dialect.set_timeout(self.cursor, 300)
            try:
                self.cursor.execute(sql)
                row = self.cursor.fetchone()
            finally:
                self.dialect.set_timeout(self.cursor, old_timeout)

            best_col, best_card = columns[0], 0
            for i, col in enumerate(test_cols):
                card = row[i] if row and row[i] is not None else 0
                if card > best_card:
                    best_card = card
                    best_col = col
            self._logger.info(f"  Seed column: {best_col} ({best_card} unique)")
            return best_col
        except Exception as e:
            self._logger.warning(f"  Seed selection failed: {e}")
            return columns[0]

    def _create_step_sample(
        self, schema: str, table: str, step: ScanStep, seed_col: str,
    ) -> str | None:
        """Create or reuse a sample temp table. Returns name or None."""
        if self._sample_pool is not None:
            return self._sample_pool.get_sample(step.row_sample_pct)
        # No pool -- create ad-hoc temp
        temp_name = f"#scan_{step.step_number}_{int(time.time())}"
        sql = self.dialect.create_sample_table(
            temp_name, schema, table, seed_col, step.row_sample_pct,
        )
        try:
            old_timeout = self.dialect.set_timeout(self.cursor, 600)
            try:
                self.cursor.execute(sql)
            finally:
                self.dialect.set_timeout(self.cursor, old_timeout)
            self.dialect.drain_cursor(self.cursor)
            return temp_name
        except Exception as e:
            self._logger.warning(f"  Temp table creation failed: {e}")
            return None

    def _cleanup_temp(self, temp_name: str | None) -> None:
        if not temp_name or (self._sample_pool is not None):
            return  # Pool manages its own temps
        try:
            self.cursor.execute(self.dialect.drop_temp_table(temp_name))
            self.dialect.drain_cursor(self.cursor)
        except Exception:
            pass

    def _execute_batched_query(
        self,
        source: str,
        columns: list[str],
        composites: list[list[str]],
    ) -> dict[str, int]:
        """Execute cardinality query, batching if needed."""
        total_exprs = len(columns) + len(composites)
        if total_exprs <= CARDINALITY_BATCH_SIZE:
            return self._execute_single_query(source, columns, composites)

        results: dict[str, int] = {}
        for batch_start in range(0, len(columns), CARDINALITY_BATCH_SIZE):
            batch_cols = columns[batch_start:batch_start + CARDINALITY_BATCH_SIZE]
            batch_comps = composites if batch_start == 0 else []
            batch_results = self._execute_single_query(
                source, batch_cols, batch_comps
            )
            if not results:
                results = batch_results
            else:
                for k, v in batch_results.items():
                    if k != "_row_count":
                        results[k] = v
        return results

    def _execute_single_query(
        self,
        source: str,
        columns: list[str],
        composites: list[list[str]],
    ) -> dict[str, int]:
        sql = self.dialect.count_distinct(source, columns, composites)
        old_timeout = self.dialect.set_timeout(self.cursor, 600)
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
        finally:
            self.dialect.set_timeout(self.cursor, old_timeout)

        if not row:
            return {"_row_count": 0}

        results: dict[str, int] = {}
        desc = self.cursor.description
        for i, col_info in enumerate(desc):
            col_name = col_info[0]
            value = int(row[i]) if row[i] is not None else 0
            if col_name == "_row_count":
                results["_row_count"] = value
            elif col_name.startswith("card_"):
                idx = int(col_name[5:])
                results[columns[idx]] = value
            elif col_name.startswith("comp_"):
                idx = int(col_name[5:])
                if idx < len(composites):
                    key = " + ".join(composites[idx])
                    results[key] = value
        return results

    def _create_result(
        self,
        view_name: str,
        total_rows: int,
        total_cols: int,
        status: str,
        pk_columns: list[str] | None,
        confidence: float,
        start_time: datetime,
        steps_executed: int,
        candidates_tested: int,
        composites_tested: int,
        step_timings: dict[int, float],
        step_history: list[StepResult],
        escalation_reason: str | None = None,
    ) -> ScanResult:
        return ScanResult(
            view_name=view_name,
            total_rows=total_rows,
            total_cols=total_cols,
            status=status,
            primary_key=pk_columns,
            confidence=confidence,
            steps_executed=steps_executed,
            candidates_tested=candidates_tested,
            composites_tested=composites_tested,
            start_time=start_time,
            end_time=datetime.now(UTC),
            step_timings=step_timings,
            step_history=step_history,
            escalation_reason=escalation_reason,
        )
