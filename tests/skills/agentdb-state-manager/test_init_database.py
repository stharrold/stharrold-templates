#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for AgentDB schema initialization."""

# Import module under test
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "agentdb-state-manager" / "scripts"))

from init_database import SCHEMA_VERSION, create_schema, generate_session_id, load_workflow_states


class TestGenerateSessionId:
    """Tests for generate_session_id()."""

    def test_returns_string(self):
        result = generate_session_id()
        assert isinstance(result, str)

    def test_returns_16_hex_chars(self):
        result = generate_session_id()
        assert len(result) == 16
        int(result, 16)  # Raises ValueError if not hex

    def test_different_calls_produce_valid_ids(self):
        # Each call returns a valid hex ID (may differ due to microsecond precision)
        id1 = generate_session_id()
        id2 = generate_session_id()
        assert len(id1) == 16
        assert len(id2) == 16


class TestLoadWorkflowStates:
    """Tests for load_workflow_states()."""

    def test_loads_valid_states(self):
        states = load_workflow_states()
        assert isinstance(states, dict)
        assert "states" in states

    def test_has_version(self):
        states = load_workflow_states()
        assert "version" in states

    def test_has_object_types(self):
        states = load_workflow_states()
        assert len(states["states"]) > 0


class TestCreateSchema:
    """Tests for create_schema() using in-memory DuckDB."""

    @pytest.fixture
    def db_path(self, tmp_path):
        return tmp_path / "test_agentdb.duckdb"

    @pytest.fixture
    def workflow_states(self):
        return load_workflow_states()

    def test_creates_schema_metadata_table(self, db_path, workflow_states):
        session_id = generate_session_id()
        result = create_schema(session_id, workflow_states, db_path)
        assert result is True

        conn = duckdb.connect(str(db_path))
        tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
        table_names = [t[0] for t in tables]
        assert "schema_metadata" in table_names
        conn.close()

    def test_creates_agent_synchronizations_table(self, db_path, workflow_states):
        session_id = generate_session_id()
        create_schema(session_id, workflow_states, db_path)

        conn = duckdb.connect(str(db_path))
        tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
        table_names = [t[0] for t in tables]
        assert "agent_synchronizations" in table_names
        conn.close()

    def test_creates_workflow_records_table(self, db_path, workflow_states):
        session_id = generate_session_id()
        create_schema(session_id, workflow_states, db_path)

        conn = duckdb.connect(str(db_path))
        tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
        table_names = [t[0] for t in tables]
        assert "workflow_records" in table_names
        conn.close()

    def test_schema_version_recorded(self, db_path, workflow_states):
        session_id = generate_session_id()
        create_schema(session_id, workflow_states, db_path)

        conn = duckdb.connect(str(db_path))
        version = conn.execute("SELECT schema_version FROM schema_metadata WHERE schema_name = 'agentdb_sync_schema'").fetchone()
        assert version is not None
        assert version[0] == SCHEMA_VERSION
        conn.close()

    def test_session_metadata_recorded(self, db_path, workflow_states):
        session_id = generate_session_id()
        create_schema(session_id, workflow_states, db_path)

        conn = duckdb.connect(str(db_path))
        sid = conn.execute("SELECT value FROM session_metadata WHERE key = 'session_id'").fetchone()
        assert sid is not None
        assert sid[0] == session_id
        conn.close()

    def test_idempotent_schema_creation(self, db_path, workflow_states):
        session_id = generate_session_id()
        result1 = create_schema(session_id, workflow_states, db_path)
        result2 = create_schema(session_id, workflow_states, db_path)
        assert result1 is True
        assert result2 is True
