#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for check_ascii_only.py edge cases."""

import os
import sys
from pathlib import Path

import pytest

# Add the scripts directory to the path for imports
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / ".gemini" / "skills" / "workflow-utilities" / "scripts"),
)

from check_ascii_only import (
    ASCII_REPLACEMENTS,
    check_file,
    check_paths,
    find_non_ascii,
    get_replacement,
    is_ascii,
    should_skip,
)


class TestIsAscii:
    """Tests for is_ascii() function."""

    def test_ascii_only_returns_true(self):
        """Pure ASCII text returns True."""
        assert is_ascii("Hello, World!")
        assert is_ascii("def foo(): pass")
        assert is_ascii("# Comment with symbols: @#$%^&*()")

    def test_unicode_returns_false(self):
        """Text with Unicode returns False."""
        assert not is_ascii("Hello \u2713")  # checkmark
        assert not is_ascii("\u2192 arrow")  # arrow
        assert not is_ascii("emoji \U0001f389")  # party

    def test_empty_string_returns_true(self):
        """Empty string is valid ASCII."""
        assert is_ascii("")

    def test_newlines_and_tabs_are_ascii(self):
        """Control characters like newlines are ASCII."""
        assert is_ascii("line1\nline2\ttab")


class TestFindNonAscii:
    """Tests for find_non_ascii() function."""

    def test_returns_empty_for_ascii(self):
        """Returns empty list for ASCII-only text."""
        assert find_non_ascii("Hello World") == []

    def test_finds_single_unicode_char(self):
        """Finds single Unicode character with position."""
        result = find_non_ascii("OK \u2713")
        assert len(result) == 1
        assert result[0] == (1, 4, "\u2713")

    def test_finds_multiple_unicode_chars(self):
        """Finds multiple Unicode characters."""
        result = find_non_ascii("\u2713 and \u2717")
        assert len(result) == 2
        assert result[0][2] == "\u2713"
        assert result[1][2] == "\u2717"

    def test_correct_line_numbers(self):
        """Reports correct line numbers (1-based)."""
        result = find_non_ascii("line1\nline2 \u2713\nline3")
        assert len(result) == 1
        assert result[0][0] == 2  # Line 2

    def test_correct_column_numbers(self):
        """Reports correct column numbers (1-based)."""
        result = find_non_ascii("abc\u2713def")
        assert len(result) == 1
        assert result[0][1] == 4  # Column 4


class TestGetReplacement:
    """Tests for get_replacement() function."""

    def test_known_replacements(self):
        """Returns correct replacement for known characters."""
        assert get_replacement("\u2713") == "[OK]"
        assert get_replacement("\u2717") == "[FAIL]"
        assert get_replacement("\u2192") == "->"
        assert get_replacement("\u2265") == ">="

    def test_unknown_returns_none(self):
        """Returns None for unknown characters."""
        assert get_replacement("\u00e9") is None  # e with accent
        assert get_replacement("\u4e2d") is None  # Chinese character

    def test_emoji_replacements(self):
        """Returns correct replacement for emojis."""
        assert get_replacement("\U0001f389") == "[DONE]"
        assert get_replacement("\U0001f680") == "[GO]"


class TestShouldSkip:
    """Tests for should_skip() function."""

    def test_skips_check_ascii_only(self):
        """Skips check_ascii_only.py itself."""
        assert should_skip(Path("check_ascii_only.py"))
        assert should_skip(Path("some/path/check_ascii_only.py"))

    def test_skips_git_directory(self):
        """Skips .git directory."""
        assert should_skip(Path(".git/hooks/pre-commit"))

    def test_skips_venv(self):
        """Skips .venv directory."""
        assert should_skip(Path(".venv/lib/python3.11/site.py"))

    def test_skips_pycache(self):
        """Skips __pycache__ directory."""
        assert should_skip(Path("src/__pycache__/module.cpython-311.pyc"))

    def test_skips_agents_directory(self):
        """Skips .agents directory (auto-synced mirror)."""
        assert should_skip(Path(".agents/workflow-utilities/scripts/foo.py"))

    def test_skips_archived_directory(self):
        """Skips ARCHIVED directory."""
        assert should_skip(Path("ARCHIVED/old_module.py"))

    def test_does_not_skip_regular_files(self):
        """Does not skip regular Python files."""
        assert not should_skip(Path("src/module.py"))
        assert not should_skip(Path(".gemini/skills/foo/scripts/bar.py"))


