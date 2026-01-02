#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Integration test for backward compatibility.

Tests that non-worktree repositories work identically to expected behavior.
"""

import sys
from pathlib import Path

# Add the worktree_context module to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / ".gemini/skills/workflow-utilities/scripts"),
)


class TestBackwardCompatibility:
    """Integration tests for backward compatibility."""

    def test_all_functions_work_in_main_repo(self):
        """Given: Main repository (not worktree).
        When: All worktree functions called.
        Then: All functions work without error.
        """
        from worktree_context import (
            cleanup_orphaned_state,
            get_state_dir,
            get_worktree_context,
            get_worktree_id,
        )

        # All functions should work
        ctx = get_worktree_context()
        assert ctx is not None

        worktree_id = get_worktree_id()
        assert worktree_id is not None

        state_dir = get_state_dir()
        assert state_dir is not None

        orphaned = cleanup_orphaned_state(ctx.worktree_root)
        assert isinstance(orphaned, list)

    def test_state_dir_created_at_repo_root(self):
        """Given: Main repository (not worktree).
        When: get_state_dir() called.
        Then: State directory created at repo root.
        """
        from worktree_context import get_state_dir, get_worktree_context

        ctx = get_worktree_context()
        state_dir = get_state_dir()

        # State directory should be at worktree_root (which is repo root for main repo)
        assert state_dir.parent == ctx.worktree_root

    def test_worktree_id_derived_from_repo_root(self):
        """Given: Main repository (not worktree).
        When: get_worktree_id() called.
        Then: ID is derived from repo root path.
        """
        import hashlib

        from worktree_context import get_worktree_context, get_worktree_id

        ctx = get_worktree_context()
        worktree_id = get_worktree_id()

        # ID should match SHA-256 of worktree_root
        expected_id = hashlib.sha256(str(ctx.worktree_root).encode()).hexdigest()[:12]
        assert worktree_id == expected_id

    def test_no_behavioral_changes_from_non_worktree(self):
        """Given: Main repository (not worktree).
        When: Worktree functions used.
        Then: Behavior is consistent and predictable.
        """
        from worktree_context import get_state_dir, get_worktree_context

        ctx = get_worktree_context()
        state_dir = get_state_dir()

        # In main repo, worktree_root should be the actual repo root
        assert ctx.worktree_root.exists()
        assert (ctx.worktree_root / ".git").exists()

        # State directory should be a child of worktree_root
        assert state_dir.parent == ctx.worktree_root

        # git_common_dir should be .git in the repo
        assert ctx.git_common_dir.exists()
