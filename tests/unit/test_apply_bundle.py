# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for scripts/apply_bundle.py."""

import subprocess


def test_apply_bundle_help_exits_zero():
    result = subprocess.run(
        ["python", "scripts/apply_bundle.py", "--help"],
        capture_output=True,
        text=True,
        cwd="/Users/stharrold/Documents/GitHub/stharrold-templates",
    )
    assert result.returncode == 0
    assert "bundle" in result.stdout.lower()
