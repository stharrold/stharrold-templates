# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""FK validation using progressive sampling and FULL OUTER JOIN.

Validates FK candidates with a 7-step progressive sampling algorithm:
    Step 1: 0.1% rows, test all FK pairs
    Step 2: 0.3% rows (0% disjoint early termination)
    Step 3: 1% rows (low-stable early termination)
    Step 4: 3% rows (escalation checkpoint)
    Step 5: 10% rows
    Step 6: 30% rows
    Step 7: 100% rows (full validation)

Early termination optimizations:
    1. 0% disjoint (step 2): populations are disjoint -> terminate
    2. High confirm (step 2): >= 99% stable -> confirm valid
    3. Low stable (step 3): < 50% stable across 3 steps -> terminate
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from data_catalog.services.sql_dialect import SQLDialect
from data_catalog.services.fk_discovery import FKCandidate, FKValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationStep:
    """Configuration for a single validation step."""

    step_number: int
    row_pct: float
    integrity_threshold: float
    timeout_seconds: int


VALIDATION_STEPS = [
    ValidationStep(1, 0.1, 90.0, 60),
    ValidationStep(2, 0.3, 95.0, 120),
    ValidationStep(3, 1.0, 97.0, 180),
    ValidationStep(4, 3.0, 98.0, 300),
    ValidationStep(5, 10.0, 99.0, 300),
    ValidationStep(6, 30.0, 99.5, 300),
    ValidationStep(7, 100.0, 99.9, 600),
]


