# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Pipeline orchestrator for data catalog discovery.

Coordinates all phases of the discovery pipeline with unified progress
tracking, transaction boundaries, and error handling.

Phases:
1. PK Discovery - Pattern-based and progressive scanning
2. Cardinality Scanning - Column cardinality at progressive sample levels
3. Value Frequencies - Top-N values per column (UNPIVOT + fallback)
4. Semantic Vectors - ONNX centroid vectors from value frequencies
5. FK Discovery - Pattern-based + vector similarity candidates
6. FK Validation - Progressive FULL OUTER JOIN (7 steps)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from data_catalog.db.models import PipelinePhaseLog
from data_catalog.db.repositories import AssetRepository
from data_catalog.services.sql_dialect import SQLDialect

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the discovery pipeline."""

    schema_pattern: str
    """Schema pattern to analyze (e.g., 'dbo')"""

    sample_pct: float = 10.0
    top_n_values: int = 100
    min_fk_similarity: float = 0.85
    fk_top_n_per_column: int = 3
    fk_min_confidence: float = 0.75
    fk_max_vector_candidates: int = 500
    validate_fks: bool = True
    persist_results: bool = True

    # Phase control
    skip_pk_discovery: bool = False
    skip_cardinality: bool = False
    skip_frequencies: bool = False
    skip_semantic_vectors: bool = False


@dataclass
class PhaseResult:
    """Result from a single pipeline phase."""

    phase_name: str
    status: str  # 'success', 'skipped', 'error'
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    items_processed: int = 0
    items_total: int = 0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""

    schema_name: str
    started_at: datetime
    completed_at: datetime
    total_duration_seconds: float
    status: str  # 'success', 'partial', 'error'
    phases: list[PhaseResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # Aggregate metrics
    pk_discovered: int = 0
    pk_no_natural: int = 0
    cardinality_columns: int = 0
    frequency_columns: int = 0
    vectors_computed: int = 0
    fk_candidates: int = 0
    fk_confirmed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "total_duration_seconds": round(self.total_duration_seconds, 2),
            "status": self.status,
            "phases": [
                {
                    "phase_name": p.phase_name,
                    "status": p.status,
                    "duration_seconds": round(p.duration_seconds, 2),
                    "items_processed": p.items_processed,
                    "errors": p.errors,
                }
                for p in self.phases
            ],
            "metrics": {
                "pk_discovered": self.pk_discovered,
                "pk_no_natural": self.pk_no_natural,
                "cardinality_columns": self.cardinality_columns,
                "frequency_columns": self.frequency_columns,
                "vectors_computed": self.vectors_computed,
                "fk_candidates": self.fk_candidates,
                "fk_confirmed": self.fk_confirmed,
            },
            "errors": self.errors,
        }


class PipelineOrchestrator:
    """Orchestrates the complete data catalog discovery pipeline.

    Coordinates 6 phases with unified progress tracking, transaction
    boundaries, and error handling. Services are lazily initialized.

    Usage::

        from data_catalog.db.connection import get_db
        from data_catalog.services.pipeline_orchestrator import (
            PipelineOrchestrator, PipelineConfig,
        )

        with get_db() as db:
            orchestrator = PipelineOrchestrator(db, cursor, dialect)
            config = PipelineConfig(schema_pattern="dbo")
            result = orchestrator.run(config)
    """

    def __init__(
        self,
        db: Session,
        source_cursor: Any,
        dialect: SQLDialect,
        pk_config_path: Path | None = None,
        fk_config_path: Path | None = None,
    ) -> None:
        self.db = db
        self.source_cursor = source_cursor
        self.dialect = dialect
        self._pk_config_path = pk_config_path
        self._fk_config_path = fk_config_path
        self._repo: AssetRepository | None = None

        # Lazy service instances
        self._grain_service = None
        self._cardinality_scanner = None
        self._vector_service = None
        self._fk_service = None
        self._sample_pool = None

    @property
    def repo(self) -> AssetRepository:
        if self._repo is None:
            self._repo = AssetRepository(self.db)
        return self._repo

    def _get_sample_pool(self):
        """Lazy-init shared sample pool."""
        if self._sample_pool is None:
            from data_catalog.services.sample_pool import SamplePool
            self._sample_pool = SamplePool(
                self.source_cursor, self.dialect
            )
        return self._sample_pool

    def _log_phase(
        self,
        phase_name: str,
        status: str,
        duration: float,
        items: int = 0,
        error: str | None = None,
    ) -> None:
        """Log phase execution to PipelinePhaseLog."""
        log_entry = PipelinePhaseLog(
            id=str(uuid4()),
            phase_name=phase_name,
            status=status,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            duration_seconds=duration,
            items_processed=items,
            error_message=error,
        )
        self.db.add(log_entry)
        self.db.commit()

    def _run_phase(
        self,
        phase_name: str,
        phase_fn,
        config: PipelineConfig,
        progress_callback=None,
    ) -> PhaseResult:
        """Execute a single phase with timing and error handling."""
        started = datetime.now(UTC)
        t0 = time.time()

        try:
            result_meta = phase_fn(config, progress_callback)
            elapsed = time.time() - t0
            completed = datetime.now(UTC)

            phase_result = PhaseResult(
                phase_name=phase_name,
                status="success",
                started_at=started,
                completed_at=completed,
                duration_seconds=elapsed,
                items_processed=result_meta.get("items", 0),
                items_total=result_meta.get("total", 0),
                metadata=result_meta,
            )
            self._log_phase(phase_name, "success", elapsed, result_meta.get("items", 0))
            return phase_result

        except Exception as e:
            elapsed = time.time() - t0
            completed = datetime.now(UTC)
            error_msg = str(e)
            logger.error(f"Phase {phase_name} failed: {error_msg}")

            self._log_phase(phase_name, "error", elapsed, error=error_msg)
            return PhaseResult(
                phase_name=phase_name,
                status="error",
                started_at=started,
                completed_at=completed,
                duration_seconds=elapsed,
                errors=[error_msg],
            )

    def _phase_pk_discovery(self, config, callback=None) -> dict:
        """Phase 1: Discover primary keys for all assets."""
        from data_catalog.services.grain_discovery import GrainDiscoveryService

        service = GrainDiscoveryService(
            self.db,
            self.source_cursor,
            dialect=self.dialect,
            config_path=self._pk_config_path,
            sample_pool=self._get_sample_pool(),
        )

        assets = self.repo.find_by_schema_pattern(config.schema_pattern)
        discovered = 0
        no_pk = 0

        for i, asset in enumerate(assets, 1):
            if callback:
                callback("pk_discovery", {
                    "asset": asset.qualified_name,
                    "current": i,
                    "total": len(assets),
                })

            try:
                result = service.discover_grain(asset.qualified_name)
                if result.grain:
                    discovered += 1
                    service.sync_to_catalog(asset.qualified_name, result)
                elif result.method == "no-pk":
                    no_pk += 1
            except Exception as e:
                logger.warning(f"  PK discovery failed for {asset.qualified_name}: {e}")

        return {"items": discovered + no_pk, "total": len(assets),
                "discovered": discovered, "no_pk": no_pk}

    def _phase_cardinality(self, config, callback=None) -> dict:
        """Phase 2: Scan column cardinality."""
        from data_catalog.services.cardinality_scanner import CardinalityScanner

        scanner = CardinalityScanner(
            self.db, self.source_cursor, self.dialect,
            sample_pool=self._get_sample_pool(),
        )
        result = scanner.scan_schema(config.schema_pattern, callback)
        return {"items": result.get("assets_scanned", 0),
                "total_columns": result.get("total_columns", 0)}

    def _phase_frequencies(self, config, callback=None) -> dict:
        """Phase 3: Scan value frequencies."""
        from data_catalog.services.cardinality_scanner import CardinalityScanner

        scanner = CardinalityScanner(
            self.db, self.source_cursor, self.dialect,
            sample_pool=self._get_sample_pool(),
        )

        assets = self.repo.find_by_schema_pattern(config.schema_pattern)
        import re
        total_cols = 0
        for i, asset in enumerate(assets, 1):
            if callback:
                callback("frequencies", {
                    "asset": asset.qualified_name,
                    "current": i,
                    "total": len(assets),
                })
            match = re.match(r"\[([^\]]+)\]\.\[([^\]]+)\]", asset.qualified_name)
            if not match:
                continue
            schema, table = match.group(1), match.group(2)
            result = scanner.scan_frequencies(
                asset, schema, table,
                sample_pct=config.sample_pct,
                top_n=config.top_n_values,
            )
            total_cols += result.get("columns_scanned", 0)

        return {"items": len(assets), "total_columns": total_cols}

    def _phase_vectors(self, config, callback=None) -> dict:
        """Phase 4: Compute semantic vectors from frequencies."""
        from data_catalog.services.vector_similarity import VectorSimilarityService

        service = VectorSimilarityService(self.db)
        result = service.compute_semantic_vectors(config.schema_pattern)
        return {"items": result.get("vectors_computed", 0)}

    def _phase_fk_discovery(self, config, callback=None) -> dict:
        """Phase 5: Discover FK candidates."""
        from data_catalog.services.fk_discovery import FKDiscoveryService

        service = FKDiscoveryService(self.db)
        assets = self.repo.find_by_schema_pattern(config.schema_pattern)
        candidates = 0
        for asset in assets:
            results = service.discover_candidates(asset.qualified_name)
            candidates += len(results)
        return {"items": candidates, "total": len(assets)}

    def _phase_fk_validation(self, config, callback=None) -> dict:
        """Phase 6: Validate FK candidates against source database."""
        from data_catalog.services.fk_discovery import ExtendedFKDiscoveryService

        service = ExtendedFKDiscoveryService(
            self.db, self.source_cursor, self.dialect
        )
        assets = self.repo.find_by_schema_pattern(config.schema_pattern)
        confirmed = 0
        for i, asset in enumerate(assets, 1):
            if callback:
                callback("fk_validation", {
                    "asset": asset.qualified_name,
                    "current": i,
                    "total": len(assets),
                })
            try:
                results = service.discover_with_patterns(asset.qualified_name)
                confirmed += sum(
                    1 for r in results
                    if r.validation and r.validation.match_pct >= 99.0
                )
            except Exception as e:
                logger.warning(f"  FK validation failed for {asset.qualified_name}: {e}")

        return {"items": confirmed, "total": len(assets)}

    def run(
        self,
        config: PipelineConfig,
        progress_callback=None,
    ) -> PipelineResult:
        """Execute the full discovery pipeline.

        Args:
            config: Pipeline configuration.
            progress_callback: Optional callback(phase_name, info_dict).

        Returns:
            PipelineResult with per-phase details and aggregate metrics.
        """
        started = datetime.now(UTC)
        t0 = time.time()
        phases: list[PhaseResult] = []

        logger.info(f"Starting pipeline for schema: {config.schema_pattern}")

        # Phase 1: PK Discovery
        if not config.skip_pk_discovery:
            phase = self._run_phase(
                "pk_discovery", self._phase_pk_discovery, config, progress_callback
            )
            phases.append(phase)

        # Phase 2: Cardinality
        if not config.skip_cardinality:
            phase = self._run_phase(
                "cardinality", self._phase_cardinality, config, progress_callback
            )
            phases.append(phase)

        # Phase 3: Frequencies
        if not config.skip_frequencies:
            phase = self._run_phase(
                "frequencies", self._phase_frequencies, config, progress_callback
            )
            phases.append(phase)

        # Phase 4: Semantic Vectors
        if not config.skip_semantic_vectors:
            phase = self._run_phase(
                "vectors", self._phase_vectors, config, progress_callback
            )
            phases.append(phase)

        # Phase 5: FK Discovery
        phase = self._run_phase(
            "fk_discovery", self._phase_fk_discovery, config, progress_callback
        )
        phases.append(phase)

        # Phase 6: FK Validation
        if config.validate_fks:
            phase = self._run_phase(
                "fk_validation", self._phase_fk_validation, config, progress_callback
            )
            phases.append(phase)

        # Aggregate results
        elapsed = time.time() - t0
        completed = datetime.now(UTC)
        has_errors = any(p.status == "error" for p in phases)
        all_errors = any(p.status != "skipped" and p.status == "error" for p in phases)

        result = PipelineResult(
            schema_name=config.schema_pattern,
            started_at=started,
            completed_at=completed,
            total_duration_seconds=elapsed,
            status="error" if all_errors else ("partial" if has_errors else "success"),
            phases=phases,
            errors=[e for p in phases for e in p.errors],
        )

        logger.info(
            f"Pipeline complete: {result.status} in {elapsed:.1f}s "
            f"({len(phases)} phases)"
        )

        return result
