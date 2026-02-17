# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for pipeline orchestrator."""
from __future__ import annotations

from uuid import uuid4

import pytest

from data_catalog.db.models import Asset, PipelinePhaseLog
from data_catalog.services.pipeline_orchestrator import (
    PhaseResult,
    PipelineConfig,
    PipelineResult,
)


class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""

    def test_defaults(self):
        config = PipelineConfig(schema_pattern="dbo")
        assert config.schema_pattern == "dbo"
        assert config.sample_pct == 10.0
        assert config.top_n_values == 100
        assert config.validate_fks is True
        assert config.skip_pk_discovery is False

    def test_custom_config(self):
        config = PipelineConfig(
            schema_pattern="staging",
            sample_pct=1.0,
            skip_pk_discovery=True,
            skip_cardinality=True,
        )
        assert config.sample_pct == 1.0
        assert config.skip_pk_discovery is True
        assert config.skip_cardinality is True


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_to_dict(self):
        from datetime import UTC, datetime

        result = PipelineResult(
            schema_name="dbo",
            started_at=datetime(2025, 1, 1, tzinfo=UTC),
            completed_at=datetime(2025, 1, 1, 0, 5, tzinfo=UTC),
            total_duration_seconds=300.0,
            status="success",
            pk_discovered=10,
            fk_confirmed=5,
        )

        d = result.to_dict()
        assert d["schema_name"] == "dbo"
        assert d["status"] == "success"
        assert d["metrics"]["pk_discovered"] == 10
        assert d["metrics"]["fk_confirmed"] == 5


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_success(self):
        from datetime import UTC, datetime

        result = PhaseResult(
            phase_name="pk_discovery",
            status="success",
            started_at=datetime(2025, 1, 1, tzinfo=UTC),
            completed_at=datetime(2025, 1, 1, 0, 1, tzinfo=UTC),
            duration_seconds=60.0,
            items_processed=50,
            items_total=50,
        )
        assert result.status == "success"
        assert result.items_processed == 50

    def test_error(self):
        from datetime import UTC, datetime

        result = PhaseResult(
            phase_name="fk_validation",
            status="error",
            started_at=datetime(2025, 1, 1, tzinfo=UTC),
            completed_at=datetime(2025, 1, 1, tzinfo=UTC),
            duration_seconds=0.5,
            errors=["Connection timeout"],
        )
        assert result.status == "error"
        assert len(result.errors) == 1


class TestPipelinePhaseLog:
    """Tests for PipelinePhaseLog model persistence."""

    def test_log_phase(self, db):
        from datetime import UTC, datetime

        log = PipelinePhaseLog(
            id=str(uuid4()),
            run_id=str(uuid4()),
            schema_pattern="dbo",
            phase_name="pk_discovery",
            status="success",
            started_at=datetime(2025, 1, 1, tzinfo=UTC),
            completed_at=datetime(2025, 1, 1, 0, 1, tzinfo=UTC),
            duration_seconds=60.0,
            items_processed=50,
        )
        db.add(log)
        db.commit()

        loaded = db.query(PipelinePhaseLog).first()
        assert loaded.phase_name == "pk_discovery"
        assert loaded.status == "success"
        assert loaded.items_processed == 50
