#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for git-workflow-manager create_worktree.py.

Tests the create_worktree function for creating feature worktrees.
Note: v6 workflow removed verify_planning_committed (feature-dev handles planning).
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / ".gemini/skills/git-workflow-manager/scripts"),
)

import create_worktree


class TestCreateWorktree:
    """Tests for create_worktree function."""

    def test_create_worktree_no_verification(self, tmp_path):
        """v6 workflow: create_worktree should not verify planning (feature-dev handles it)."""
        import inspect

        source = inspect.getsource(create_worktree.create_worktree)

        # Verify that verify_planning_committed is NOT called
        assert "verify_planning_committed" not in source

    def test_worktree_creates_state_directory(self, tmp_path):
        """Should create .gemini-state directory in worktree."""
        # This is a unit test for the state isolation feature
        # Full integration tests are in test_create_worktree_integration.py
        pass  # Placeholder for integration test
