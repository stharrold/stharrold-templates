#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for AgentDB checkpoint manager."""

import sys
from pathlib import Path

# Import module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "agentdb-state-manager" / "scripts"))

from checkpoint_manager import list_checkpoints, restore_checkpoint, store_checkpoint


class TestStoreCheckpoint:
    """Tests for store_checkpoint()."""

    def test_prints_sql_for_todo_file(self, capsys):
        store_checkpoint("TODO_feature_auth.md")
        output = capsys.readouterr().out
        assert "Storing checkpoint from TODO_feature_auth.md" in output
        assert "INSERT INTO workflow_records" in output
        assert "checkpoint" in output

    def test_generates_checkpoint_id(self, capsys):
        store_checkpoint("TODO_feature_test.md")
        output = capsys.readouterr().out
        assert "checkpoint_" in output

    def test_includes_metadata(self, capsys):
        store_checkpoint("TODO_feature_test.md")
        output = capsys.readouterr().out
        assert "token_count" in output
        assert "resume_instructions" in output


class TestListCheckpoints:
    """Tests for list_checkpoints()."""

    def test_prints_sql_query(self, capsys):
        list_checkpoints()
        output = capsys.readouterr().out
        assert "SELECT" in output
        assert "checkpoint" in output
        assert "ORDER BY" in output


class TestRestoreCheckpoint:
    """Tests for restore_checkpoint()."""

    def test_prints_restore_sql(self, capsys):
        restore_checkpoint("checkpoint_20250101T000000Z")
        output = capsys.readouterr().out
        assert "Restoring checkpoint checkpoint_20250101T000000Z" in output
        assert "SELECT" in output
        assert "LIMIT 1" in output
