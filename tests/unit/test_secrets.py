#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for secrets management scripts.

Tests cover:
- Environment detection (CI, container)
- Secret resolution logic
- Configuration loading
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestCIDetection:
    """Tests for CI environment detection."""

    def test_github_actions_detected(self):
        """Should detect GitHub Actions via GITHUB_ACTIONS env var."""
        # Import inside test to avoid module-level side effects
        import secrets_run

        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            assert secrets_run.is_ci() is True

    def test_azure_devops_detected(self):
        """Should detect Azure DevOps via TF_BUILD env var."""
        import secrets_run

        with patch.dict(os.environ, {"TF_BUILD": "True"}, clear=False):
            assert secrets_run.is_ci() is True

    def test_gitlab_ci_detected(self):
        """Should detect GitLab CI via GITLAB_CI env var."""
        import secrets_run

        with patch.dict(os.environ, {"GITLAB_CI": "true"}, clear=False):
            assert secrets_run.is_ci() is True

    def test_generic_ci_detected(self):
        """Should detect generic CI via CI env var."""
        import secrets_run

        with patch.dict(os.environ, {"CI": "true"}, clear=False):
            assert secrets_run.is_ci() is True

    def test_no_ci_when_env_empty(self):
        """Should return False when no CI env vars set."""
        import secrets_run

        # Clear all CI-related env vars
        env_without_ci = {
            k: v
            for k, v in os.environ.items()
            if k
            not in (
                "CI",
                "GITHUB_ACTIONS",
                "GITLAB_CI",
                "TF_BUILD",
                "JENKINS_URL",
                "CIRCLECI",
                "TRAVIS",
                "BUILDKITE",
                "DRONE",
                "CODEBUILD_BUILD_ID",
            )
        }
        with patch.dict(os.environ, env_without_ci, clear=True):
            assert secrets_run.is_ci() is False


class TestContainerDetection:
    """Tests for container environment detection."""

    def test_docker_detected_via_dockerenv(self):
        """Should detect Docker via /.dockerenv file."""
        import secrets_run

        with patch.object(Path, "exists", return_value=True):
            # First call is for /.dockerenv
            assert secrets_run.is_container() is True

    def test_no_container_when_no_indicators(self):
        """Should return False when no container indicators present."""
        import secrets_run

        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "read_text", return_value="1:name=systemd:/"):
                assert secrets_run.is_container() is False


class TestSecretResolution:
    """Tests for secret resolution logic."""

    def test_env_var_takes_precedence(self):
        """Environment variable should override keyring."""
        import secrets_run

        with patch.dict(os.environ, {"TEST_SECRET": "from_env"}, clear=False):
            value, source = secrets_run.resolve_secret("TEST_SECRET", "test-service", False, False)
            assert value == "from_env"
            assert source == "environment"

    def test_ci_mode_requires_env_var(self):
        """In CI mode, missing env var should return None."""
        import secrets_run

        with patch.dict(os.environ, {}, clear=False):
            # Remove TEST_SECRET if it exists
            os.environ.pop("TEST_SECRET", None)
            value, source = secrets_run.resolve_secret("TEST_SECRET", "test-service", True, False)
            assert value is None
            assert "CI/container mode" in source

    def test_container_mode_requires_env_var(self):
        """In container mode, missing env var should return None."""
        import secrets_run

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEST_SECRET", None)
            value, source = secrets_run.resolve_secret("TEST_SECRET", "test-service", False, True)
            assert value is None
            assert "CI/container mode" in source

    def test_local_mode_uses_keyring(self):
        """In local mode, should try keyring when env var not set."""
        import secrets_run

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEST_SECRET", None)
            with patch.object(secrets_run, "get_secret_from_keyring", return_value="from_keyring"):
                value, source = secrets_run.resolve_secret("TEST_SECRET", "test-service", False, False)
                assert value == "from_keyring"
                assert source == "keyring"

    def test_local_mode_keyring_not_found(self):
        """In local mode, missing keyring secret should return None."""
        import secrets_run

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEST_SECRET", None)
            with patch.object(secrets_run, "get_secret_from_keyring", return_value=None):
                value, source = secrets_run.resolve_secret("TEST_SECRET", "test-service", False, False)
                assert value is None
                assert source == "not found"


class TestConfigLoading:
    """Tests for secrets.toml configuration loading."""

    def test_load_config_parses_required(self, tmp_path):
        """Should parse required secrets list."""
        import secrets_run

        config_content = """
[secrets]
required = ["SECRET_A", "SECRET_B"]
optional = ["SECRET_C"]

[keyring]
service = "test-service"
"""
        config_file = tmp_path / "secrets.toml"
        config_file.write_text(config_content)

        with patch.object(secrets_run, "get_repo_root", return_value=tmp_path):
            config = secrets_run.load_secrets_config(tmp_path)
            assert config["required"] == ["SECRET_A", "SECRET_B"]
            assert config["optional"] == ["SECRET_C"]
            assert config["service"] == "test-service"

    def test_load_config_handles_empty_lists(self, tmp_path):
        """Should handle empty secrets lists."""
        import secrets_run

        config_content = """
[secrets]
required = []
optional = []

[keyring]
service = "empty-service"
"""
        config_file = tmp_path / "secrets.toml"
        config_file.write_text(config_content)

        with patch.object(secrets_run, "get_repo_root", return_value=tmp_path):
            config = secrets_run.load_secrets_config(tmp_path)
            assert config["required"] == []
            assert config["optional"] == []


