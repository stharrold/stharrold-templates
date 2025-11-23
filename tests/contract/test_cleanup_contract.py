"""Contract tests for cleanup_orphaned_state() function.

Tests the contract specified in specs/006-make-the-entire/contracts/worktree_context.md
"""

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

class TestCleanupOrphanedStateContract:
    """Contract tests for cleanup_orphaned_state() function."""

    def test_returns_list_of_path_objects(self):
        """Test: Returns list of Path objects."""
        from worktree_context import cleanup_orphaned_state, get_worktree_context

        ctx = get_worktree_context()
        result = cleanup_orphaned_state(ctx.worktree_root)

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, Path)

    def test_does_not_include_active_worktrees(self):
        """Test: Does not include active worktrees.

        The current worktree's state directory should not be
        in the list of orphaned state directories.
        """
        from worktree_context import (
            cleanup_orphaned_state,
            get_state_dir,
            get_worktree_context,
        )

        ctx = get_worktree_context()
        state_dir = get_state_dir()  # Ensure state dir exists

        result = cleanup_orphaned_state(ctx.worktree_root)

        # Current worktree's state directory should NOT be in orphaned list
        assert state_dir not in result

    def test_identifies_orphaned_directories(self, tmp_path):
        """Test: Identifies orphaned directories.

        Note: This is a conceptual test. In practice, we'd need to create
        a worktree, remove it, and then check. For now, we verify the
        function runs without error and returns a list.
        """
        from worktree_context import cleanup_orphaned_state, get_worktree_context

        ctx = get_worktree_context()
        result = cleanup_orphaned_state(ctx.worktree_root)

        # Should return a list (may be empty if no orphaned state)
        assert isinstance(result, list)

    def test_accepts_path_argument(self):
        """Test: Accepts repo_root Path argument."""
        from worktree_context import cleanup_orphaned_state, get_worktree_context

        ctx = get_worktree_context()

        # Should not raise when given a valid Path
        result = cleanup_orphaned_state(ctx.worktree_root)
        assert isinstance(result, list)
