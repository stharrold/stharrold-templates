# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Data model definitions for pipeline configuration and results.

Dataclasses for pipeline phases, grain discovery results, and
graph analysis configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class GrainResult:
    """Result of grain (PK) discovery for a single asset.

    Attributes:
        qualified_name: Fully qualified asset name.
        status: Discovery outcome.
        primary_key: Business PK columns (uniqueness-minimized).
        pk_minimal: FD-minimized architectural PK (may be smaller).
        fd_removed: Columns removed by functional dependency analysis.
        method: Discovery method name.
        confidence: Confidence score (0.0-1.0).
        metadata: Additional discovery metadata.
    """

    qualified_name: str
    status: Literal["confirmed", "no_natural_pk", "unknown", "error"]
    primary_key: list[str] | None = None
    pk_minimal: list[str] | None = None
    fd_removed: list[str] | None = None
    method: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelinePhaseConfig:
    """Configuration for a single pipeline phase.

    Attributes:
        name: Phase name (e.g. "pk_discovery", "fk_discovery").
        enabled: Whether this phase is enabled.
        depends_on: Phases that must complete first.
        options: Phase-specific options.
    """

    name: str
    enabled: bool = True
    depends_on: list[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Configuration for the full 11-phase pipeline.

    Attributes:
        phases: Ordered list of phase configurations.
        batches: Named sets of assets to process.
        source_connection: Source database connection info.
    """

    phases: list[PipelinePhaseConfig] = field(default_factory=list)
    batches: dict[str, dict] = field(default_factory=dict)
    source_connection: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def default(cls) -> PipelineConfig:
        """Create default 11-phase pipeline configuration."""
        return cls(
            phases=[
                PipelinePhaseConfig("seed"),
                PipelinePhaseConfig(
                    "enrich", depends_on=["seed"]
                ),
                PipelinePhaseConfig(
                    "pipeline", depends_on=["enrich"]
                ),
                PipelinePhaseConfig(
                    "vectors", depends_on=["pipeline"]
                ),
                PipelinePhaseConfig(
                    "fk", depends_on=["enrich", "vectors"]
                ),
                PipelinePhaseConfig(
                    "col_populate", depends_on=["fk"]
                ),
                PipelinePhaseConfig("col_prepare"),
                PipelinePhaseConfig(
                    "col_describe", depends_on=["col_prepare"]
                ),
                PipelinePhaseConfig(
                    "col_import", depends_on=["col_describe"]
                ),
                PipelinePhaseConfig(
                    "col_embed", depends_on=["col_import"]
                ),
                PipelinePhaseConfig(
                    "graph_analyze", depends_on=["col_embed"]
                ),
            ]
        )


@dataclass
class GraphConfig:
    """Configuration for graph analysis.

    Attributes:
        min_cluster_size: Minimum cluster size for HDBSCAN.
        expand_hops: BFS expansion depth for RAG search.
        pagerank_alpha: PageRank damping factor.
    """

    min_cluster_size: int = 3
    expand_hops: int = 1
    pagerank_alpha: float = 0.85


@dataclass
class BatchDefinition:
    """Definition of a pipeline batch (set of assets).

    Attributes:
        name: Batch name.
        schema: Source database schema.
        tables: Table/view names to include.
        asset_type: Asset type (table or view).
    """

    name: str
    schema: str
    tables: list[str] = field(default_factory=list)
    asset_type: str = "table"