class TestSecretsInjection:
    """Tests for secrets injection into environment."""

    def test_inject_required_secret_success(self, tmp_path):
        """Should inject required secret from keyring."""
        import secrets_run

        config_content = """
[secrets]
required = ["INJECT_TEST"]
optional = []

[keyring]
service = "test-service"
"""
        config_file = tmp_path / "secrets.toml"
        config_file.write_text(config_content)

        with patch.object(secrets_run, "get_repo_root", return_value=tmp_path):
            with patch.object(secrets_run, "is_ci", return_value=False):
                with patch.object(secrets_run, "is_container", return_value=False):
                    with patch.object(secrets_run, "get_secret_from_keyring", return_value="test_value"):
                        # Remove env var if it exists
                        os.environ.pop("INJECT_TEST", None)

                        config = secrets_run.load_secrets_config(tmp_path)
                        missing_req, missing_opt = secrets_run.inject_secrets(config)

                        assert missing_req == []
                        assert os.environ.get("INJECT_TEST") == "test_value"

                        # Cleanup
                        os.environ.pop("INJECT_TEST", None)

    def test_inject_missing_required_secret(self, tmp_path):
        """Should report missing required secret."""
        import secrets_run

        config_content = """
[secrets]
required = ["MISSING_SECRET"]
optional = []

[keyring]
service = "test-service"
"""
        config_file = tmp_path / "secrets.toml"
        config_file.write_text(config_content)

        with patch.object(secrets_run, "get_repo_root", return_value=tmp_path):
            with patch.object(secrets_run, "is_ci", return_value=False):
                with patch.object(secrets_run, "is_container", return_value=False):
                    with patch.object(secrets_run, "get_secret_from_keyring", return_value=None):
                        os.environ.pop("MISSING_SECRET", None)

                        config = secrets_run.load_secrets_config(tmp_path)
                        missing_req, missing_opt = secrets_run.inject_secrets(config)

                        assert "MISSING_SECRET" in missing_req

    def test_inject_missing_optional_secret(self, tmp_path):
        """Should warn but not fail for missing optional secret."""
        import secrets_run

        config_content = """
[secrets]
required = []
optional = ["OPTIONAL_SECRET"]

[keyring]
service = "test-service"
"""
        config_file = tmp_path / "secrets.toml"
        config_file.write_text(config_content)

        with patch.object(secrets_run, "get_repo_root", return_value=tmp_path):
            with patch.object(secrets_run, "is_ci", return_value=False):
                with patch.object(secrets_run, "is_container", return_value=False):
                    with patch.object(secrets_run, "get_secret_from_keyring", return_value=None):
                        os.environ.pop("OPTIONAL_SECRET", None)

                        config = secrets_run.load_secrets_config(tmp_path)
                        missing_req, missing_opt = secrets_run.inject_secrets(config)

                        assert missing_req == []  # No required failures
                        assert "OPTIONAL_SECRET" in missing_opt


class TestSecretsSetup:
    """Tests for secrets_setup.py functionality."""

    def test_check_mode_returns_zero_when_all_present(self, tmp_path):
        """--check should return 0 when all secrets exist."""
        import secrets_setup

        config_content = """
[secrets]
required = ["CHECK_SECRET"]
optional = []

[keyring]
service = "test-service"
"""
        config_file = tmp_path / "secrets.toml"
        config_file.write_text(config_content)

        with patch.object(secrets_setup, "get_repo_root", return_value=tmp_path):
            with patch.object(secrets_setup, "get_secret", return_value="exists"):
                config = secrets_setup.load_secrets_config(tmp_path)
                result = secrets_setup.check_secrets(config)
                assert result == 0

    def test_check_mode_returns_one_when_missing(self, tmp_path):
        """--check should return 1 when secrets are missing."""
        import secrets_setup

        config_content = """
[secrets]
required = ["MISSING"]
optional = []

[keyring]
service = "test-service"
"""
        config_file = tmp_path / "secrets.toml"
        config_file.write_text(config_content)

        with patch.object(secrets_setup, "get_repo_root", return_value=tmp_path):
            with patch.object(secrets_setup, "get_secret", return_value=None):
                config = secrets_setup.load_secrets_config(tmp_path)
                result = secrets_setup.check_secrets(config)
                assert result == 1
