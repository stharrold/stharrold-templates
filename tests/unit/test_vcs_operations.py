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
    _parse_github_remote,
    _query_azure_review_threads,
    _query_github_review_threads,
    _run,
    check_auth,
    create_issue,
    create_pr,
    create_release,
    get_contrib_branch,
    get_username,
    query_pr_review_threads,
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
        """Should raise RuntimeError when gh CLI is not available."""
        mock_run.side_effect = RuntimeError("'gh' CLI not found")
        with pytest.raises(RuntimeError, match="gh"):
            create_release("v1.0.0", provider=VCSProvider.GITHUB)

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
# _parse_github_remote
# ---------------------------------------------------------------------------


class TestParseGithubRemote:
    """Tests for _parse_github_remote helper."""

    @patch("vcs.operations.subprocess.check_output")
    def test_https_url(self, mock_output):
        mock_output.return_value = "https://github.com/owner/repo.git"
        owner, repo = _parse_github_remote()
        assert owner == "owner"
        assert repo == "repo"

    @patch("vcs.operations.subprocess.check_output")
    def test_ssh_url(self, mock_output):
        mock_output.return_value = "git@github.com:owner/repo.git"
        owner, repo = _parse_github_remote()
        assert owner == "owner"
        assert repo == "repo"

    @patch("vcs.operations.subprocess.check_output")
    def test_https_url_no_git_suffix(self, mock_output):
        mock_output.return_value = "https://github.com/owner/repo"
        owner, repo = _parse_github_remote()
        assert owner == "owner"
        assert repo == "repo"

    @patch("vcs.operations.subprocess.check_output")
    def test_unsupported_url_format(self, mock_output):
        mock_output.return_value = "svn://example.com/owner/repo"
        with pytest.raises(RuntimeError, match="Unsupported remote URL format"):
            _parse_github_remote()

    @patch("vcs.operations.subprocess.check_output")
    def test_malformed_url_missing_repo(self, mock_output):
        mock_output.return_value = "https://github.com/owner"
        with pytest.raises(RuntimeError, match="Failed to parse owner/repo"):
            _parse_github_remote()

    @patch("vcs.operations.subprocess.check_output")
    def test_git_not_found(self, mock_output):
        mock_output.side_effect = FileNotFoundError("git not found")
        with pytest.raises(RuntimeError, match="Failed to read git remote URL"):
            _parse_github_remote()


# ---------------------------------------------------------------------------
# query_pr_review_threads (GitHub)
# ---------------------------------------------------------------------------


class TestQueryGithubReviewThreads:
    """Tests for _query_github_review_threads."""

    GRAPHQL_RESPONSE = {
        "data": {
            "repository": {
                "pullRequest": {
                    "url": "https://github.com/owner/repo/pull/42",
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": "thread-1",
                                "isResolved": False,
                                "comments": {
                                    "nodes": [
                                        {
                                            "url": "https://github.com/owner/repo/pull/42#discussion_thread-1",
                                            "path": "src/main.py",
                                            "line": 10,
                                            "author": {"login": "reviewer"},
                                            "body": "Fix this bug",
                                            "createdAt": "2025-01-15T12:00:00Z",
                                        }
                                    ]
                                },
                            },
                            {
                                "id": "thread-2",
                                "isResolved": True,
                                "comments": {
                                    "nodes": [
                                        {
                                            "url": "https://github.com/owner/repo/pull/42#discussion_thread-2",
                                            "path": "src/utils.py",
                                            "line": 20,
                                            "author": {"login": "reviewer"},
                                            "body": "Already resolved",
                                            "createdAt": "2025-01-14T12:00:00Z",
                                        }
                                    ]
                                },
                            },
                            {
                                "id": "thread-3",
                                "isResolved": False,
                                "comments": {"nodes": []},
                            },
                        ]
                    },
                }
            }
        }
    }

    @patch("vcs.operations._parse_github_remote", return_value=("owner", "repo"))
    @patch("vcs.operations._run")
    def test_filters_resolved_and_empty_threads(self, mock_run, _mock_remote):
        """Should return only unresolved threads with comments."""
        import json

        mock_run.return_value = json.dumps(self.GRAPHQL_RESPONSE)

        result = _query_github_review_threads(42)

        assert len(result) == 1
        assert result[0]["id"] == "thread-1"
        assert result[0]["file"] == "src/main.py"
        assert result[0]["line"] == 10
        assert result[0]["author"] == "reviewer"
        assert result[0]["body"] == "Fix this bug"

    @patch("vcs.operations._parse_github_remote", return_value=("owner", "repo"))
    @patch("vcs.operations._run")
    def test_invalid_json_raises(self, mock_run, _mock_remote):
        """Should raise RuntimeError on invalid JSON."""
        mock_run.return_value = "not-json"

        with pytest.raises(RuntimeError, match="Failed to parse GitHub GraphQL response"):
            _query_github_review_threads(42)

    @patch("vcs.operations._parse_github_remote", return_value=("owner", "repo"))
    @patch("vcs.operations._run")
    def test_missing_keys_raises(self, mock_run, _mock_remote):
        """Should raise RuntimeError on unexpected response structure."""
        import json

        mock_run.return_value = json.dumps({"data": {}})

        with pytest.raises(RuntimeError, match="Failed to parse GitHub review threads"):
            _query_github_review_threads(42)

    @patch("vcs.operations._parse_github_remote", return_value=("owner", "repo"))
    @patch("vcs.operations._run")
    def test_handles_missing_author(self, mock_run, _mock_remote):
        """Should use 'Unknown' when comment has no author."""
        import json

        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "url": "https://github.com/owner/repo/pull/42",
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "id": "thread-1",
                                    "isResolved": False,
                                    "comments": {
                                        "nodes": [
                                            {
                                                "body": "comment",
                                                "createdAt": "2025-01-15T12:00:00Z",
                                            }
                                        ]
                                    },
                                }
                            ]
                        },
                    }
                }
            }
        }
        mock_run.return_value = json.dumps(response)

        result = _query_github_review_threads(42)

        assert result[0]["author"] == "Unknown"


