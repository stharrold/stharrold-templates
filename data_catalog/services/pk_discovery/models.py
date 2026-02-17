# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Data models for PK Discovery.

Defines the dataclasses used throughout the progressive scanning
algorithm for configuration, state tracking, and results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class ScanStep:
    """Configuration for a single progressive scan step.

    The progressive algorithm uses 7 steps with inverse progression:
    - Early steps: small row samples, many columns
    - Later steps: large row samples, few columns
    """

    step_number: int
    row_sample_pct: float
    col_subset_pct: float
    row_count: int = 0
    col_count: int = 0
    timeout_seconds: int = 300


@dataclass
class ColumnCandidate:
    """Tracks a column through progressive scanning."""

    column_name: str
    data_type: str
    ordinal_position: int
    pk_priority: int = 5
    selectivity: dict[int, float] = field(default_factory=dict)
    eliminated_at_step: int | None = None
    elimination_reason: str | None = None

    def is_eliminated(self) -> bool:
        return self.eliminated_at_step is not None

    def latest_selectivity(self) -> float:
        if not self.selectivity:
            return 0.0
        return self.selectivity[max(self.selectivity.keys())]


@dataclass
class CompositeCandidate:
    """Tracks a composite key candidate."""

    columns: list[str]
    selectivity: dict[int, float] = field(default_factory=dict)

    @property
    def column_count(self) -> int:
        return len(self.columns)

    def key_string(self) -> str:
        return " + ".join(self.columns)

    def latest_selectivity(self) -> float:
        if not self.selectivity:
            return 0.0
        return self.selectivity[max(self.selectivity.keys())]


@dataclass
class StepResult:
    """Result of a single scan step."""

    step_number: int
    row_sample: int
    columns_tested: list[str]
    sample_rows: int
    cardinalities: dict[str, int]
    selectivities: dict[str, float]
    candidates_promoted: list[str]
    candidates_eliminated: list[str]
    best_candidate: str | None
    best_selectivity: float | None
    duration_seconds: float


@dataclass
class ScanResult:
    """Final result of progressive scanning."""

    view_name: str
    total_rows: int
    total_cols: int
    status: Literal["confirmed", "escalated", "error"]
    primary_key: list[str] | None
    confidence: float
    steps_executed: int
    candidates_tested: int
    composites_tested: int
    start_time: datetime
    end_time: datetime
    step_timings: dict[int, float]
    step_history: list[StepResult]
    escalation_reason: str | None = None

    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()

    def to_metadata_dict(self) -> dict:
        return {
            "method": "progressive_scan_v3",
            "discovered_at": self.end_time.isoformat(),
            "status": self.status,
            "steps_executed": self.steps_executed,
            "candidates_tested": self.candidates_tested,
            "composites_tested": self.composites_tested,
            "duration_seconds": self.duration_seconds,
            "confidence": self.confidence,
            "escalation_reason": self.escalation_reason,
            "step_timings": self.step_timings,
        }


@dataclass
class Decision:
    """Decision made by the DecisionEngine after a step."""

    pk_found: bool = False
    pk_columns: list[str] | None = None
    escalate: bool = False
    escalation_reason: str | None = None
    skip_to_validation: bool = False
    promoted_candidates: list[ColumnCandidate] = field(default_factory=list)
    promoted_composites: list[CompositeCandidate] = field(default_factory=list)
    eliminated_candidates: list[str] = field(default_factory=list)
    best_candidate: str | None = None
    best_selectivity: float | None = None
