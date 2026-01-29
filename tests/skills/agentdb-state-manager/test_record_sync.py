#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for AgentDB record_sync operations."""

import sys
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

# Import modules under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "agentdb-state-manager" / "scripts"))

from init_database import create_schema, generate_session_id, load_workflow_states
from record_sync import VALID_PATTERNS, VALID_SYNC_TYPES, record_sync


@pytest.fixture
def initialized_db(tmp_path):
    """Create an initialized AgentDB database for testing."""
    db_path = tmp_path / "test_agentdb.duckdb"
    session_id = generate_session_id()
    workflow_states = load_workflow_states()
    create_schema(session_id, workflow_states, db_path)
    return db_path


class TestRecordSyncValidation:
    """Tests for record_sync input validation."""

    def test_rejects_invalid_sync_type(self, initialized_db):
        with pytest.raises(ValueError, match="Invalid sync-type"):
            record_sync(
                sync_type="invalid_type",
                pattern="phase_1_specify",
                worktree="/tmp/test",
            )

    def test_valid_sync_types_constant(self):
        assert "workflow_transition" in VALID_SYNC_TYPES
        assert "quality_gate" in VALID_SYNC_TYPES
        assert "file_update" in VALID_SYNC_TYPES

    def test_valid_patterns_constant(self):
        assert "phase_1_specify" in VALID_PATTERNS
        assert "phase_2_plan" in VALID_PATTERNS
        assert "quality_gate_passed" in VALID_PATTERNS


class TestRecordSyncOperations:
    """Tests for record_sync database operations."""

    def test_records_workflow_transition(self, initialized_db):
        with patch("record_sync.get_database_path", return_value=initialized_db):
            sync_id = record_sync(
                sync_type="workflow_transition",
                pattern="phase_1_specify",
                source="planning/test",
                target="specs/test",
                worktree="/tmp/test-worktree",
            )

        assert isinstance(sync_id, str)
        assert len(sync_id) == 36  # UUID format

        # Verify record exists in database
        conn = duckdb.connect(str(initialized_db))
        row = conn.execute("SELECT sync_type, pattern, status FROM agent_synchronizations WHERE sync_id = ?", [sync_id]).fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "workflow_transition"
        assert row[1] == "phase_1_specify"
        assert row[2] == "completed"

    def test_records_quality_gate(self, initialized_db):
        with patch("record_sync.get_database_path", return_value=initialized_db):
            sync_id = record_sync(
                sync_type="quality_gate",
                pattern="quality_gate_passed",
                worktree="/tmp/test",
            )

        conn = duckdb.connect(str(initialized_db))
        row = conn.execute("SELECT sync_type, pattern FROM agent_synchronizations WHERE sync_id = ?", [sync_id]).fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "quality_gate"
        assert row[1] == "quality_gate_passed"

    def test_records_with_metadata(self, initialized_db):
        metadata = {"coverage": 85.5, "tests_passed": 277}
        with patch("record_sync.get_database_path", return_value=initialized_db):
            sync_id = record_sync(
                sync_type="quality_gate",
                pattern="quality_gate_passed",
                worktree="/tmp/test",
                metadata=metadata,
            )

        conn = duckdb.connect(str(initialized_db))
        row = conn.execute("SELECT metadata FROM agent_synchronizations WHERE sync_id = ?", [sync_id]).fetchone()
        conn.close()

        assert row is not None
        # DuckDB returns metadata as a string or dict depending on version
        assert "277" in str(row[0])

    def test_records_source_and_target(self, initialized_db):
        with patch("record_sync.get_database_path", return_value=initialized_db):
            sync_id = record_sync(
                sync_type="workflow_transition",
                pattern="phase_2_plan",
                source="planning/auth",
                target="specs/auth",
                worktree="/tmp/test",
            )

        conn = duckdb.connect(str(initialized_db))
        row = conn.execute("SELECT source_location, target_location FROM agent_synchronizations WHERE sync_id = ?", [sync_id]).fetchone()
        conn.close()

        assert row[0] == "planning/auth"
        assert row[1] == "specs/auth"

    def test_multiple_records_unique_ids(self, initialized_db):
        ids = []
        with patch("record_sync.get_database_path", return_value=initialized_db):
            for i in range(3):
                sync_id = record_sync(
                    sync_type="workflow_transition",
                    pattern=f"phase_{i + 1}_specify" if i == 0 else "phase_2_plan",
                    worktree="/tmp/test",
                )
                ids.append(sync_id)

        assert len(set(ids)) == 3  # All unique

        conn = duckdb.connect(str(initialized_db))
        count = conn.execute("SELECT COUNT(*) FROM agent_synchronizations").fetchone()
        conn.close()
        assert count[0] == 3
