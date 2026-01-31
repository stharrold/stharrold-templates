#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for tech-stack-adapter detect_stack.py."""

import json
import sys
from pathlib import Path

# Add the scripts directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "tech-stack-adapter" / "scripts"))

from detect_stack import detect_stack


class TestDetectStack:
    """Tests for detect_stack() function."""

    def test_returns_dict(self):
        """detect_stack() returns a dictionary."""
        config = detect_stack()
        assert isinstance(config, dict)

    def test_has_required_keys(self):
        """detect_stack() returns all required configuration keys."""
        config = detect_stack()
        required_keys = [
            "stack",
            "package_manager",
            "project_name",
            "repo_root",
            "install_cmd",
            "test_cmd",
            "build_cmd",
            "coverage_cmd",
            "coverage_check",
            "database",
            "orm",
            "migrate_cmd",
            "container",
            "has_containerfile",
            "has_compose",
            "test_framework",
            "has_pytest_cov",
        ]
        for key in required_keys:
            assert key in config, f"Missing required key: {key}"

    def test_detects_python_stack(self):
        """detect_stack() detects Python as the stack."""
        config = detect_stack()
        assert config["stack"] == "python"
        assert config["package_manager"] == "uv"

    def test_detects_project_name(self):
        """detect_stack() detects the project name from pyproject.toml."""
        config = detect_stack()
        assert config["project_name"] == "stharrold-templates"

    def test_repo_root_is_absolute(self):
        """detect_stack() returns an absolute repo_root path."""
        config = detect_stack()
        assert Path(config["repo_root"]).is_absolute()

    def test_output_is_json_serializable(self):
        """detect_stack() output can be serialized to JSON."""
        config = detect_stack()
        json_str = json.dumps(config, indent=2)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed == config
