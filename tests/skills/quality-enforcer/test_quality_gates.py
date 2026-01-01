#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for quality-enforcer run_quality_gates.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / ".gemini/skills/quality-enforcer/scripts"),
)

from run_quality_gates import (
    check_build,
    check_coverage,
    check_linting,
    get_worktree_info,
    run_all_quality_gates,
    run_tests,
    sync_ai_config,
)


class TestGetWorktreeInfo:
    """Tests for get_worktree_info function."""

    def test_returns_dict_with_required_keys(self):
        """Should return dict with worktree_id and worktree_root keys."""
        result = get_worktree_info()
        assert isinstance(result, dict)
        assert "worktree_id" in result
        assert "worktree_root" in result

    def test_worktree_root_is_path_string(self):
        """Should return worktree_root as a string path."""
        result = get_worktree_info()
        assert isinstance(result["worktree_root"], str)


class TestRunTests:
    """Tests for run_tests function."""

    @patch("run_quality_gates.subprocess.run")
    @patch("run_quality_gates.get_command_prefix")
    def test_run_tests_success(self, mock_prefix, mock_run):
        """Should return True when tests pass."""
        mock_prefix.return_value = ["uv", "run"]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = run_tests()

        assert result is True
        mock_run.assert_called_once()

    @patch("run_quality_gates.subprocess.run")
    @patch("run_quality_gates.get_command_prefix")
    def test_run_tests_failure(self, mock_prefix, mock_run):
        """Should return False when tests fail."""
        mock_prefix.return_value = ["uv", "run"]
        mock_run.return_value = MagicMock(returncode=1, stdout="FAILED", stderr="")

        result = run_tests()

        assert result is False


class TestCheckCoverage:
    """Tests for check_coverage function."""

    @patch("run_quality_gates.subprocess.run")
    @patch("run_quality_gates.get_command_prefix")
    def test_check_coverage_calls_script(self, mock_prefix, mock_run):
        """Should call check_coverage.py script with threshold."""
        mock_prefix.return_value = ["uv", "run"]
        mock_run.return_value = MagicMock(returncode=0, stdout="Coverage: 85%")

        result = check_coverage(80)

        assert result is True
        mock_run.assert_called_once()
        # Verify threshold is passed as argument
        call_args = mock_run.call_args[0][0]
        assert "80" in call_args

    @patch("run_quality_gates.subprocess.run")
    @patch("run_quality_gates.get_command_prefix")
    def test_check_coverage_below_threshold(self, mock_prefix, mock_run):
        """Should return False when coverage below threshold."""
        mock_prefix.return_value = ["uv", "run"]
        mock_run.return_value = MagicMock(returncode=1, stdout="Coverage: 50%")

        result = check_coverage(80)

        assert result is False


class TestCheckBuild:
    """Tests for check_build function."""

    @patch("run_quality_gates.subprocess.run")
    @patch("run_quality_gates.get_uv_command_prefix")
    def test_check_build_success(self, mock_prefix, mock_run):
        """Should return True when build succeeds."""
        mock_prefix.return_value = ["uv"]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = check_build()

        assert result is True

    @patch("run_quality_gates.subprocess.run")
    @patch("run_quality_gates.get_uv_command_prefix")
    def test_check_build_failure(self, mock_prefix, mock_run):
        """Should return False when build fails."""
        mock_prefix.return_value = ["uv"]
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Build error")

        result = check_build()

        assert result is False


class TestCheckLinting:
    """Tests for check_linting function."""

    @patch("run_quality_gates.subprocess.run")
    @patch("run_quality_gates.get_command_prefix")
    def test_check_linting_success(self, mock_prefix, mock_run):
        """Should return True when linting passes."""
        mock_prefix.return_value = ["uv", "run"]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = check_linting()

        assert result is True

    @patch("run_quality_gates.subprocess.run")
    @patch("run_quality_gates.get_command_prefix")
    def test_check_linting_failure(self, mock_prefix, mock_run):
        """Should return False when linting fails."""
        mock_prefix.return_value = ["uv", "run"]
        mock_run.return_value = MagicMock(returncode=1, stdout="Linting errors", stderr="")

        result = check_linting()

        assert result is False


