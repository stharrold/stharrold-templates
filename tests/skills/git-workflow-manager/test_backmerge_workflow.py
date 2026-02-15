#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for git-workflow-manager backmerge_workflow.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / ".claude/skills/git-workflow-manager/scripts"),
)

from backmerge_workflow import (
    find_release_branch,
    get_current_branch,
    get_latest_version,
    return_to_editable_branch,
    step_pr_develop,
)


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    @patch("backmerge_workflow.run_cmd")
    def test_returns_branch_name(self, mock_run):
        """Should return current branch name."""
        mock_run.return_value = MagicMock(stdout="contrib/stharrold\n", returncode=0)

        result = get_current_branch()

        assert result == "contrib/stharrold"

    @patch("backmerge_workflow.run_cmd")
    def test_strips_whitespace(self, mock_run):
        """Should strip whitespace from branch name."""
        mock_run.return_value = MagicMock(stdout="  main  \n", returncode=0)

        result = get_current_branch()

        assert result == "main"


class TestGetLatestVersion:
    """Tests for get_latest_version function."""

    @patch("backmerge_workflow.run_cmd")
    def test_returns_version_tag(self, mock_run):
        """Should return latest version tag from main."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch
            MagicMock(stdout="v1.5.0\n", returncode=0),  # git describe
        ]

        result = get_latest_version()

        assert result == "v1.5.0"

    @patch("backmerge_workflow.run_cmd")
    def test_returns_none_when_no_tags(self, mock_run):
        """Should return None when no tags exist."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch
            MagicMock(stdout="", returncode=1),  # git describe fails
        ]

        result = get_latest_version()

        assert result is None


class TestFindReleaseBranch:
    """Tests for find_release_branch function."""

    @patch("backmerge_workflow.run_cmd")
    def test_finds_specific_version_branch(self, mock_run):
        """Should find release branch for specific version."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch
            MagicMock(stdout="  origin/release/v1.5.0\n", returncode=0),  # git branch -r
        ]

        result = find_release_branch("v1.5.0")

        assert result == "release/v1.5.0"

    @patch("backmerge_workflow.run_cmd")
    def test_returns_none_when_version_not_found(self, mock_run):
        """Should return None when specific version branch doesn't exist."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch
            MagicMock(stdout="", returncode=0),  # git branch -r (empty)
        ]

        result = find_release_branch("v1.5.0")

        assert result is None

    @patch("backmerge_workflow.run_cmd")
    def test_finds_most_recent_release_branch(self, mock_run):
        """Should find most recent release branch when no version specified."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch
            MagicMock(
                # git for-each-ref --sort=-version:refname returns highest version first
                stdout="origin/release/v1.5.0\norigin/release/v1.4.0\n",
                returncode=0,
            ),  # git for-each-ref
        ]

        result = find_release_branch(None)

        assert result == "release/v1.5.0"

    @patch("backmerge_workflow.run_cmd")
    def test_returns_none_when_no_release_branches(self, mock_run):
        """Should return None when no release branches exist."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch
            MagicMock(stdout="", returncode=0),  # git for-each-ref (empty)
        ]

        result = find_release_branch(None)

        assert result is None


class TestReturnToEditableBranch:
    """Tests for return_to_editable_branch function."""

    @patch("backmerge_workflow.get_current_branch")
    @patch("backmerge_workflow.get_contrib_branch")
    def test_returns_true_when_already_on_contrib(self, mock_contrib, mock_current):
        """Should return True without checkout when already on contrib."""
        mock_contrib.return_value = "contrib/stharrold"
        mock_current.return_value = "contrib/stharrold"

        result = return_to_editable_branch()

        assert result is True

    @patch("backmerge_workflow.run_cmd")
    @patch("backmerge_workflow.get_current_branch")
    @patch("backmerge_workflow.get_contrib_branch")
    def test_checks_out_contrib_when_on_different_branch(self, mock_contrib, mock_current, mock_run):
        """Should checkout contrib when on a different branch."""
        mock_contrib.return_value = "contrib/stharrold"
        mock_current.return_value = "release/v1.5.0"
        mock_run.return_value = MagicMock(returncode=0)

        result = return_to_editable_branch()

        assert result is True
        mock_run.assert_called_once()
        assert "checkout" in mock_run.call_args[0][0]

    @patch("backmerge_workflow.run_cmd")
    @patch("backmerge_workflow.get_current_branch")
    @patch("backmerge_workflow.get_contrib_branch")
    def test_returns_false_on_checkout_failure(self, mock_contrib, mock_current, mock_run):
        """Should return False when checkout fails."""
        mock_contrib.return_value = "contrib/stharrold"
        mock_current.return_value = "release/v1.5.0"
        mock_run.return_value = MagicMock(returncode=1, stderr="error")

        result = return_to_editable_branch()

        assert result is False


