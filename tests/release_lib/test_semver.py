#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for release_lib.semver (canonical home, moved from the
git-workflow-manager semantic_version.py shim in issue #240)."""

from pathlib import Path
from unittest.mock import patch

from release_lib.semver import (
    analyze_changes,
    bump_version,
    calculate_semantic_version,
    get_changed_files,
    get_last_tag,
    next_version_from_tag,
)


class TestGetChangedFiles:
    """Tests for get_changed_files function."""

    @patch("release_lib.semver.subprocess.check_output")
    def test_returns_list_of_files(self, mock_output):
        """Should return list of changed files."""
        mock_output.return_value = "src/main.py\ntests/test_main.py\n"

        result = get_changed_files("develop")

        assert result == ["src/main.py", "tests/test_main.py"]

    @patch("release_lib.semver.subprocess.check_output")
    def test_returns_empty_list_when_no_changes(self, mock_output):
        """Should return empty list when no files changed."""
        mock_output.return_value = ""

        result = get_changed_files("develop")

        assert result == []

    @patch("release_lib.semver.subprocess.check_output")
    def test_handles_subprocess_error(self, mock_output):
        """Should return empty list on subprocess error."""
        from subprocess import CalledProcessError

        mock_output.side_effect = CalledProcessError(1, "git")

        result = get_changed_files("develop")

        assert result == []

    @patch("release_lib.semver.subprocess.check_output")
    def test_uses_three_dot_diff(self, mock_output):
        """Should use three-dot diff for merge-base comparison."""
        mock_output.return_value = ""

        get_changed_files("develop")

        call_args = mock_output.call_args[0][0]
        assert "develop...HEAD" in call_args


class TestAnalyzeChanges:
    """Tests for analyze_changes function."""

    def test_api_changes_trigger_major(self):
        """Should return major when API files changed."""
        with patch.object(Path, "exists", return_value=True):
            result = analyze_changes(["src/api/endpoints.py"])
        assert result == "major"

    def test_new_src_files_trigger_minor(self):
        """Should return minor when new source files added."""
        with patch.object(Path, "exists", return_value=True):
            result = analyze_changes(["src/new_module.py"])
        assert result == "minor"

    def test_test_files_trigger_patch(self):
        """Should return patch when only test files changed."""
        result = analyze_changes(["tests/test_new.py"])
        assert result == "patch"

    def test_docs_files_trigger_patch(self):
        """Should return patch when only docs changed."""
        result = analyze_changes(["docs/README.md"])
        assert result == "patch"

    def test_config_files_trigger_patch(self):
        """Should return patch when config files changed."""
        result = analyze_changes(["pyproject.toml"])
        assert result == "patch"

    def test_requirements_trigger_patch(self):
        """Should return patch when requirements.txt changed."""
        result = analyze_changes(["requirements.txt"])
        assert result == "patch"

    def test_uv_lock_trigger_patch(self):
        """Should return patch when uv.lock changed."""
        result = analyze_changes(["uv.lock"])
        assert result == "patch"

    def test_empty_changes_trigger_patch(self):
        """Should return patch when no changes detected."""
        result = analyze_changes([])
        assert result == "patch"

    def test_major_takes_priority(self):
        """Major should take priority over minor and patch."""
        with patch.object(Path, "exists", return_value=True):
            result = analyze_changes(
                [
                    "src/api/breaking.py",  # major
                    "src/new_feature.py",  # minor
                    "tests/test_new.py",  # patch
                ]
            )
        assert result == "major"

    def test_minor_takes_priority_over_patch(self):
        """Minor should take priority over patch."""
        with patch.object(Path, "exists", return_value=True):
            result = analyze_changes(
                [
                    "src/new_feature.py",  # minor
                    "tests/test_new.py",  # patch
                ]
            )
        assert result == "minor"


class TestBumpVersion:
    """Tests for bump_version function."""

    def test_bump_major_version(self):
        """Should increment major and reset minor/patch."""
        result = bump_version("v1.2.3", "major")
        assert result == "v2.0.0"

    def test_bump_minor_version(self):
        """Should increment minor and reset patch."""
        result = bump_version("v1.2.3", "minor")
        assert result == "v1.3.0"

    def test_bump_patch_version(self):
        """Should only increment patch."""
        result = bump_version("v1.2.3", "patch")
        assert result == "v1.2.4"

    def test_handles_version_without_v_prefix(self):
        """Should handle version without 'v' prefix."""
        result = bump_version("1.2.3", "patch")
        assert result == "v1.2.4"

    def test_handles_invalid_version_format(self):
        """Should default to v1.0.0 for invalid format."""
        result = bump_version("invalid", "patch")
        assert result == "v1.0.0"

    def test_handles_partial_version(self):
        """Should default to v1.0.0 for partial version."""
        result = bump_version("v1.2", "patch")
        assert result == "v1.0.0"

    def test_major_resets_minor_and_patch(self):
        """Major bump should reset both minor and patch to 0."""
        result = bump_version("v1.2.3", "major")
        assert result == "v2.0.0"

    def test_minor_resets_patch_only(self):
        """Minor bump should reset only patch to 0."""
        result = bump_version("v1.2.3", "minor")
        assert result == "v1.3.0"