# ---------------------------------------------------------------------------
# query_pr_review_threads (Azure DevOps)
# ---------------------------------------------------------------------------


class TestQueryAzureReviewThreads:
    """Tests for _query_azure_review_threads."""

    @patch("vcs.operations._run")
    def test_parses_azure_threads(self, mock_run):
        """Should parse Azure DevOps thread response."""
        import json

        threads = [
            {
                "id": 1,
                "comments": [
                    {
                        "author": {"uniqueName": "user@org.com"},
                        "content": "Please fix",
                        "publishedDate": "2025-01-15T12:00:00Z",
                    }
                ],
            }
        ]
        mock_run.return_value = json.dumps(threads)

        result = _query_azure_review_threads(42)

        assert len(result) == 1
        assert result[0]["id"] == "1"
        assert result[0]["author"] == "user@org.com"
        assert result[0]["body"] == "Please fix"

    @patch("vcs.operations._run")
    def test_skips_threads_without_comments(self, mock_run):
        """Should skip threads that have no comments."""
        import json

        threads = [{"id": 1, "comments": []}, {"id": 2}]
        mock_run.return_value = json.dumps(threads)

        result = _query_azure_review_threads(42)

        assert len(result) == 0

    @patch("vcs.operations._run")
    def test_handles_null_response(self, mock_run):
        """Should handle null/empty response."""
        mock_run.return_value = "null"

        result = _query_azure_review_threads(42)

        assert result == []

    @patch("vcs.operations._run")
    def test_invalid_json_raises(self, mock_run):
        """Should raise RuntimeError on invalid JSON."""
        mock_run.return_value = "not-json"

        with pytest.raises(RuntimeError, match="Failed to parse Azure DevOps threads"):
            _query_azure_review_threads(42)


# ---------------------------------------------------------------------------
# query_pr_review_threads (dispatch)
# ---------------------------------------------------------------------------


class TestQueryPrReviewThreads:
    """Tests for the public query_pr_review_threads dispatch."""

    @patch("vcs.operations._query_github_review_threads")
    def test_dispatches_to_github(self, mock_github):
        mock_github.return_value = [{"id": "1"}]
        result = query_pr_review_threads(42, provider=VCSProvider.GITHUB)
        assert result == [{"id": "1"}]
        mock_github.assert_called_once_with(42)

    @patch("vcs.operations._query_azure_review_threads")
    def test_dispatches_to_azure(self, mock_azure):
        mock_azure.return_value = []
        result = query_pr_review_threads(42, provider=VCSProvider.AZURE_DEVOPS)
        assert result == []
        mock_azure.assert_called_once_with(42)


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
