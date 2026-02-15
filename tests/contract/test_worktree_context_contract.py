#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Contract tests for get_worktree_context() function.

Tests the contract specified in specs/006-make-the-entire/contracts/worktree_context.md
"""

import sys
from pathlib import Path

# Add the worktree_context module to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / ".claude/skills/workflow-utilities/scripts"),
)

import pytest


class TestGetWorktreeContextContract:
    """Contract tests for get_worktree_context() function."""

    def test_returns_worktree_context_dataclass(self):
        """Test: Returns WorktreeContext dataclass."""
        from worktree_context import WorktreeContext, get_worktree_context

        result = get_worktree_context()
        assert isinstance(result, WorktreeContext)

    def test_worktree_root_is_valid_path(self):
        """Test: worktree_root is valid Path."""
        from worktree_context import get_worktree_context

        result = get_worktree_context()
        assert isinstance(result.worktree_root, Path)
        assert result.worktree_root.exists()
        assert result.worktree_root.is_dir()

    def test_worktree_id_is_12_char_hex_string(self):
        """Test: worktree_id is 12-char hex string."""
        from worktree_context import get_worktree_context

        result = get_worktree_context()
        assert isinstance(result.worktree_id, str)
        assert len(result.worktree_id) == 12
        # Validate it's a valid hex string
        int(result.worktree_id, 16)

    def test_is_worktree_is_boolean(self):
        """Test: is_worktree is boolean."""
        from worktree_context import get_worktree_context

        result = get_worktree_context()
        assert isinstance(result.is_worktree, bool)

    def test_raises_runtime_error_when_not_in_git_repo(self, tmp_path, monkeypatch):
        """Test: Raises RuntimeError when not in git repo."""
        from worktree_context import get_worktree_context

        # Change to a non-git directory
        monkeypatch.chdir(tmp_path)

        with pytest.raises(RuntimeError):
            get_worktree_context()

    def test_git_common_dir_is_valid_path(self):
        """Test: git_common_dir is valid Path."""
        from worktree_context import get_worktree_context

        result = get_worktree_context()
        assert isinstance(result.git_common_dir, Path)
        assert result.git_common_dir.exists()

    def test_branch_name_is_string(self):
        """Test: branch_name is string."""
        from worktree_context import get_worktree_context

        result = get_worktree_context()
        assert isinstance(result.branch_name, str)
        assert len(result.branch_name) > 0

    def test_state_dir_property_returns_path(self):
        """Test: state_dir property returns correct path."""
        from worktree_context import get_worktree_context

        result = get_worktree_context()
        assert result.state_dir == result.worktree_root / ".claude-state"
