#!/usr/bin/env python3
"""Tests for git-workflow-manager create_worktree.py.

Tests the verify_planning_committed function and its integration
with the create_worktree function.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / ".claude/skills/git-workflow-manager/scripts"),
)

import create_worktree

# Import for direct function tests
from create_worktree import verify_planning_committed


class TestVerifyPlanningCommitted:
    """Tests for verify_planning_committed function."""

    def test_planning_dir_exists_passes(self, tmp_path):
        """Should pass when planning directory exists and is clean."""
        # Create planning directory
        planning_dir = tmp_path / "planning" / "my-feature"
        planning_dir.mkdir(parents=True)
        (planning_dir / "requirements.md").write_text("# Requirements")

        # Mock git commands to return clean state
        with patch("create_worktree.subprocess.run") as mock_run:
            # Mock git status --porcelain (no changes)
            mock_status = MagicMock()
            mock_status.stdout = ""
            mock_status.returncode = 0

            # Mock git fetch
            mock_fetch = MagicMock()
            mock_fetch.returncode = 0

            # Mock git branch --show-current
            mock_branch = MagicMock()
            mock_branch.stdout = "contrib/stharrold"
            mock_branch.returncode = 0

            # Mock git rev-list (not ahead)
            mock_revlist = MagicMock()
            mock_revlist.stdout = "0"
            mock_revlist.returncode = 0

            mock_run.side_effect = [mock_status, mock_fetch, mock_branch, mock_revlist]

            # Should not raise
            verify_planning_committed("my-feature", tmp_path)

    def test_planning_dir_missing_fails(self, tmp_path):
        """Should fail with clear error when planning directory missing."""
        # No planning directory created

        with pytest.raises(ValueError) as exc_info:
            verify_planning_committed("missing-feature", tmp_path)

        error_msg = str(exc_info.value)
        assert "Planning directory not found" in error_msg
        assert "planning/missing-feature/" in error_msg
        assert "Run /1_specify" in error_msg
        assert "requirements.md" in error_msg

    def test_uncommitted_changes_fails(self, tmp_path):
        """Should fail when planning directory has uncommitted changes."""
        # Create planning directory
        planning_dir = tmp_path / "planning" / "dirty-feature"
        planning_dir.mkdir(parents=True)
        (planning_dir / "requirements.md").write_text("# Requirements")

        with patch("create_worktree.subprocess.run") as mock_run:
            # Mock git status --porcelain (has changes)
            mock_status = MagicMock()
            mock_status.stdout = " M planning/dirty-feature/requirements.md\n"
            mock_status.returncode = 0

            mock_run.return_value = mock_status

            with pytest.raises(ValueError) as exc_info:
                verify_planning_committed("dirty-feature", tmp_path)

            error_msg = str(exc_info.value)
            assert "Uncommitted changes detected" in error_msg
            assert "planning/dirty-feature/" in error_msg
            assert "git add" in error_msg
            assert "git commit" in error_msg

    def test_unpushed_commits_fails(self, tmp_path):
        """Should fail when local branch is ahead of remote."""
        # Create planning directory
        planning_dir = tmp_path / "planning" / "unpushed-feature"
        planning_dir.mkdir(parents=True)
        (planning_dir / "requirements.md").write_text("# Requirements")

        with patch("create_worktree.subprocess.run") as mock_run:
            # Mock git status --porcelain (clean)
            mock_status = MagicMock()
            mock_status.stdout = ""
            mock_status.returncode = 0

            # Mock git fetch
            mock_fetch = MagicMock()
            mock_fetch.returncode = 0

            # Mock git branch --show-current
            mock_branch = MagicMock()
            mock_branch.stdout = "contrib/stharrold"
            mock_branch.returncode = 0

            # Mock git rev-list (2 commits ahead)
            mock_revlist = MagicMock()
            mock_revlist.stdout = "2"
            mock_revlist.returncode = 0

            mock_run.side_effect = [mock_status, mock_fetch, mock_branch, mock_revlist]

            with pytest.raises(ValueError) as exc_info:
                verify_planning_committed("unpushed-feature", tmp_path)

            error_msg = str(exc_info.value)
            assert "2 commit(s) ahead of remote" in error_msg
            assert "git push" in error_msg

    def test_remote_branch_missing_passes(self, tmp_path):
        """Should pass when remote branch doesn't exist (new branch)."""
        # Create planning directory
        planning_dir = tmp_path / "planning" / "new-feature"
        planning_dir.mkdir(parents=True)
        (planning_dir / "requirements.md").write_text("# Requirements")

        with patch("create_worktree.subprocess.run") as mock_run:
            # Mock git status --porcelain (clean)
            mock_status = MagicMock()
            mock_status.stdout = ""
            mock_status.returncode = 0

            # Mock git fetch
            mock_fetch = MagicMock()
            mock_fetch.returncode = 0

            # Mock git branch --show-current
            mock_branch = MagicMock()
            mock_branch.stdout = "contrib/stharrold"
            mock_branch.returncode = 0

            # Mock git rev-list (fails because remote doesn't exist)
            mock_revlist = MagicMock()
            mock_revlist.stdout = ""
            mock_revlist.returncode = 128  # Git error code for missing ref

            mock_run.side_effect = [mock_status, mock_fetch, mock_branch, mock_revlist]

            # Should not raise (remote branch doesn't exist, that's OK)
            verify_planning_committed("new-feature", tmp_path)


class TestCreateWorktreeWithVerification:
    """Tests for create_worktree integration with verify_planning_committed.

    These tests verify that the workflow_type correctly determines
    whether verification is called or skipped.

    Note: Full integration tests are in test_create_worktree_integration.py
    """

    def test_feature_worktree_calls_verification(self, tmp_path):
        """Should call verify_planning_committed for feature worktrees.

        Verifies by checking that ValueError is raised when planning
        directory is missing (which means verification was called).
        """
        # Create a mock git repo structure without planning
        (tmp_path / ".git").mkdir()

        with patch("create_worktree.subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = str(tmp_path) + "\n"

            with patch("create_worktree.subprocess.run") as mock_run:
                # git rev-parse --verify succeeds
                mock_run.return_value = MagicMock(returncode=0)

                # Should raise ValueError because planning dir is missing
                # This proves verification was called
                with pytest.raises(ValueError) as exc_info:
                    from create_worktree import create_worktree as cw_func

                    cw_func("feature", "test-feature", "contrib/stharrold")

                assert "Planning directory not found" in str(exc_info.value)

    def test_workflow_type_determines_verification(self):
        """Verify that only feature type triggers verification.

        This is a code inspection test - we verify the logic in the
        create_worktree function checks workflow_type == 'feature'.
        """
        import inspect

        source = inspect.getsource(create_worktree.create_worktree)

        # The verification should only be called for feature type
        assert 'if workflow_type == "feature"' in source
        assert "verify_planning_committed" in source
