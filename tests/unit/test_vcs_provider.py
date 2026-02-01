#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for vcs.provider module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add VCS module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude/skills/workflow-utilities/scripts"))

from vcs import provider as provider_module
from vcs.provider import VCSProvider, detect_provider


@pytest.fixture(autouse=True)
def _clear_provider_cache():
    """Reset cached provider before each test."""
    provider_module._cached_provider = None
    yield
    provider_module._cached_provider = None


class TestVCSProvider:
    """Tests for VCSProvider enum."""

    def test_github_value(self):
        assert VCSProvider.GITHUB.value == "github"

    def test_azure_devops_value(self):
        assert VCSProvider.AZURE_DEVOPS.value == "azure_devops"


class TestDetectProvider:
    """Tests for detect_provider function."""

    @patch("subprocess.check_output")
    def test_github_https_url(self, mock_check):
        mock_check.return_value = "https://github.com/user/repo.git\n"
        result = detect_provider()
        assert result == VCSProvider.GITHUB

    @patch("subprocess.check_output")
    def test_github_ssh_url(self, mock_check):
        mock_check.return_value = "git@github.com:user/repo.git\n"
        result = detect_provider()
        assert result == VCSProvider.GITHUB

    @patch("subprocess.check_output")
    def test_azure_devops_url(self, mock_check):
        mock_check.return_value = "https://dev.azure.com/org/project/_git/repo\n"
        result = detect_provider()
        assert result == VCSProvider.AZURE_DEVOPS

    @patch("subprocess.check_output")
    def test_visualstudio_url(self, mock_check):
        mock_check.return_value = "https://org.visualstudio.com/project/_git/repo\n"
        result = detect_provider()
        assert result == VCSProvider.AZURE_DEVOPS

    @patch("subprocess.check_output")
    def test_unknown_url_raises(self, mock_check):
        mock_check.return_value = "https://gitlab.com/user/repo.git\n"
        with pytest.raises(RuntimeError, match="Unrecognised VCS provider"):
            detect_provider()

    @patch("subprocess.check_output")
    def test_git_not_found_raises(self, mock_check):
        mock_check.side_effect = FileNotFoundError()
        with pytest.raises(RuntimeError, match="'git' CLI not found"):
            detect_provider()

    @patch("subprocess.check_output")
    def test_git_command_fails_raises(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(1, "git", stderr="fatal: not a git repo")
        with pytest.raises(RuntimeError, match="Failed to read git remote URL"):
            detect_provider()

    @patch("subprocess.check_output")
    def test_timeout_raises(self, mock_check):
        mock_check.side_effect = subprocess.TimeoutExpired("git", 10)
        with pytest.raises(RuntimeError, match="Timeout"):
            detect_provider()

    @patch("subprocess.check_output")
    def test_caching_avoids_repeated_calls(self, mock_check):
        mock_check.return_value = "https://github.com/user/repo.git\n"

        result1 = detect_provider()
        result2 = detect_provider()

        assert result1 == result2 == VCSProvider.GITHUB
        assert mock_check.call_count == 1  # Only called once due to caching
