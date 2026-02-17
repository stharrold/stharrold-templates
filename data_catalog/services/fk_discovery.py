# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""FK discovery service using pattern matching and semantic similarity.

Discovers foreign key relationships between assets by:
1. Pattern matching (naming conventions, composite keys)
2. Semantic similarity (vector comparison of column values)
3. Validation against source database (progressive sampling)

The discovery flow:
    assets -> patterns -> candidates -> dedup -> rank -> validate
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from data_catalog.db.models import Asset, ColumnVector, Relationship
from data_catalog.utils.sql_safety import validate_identifier

logger = logging.getLogger(__name__)


@dataclass
class FKCandidate:
    """A candidate foreign key relationship."""

    parent_view: str          # FK table (child)
    parent_columns: list[str]
    referenced_view: str      # PK table (parent)
    referenced_columns: list[str]
    pattern_name: str         # Which pattern discovered this
    priority: int = 5
    confidence: float = 0.0
    relationship_type: str = "implicit"
    evidence: dict = field(default_factory=dict)


@dataclass
class FKValidationResult:
    """Result of validating an FK candidate against the source database."""

    candidate: FKCandidate
    match_pct: float = 0.0
    orphan_pct: float = 0.0
    pk_only_pct: float = 0.0
    total_fk_rows: int = 0
    total_pk_rows: int = 0
    match_count: int = 0
    orphan_count: int = 0
    pk_only_count: int = 0
    step_number: int = 0
    duration_seconds: float = 0.0
    error: str | None = None


@dataclass
class FKDiscoveryResult:
    """Result of FK discovery for a single asset pair."""

    parent_asset: str
    referenced_asset: str
    candidates: list[FKCandidate] = field(default_factory=list)
    validation: FKValidationResult | None = None
    has_relationship: bool = False
    cardinality: str | None = None  # '1:1', '1:N', 'N:M'


class FKDiscoveryService:
    """Discovers FK relationships using pattern matching.

    This is the pattern-only discovery service (no source DB validation).
    For validated discovery, use ExtendedFKDiscoveryService which adds
    progressive sampling validation.

    Args:
        db: SQLAlchemy session for the catalog metadata store.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self._logger = logging.getLogger(f"{__name__}.FKDiscoveryService")

    def discover_candidates(
        self,
        asset: Asset,
        all_assets: list[Asset] | None = None,
        fk_top_n_per_column: int = 3,
    ) -> list[FKCandidate]:
        """Discover FK candidates for an asset using pattern matching.

        Args:
            asset: The asset to discover FKs for.
            all_assets: All assets to match against (loaded if None).
            fk_top_n_per_column: Max candidates per column.

        Returns:
            List of FK candidates ranked by priority.
        """
        if all_assets is None:
            all_assets = (
                self.db.query(Asset)
                .filter(Asset.asset_type.in_(["view", "table"]))
                .all()
            )

        # Get PK columns for target assets
        pk_map = self._build_pk_map(all_assets)
        if not pk_map:
            self._logger.warning("No assets with confirmed PKs found")
            return []

        # Get source columns
        source_columns = self._get_asset_columns(asset)
        if not source_columns:
            return []

        # Run patterns
        from data_catalog.services.fk_patterns import FKPatternRegistry

        registry = FKPatternRegistry()
        registry.register_defaults()

        candidates: list[FKCandidate] = []
        seen: set[str] = set()

        for pattern in registry.get_patterns():
            for col_name in source_columns:
                for target_name, pk_cols in pk_map.items():
                    if target_name == asset.qualified_name:
                        continue  # Skip self

                    matches = pattern.match(
                        col_name, target_name, pk_cols, asset.qualified_name
                    )
                    for match in matches:
                        key = (
                            f"{match.parent_view}:{match.parent_columns}->"
                            f"{match.referenced_view}:{match.referenced_columns}"
                        )
                        if key not in seen:
                            seen.add(key)
                            candidates.append(match)

        # Rank and deduplicate
        candidates.sort(key=lambda c: (c.priority, -c.confidence))

        # Top N per column
        if fk_top_n_per_column:
            col_counts: dict[str, int] = {}
            filtered = []
            for c in candidates:
                col_key = "|".join(c.parent_columns)
                count = col_counts.get(col_key, 0)
                if count < fk_top_n_per_column:
                    filtered.append(c)
                    col_counts[col_key] = count + 1
            candidates = filtered

        self._logger.info(
            f"Discovered {len(candidates)} FK candidates for "
            f"{asset.qualified_name}"
        )
        return candidates

    def _build_pk_map(self, assets: list[Asset]) -> dict[str, list[str]]:
        """Build map of qualified_name -> PK columns."""
        pk_map: dict[str, list[str]] = {}
        for asset in assets:
            meta = asset.schema_metadata or {}
            # Check pk_minimal first, then primary_key, then pk_columns
            pk = (
                meta.get("pk_minimal")
                or meta.get("primary_key")
                or meta.get("pk_columns")
            )
            if pk and meta.get("grain_status") == "confirmed":
                pk_map[asset.qualified_name] = pk
        return pk_map

    def _get_asset_columns(self, asset: Asset) -> list[str]:
        """Get column names from asset metadata."""
        meta = asset.schema_metadata or {}
        columns = meta.get("columns", [])
        return [
            c["name"] for c in columns if isinstance(c, dict) and "name" in c
        ]


class ExtendedFKDiscoveryService(FKDiscoveryService):
    """FK discovery with source database validation.

    Extends FKDiscoveryService with progressive sampling validation
    against the source database.

    Args:
        db: SQLAlchemy session.
        source_cursor: Database cursor for source queries.
        dialect: SQL dialect for query generation.
    """

    def __init__(
        self, db: Session, source_cursor: Any, dialect: Any = None
    ) -> None:
        super().__init__(db)
        self.source_cursor = source_cursor
        self.dialect = dialect

    def discover_with_validation(
        self,
        asset: Asset,
        all_assets: list[Asset] | None = None,
    ) -> list[FKDiscoveryResult]:
        """Discover and validate FK candidates.

        Returns:
            List of FKDiscoveryResult with validation metrics.
        """
        from data_catalog.services.fk_validator import ProgressiveFKValidator

        candidates = self.discover_candidates(asset, all_assets)
        results: list[FKDiscoveryResult] = []

        if not candidates or not self.source_cursor:
            return results

        validator = ProgressiveFKValidator(
            self.source_cursor, dialect=self.dialect
        )

        for candidate in candidates:
            try:
                validation = validator.validate(candidate)
                result = FKDiscoveryResult(
                    parent_asset=candidate.parent_view,
                    referenced_asset=candidate.referenced_view,
                    candidates=[candidate],
                    validation=validation,
                    has_relationship=validation.match_pct >= 99.0,
                )
                results.append(result)
            except Exception as e:
                self._logger.warning(
                    f"Validation failed for {candidate.parent_view} -> "
                    f"{candidate.referenced_view}: {e}"
                )
                result = FKDiscoveryResult(
                    parent_asset=candidate.parent_view,
                    referenced_asset=candidate.referenced_view,
                    candidates=[candidate],
                    has_relationship=False,
                )
                results.append(result)

        return results
