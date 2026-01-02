#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Integration test for state directory creation.

Tests that state directory is created with correct files.
"""

import sys
from pathlib import Path

# Add the worktree_context module to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / ".gemini/skills/workflow-utilities/scripts"),
)


class TestStateDirectoryCreation:
    """Integration tests for state directory creation."""

    def test_directory_created_with_correct_path(self):
        """Given: No .gemini-state/ exists (or exists).
        When: get_state_dir() called.
        Then: Directory exists at worktree_root/.gemini-state/.
        """
        from worktree_context import get_state_dir, get_worktree_context

        ctx = get_worktree_context()
        state_dir = get_state_dir()

        assert state_dir.exists()
        assert state_dir.is_dir()
        assert state_dir == ctx.worktree_root / ".gemini-state"

    def test_gitignore_file_created(self):
        """Given: get_state_dir() called.
        Then: .gitignore file exists with correct content.
        """
        from worktree_context import get_state_dir

        state_dir = get_state_dir()
        gitignore = state_dir / ".gitignore"

        assert gitignore.exists()
        content = gitignore.read_text()
        assert "*" in content

    def test_worktree_id_file_created(self):
        """Given: get_state_dir() called.
        Then: .worktree-id file exists with correct content.
        """
        from worktree_context import get_state_dir, get_worktree_id

        state_dir = get_state_dir()
        worktree_id_file = state_dir / ".worktree-id"

        assert worktree_id_file.exists()
        content = worktree_id_file.read_text().strip()

        # Should match get_worktree_id()
        assert content == get_worktree_id()

    def test_state_dir_idempotent(self):
        """Given: get_state_dir() called multiple times.
        Then: Same directory returned, existing files not corrupted.
        """
        from worktree_context import get_state_dir

        # First call
        state_dir1 = get_state_dir()
        gitignore1 = (state_dir1 / ".gitignore").read_text()
        worktree_id1 = (state_dir1 / ".worktree-id").read_text()

        # Second call
        state_dir2 = get_state_dir()
        gitignore2 = (state_dir2 / ".gitignore").read_text()
        worktree_id2 = (state_dir2 / ".worktree-id").read_text()

        assert state_dir1 == state_dir2
        assert gitignore1 == gitignore2
        assert worktree_id1 == worktree_id2

    def test_state_dir_is_gitignored(self):
        """Given: State directory created.
        Then: .gemini-state/ is in root .gitignore.
        """
        from worktree_context import get_state_dir, get_worktree_context

        ctx = get_worktree_context()
        get_state_dir()  # Ensure it exists

        root_gitignore = ctx.worktree_root / ".gitignore"
        if root_gitignore.exists():
            content = root_gitignore.read_text()
            assert ".gemini-state" in content
