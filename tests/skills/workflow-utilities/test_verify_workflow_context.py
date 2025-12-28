#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for verify_workflow_context.py pending worktree detection."""

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
