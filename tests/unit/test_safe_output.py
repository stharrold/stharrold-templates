#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for safe_output.py - ASCII-only cross-platform output utilities.

Issue: #102 - Verify all output is ASCII-only for maximum compatibility.
"""

import sys

import pytest

# Add workflow-utilities/scripts to path
sys.path.insert(0, ".claude/skills/workflow-utilities/scripts")

from safe_output import (
    SYMBOLS,
    format_arrow,
    format_check,
    format_cross,
    format_info,
    format_warning,
    print_error,
    print_info,
    print_success,
    print_warning,
    safe_print,
)


class TestSymbols:
    """Test SYMBOLS dictionary."""

    def test_symbols_keys(self):
        """Test SYMBOLS has expected keys."""
        expected_keys = {"checkmark", "cross", "arrow", "bullet", "warning", "info"}
        assert set(SYMBOLS.keys()) == expected_keys

    def test_symbols_values_are_strings(self):
        """Test all SYMBOLS values are strings."""
        for symbol in SYMBOLS.values():
            assert isinstance(symbol, str)
            assert len(symbol) > 0

    def test_symbols_are_ascii_only(self):
        """Test all SYMBOLS values are ASCII-only (Issue #102)."""
        for name, symbol in SYMBOLS.items():
            assert symbol.isascii(), f"Symbol '{name}' contains non-ASCII: {symbol!r}"

    def test_symbols_expected_values(self):
        """Test SYMBOLS have expected ASCII values."""
        assert SYMBOLS["checkmark"] == "[OK]"
        assert SYMBOLS["cross"] == "[FAIL]"
        assert SYMBOLS["arrow"] == "->"
        assert SYMBOLS["bullet"] == "*"
        assert SYMBOLS["warning"] == "[WARN]"
        assert SYMBOLS["info"] == "[INFO]"


class TestSafePrint:
    """Test safe_print function."""

    def test_safe_print_normal(self, capsys):
        """Test safe_print with ASCII text."""
        safe_print("Hello World")
        captured = capsys.readouterr()
        assert "Hello World" in captured.out

    def test_safe_print_with_kwargs(self, capsys):
        """Test safe_print preserves print kwargs."""
        safe_print("Test", end="", sep="|")
        captured = capsys.readouterr()
        assert "Test" in captured.out
        assert not captured.out.endswith("\n")  # end=""

    def test_safe_print_output_is_ascii(self, capsys):
        """Test safe_print output is ASCII-only (Issue #102)."""
        safe_print("Test message")
        captured = capsys.readouterr()
        assert captured.out.isascii(), f"Output contains non-ASCII: {captured.out!r}"


class TestFormatFunctions:
    """Test format_* helper functions."""

    def test_format_check(self):
        """Test format_check adds [OK] prefix."""
        result = format_check("Success")
        assert result == "[OK] Success"
        assert result.isascii()

    def test_format_cross(self):
        """Test format_cross adds [FAIL] prefix."""
        result = format_cross("Error")
        assert result == "[FAIL] Error"
        assert result.isascii()

    def test_format_arrow(self):
        """Test format_arrow creates arrow between items."""
        result = format_arrow("A", "B")
        assert result == "A -> B"
        assert result.isascii()

    def test_format_warning(self):
        """Test format_warning adds [WARN] prefix."""
        result = format_warning("Warning")
        assert result == "[WARN] Warning"
        assert result.isascii()

    def test_format_info(self):
        """Test format_info adds [INFO] prefix."""
        result = format_info("Info message")
        assert result == "[INFO] Info message"
        assert result.isascii()


class TestPrintConvenience:
    """Test print_* convenience functions."""

    def test_print_success(self, capsys):
        """Test print_success outputs [OK] formatted message."""
        print_success("Operation completed")
        captured = capsys.readouterr()
        assert "[OK] Operation completed" in captured.out
        assert captured.out.isascii()

    def test_print_error(self, capsys):
        """Test print_error outputs [FAIL] formatted message."""
        print_error("Operation failed")
        captured = capsys.readouterr()
        assert "[FAIL] Operation failed" in captured.out
        assert captured.out.isascii()

    def test_print_warning(self, capsys):
        """Test print_warning outputs [WARN] formatted message."""
        print_warning("Deprecated feature")
        captured = capsys.readouterr()
        assert "[WARN] Deprecated feature" in captured.out
        assert captured.out.isascii()

    def test_print_info(self, capsys):
        """Test print_info outputs [INFO] formatted message."""
        print_info("Information message")
        captured = capsys.readouterr()
        assert "[INFO] Information message" in captured.out
        assert captured.out.isascii()


class TestIntegration:
    """Integration tests for safe_output module."""

    def test_format_functions_composition(self):
        """Test composing multiple format functions."""
        check_msg = format_check("Step 1")
        arrow_msg = format_arrow(check_msg, "Step 2")
        warning_msg = format_warning(arrow_msg)

        assert "Step 1" in warning_msg
        assert "Step 2" in warning_msg
        assert warning_msg.isascii()

    def test_safe_print_preserves_type_coercion(self, capsys):
        """Test safe_print handles non-string arguments."""
        safe_print("Count:", 42, True, None)
        captured = capsys.readouterr()
        assert "Count:" in captured.out
        assert "42" in captured.out
        assert "True" in captured.out
        assert "None" in captured.out
        assert captured.out.isascii()

    def test_all_output_ascii_with_encoding_restriction(self, capsys):
        """Test output works with ASCII-only encoding (Issue #102 main test)."""
        # This test verifies the core requirement: no UnicodeEncodeError
        print_success("test")
        print_error("test")
        print_warning("test")
        print_info("test")

        captured = capsys.readouterr()
        # All output must be ASCII-encodable
        try:
            captured.out.encode("ascii")
        except UnicodeEncodeError:
            pytest.fail(f"Output contains non-ASCII characters: {captured.out!r}")