class TestSyncAiConfig:
    """Tests for sync_ai_config function."""

    @patch("run_quality_gates.subprocess.run")
    def test_sync_skipped_when_no_changes(self, mock_run):
        """Should skip sync when GEMINI.md not modified."""
        mock_run.return_value = MagicMock(returncode=0, stdout="other_file.py")

        result = sync_ai_config()

        assert result is True

    @patch("run_quality_gates.shutil.copy")
    @patch("run_quality_gates.Path")
    @patch("run_quality_gates.subprocess.run")
    def test_sync_triggered_when_gemini_md_modified(self, mock_run, mock_path, mock_copy):
        """Should perform sync when GEMINI.md is modified."""
        mock_run.return_value = MagicMock(returncode=0, stdout="GEMINI.md")
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        result = sync_ai_config()

        assert result is True


class TestRunAllQualityGates:
    """Tests for run_all_quality_gates function."""

    @patch("run_quality_gates.sync_ai_config")
    @patch("run_quality_gates.check_linting")
    @patch("run_quality_gates.check_build")
    @patch("run_quality_gates.run_tests")
    @patch("run_quality_gates.check_coverage")
    @patch("run_quality_gates.get_worktree_info")
    def test_all_gates_pass(self, mock_worktree, mock_coverage, mock_tests, mock_build, mock_lint, mock_sync):
        """Should return True when all gates pass."""
        mock_worktree.return_value = {"worktree_id": "", "worktree_root": "/tmp"}
        mock_coverage.return_value = True
        mock_tests.return_value = True
        mock_build.return_value = True
        mock_lint.return_value = True
        mock_sync.return_value = True

        passed, results = run_all_quality_gates(coverage_threshold=80)

        assert passed is True
        assert results["coverage"]["passed"] is True
        assert results["tests"]["passed"] is True
        assert results["build"]["passed"] is True
        assert results["linting"]["passed"] is True
        assert results["ai_config_sync"]["passed"] is True

    @patch("run_quality_gates.sync_ai_config")
    @patch("run_quality_gates.check_linting")
    @patch("run_quality_gates.check_build")
    @patch("run_quality_gates.run_tests")
    @patch("run_quality_gates.check_coverage")
    @patch("run_quality_gates.get_worktree_info")
    def test_fails_when_one_gate_fails(self, mock_worktree, mock_coverage, mock_tests, mock_build, mock_lint, mock_sync):
        """Should return False when any gate fails."""
        mock_worktree.return_value = {"worktree_id": "", "worktree_root": "/tmp"}
        mock_coverage.return_value = True
        mock_tests.return_value = False  # Tests fail
        mock_build.return_value = True
        mock_lint.return_value = True
        mock_sync.return_value = True

        passed, results = run_all_quality_gates(coverage_threshold=80)

        assert passed is False
        assert results["tests"]["passed"] is False

    @patch("run_quality_gates.sync_ai_config")
    @patch("run_quality_gates.check_linting")
    @patch("run_quality_gates.check_build")
    @patch("run_quality_gates.run_tests")
    @patch("run_quality_gates.check_coverage")
    @patch("run_quality_gates.get_worktree_info")
    def test_coverage_threshold_passed_to_check_coverage(self, mock_worktree, mock_coverage, mock_tests, mock_build, mock_lint, mock_sync):
        """Should pass coverage_threshold to check_coverage."""
        mock_worktree.return_value = {"worktree_id": "", "worktree_root": "/tmp"}
        mock_coverage.return_value = True
        mock_tests.return_value = True
        mock_build.return_value = True
        mock_lint.return_value = True
        mock_sync.return_value = True

        run_all_quality_gates(coverage_threshold=90)

        mock_coverage.assert_called_once_with(90)
