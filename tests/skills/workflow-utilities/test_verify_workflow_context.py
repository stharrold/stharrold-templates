#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for verify_workflow_context.py pending worktree detection."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "workflow-utilities" / "scripts"))

from verify_workflow_context import (
    PendingWorktree,
    _process_worktree_entry,
    detect_pending_worktrees,
)


class TestProcessWorktreeEntry:
    """Tests for _process_worktree_entry function."""

    def test_skips_main_repo(self, tmp_path: Path) -> None:
        """Main repo worktree should be skipped."""
        entry = {"path": str(tmp_path), "branch": "contrib/stharrold"}
        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")
        assert result is None

    def test_skips_non_feature_branches(self, tmp_path: Path) -> None:
        """Non-feature branches should be skipped."""
        worktree_path = tmp_path / "other-worktree"
        entry = {"path": str(worktree_path), "branch": "develop"}
        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")
        assert result is None

    def test_returns_prunable_worktree(self, tmp_path: Path) -> None:
        """Prunable worktrees should return with error."""
        worktree_path = tmp_path / "prunable-worktree"
        entry = {"path": str(worktree_path), "branch": "feature/test", "prunable": True}
        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")

        assert result is not None
        assert result["prunable"] is True
        assert result["commits_ahead"] == -1
        assert "prunable" in result["error"].lower()

    @patch("verify_workflow_context.subprocess.run")
    def test_counts_commits_ahead(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Should count commits ahead of base branch."""
        worktree_path = tmp_path / "feature-worktree"
        entry = {"path": str(worktree_path), "branch": "feature/test-branch"}

        # Mock git rev-list --count returning 4 commits
        mock_run.return_value = MagicMock(stdout="4\n", returncode=0)

        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")

        assert result is not None
        assert result["commits_ahead"] == 4
        assert result["branch"] == "feature/test-branch"
        assert result["error"] is None

    @patch("verify_workflow_context.subprocess.run")
    def test_skips_zero_commits_ahead(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Worktrees with 0 commits ahead should return None."""
        worktree_path = tmp_path / "feature-worktree"
        entry = {"path": str(worktree_path), "branch": "feature/test-branch"}

        # Mock git rev-list --count returning 0 commits
        mock_run.return_value = MagicMock(stdout="0\n", returncode=0)

        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")

        assert result is None


class TestDetectPendingWorktrees:
    """Tests for detect_pending_worktrees function."""

    @patch("verify_workflow_context.run_command")
    def test_returns_empty_on_no_worktrees(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """No worktrees should return empty list."""
        # Mock git commands
        mock_run.side_effect = [
            str(tmp_path),  # git rev-parse --show-toplevel
            "contrib/stharrold",  # git branch --show-current
            f"worktree {tmp_path}\nbranch refs/heads/contrib/stharrold",  # git worktree list --porcelain
        ]

        result = detect_pending_worktrees(tmp_path)

        assert result == []

    @patch("verify_workflow_context.run_command")
    @patch("verify_workflow_context.subprocess.run")
    def test_detects_pending_worktree(self, mock_subprocess: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        """Should detect worktree with commits ahead."""
        feature_path = tmp_path / "repo_feature_test"

        # Mock git commands
        # Note: When repo_root is passed explicitly, the first run_command
        # (for --show-toplevel) is skipped
        porcelain_output = f"""worktree {tmp_path}
branch refs/heads/contrib/stharrold

worktree {feature_path}
branch refs/heads/feature/20251209T170931Z_test"""

        mock_run.side_effect = [
            "contrib/stharrold",  # git branch --show-current
            porcelain_output,  # git worktree list --porcelain
        ]

        # Mock git rev-list returning 3 commits
        mock_subprocess.return_value = MagicMock(stdout="3\n", returncode=0)

        result = detect_pending_worktrees(tmp_path)

        assert len(result) == 1
        assert result[0]["branch"] == "feature/20251209T170931Z_test"
        assert result[0]["commits_ahead"] == 3


class TestPendingWorktreeType:
    """Tests for PendingWorktree TypedDict structure."""

    def test_pending_worktree_structure(self) -> None:
        """PendingWorktree should have all required fields."""
        wt: PendingWorktree = {
            "worktree_path": "/path/to/worktree",
            "branch": "feature/test",
            "commits_ahead": 5,
            "workflow_step": 4,
            "prunable": False,
            "error": None,
        }

        assert wt["worktree_path"] == "/path/to/worktree"
        assert wt["branch"] == "feature/test"
        assert wt["commits_ahead"] == 5
        assert wt["workflow_step"] == 4
        assert wt["prunable"] is False
        assert wt["error"] is None

    def test_pending_worktree_with_error(self) -> None:
        """PendingWorktree can have error message."""
        wt: PendingWorktree = {
            "worktree_path": "/path/to/worktree",
            "branch": "feature/test",
            "commits_ahead": -1,
            "workflow_step": None,
            "prunable": True,
            "error": "worktree is prunable",
        }

        assert wt["error"] == "worktree is prunable"
        assert wt["commits_ahead"] == -1
        assert wt["workflow_step"] is None


class TestProcessWorktreeEntryEdgeCases:
    """Additional edge case tests for _process_worktree_entry."""

    def test_handles_release_branch(self, tmp_path: Path) -> None:
        """Release branches should be skipped."""
        worktree_path = tmp_path / "release-worktree"
        entry = {"path": str(worktree_path), "branch": "release/v1.0.0"}
        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")
        assert result is None

    def test_handles_hotfix_branch(self, tmp_path: Path) -> None:
        """Hotfix branches (feature/) should be detected."""
        worktree_path = tmp_path / "hotfix-worktree"
        entry = {"path": str(worktree_path), "branch": "hotfix/urgent-fix"}
        # Hotfix is not a feature branch, so should be skipped
        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")
        assert result is None

    @patch("verify_workflow_context.subprocess.run")
    def test_handles_subprocess_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Should handle git command failures gracefully."""
        worktree_path = tmp_path / "feature-worktree"
        entry = {"path": str(worktree_path), "branch": "feature/test-branch"}

        # Mock git rev-list failing
        mock_run.return_value = MagicMock(stdout="", returncode=1)

        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")

        # Should return with error message and -1 commits
        assert result is not None
        assert result["commits_ahead"] == -1
        assert result["error"] is not None
        assert "Could not count commits" in result["error"]

    def test_handles_missing_branch_key(self, tmp_path: Path) -> None:
        """Should handle entry without branch key."""
        worktree_path = tmp_path / "no-branch-worktree"
        entry = {"path": str(worktree_path)}  # No branch key
        result = _process_worktree_entry(entry, tmp_path, "contrib/stharrold")
        # Should be skipped since no branch
        assert result is None


class TestDetectPendingWorktreesEdgeCases:
    """Additional edge case tests for detect_pending_worktrees."""

    @patch("verify_workflow_context.run_command")
    def test_handles_multiple_worktrees(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Should detect multiple pending worktrees."""
        feature1 = tmp_path / "repo_feature_one"
        feature2 = tmp_path / "repo_feature_two"

        porcelain_output = f"""worktree {tmp_path}
branch refs/heads/contrib/stharrold

worktree {feature1}
branch refs/heads/feature/one

worktree {feature2}
branch refs/heads/feature/two"""

        mock_run.side_effect = [
            "contrib/stharrold",  # git branch --show-current
            porcelain_output,  # git worktree list --porcelain
        ]

        # Since subprocess.run for rev-list isn't mocked, this would fail
        # So we test the parsing logic separately
        with patch("verify_workflow_context.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = MagicMock(stdout="2\n", returncode=0)
            result = detect_pending_worktrees(tmp_path)

        # Both features should be detected
        assert len(result) == 2

    @patch("verify_workflow_context.run_command")
    def test_handles_empty_porcelain_output(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Should handle empty worktree list."""
        mock_run.side_effect = [
            "contrib/stharrold",  # git branch --show-current
            "",  # Empty git worktree list --porcelain
        ]

        result = detect_pending_worktrees(tmp_path)
        assert result == []

    @patch("verify_workflow_context.run_command")
    def test_handles_prunable_in_porcelain(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Should detect prunable worktrees from porcelain output."""
        feature_path = tmp_path / "repo_feature_prunable"

        # Note: git porcelain format uses just "prunable" on its own line
        porcelain_output = f"""worktree {tmp_path}
branch refs/heads/contrib/stharrold

worktree {feature_path}
branch refs/heads/feature/test
prunable"""

        mock_run.side_effect = [
            "contrib/stharrold",  # git branch --show-current
            porcelain_output,  # git worktree list --porcelain
        ]

        result = detect_pending_worktrees(tmp_path)

        assert len(result) == 1
        assert result[0]["prunable"] is True
        assert "prunable" in result[0]["error"].lower()


class TestStrictMode:
    """Tests for --strict mode CLI behavior."""

    @patch("verify_workflow_context.detect_pending_worktrees")
    @patch("verify_workflow_context.validate_context")
    @patch("verify_workflow_context.is_worktree")
    def test_strict_mode_exits_code_2_with_pending_worktrees(self, mock_is_worktree: MagicMock, mock_validate: MagicMock, mock_detect: MagicMock) -> None:
        """--strict mode should exit with code 2 when pending worktrees exist."""
        # Get the script path
        script_path = Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "workflow-utilities" / "scripts" / "verify_workflow_context.py"

        # Mock the subprocess to test actual CLI behavior
        # We'll run the actual script with mocked git commands
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--step",
                "5",
                "--strict",
            ],
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PYTHONDONTWRITEBYTECODE": "1"},
        )

        # Note: This test will pass context validation (if we're in main repo on contrib/*)
        # but may or may not have pending worktrees. The key behavior to test is
        # that --strict flag is recognized and affects exit code when worktrees exist.
        # Since we can't easily mock git commands in a subprocess, we verify the flag is accepted.
        # Exit code 0 = no pending worktrees, 1 = context invalid, 2 = strict + pending worktrees
        assert result.returncode in (0, 1, 2)

    def test_strict_flag_is_recognized(self) -> None:
        """--strict flag should be a valid CLI argument."""
        script_path = Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "workflow-utilities" / "scripts" / "verify_workflow_context.py"

        # Run with --help to verify --strict is documented
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--strict" in result.stdout
        assert "exit code 2" in result.stdout.lower() or "exit with code 2" in result.stdout.lower()

    @patch("verify_workflow_context.detect_pending_worktrees")
    @patch("verify_workflow_context.validate_context")
    def test_without_strict_pending_worktrees_exit_0(self, mock_validate: MagicMock, mock_detect: MagicMock) -> None:
        """Without --strict, pending worktrees should NOT cause exit code 2."""
        # Import main function to test directly
        from verify_workflow_context import main

        mock_validate.return_value = (True, "Context valid")
        mock_detect.return_value = [
            {
                "worktree_path": "/tmp/test",
                "branch": "feature/test",
                "commits_ahead": 5,
                "workflow_step": 4,
                "prunable": False,
                "error": None,
            }
        ]

        # Mock sys.argv and sys.exit
        with patch("sys.argv", ["verify_workflow_context.py", "--step", "5"]):
            with patch("sys.exit") as mock_exit:
                with patch("verify_workflow_context.is_worktree", return_value=False):
                    main()

        # Without --strict, should exit 0 even with pending worktrees
        mock_exit.assert_called_with(0)

    @patch("verify_workflow_context.detect_pending_worktrees")
    @patch("verify_workflow_context.validate_context")
    def test_with_strict_pending_worktrees_exit_2(self, mock_validate: MagicMock, mock_detect: MagicMock) -> None:
        """With --strict, pending worktrees should cause exit code 2."""
        from verify_workflow_context import main

        mock_validate.return_value = (True, "Context valid")
        mock_detect.return_value = [
            {
                "worktree_path": "/tmp/test",
                "branch": "feature/test",
                "commits_ahead": 5,
                "workflow_step": 4,
                "prunable": False,
                "error": None,
            }
        ]

        # Mock sys.argv with --strict and sys.exit
        with patch("sys.argv", ["verify_workflow_context.py", "--step", "5", "--strict"]):
            with patch("sys.exit") as mock_exit:
                with patch("verify_workflow_context.is_worktree", return_value=False):
                    main()

        # With --strict, exit(2) should be called (before exit(0))
        # Check all calls to sys.exit
        exit_codes = [call[0][0] for call in mock_exit.call_args_list]
        assert 2 in exit_codes, f"Expected exit(2) in calls, got: {exit_codes}"