class TestCalculateSemanticVersion:
    """Tests for calculate_semantic_version function."""

    @patch("release_lib.semver.bump_version")
    @patch("release_lib.semver.analyze_changes")
    @patch("release_lib.semver.get_changed_files")
    def test_full_calculation_flow(self, mock_files, mock_analyze, mock_bump):
        """Should calculate version through full flow."""
        mock_files.return_value = ["src/new.py"]
        mock_analyze.return_value = "minor"
        mock_bump.return_value = "v1.3.0"

        result = calculate_semantic_version("develop", "v1.2.0")

        assert result == "v1.3.0"
        mock_files.assert_called_once_with("develop")
        mock_analyze.assert_called_once_with(["src/new.py"])
        mock_bump.assert_called_once_with("v1.2.0", "minor")

    @patch("release_lib.semver.get_changed_files")
    def test_returns_current_version_when_no_changes(self, mock_files):
        """Should return current version when no files changed."""
        mock_files.return_value = []

        result = calculate_semantic_version("develop", "v1.2.0")

        assert result == "v1.2.0"


class TestSemanticVersionEdgeCases:
    """Edge case tests for semantic version functions."""

    def test_version_zero_major(self):
        """Should handle v0.x.x versions."""
        result = bump_version("v0.1.0", "minor")
        assert result == "v0.2.0"

    def test_version_high_numbers(self):
        """Should handle high version numbers."""
        result = bump_version("v99.99.99", "patch")
        assert result == "v99.99.100"

    def test_resources_files_trigger_patch(self):
        """Should return patch when resources files changed."""
        result = analyze_changes(["resources/config.json"])
        assert result == "patch"


class TestGetLastTag:
    """Tests for get_last_tag function."""

    @patch("release_lib.semver.subprocess.run")
    def test_returns_tag_when_present(self, mock_run):
        """Should return the stripped tag from git describe."""
        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "v9.0.0\n"})()
        assert get_last_tag() == "v9.0.0"

    @patch("release_lib.semver.subprocess.run")
    def test_returns_none_when_no_tags(self, mock_run):
        """Should return None when git describe fails (no tags)."""
        mock_run.return_value = type("R", (), {"returncode": 128, "stdout": ""})()
        assert get_last_tag() is None

    @patch("release_lib.semver.subprocess.run")
    def test_returns_none_on_empty_output(self, mock_run):
        """Should return None when git returns success but empty output."""
        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "\n"})()
        assert get_last_tag() is None

    @patch("release_lib.semver.subprocess.run")
    def test_scopes_lookup_to_ref(self, mock_run):
        """Should pass the ref through to git describe when given."""
        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "v1.0.0\n"})()
        get_last_tag("origin/main")
        assert mock_run.call_args[0][0] == ["git", "describe", "--tags", "--abbrev=0", "origin/main"]


class TestNextVersionFromTag:
    """Tests for next_version_from_tag (the promotion-gate helper)."""

    @patch("release_lib.semver.calculate_semantic_version")
    @patch("release_lib.semver.get_last_tag")
    def test_bumps_from_last_tag(self, mock_tag, mock_calc):
        """Should feed the last tag into the version calculation."""
        mock_tag.return_value = "v9.0.0"
        mock_calc.return_value = "v9.1.0"
        assert next_version_from_tag("develop") == "v9.1.0"
        mock_calc.assert_called_once_with("develop", "v9.0.0")

    @patch("release_lib.semver.calculate_semantic_version")
    @patch("release_lib.semver.get_last_tag")
    def test_seeds_v0_when_no_tag(self, mock_tag, mock_calc):
        """Should seed v0.0.0 when the repo has no tags yet."""
        mock_tag.return_value = None
        mock_calc.return_value = "v0.0.1"
        next_version_from_tag("develop")
        mock_calc.assert_called_once_with("develop", "v0.0.0")