class TestCheckFile:
    """Tests for check_file() function."""

    def test_ascii_file_returns_empty(self, tmp_path: Path):
        """Returns empty list for ASCII-only file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    return 'bar'\n")
        assert check_file(test_file) == []

    def test_unicode_file_returns_errors(self, tmp_path: Path):
        """Returns error list for file with Unicode."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# Status: \u2713\n")
        errors = check_file(test_file)
        assert len(errors) == 1
        assert "Non-ASCII" in errors[0]

    def test_shows_fix_when_enabled(self, tmp_path: Path):
        """Shows replacement suggestion when show_fix=True."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('\u2713')\n")
        errors = check_file(test_file, show_fix=True)
        assert len(errors) == 1
        assert "[OK]" in errors[0]  # Replacement suggestion

    def test_handles_undecodable_file(self, tmp_path: Path):
        """Handles files that can't be decoded as UTF-8."""
        test_file = tmp_path / "binary.py"
        test_file.write_bytes(b"\x80\x81\x82")  # Invalid UTF-8
        errors = check_file(test_file)
        assert len(errors) == 1
        assert "Unable to decode" in errors[0]

    @pytest.mark.skipif(os.geteuid() == 0, reason="Root can read files regardless of permissions")
    def test_handles_permission_error(self, tmp_path: Path):
        """Handles files that can't be read."""
        test_file = tmp_path / "noperm.py"
        test_file.write_text("content")
        test_file.chmod(0o000)
        try:
            errors = check_file(test_file)
            assert len(errors) == 1
            assert "Unable to read" in errors[0]
        finally:
            test_file.chmod(0o644)  # Restore permissions for cleanup


class TestCheckPaths:
    """Tests for check_paths() function."""

    def test_returns_zero_for_clean_directory(self, tmp_path: Path):
        """Returns 0 when all files are ASCII-only."""
        (tmp_path / "clean.py").write_text("# Clean file\n")
        result = check_paths([tmp_path])
        assert result == 0

    def test_returns_one_for_violations(self, tmp_path: Path):
        """Returns 1 when violations are found."""
        (tmp_path / "dirty.py").write_text("# \u2713 check\n")
        result = check_paths([tmp_path])
        assert result == 1

    def test_checks_single_file(self, tmp_path: Path):
        """Can check a single file directly."""
        test_file = tmp_path / "single.py"
        test_file.write_text("# ASCII only\n")
        result = check_paths([test_file])
        assert result == 0

    def test_skips_non_python_files(self, tmp_path: Path):
        """Skips non-Python files."""
        (tmp_path / "readme.md").write_text("# \u2713 Unicode in markdown\n")
        (tmp_path / "clean.py").write_text("# ASCII\n")
        result = check_paths([tmp_path])
        assert result == 0  # Markdown file ignored

    def test_recurses_into_subdirectories(self, tmp_path: Path):
        """Recursively checks subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.py").write_text("# \u2713\n")
        result = check_paths([tmp_path])
        assert result == 1


class TestAsciiReplacements:
    """Tests for ASCII_REPLACEMENTS mapping."""

    def test_all_values_are_ascii(self):
        """All replacement values are ASCII-only."""
        for key, value in ASCII_REPLACEMENTS.items():
            assert is_ascii(value), f"Replacement for {repr(key)} is not ASCII: {value}"

    def test_common_symbols_have_replacements(self):
        """Common Unicode symbols have replacements."""
        required = [
            "\u2713",  # checkmark
            "\u2717",  # cross
            "\u2192",  # arrow
            "\u2265",  # >=
            "\u2264",  # <=
        ]
        for char in required:
            assert char in ASCII_REPLACEMENTS, f"Missing replacement for {repr(char)}"

    def test_no_empty_replacements(self):
        """No replacement values are empty (except variation selector)."""
        for key, value in ASCII_REPLACEMENTS.items():
            # Variation selector can be removed entirely
            if key != "\ufe0f":
                assert value, f"Empty replacement for {repr(key)}"
