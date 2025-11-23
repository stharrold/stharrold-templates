"""Unit tests for worktree_context module edge cases."""

import hashlib
import sys
from pathlib import Path

# Add the worktree_context module to path
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent
        / ".claude/skills/workflow-utilities/scripts"
    ),
)

import pytest


class TestWorktreeIdGeneration:
    """Unit tests for worktree ID generation."""

    def test_worktree_id_is_deterministic(self):
        """Test: Same path always produces same ID."""
        from worktree_context import get_worktree_context

        ctx1 = get_worktree_context()
        ctx2 = get_worktree_context()

        assert ctx1.worktree_id == ctx2.worktree_id

    def test_worktree_id_uses_sha256(self):
        """Test: ID is derived from SHA-256 hash of path."""
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()
        expected_id = hashlib.sha256(str(ctx.worktree_root).encode()).hexdigest()[:12]

        assert ctx.worktree_id == expected_id

    def test_worktree_id_length(self):
        """Test: ID is exactly 12 characters."""
        from worktree_context import get_worktree_id

        worktree_id = get_worktree_id()
        assert len(worktree_id) == 12

    def test_worktree_id_is_hex(self):
        """Test: ID contains only hex characters."""
        from worktree_context import get_worktree_id

        worktree_id = get_worktree_id()
        # This will raise ValueError if not valid hex
        int(worktree_id, 16)


class TestStateDirProperty:
    """Unit tests for state_dir property."""

    def test_state_dir_is_claude_state(self):
        """Test: state_dir is .claude-state in worktree_root."""
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()
        assert ctx.state_dir.name == ".claude-state"
        assert ctx.state_dir.parent == ctx.worktree_root

    def test_state_dir_uses_worktree_root(self):
        """Test: state_dir is child of worktree_root."""
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()
        assert str(ctx.worktree_root) in str(ctx.state_dir)


class TestBranchNameDetection:
    """Unit tests for branch name detection."""

    def test_branch_name_not_empty(self):
        """Test: branch_name is never empty string."""
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()
        assert len(ctx.branch_name) > 0

    def test_branch_name_is_string(self):
        """Test: branch_name is a string type."""
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()
        assert isinstance(ctx.branch_name, str)


class TestGitCommonDir:
    """Unit tests for git common directory detection."""

    def test_git_common_dir_exists(self):
        """Test: git_common_dir points to existing directory."""
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()
        assert ctx.git_common_dir.exists()

    def test_git_common_dir_is_absolute(self):
        """Test: git_common_dir is an absolute path."""
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()
        assert ctx.git_common_dir.is_absolute()


class TestCleanupOrphanedState:
    """Unit tests for cleanup_orphaned_state function."""

    def test_cleanup_returns_list(self):
        """Test: cleanup_orphaned_state always returns a list."""
        from worktree_context import cleanup_orphaned_state, get_worktree_context

        ctx = get_worktree_context()
        result = cleanup_orphaned_state(ctx.worktree_root)

        assert isinstance(result, list)

    def test_cleanup_handles_nonexistent_parent(self, tmp_path):
        """Test: cleanup_orphaned_state handles missing parent directory."""
        from worktree_context import cleanup_orphaned_state

        # This should not raise, even with a non-repo path
        result = cleanup_orphaned_state(tmp_path)
        assert isinstance(result, list)
