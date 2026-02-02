#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for secrets_run.py --get-to-stdout mode and command mode.

Tests cover:
- --get-to-stdout: env var, keyring, no trailing newline, stderr diagnostics
- --get-to-stdout: missing secret, not in config, mutual exclusivity, missing name
- --get-to-stdout: missing secrets.toml
- Command mode: still works with --get-to-stdout additions
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.secrets_run import get_secret_to_stdout, main


class TestGetToStdoutFromEnv:
    """Secret found in environment -> stdout, exit 0."""

    def test_get_to_stdout_from_env(self, capsys):
        config = {"required": ["API_KEY"], "optional": [], "service": "test-svc"}
        with (
            patch("scripts.secrets_run.load_secrets_config", return_value=config),
            patch("scripts.secrets_run.is_ci", return_value=False),
            patch("scripts.secrets_run.is_container", return_value=False),
            patch("scripts.secrets_run.resolve_secret", return_value=("s3cr3t", "environment")),
        ):
            result = get_secret_to_stdout("API_KEY", Path("/fake"))

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out == "s3cr3t"


class TestGetToStdoutFromKeyring:
    """Secret found in keyring -> stdout, exit 0."""

    def test_get_to_stdout_from_keyring(self, capsys):
        config = {"required": ["DB_PASS"], "optional": [], "service": "my-svc"}
        with (
            patch("scripts.secrets_run.load_secrets_config", return_value=config),
            patch("scripts.secrets_run.is_ci", return_value=False),
            patch("scripts.secrets_run.is_container", return_value=False),
            patch("scripts.secrets_run.resolve_secret", return_value=("keyring-val", "keyring")),
        ):
            result = get_secret_to_stdout("DB_PASS", Path("/fake"))

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out == "keyring-val"


class TestGetToStdoutNoTrailingNewline:
    """Output must have no trailing newline for pipe-friendly usage."""

    def test_no_trailing_newline(self, capsys):
        config = {"required": ["TOKEN"], "optional": [], "service": "svc"}
        with (
            patch("scripts.secrets_run.load_secrets_config", return_value=config),
            patch("scripts.secrets_run.is_ci", return_value=False),
            patch("scripts.secrets_run.is_container", return_value=False),
            patch("scripts.secrets_run.resolve_secret", return_value=("abc123", "environment")),
        ):
            get_secret_to_stdout("TOKEN", Path("/fake"))

        captured = capsys.readouterr()
        assert not captured.out.endswith("\n")
        assert captured.out == "abc123"


class TestGetToStdoutDiagnosticsToStderr:
    """[INFO]/[OK]/[FAIL] go to stderr, not stdout."""

    def test_diagnostics_to_stderr(self, capsys):
        config = {"required": ["SECRET"], "optional": [], "service": "svc"}
        with (
            patch("scripts.secrets_run.load_secrets_config", return_value=config),
            patch("scripts.secrets_run.is_ci", return_value=False),
            patch("scripts.secrets_run.is_container", return_value=False),
            patch("scripts.secrets_run.resolve_secret", return_value=("val", "environment")),
        ):
            get_secret_to_stdout("SECRET", Path("/fake"))

        captured = capsys.readouterr()
        # stdout has only the secret value
        assert captured.out == "val"
        # stderr has diagnostics
        assert "[INFO]" in captured.err
        assert "[OK]" in captured.err


class TestGetToStdoutMissingSecret:
    """Secret not found -> exit 1, stderr message."""

    def test_missing_secret(self, capsys):
        config = {"required": ["MISS"], "optional": [], "service": "svc"}
        with (
            patch("scripts.secrets_run.load_secrets_config", return_value=config),
            patch("scripts.secrets_run.is_ci", return_value=False),
            patch("scripts.secrets_run.is_container", return_value=False),
            patch("scripts.secrets_run.resolve_secret", return_value=(None, "not found")),
        ):
            result = get_secret_to_stdout("MISS", Path("/fake"))

        assert result == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "[FAIL]" in captured.err


class TestGetToStdoutNotInConfig:
    """Secret name not in secrets.toml -> exit 1."""

    def test_not_in_config(self, capsys):
        config = {"required": ["OTHER"], "optional": [], "service": "svc"}
        with patch("scripts.secrets_run.load_secrets_config", return_value=config):
            result = get_secret_to_stdout("UNKNOWN", Path("/fake"))

        assert result == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "not defined in secrets.toml" in captured.err


class TestGetToStdoutMutualExclusivity:
    """--get-to-stdout with extra args -> exit 1."""

    def test_mutual_exclusivity(self, capsys):
        with (
            patch("sys.argv", ["secrets_run.py", "--get-to-stdout", "KEY", "extra-cmd"]),
            patch("scripts.secrets_run.get_repo_root", return_value=Path("/fake")),
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "mutually exclusive" in captured.err


class TestGetToStdoutMissingName:
    """--get-to-stdout with no name -> exit 1."""

    def test_missing_name(self, capsys):
        with patch("sys.argv", ["secrets_run.py", "--get-to-stdout"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "SECRET_NAME" in captured.err


class TestGetToStdoutMissingSecretsToml:
    """No secrets.toml -> exit 1, stderr."""

    def test_missing_secrets_toml(self, capsys, tmp_path):
        # tmp_path has no secrets.toml
        with (
            patch("sys.argv", ["secrets_run.py", "--get-to-stdout", "KEY"]),
            patch("scripts.secrets_run.get_repo_root", return_value=tmp_path),
        ):
            # load_secrets_config calls sys.exit(1) when file missing
            try:
                main()
            except SystemExit as e:
                assert e.code == 1

        captured = capsys.readouterr()
        assert "secrets.toml not found" in captured.err


class TestCommandModeStillWorks:
    """Existing command mode is unaffected by --get-to-stdout additions."""

    def test_command_mode_runs_subprocess(self, capsys):
        config = {"required": [], "optional": [], "service": "svc"}
        with (
            patch("sys.argv", ["secrets_run.py", "echo", "hello"]),
            patch("scripts.secrets_run.get_repo_root", return_value=Path("/fake")),
            patch("scripts.secrets_run.load_secrets_config", return_value=config),
            patch("scripts.secrets_run.inject_secrets", return_value=([], [])),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            result = main()

        assert result == 0
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["echo", "hello"]