class ProgressiveFKValidator:
    """Validates FK candidates using progressive sampling.

    Args:
        cursor: Database cursor for source queries.
        dialect: SQL dialect for query generation. If None, uses
            a default that may not work for your database.
    """

    FK_INTEGRITY_THRESHOLD = 99.0
    PROGRESSIVE_THRESHOLD = 100_000

    def __init__(
        self,
        cursor: Any,
        dialect: SQLDialect | None = None,
    ) -> None:
        self.cursor = cursor
        self.dialect = dialect
        self._logger = logging.getLogger(
            f"{__name__}.ProgressiveFKValidator"
        )

    def validate(
        self,
        candidate: FKCandidate,
        full_validation: bool = False,
    ) -> FKValidationResult:
        """Validate FK candidate using progressive sampling.

        Args:
            candidate: FK candidate to validate.
            full_validation: If True, skip directly to 100% validation.

        Returns:
            FKValidationResult with integrity metrics.
        """
        self._logger.info(
            f"Validating FK: {candidate.parent_view} -> "
            f"{candidate.referenced_view}"
        )

        fk_row_count = self._get_row_count(candidate.parent_view)
        pk_row_count = self._get_row_count(candidate.referenced_view)

        if fk_row_count == 0:
            return FKValidationResult(
                candidate=candidate,
                error="FK table is empty",
            )

        if full_validation or fk_row_count < self.PROGRESSIVE_THRESHOLD:
            return self._validate_at_step(
                candidate,
                VALIDATION_STEPS[-1],
                fk_row_count,
                pk_row_count,
            )

        return self._validate_progressive(
            candidate,
            fk_row_count,
            pk_row_count,
        )

    def validate_bidirectional(
        self, candidate: FKCandidate
    ) -> tuple[FKValidationResult, FKValidationResult]:
        """Validate FK in both directions to determine cardinality."""
        forward = self.validate(candidate)

        reverse_candidate = FKCandidate(
            parent_view=candidate.referenced_view,
            parent_columns=candidate.referenced_columns,
            referenced_view=candidate.parent_view,
            referenced_columns=candidate.parent_columns,
            pattern_name=candidate.pattern_name,
            evidence={"direction": "reverse"},
        )
        reverse = self.validate(reverse_candidate)

        return forward, reverse

    def _validate_progressive(
        self,
        candidate: FKCandidate,
        fk_row_count: int,
        pk_row_count: int,
    ) -> FKValidationResult:
        """Run progressive validation with early termination."""
        last_result: FKValidationResult | None = None
        match_history: list[float] = []

        for step in VALIDATION_STEPS:
            start_time = time.time()

            try:
                result = self._validate_at_step(
                    candidate,
                    step,
                    fk_row_count,
                    pk_row_count,
                )
                result.step_number = step.step_number
                result.duration_seconds = time.time() - start_time

                last_result = result
                match_history.append(result.match_pct)

                self._logger.info(
                    f"Step {step.step_number}: "
                    f"match={result.match_pct:.1f}%"
                )

                # Early termination: 0% disjoint
                if step.step_number >= 2 and result.match_pct == 0.0:
                    self._logger.info(
                        "Early termination: 0% match - disjoint"
                    )
                    return result

                # Early confirmation: stable >= 99%
                if step.step_number >= 2 and result.match_pct >= 99.0:
                    if len(match_history) >= 2:
                        prev = match_history[-2]
                        if (
                            prev >= 99.0
                            and abs(result.match_pct - prev) <= 2.0
                        ):
                            self._logger.info(
                                f"Early confirmation: "
                                f"{result.match_pct:.1f}% stable"
                            )
                            return result

                # Early termination: stable low
                if step.step_number >= 3 and result.match_pct < 50.0:
                    if len(match_history) >= 3:
                        recent = match_history[-3:]
                        if max(recent) - min(recent) <= 5.0:
                            self._logger.info(
                                f"Early termination: "
                                f"{result.match_pct:.1f}% stable low"
                            )
                            return result

            except Exception as e:
                self._logger.warning(
                    f"Step {step.step_number} failed: {e}"
                )
                if last_result:
                    return last_result
                return FKValidationResult(
                    candidate=candidate,
                    error=str(e),
                )

        return last_result or FKValidationResult(candidate=candidate)

    def _validate_at_step(
        self,
        candidate: FKCandidate,
        step: ValidationStep,
        fk_row_count: int,
        pk_row_count: int,
    ) -> FKValidationResult:
        """Execute a single validation step."""
        if not self.dialect:
            return FKValidationResult(
                candidate=candidate,
                error="No dialect configured for validation",
            )

        # Build column mappings
        mappings = list(
            zip(candidate.parent_columns, candidate.referenced_columns)
        )

        # Determine seed column for sampling
        seed_col = (
            candidate.parent_columns[0]
            if candidate.parent_columns
            else None
        )

        sql = self.dialect.fk_validation_query(
            fk_table=candidate.parent_view,
            pk_table=candidate.referenced_view,
            column_mappings=mappings,
            sample_pct=step.row_pct,
            seed_col=seed_col if step.row_pct < 100 else None,
        )

        old_timeout = self.dialect.set_timeout(
            self.cursor, step.timeout_seconds
        )
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
        finally:
            self.dialect.set_timeout(self.cursor, old_timeout)

        if not row:
            return FKValidationResult(candidate=candidate)

        match_count = int(row[0] or 0)
        orphan_count = int(row[1] or 0)
        pk_only_count = int(row[2] or 0)

        total = match_count + orphan_count
        match_pct = (match_count / total * 100) if total > 0 else 0.0
        orphan_pct = (orphan_count / total * 100) if total > 0 else 0.0

        return FKValidationResult(
            candidate=candidate,
            match_pct=match_pct,
            orphan_pct=orphan_pct,
            match_count=match_count,
            orphan_count=orphan_count,
            pk_only_count=pk_only_count,
            total_fk_rows=fk_row_count,
            total_pk_rows=pk_row_count,
        )

    def _get_row_count(self, qualified_name: str) -> int:
        """Get row count for a qualified table name."""
        if not self.dialect:
            return 0
        parts = (
            qualified_name.replace("[", "").replace("]", "").split(".")
        )
        if len(parts) != 2:
            return 0
        sql = self.dialect.row_count_query(parts[0], parts[1])
        old_timeout = self.dialect.set_timeout(self.cursor, 300)
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
        finally:
            self.dialect.set_timeout(self.cursor, old_timeout)
        return int(row[0]) if row and row[0] else 0
