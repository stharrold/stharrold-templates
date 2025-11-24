"""Tests for safe_output.py - Cross-platform Unicode output utilities."""

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# Add workflow-utilities/scripts to path
sys.path.insert(0, '.claude/skills/workflow-utilities/scripts')

from safe_output import (
    SYMBOLS,
    _init_utf8,
    format_arrow,
    format_check,
    format_cross,
    format_warning,
    print_error,
    print_success,
    print_warning,
    safe_print,
)


class TestInitUtf8:
    """Test UTF-8 initialization."""

    def test_init_utf8_success(self):
        """Test _init_utf8 when reconfigure succeeds."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.reconfigure = MagicMock()
            result = _init_utf8()
            assert result is True
            mock_stdout.reconfigure.assert_called_once_with(encoding='utf-8')

    def test_init_utf8_no_reconfigure_method(self):
        """Test _init_utf8 when reconfigure doesn't exist."""
        with patch('sys.stdout', spec=[]):  # No reconfigure method
            result = _init_utf8()
            assert result is False

    def test_init_utf8_reconfigure_fails(self):
        """Test _init_utf8 when reconfigure raises exception."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.reconfigure = MagicMock(side_effect=Exception("Reconfigure failed"))
            result = _init_utf8()
            assert result is False


class TestSymbols:
    """Test SYMBOLS dictionary."""

    def test_symbols_keys(self):
        """Test SYMBOLS has expected keys."""
        expected_keys = {'checkmark', 'cross', 'arrow', 'bullet', 'warning'}
        assert set(SYMBOLS.keys()) == expected_keys

    def test_symbols_values_are_strings(self):
        """Test all SYMBOLS values are strings."""
        for symbol in SYMBOLS.values():
            assert isinstance(symbol, str)
            assert len(symbol) > 0


class TestSafePrint:
    """Test safe_print function."""

    def test_safe_print_normal(self, capsys):
        """Test safe_print with ASCII text."""
        safe_print("Hello World")
        captured = capsys.readouterr()
        assert "Hello World" in captured.out

    def test_safe_print_with_unicode(self, capsys):
        """Test safe_print with Unicode characters."""
        safe_print("✓ Success")
        captured = capsys.readouterr()
        # Should print either Unicode or ASCII depending on platform
        assert "[OK] Success" in captured.out or "✓ Success" in captured.out

    def test_safe_print_fallback_on_unicode_error(self):
        """Test safe_print falls back to ASCII on UnicodeEncodeError."""
        with patch('builtins.print') as mock_print:
            # First call raises UnicodeEncodeError, second succeeds
            mock_print.side_effect = [UnicodeEncodeError('charmap', '', 0, 1, 'character maps to undefined'), None]

            safe_print("✓ Test ✗ →  ⚠")

            # Should have been called twice: first attempt + fallback
            assert mock_print.call_count == 2

            # Second call should have ASCII replacements
            args, kwargs = mock_print.call_args
            assert "[OK]" in args[0]
            assert "[X]" in args[0]
            assert "->" in args[0]
            assert "!" in args[0]

    def test_safe_print_with_kwargs(self, capsys):
        """Test safe_print preserves print kwargs."""
        safe_print("Test", end="", sep="|")
        captured = capsys.readouterr()
        assert "Test" in captured.out
        assert not captured.out.endswith("\n")  # end=""


class TestFormatFunctions:
    """Test format_* helper functions."""

    def test_format_check(self):
        """Test format_check adds checkmark."""
        result = format_check("Success")
        assert "Success" in result
        # Should contain either Unicode checkmark or [OK]
        assert "✓" in result or "[OK]" in result

    def test_format_cross(self):
        """Test format_cross adds cross."""
        result = format_cross("Error")
        assert "Error" in result
        # Should contain either Unicode cross or [X]
        assert "✗" in result or "[X]" in result

    def test_format_arrow(self):
        """Test format_arrow creates arrow between items."""
        result = format_arrow("A", "B")
        assert "A" in result
        assert "B" in result
        # Should contain either Unicode arrow or ->
        assert "→" in result or "->" in result

    def test_format_warning(self):
        """Test format_warning adds warning symbol."""
        result = format_warning("Warning")
        assert "Warning" in result
        # Should contain either Unicode warning or !
        assert "⚠" in result or "!" in result


class TestPrintConvenience:
    """Test print_* convenience functions."""

    def test_print_success(self, capsys):
        """Test print_success outputs formatted success message."""
        print_success("Operation completed")
        captured = capsys.readouterr()
        assert "Operation completed" in captured.out
        # Should have checkmark or [OK]
        assert "✓" in captured.out or "[OK]" in captured.out

    def test_print_error(self, capsys):
        """Test print_error outputs formatted error message."""
        print_error("Operation failed")
        captured = capsys.readouterr()
        assert "Operation failed" in captured.out
        # Should have cross or [X]
        assert "✗" in captured.out or "[X]" in captured.out

    def test_print_warning(self, capsys):
        """Test print_warning outputs formatted warning message."""
        print_warning("Deprecated feature")
        captured = capsys.readouterr()
        assert "Deprecated feature" in captured.out
        # Should have warning or !
        assert "⚠" in captured.out or "!" in captured.out


class TestIntegration:
    """Integration tests for safe_output module."""

    def test_multiple_symbols_in_one_message(self, capsys):
        """Test message with multiple Unicode symbols."""
        safe_print("✓ Success ✗ Failed → Next ⚠ Warning")
        captured = capsys.readouterr()
        # Should handle all symbols gracefully
        assert len(captured.out) > 0
        # At minimum, should not raise exception

    def test_format_functions_composition(self):
        """Test composing multiple format functions."""
        check_msg = format_check("Step 1")
        arrow_msg = format_arrow(check_msg, "Step 2")
        warning_msg = format_warning(arrow_msg)

        assert "Step 1" in warning_msg
        assert "Step 2" in warning_msg

    def test_safe_print_preserves_type_coercion(self, capsys):
        """Test safe_print handles non-string arguments."""
        safe_print("Count:", 42, True, None)
        captured = capsys.readouterr()
        assert "Count:" in captured.out
        assert "42" in captured.out
        assert "True" in captured.out
        assert "None" in captured.out
