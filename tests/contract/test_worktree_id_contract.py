#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Contract tests for get_worktree_id() function.

Tests the contract specified in specs/006-make-the-entire/contracts/worktree_context.md
"""

import sys
from pathlib import Path

# Add the worktree_context module to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / ".gemini/skills/workflow-utilities/scripts"),
)

import pytest


class TestGetWorktreeIdContract:
    """Contract tests for get_worktree_id() function."""

    def test_returns_12_char_hex_string(self):
        """Test: Returns 12-char hex string."""
        from worktree_context import get_worktree_id

        result = get_worktree_id()
        assert isinstance(result, str)
        assert len(result) == 12
        # Validate it's a valid hex string
        int(result, 16)

    def test_stable_across_multiple_calls(self):
        """Test: Stable across multiple calls."""
        from worktree_context import get_worktree_id

        result1 = get_worktree_id()
        result2 = get_worktree_id()
        result3 = get_worktree_id()

        assert result1 == result2 == result3

    def test_different_for_different_paths(self):
        """Test: Different for different paths (conceptual test).

        Note: This test validates the algorithm - different input paths
        should produce different IDs. We test this by verifying the
        ID is derived from the worktree_root path.
        """
        from worktree_context import get_worktree_context, get_worktree_id

        ctx = get_worktree_context()
        worktree_id = get_worktree_id()

        # The ID should be derived from worktree_root
        # Verify by checking the algorithm matches
        import hashlib

        expected_id = hashlib.sha256(str(ctx.worktree_root).encode()).hexdigest()[:12]
        assert worktree_id == expected_id

    def test_raises_runtime_error_when_not_in_git_repo(self, tmp_path, monkeypatch):
        """Test: Raises RuntimeError when not in git repo."""
        from worktree_context import get_worktree_id

        # Change to a non-git directory
        monkeypatch.chdir(tmp_path)

        with pytest.raises(RuntimeError):
            get_worktree_id()
