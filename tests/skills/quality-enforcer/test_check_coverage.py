#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for quality-enforcer check_coverage.py."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add scripts to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / ".gemini/skills/quality-enforcer/scripts"),
)

from check_coverage import check_coverage


class TestCheckCoverage:
    """Tests for check_coverage function."""

    @patch("check_coverage.Path")
    @patch("check_coverage.subprocess.run")
    def test_coverage_above_threshold(self, mock_run, mock_path):
        """Should return True when coverage exceeds threshold."""
        mock_run.return_value = MagicMock(returncode=0)
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        coverage_data = {"totals": {"percent_covered": 85.5}}

        with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
            passed, coverage = check_coverage(80)

        assert passed is True
        assert coverage == 85.5

    @patch("check_coverage.Path")
    @patch("check_coverage.subprocess.run")
    def test_coverage_below_threshold(self, mock_run, mock_path):
        """Should return False when coverage below threshold."""
        mock_run.return_value = MagicMock(returncode=0)
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        coverage_data = {"totals": {"percent_covered": 50.0}}

        with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
            passed, coverage = check_coverage(80)

        assert passed is False
        assert coverage == 50.0

    @patch("check_coverage.Path")
    @patch("check_coverage.subprocess.run")
    def test_coverage_exactly_at_threshold(self, mock_run, mock_path):
        """Should return True when coverage equals threshold."""
        mock_run.return_value = MagicMock(returncode=0)
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        coverage_data = {"totals": {"percent_covered": 80.0}}

        with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
            passed, coverage = check_coverage(80)

        assert passed is True
        assert coverage == 80.0

    @patch("check_coverage.Path")
    @patch("check_coverage.subprocess.run")
    def test_fallback_when_coverage_json_missing(self, mock_run, mock_path):
        """Should return 0.0 coverage when JSON file not found."""
        mock_run.return_value = MagicMock(returncode=0)
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        passed, coverage = check_coverage(80)

        assert passed is False
        assert coverage == 0.0

    @patch("check_coverage.subprocess.run")
    def test_returns_false_when_uv_not_found(self, mock_run):
        """Should return False when uv command not found."""
        mock_run.side_effect = FileNotFoundError("uv not found")

        passed, coverage = check_coverage(80)

        assert passed is False
        assert coverage == 0.0

    @patch("check_coverage.Path")
    @patch("check_coverage.subprocess.run")
    def test_custom_threshold(self, mock_run, mock_path):
        """Should use custom threshold when provided."""
        mock_run.return_value = MagicMock(returncode=0)
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        coverage_data = {"totals": {"percent_covered": 95.0}}

        with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
            # 95% coverage should fail with 100% threshold
            passed, coverage = check_coverage(100)

        assert passed is False

        with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
            # 95% coverage should pass with 90% threshold
            passed, coverage = check_coverage(90)

        assert passed is True


class TestCheckCoverageEdgeCases:
    """Edge case tests for check_coverage function."""

    @patch("check_coverage.Path")
    @patch("check_coverage.subprocess.run")
    def test_zero_threshold(self, mock_run, mock_path):
        """Should pass with zero threshold."""
        mock_run.return_value = MagicMock(returncode=0)
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        coverage_data = {"totals": {"percent_covered": 0.0}}

        with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
            passed, coverage = check_coverage(0)

        assert passed is True

    @patch("check_coverage.Path")
    @patch("check_coverage.subprocess.run")
    def test_handles_exception_gracefully(self, mock_run, mock_path):
        """Should handle exceptions gracefully."""
        mock_run.return_value = MagicMock(returncode=0)
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        # Simulate JSON parse error
        with patch("builtins.open", mock_open(read_data="invalid json")):
            passed, coverage = check_coverage(80)

        assert passed is False
        assert coverage == 0.0
