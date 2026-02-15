#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for AgentDB query_workflow_state operations."""

import sys
from pathlib import Path
from unittest.mock import patch

# Import modules under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "agentdb-state-manager" / "scripts"))

from query_workflow_state import PHASE_MAP, get_workflow_state


class TestPhaseMap:
    """Tests for PHASE_MAP entries."""

    def test_v7x1_phase_map_entries(self):
        """Verify PHASE_MAP has v7x1 entries with correct next_command."""
        assert "phase_v7x1_1_worktree" in PHASE_MAP
        assert "phase_v7x1_2_integrate" in PHASE_MAP
        assert "phase_v7x1_3_release" in PHASE_MAP
        assert "phase_v7x1_4_backmerge" in PHASE_MAP

        # Verify next_command values
        assert PHASE_MAP["phase_v7x1_1_worktree"][2] == "/workflow:v7x1_2-integrate"
        assert PHASE_MAP["phase_v7x1_2_integrate"][2] == "/workflow:v7x1_3-release"
        assert PHASE_MAP["phase_v7x1_3_release"][2] == "/workflow:v7x1_4-backmerge"
        assert PHASE_MAP["phase_v7x1_4_backmerge"][2] is None

    def test_v7x1_phase_numbers(self):
        """Verify v7x1 phase numbers are sequential 1-4."""
        assert PHASE_MAP["phase_v7x1_1_worktree"][0] == 1
        assert PHASE_MAP["phase_v7x1_2_integrate"][0] == 2
        assert PHASE_MAP["phase_v7x1_3_release"][0] == 3
        assert PHASE_MAP["phase_v7x1_4_backmerge"][0] == 4

    def test_v7x1_phase_names(self):
        """Verify v7x1 phase names."""
        assert PHASE_MAP["phase_v7x1_1_worktree"][1] == "worktree"
        assert PHASE_MAP["phase_v7x1_2_integrate"][1] == "integrate"
        assert PHASE_MAP["phase_v7x1_3_release"][1] == "release"
        assert PHASE_MAP["phase_v7x1_4_backmerge"][1] == "backmerge"

    def test_legacy_phases_still_present(self):
        """Verify legacy phase_1 through phase_7 entries are preserved."""
        for i in range(1, 8):
            assert any(k.startswith(f"phase_{i}_") for k in PHASE_MAP), f"No phase_{i}_* key in PHASE_MAP"


class TestGetWorkflowState:
    """Tests for get_workflow_state function."""

    def test_get_workflow_state_no_db(self):
        """When no DB exists, returns phase None and next /1_specify."""
        with patch("query_workflow_state.get_database_path", return_value=None):
            state = get_workflow_state(worktree="/tmp/test")

        assert state["phase"] is None
        assert state["next_command"] == "/1_specify"
        assert "error" in state or state.get("phase_name") is None
