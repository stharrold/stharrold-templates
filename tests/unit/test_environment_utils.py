# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for shared environment detection utilities."""

import os
from unittest.mock import patch

from scripts.environment_utils import is_ci, is_container


class TestIsCI:
    """Tests for is_ci() function."""

    def test_returns_false_in_normal_env(self):
        with patch.dict(os.environ, {}, clear=True):
            assert is_ci() is False

    def test_returns_true_when_ci_var_set(self):
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            assert is_ci() is True

    def test_returns_true_when_github_actions_set(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            assert is_ci() is True

    def test_returns_true_when_gitlab_ci_set(self):
        with patch.dict(os.environ, {"GITLAB_CI": "true"}, clear=True):
            assert is_ci() is True

    def test_returns_true_when_jenkins_set(self):
        with patch.dict(os.environ, {"JENKINS_URL": "http://ci.example.com"}, clear=True):
            assert is_ci() is True


class TestIsContainer:
    """Tests for is_container() function."""

    def test_returns_false_normally(self):
        with patch("pathlib.Path.exists", return_value=False):
            assert is_container() is False

    def test_returns_true_when_dockerenv_exists(self):
        def mock_exists(self):
            return str(self) == "/.dockerenv"

        with patch("pathlib.Path.exists", mock_exists):
            assert is_container() is True
