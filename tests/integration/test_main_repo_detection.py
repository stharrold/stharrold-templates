"""Integration test for main repository detection.

Tests worktree detection when running in main repository (not a worktree).
"""

import sys
from pathlib import Path

# Add the worktree_context module to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / ".claude/skills/workflow-utilities/scripts"),
)


class TestMainRepoDetection:
    """Integration tests for main repository detection."""

    def test_is_worktree_false_in_main_repo(self):
        """Given: Running in main repository.
        When: get_worktree_context() called.
        Then: is_worktree=False.
        """
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()

        # In the main repo, .git is a directory, not a file
        git_path = ctx.worktree_root / ".git"
        if git_path.is_dir():
            assert ctx.is_worktree is False
        else:
            # We're in a worktree (git_path is a file)
            assert ctx.is_worktree is True

    def test_stable_id_across_calls(self):
        """Given: Running in main repository.
        When: get_worktree_context() called multiple times.
        Then: worktree_id is stable.
        """
        from worktree_context import get_worktree_context

        ctx1 = get_worktree_context()
        ctx2 = get_worktree_context()
        ctx3 = get_worktree_context()

        assert ctx1.worktree_id == ctx2.worktree_id == ctx3.worktree_id

    def test_worktree_root_matches_git_toplevel(self):
        """Given: Running in main repository.
        When: get_worktree_context() called.
        Then: worktree_root matches git rev-parse --show-toplevel.
        """
        import subprocess

        from worktree_context import get_worktree_context

        ctx = get_worktree_context()

        expected_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())

        assert ctx.worktree_root == expected_root

    def test_branch_name_matches_git_branch(self):
        """Given: Running in main repository.
        When: get_worktree_context() called.
        Then: branch_name matches git branch --show-current, or short commit hash if detached HEAD.
        """
        import subprocess

        from worktree_context import get_worktree_context

        ctx = get_worktree_context()

        expected_branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()

        if expected_branch:
            # On a named branch
            assert ctx.branch_name == expected_branch
        else:
            # Detached HEAD (e.g., in CI) - should return short commit hash
            expected_short_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
            assert ctx.branch_name == expected_short_hash
