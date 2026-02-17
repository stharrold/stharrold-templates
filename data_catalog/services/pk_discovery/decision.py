# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Decision Engine for PK Discovery.

Implements decision logic for the progressive scanning algorithm:
candidate promotion/elimination, escalation rules, composite key generation.

Decision Rules:
    - Step 1: Eliminate if selectivity < 0.5
    - Step 2: Eliminate if selectivity < 0.3
    - Step 4: Escalate if best selectivity < 0.8
    - Any step: Promote immediately if selectivity = 1.0
"""

import logging
from itertools import combinations

from data_catalog.services.pk_discovery.models import (
    ColumnCandidate,
    CompositeCandidate,
    Decision,
    ScanStep,
)

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Makes decisions about candidate promotion, elimination, and escalation."""

    STEP_THRESHOLDS = {
        1: 0.5,
        2: 0.3,
        3: 0.2,
        4: 0.1,
        5: 0.05,
        6: 0.05,
        7: 0.0,
    }

    ESCALATION_THRESHOLD = 0.8
    ESCALATION_STEP = 4
    PERFECT_SELECTIVITY = 1.0
    MAX_COMPOSITE_COLS = 5
    MAX_COMPOSITES_PER_STEP = 50
    COMPOSITE_START_STEP = 3

    def __init__(self) -> None:
        self._logger = logging.getLogger(f"{__name__}.DecisionEngine")

    def decide(
        self,
        step: ScanStep,
        candidates: list[ColumnCandidate],
        composites: list[CompositeCandidate],
        selectivities: dict[str, float],
        row_count: int,
    ) -> Decision:
        decision = Decision()

        perfect_candidates = self._find_perfect_candidates(
            candidates, composites, selectivities
        )
        if perfect_candidates:
            self._logger.info(
                f"Step {step.step_number}: Found perfect candidate(s): "
                f"{perfect_candidates}"
            )
            decision.pk_found = True
            decision.pk_columns = perfect_candidates
            decision.best_candidate = (
                perfect_candidates[0]
                if len(perfect_candidates) == 1
                else " + ".join(perfect_candidates)
            )
            decision.best_selectivity = 1.0
            return decision

        if step.step_number >= self.ESCALATION_STEP:
            best_selectivity = self._get_best_selectivity(
                candidates, composites, selectivities
            )
            if best_selectivity < self.ESCALATION_THRESHOLD:
                self._logger.warning(
                    f"Step {step.step_number}: Best selectivity "
                    f"{best_selectivity:.1%} < {self.ESCALATION_THRESHOLD:.0%} "
                    f"threshold - escalating"
                )
                decision.escalate = True
                decision.escalation_reason = (
                    f"Best selectivity {best_selectivity:.1%} < "
                    f"{self.ESCALATION_THRESHOLD:.0%} at Step {step.step_number}"
                )
                decision.best_selectivity = best_selectivity
                return decision

        threshold = self._get_threshold(step.step_number)
        promoted, eliminated = self._partition_candidates(
            candidates, selectivities, threshold, step.step_number
        )

        decision.promoted_candidates = promoted
        decision.eliminated_candidates = [
            c.column_name for c in candidates if c.is_eliminated()
        ]

        promoted_composites = self._filter_composites(
            composites, selectivities, threshold, step.step_number
        )
        decision.promoted_composites = promoted_composites

        best_name, best_sel = self._get_best_candidate(
            promoted, promoted_composites, selectivities
        )
        decision.best_candidate = best_name
        decision.best_selectivity = best_sel if best_sel is not None else 0.0

        if best_sel and best_sel >= 0.99:
            decision.skip_to_validation = True
            self._logger.info(
                f"Step {step.step_number}: High selectivity {best_sel:.1%} "
                f"- skipping to validation"
            )

        return decision

    def generate_composites(
        self,
        candidates: list[ColumnCandidate],
        step: ScanStep,
        max_cols: int = 2,
    ) -> list[CompositeCandidate]:
        if step.step_number < self.COMPOSITE_START_STEP:
            return []

        active = [c for c in candidates if not c.is_eliminated()]
        active.sort(key=lambda c: c.latest_selectivity(), reverse=True)

        top_n = min(10, len(active))
        top_candidates = active[:top_n]

        composites: list[CompositeCandidate] = []

        for size in range(2, max_cols + 1):
            for combo in combinations(top_candidates, size):
                if len(composites) >= self.MAX_COMPOSITES_PER_STEP:
                    break
                columns = [c.column_name for c in combo]
                composites.append(CompositeCandidate(columns=columns))
            if len(composites) >= self.MAX_COMPOSITES_PER_STEP:
                break

        self._logger.debug(
            f"Step {step.step_number}: Generated {len(composites)} "
            f"composite candidates"
        )
        return composites

    def calculate_selectivity(self, distinct_count: int, total_rows: int) -> float:
        if total_rows == 0:
            return 0.0
        return distinct_count / total_rows

    def _find_perfect_candidates(
        self,
        candidates: list[ColumnCandidate],
        composites: list[CompositeCandidate],
        selectivities: dict[str, float],
    ) -> list[str] | None:
        for candidate in candidates:
            if candidate.is_eliminated():
                continue
            sel = selectivities.get(candidate.column_name, 0.0)
            if sel >= self.PERFECT_SELECTIVITY:
                return [candidate.column_name]

        for composite in composites:
            key = composite.key_string()
            sel = selectivities.get(key, 0.0)
            if sel >= self.PERFECT_SELECTIVITY:
                return composite.columns

        return None

    def _get_best_selectivity(
        self,
        candidates: list[ColumnCandidate],
        composites: list[CompositeCandidate],
        selectivities: dict[str, float],
    ) -> float:
        best = 0.0
        for candidate in candidates:
            if candidate.is_eliminated():
                continue
            sel = selectivities.get(candidate.column_name, 0.0)
            best = max(best, sel)
        for composite in composites:
            key = composite.key_string()
            sel = selectivities.get(key, 0.0)
            best = max(best, sel)
        return best

    def _get_threshold(self, step_number: int) -> float:
        return self.STEP_THRESHOLDS.get(step_number, 0.0)

    def _partition_candidates(
        self,
        candidates: list[ColumnCandidate],
        selectivities: dict[str, float],
        threshold: float,
        step_number: int,
    ) -> tuple[list[ColumnCandidate], list[ColumnCandidate]]:
        promoted: list[ColumnCandidate] = []
        eliminated: list[ColumnCandidate] = []

        for candidate in candidates:
            if candidate.is_eliminated():
                eliminated.append(candidate)
                continue
            sel = selectivities.get(candidate.column_name, 0.0)
            candidate.selectivity[step_number] = sel
            if sel < threshold:
                candidate.eliminated_at_step = step_number
                candidate.elimination_reason = (
                    f"Selectivity {sel:.1%} < {threshold:.0%} threshold"
                )
                eliminated.append(candidate)
            else:
                promoted.append(candidate)
        return promoted, eliminated

    def _filter_composites(
        self,
        composites: list[CompositeCandidate],
        selectivities: dict[str, float],
        threshold: float,
        step_number: int,
    ) -> list[CompositeCandidate]:
        promoted: list[CompositeCandidate] = []
        for composite in composites:
            key = composite.key_string()
            sel = selectivities.get(key, 0.0)
            composite.selectivity[step_number] = sel
            if sel >= threshold:
                promoted.append(composite)
        return promoted

    def _get_best_candidate(
        self,
        candidates: list[ColumnCandidate],
        composites: list[CompositeCandidate],
        selectivities: dict[str, float],
    ) -> tuple[str | None, float | None]:
        best_name: str | None = None
        best_sel: float = 0.0

        for candidate in candidates:
            sel = selectivities.get(candidate.column_name, 0.0)
            if sel > best_sel:
                best_sel = sel
                best_name = candidate.column_name

        for composite in composites:
            key = composite.key_string()
            sel = selectivities.get(key, 0.0)
            if sel > best_sel:
                best_sel = sel
                best_name = key

        return best_name, best_sel if best_name else None