class TestBackmergeWorkflowEdgeCases:
    """Edge case tests for backmerge workflow functions."""

    @patch("backmerge_workflow.run_cmd")
    def test_handles_whitespace_in_branch_list(self, mock_run):
        """Should handle whitespace in branch list output."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch
            MagicMock(
                stdout="  origin/release/v1.5.0  \n",
                returncode=0,
            ),
        ]

        result = find_release_branch("v1.5.0")

        assert result == "release/v1.5.0"

    @patch("backmerge_workflow.run_cmd")
    def test_version_tag_with_leading_v(self, mock_run):
        """Should handle version tags with leading v."""
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(stdout="v7.0.0\n", returncode=0),
        ]

        result = get_latest_version()
        assert result == "v7.0.0"

    @patch("backmerge_workflow.run_cmd")
    def test_multiple_release_branches_returns_highest_version(self, mock_run):
        """Should return highest version when multiple exist (semantic sort)."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch
            MagicMock(
                # git for-each-ref --sort=-version:refname returns highest first
                stdout="origin/release/v1.10.0\norigin/release/v1.9.0\norigin/release/v1.2.0\n",
                returncode=0,
            ),
        ]

        result = find_release_branch(None)

        assert result == "release/v1.10.0"


class TestStepPrDevelopNoCommitsFallback:
    """Tests for step_pr_develop fallback when release branch has no unique commits."""

    @patch("backmerge_workflow.create_pr")
    @patch("backmerge_workflow.return_to_editable_branch")
    @patch("backmerge_workflow.find_release_branch")
    @patch("backmerge_workflow.get_latest_version")
    @patch("backmerge_workflow.run_cmd")
    def test_pr_develop_no_commits_fallback_to_main(self, mock_run, mock_version, mock_find, mock_return, mock_create_pr):
        """Should fall back to main -> develop PR when release has no unique commits."""
        mock_version.return_value = "v1.6.0"
        mock_find.return_value = "release/v1.6.0"
        mock_return.return_value = True

        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch origin
            MagicMock(stdout="2\n", returncode=0),  # git rev-list --count (behind)
            MagicMock(returncode=0),  # git checkout release branch
        ]

        # First create_pr call raises "No commits between", second succeeds
        mock_create_pr.side_effect = [
            RuntimeError("No commits between develop and release/v1.6.0"),
            "https://github.com/org/repo/pull/99",
        ]

        result = step_pr_develop()

        assert result is True
        # Verify fallback PR was created with main as head
        assert mock_create_pr.call_count == 2
        fallback_call = mock_create_pr.call_args_list[1]
        assert fallback_call[1]["head"] == "main"

    @patch("backmerge_workflow.create_pr")
    @patch("backmerge_workflow.return_to_editable_branch")
    @patch("backmerge_workflow.find_release_branch")
    @patch("backmerge_workflow.get_latest_version")
    @patch("backmerge_workflow.run_cmd")
    def test_pr_develop_no_commits_fallback_already_exists(self, mock_run, mock_version, mock_find, mock_return, mock_create_pr):
        """Should return True when fallback PR already exists."""
        mock_version.return_value = "v1.6.0"
        mock_find.return_value = "release/v1.6.0"
        mock_return.return_value = True

        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch origin
            MagicMock(stdout="2\n", returncode=0),  # git rev-list --count (behind)
            MagicMock(returncode=0),  # git checkout release branch
        ]

        mock_create_pr.side_effect = [
            RuntimeError("No commits between develop and release/v1.6.0"),
            RuntimeError("a pull request already exists"),
        ]

        result = step_pr_develop()

        assert result is True

    @patch("backmerge_workflow.create_pr")
    @patch("backmerge_workflow.return_to_editable_branch")
    @patch("backmerge_workflow.find_release_branch")
    @patch("backmerge_workflow.get_latest_version")
    @patch("backmerge_workflow.run_cmd")
    def test_pr_develop_no_commits_fallback_fails(self, mock_run, mock_version, mock_find, mock_return, mock_create_pr):
        """Should return False when fallback PR creation fails."""
        mock_version.return_value = "v1.6.0"
        mock_find.return_value = "release/v1.6.0"
        mock_return.return_value = True

        mock_run.side_effect = [
            MagicMock(returncode=0),  # git fetch origin
            MagicMock(stdout="2\n", returncode=0),  # git rev-list --count (behind)
            MagicMock(returncode=0),  # git checkout release branch
        ]

        mock_create_pr.side_effect = [
            RuntimeError("No commits between develop and release/v1.6.0"),
            RuntimeError("some other error"),
        ]

        result = step_pr_develop()

        assert result is False
