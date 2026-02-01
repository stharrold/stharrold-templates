#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for vcs.operations module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add VCS module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude/skills/workflow-utilities/scripts"))

from vcs import provider as provider_module
from vcs.operations import (
    _run,
    check_auth,
    create_issue,
    create_pr,
    create_release,
    get_contrib_branch,
    get_username,
)
from vcs.provider import VCSProvider


@pytest.fixture(autouse=True)
def _clear_provider_cache():
    """Reset cached provider before each test."""
    provider_module._cached_provider = None
    yield
    provider_module._cached_provider = None


# ---------------------------------------------------------------------------
# _run helper
# ---------------------------------------------------------------------------


class TestRun:
    """Tests for _run helper."""

    @patch("subprocess.check_output")
    def test_returns_stripped_stdout(self, mock_check):
        mock_check.return_value = "  hello world  \n"
        assert _run(["echo", "hello"]) == "hello world"

    @patch("subprocess.check_output")
    def test_file_not_found_raises_runtime(self, mock_check):
        mock_check.side_effect = FileNotFoundError()
        with pytest.raises(RuntimeError, match="CLI not found"):
            _run(["nonexistent"])

    @patch("subprocess.check_output")
    def test_called_process_error_raises_runtime(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(1, "gh", stderr="some error")
        with pytest.raises(RuntimeError, match="some error"):
            _run(["gh", "pr", "list"])

    @patch("subprocess.check_output")
    def test_timeout_raises_runtime(self, mock_check):
        mock_check.side_effect = subprocess.TimeoutExpired("gh", 30)
        with pytest.raises(RuntimeError, match="Timeout"):
            _run(["gh", "long-command"])


# ---------------------------------------------------------------------------
# get_username
# ---------------------------------------------------------------------------


class TestGetUsername:
    """Tests for get_username function."""

    @patch("vcs.operations._run")
    def test_github_returns_login(self, mock_run):
        mock_run.return_value = "octocat"
        result = get_username(provider=VCSProvider.GITHUB)
        assert result == "octocat"
        mock_run.assert_called_once_with(["gh", "api", "user", "--jq", ".login"], timeout=10)

    @patch("vcs.operations._run")
    def test_azure_returns_unique_name(self, mock_run):
        mock_run.return_value = "user@org.com"
        result = get_username(provider=VCSProvider.AZURE_DEVOPS)
        assert result == "user@org.com"

    @patch("vcs.operations._run")
    def test_fallback_empty_string_on_error(self, mock_run):
        mock_run.side_effect = RuntimeError("CLI not found")
        result = get_username(fallback="", provider=VCSProvider.GITHUB)
        assert result == ""

    @patch("vcs.operations._run")
    def test_fallback_custom_value_on_error(self, mock_run):
        mock_run.side_effect = RuntimeError("CLI not found")
        result = get_username(fallback="default_user", provider=VCSProvider.GITHUB)
        assert result == "default_user"

    @patch("vcs.operations._run")
    def test_fallback_none_propagates_error(self, mock_run):
        mock_run.side_effect = RuntimeError("auth failed")
        with pytest.raises(RuntimeError, match="auth failed"):
            get_username(fallback=None, provider=VCSProvider.GITHUB)


# ---------------------------------------------------------------------------
# get_contrib_branch
# ---------------------------------------------------------------------------


class TestGetContribBranch:
    """Tests for get_contrib_branch function."""

    @patch("vcs.operations.get_username")
    def test_returns_contrib_prefix(self, mock_user):
        mock_user.return_value = "octocat"
        result = get_contrib_branch(provider=VCSProvider.GITHUB)
        assert result == "contrib/octocat"

    @patch("vcs.operations.get_username")
    def test_fallback_stharrold_default(self, mock_user):
        mock_user.return_value = "stharrold"  # default fallback
        result = get_contrib_branch(provider=VCSProvider.GITHUB)
        assert result == "contrib/stharrold"

    @patch("vcs.operations.get_username")
    def test_fallback_none_raises_on_empty(self, mock_user):
        mock_user.return_value = ""
        with pytest.raises(RuntimeError, match="Failed to get VCS username"):
            get_contrib_branch(fallback=None, provider=VCSProvider.GITHUB)


# ---------------------------------------------------------------------------
# create_pr
# ---------------------------------------------------------------------------


class TestCreatePr:
    """Tests for create_pr function."""

    @patch("vcs.operations._run")
    def test_github_pr_create(self, mock_run):
        mock_run.return_value = "https://github.com/org/repo/pull/42"
        result = create_pr(
            base="develop",
            head="contrib/user",
            title="test PR",
            body="body text",
            provider=VCSProvider.GITHUB,
        )
        assert result == "https://github.com/org/repo/pull/42"
        cmd = mock_run.call_args[0][0]
        assert cmd[:3] == ["gh", "pr", "create"]
        assert "--fill" not in cmd

    @patch("vcs.operations._run")
    def test_github_pr_create_with_fill(self, mock_run):
        mock_run.return_value = "https://github.com/org/repo/pull/42"
        create_pr(
            base="develop",
            head="contrib/user",
            title="test",
            body="body",
            fill=True,
            provider=VCSProvider.GITHUB,
        )
        cmd = mock_run.call_args[0][0]
        assert "--fill" in cmd

    @patch("vcs.operations._run")
    def test_azure_pr_create(self, mock_run):
        mock_run.return_value = '{"pullRequestId": 99}'
        result = create_pr(
            base="develop",
            head="feature/x",
            title="test",
            body="body",
            provider=VCSProvider.AZURE_DEVOPS,
        )
        assert "99" in result
        cmd = mock_run.call_args[0][0]
        assert cmd[:4] == ["az", "repos", "pr", "create"]

    @patch("vcs.operations._run")
    def test_already_exists_error_propagates(self, mock_run):
        mock_run.side_effect = RuntimeError("a pull request already exists")
        with pytest.raises(RuntimeError, match="already exists"):
            create_pr(
                base="develop",
                head="contrib/user",
                title="test",
                body="body",
                provider=VCSProvider.GITHUB,
            )


# ---------------------------------------------------------------------------
# create_release
# ---------------------------------------------------------------------------


class TestCreateRelease:
    """Tests for create_release function."""

    @patch("vcs.operations._run")
    def test_github_release(self, mock_run):
        mock_run.return_value = "https://github.com/org/repo/releases/tag/v1.0.0"
        result = create_release("v1.0.0", provider=VCSProvider.GITHUB)
        assert result == "https://github.com/org/repo/releases/tag/v1.0.0"

    @patch("vcs.operations._run")
    def test_github_release_gh_not_available(self, mock_run):
        mock_run.side_effect = RuntimeError("'gh' CLI not found")
        result = create_release("v1.0.0", provider=VCSProvider.GITHUB)
        assert result is None

    def test_azure_returns_none(self):
        result = create_release("v1.0.0", provider=VCSProvider.AZURE_DEVOPS)
        assert result is None


# ---------------------------------------------------------------------------
# create_issue
# ---------------------------------------------------------------------------


class TestCreateIssue:
    """Tests for create_issue function."""

    @patch("vcs.operations._run")
    def test_github_issue_basic(self, mock_run):
        mock_run.return_value = "https://github.com/org/repo/issues/10"
        result = create_issue(title="Bug", body="details", provider=VCSProvider.GITHUB)
        assert "issues/10" in result

    @patch("vcs.operations._run")
    def test_github_issue_with_labels_and_assignee(self, mock_run):
        mock_run.return_value = "https://github.com/org/repo/issues/10"
        create_issue(
            title="Bug",
            body="details",
            labels=["bug", "priority"],
            assignee_self=True,
            provider=VCSProvider.GITHUB,
        )
        cmd = mock_run.call_args[0][0]
        assert "--label" in cmd
        assert "bug" in cmd
        assert "priority" in cmd
        assert "--assignee" in cmd
        assert "@me" in cmd

    @patch("vcs.operations._run")
    def test_azure_work_item(self, mock_run):
        mock_run.return_value = '{"id": 42}'
        result = create_issue(title="Task", body="details", provider=VCSProvider.AZURE_DEVOPS)
        assert "42" in result


# ---------------------------------------------------------------------------
# check_auth
# ---------------------------------------------------------------------------


class TestCheckAuth:
    """Tests for check_auth function."""

    @patch("vcs.operations._run")
    def test_github_authenticated(self, mock_run):
        mock_run.return_value = "Logged in"
        assert check_auth(provider=VCSProvider.GITHUB) is True

    @patch("vcs.operations._run")
    def test_github_not_authenticated(self, mock_run):
        mock_run.side_effect = RuntimeError("not authenticated")
        assert check_auth(provider=VCSProvider.GITHUB) is False

    @patch("vcs.operations._run")
    def test_azure_authenticated(self, mock_run):
        mock_run.return_value = "account info"
        assert check_auth(provider=VCSProvider.AZURE_DEVOPS) is True

    @patch("vcs.operations._run")
    def test_azure_not_authenticated(self, mock_run):
        mock_run.side_effect = RuntimeError("not logged in")
        assert check_auth(provider=VCSProvider.AZURE_DEVOPS) is False
