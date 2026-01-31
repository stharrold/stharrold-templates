#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for workflow-orchestrator skill structure and documentation."""

from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "workflow-orchestrator"


class TestOrchestratorStructure:
    """Tests for workflow-orchestrator directory structure."""

    def test_skill_directory_exists(self):
        """Workflow orchestrator skill directory exists."""
        assert SKILL_DIR.is_dir()

    def test_required_files_exist(self):
        """All required skill files exist."""
        required_files = ["SKILL.md", "CLAUDE.md", "README.md", "CHANGELOG.md"]
        for filename in required_files:
            assert (SKILL_DIR / filename).is_file(), f"Missing required file: {filename}"

    def test_archived_directory_exists(self):
        """ARCHIVED subdirectory exists."""
        assert (SKILL_DIR / "ARCHIVED").is_dir()

    def test_scripts_directory_exists(self):
        """Scripts directory exists with __init__.py."""
        scripts_dir = SKILL_DIR / "scripts"
        assert scripts_dir.is_dir()
        assert (scripts_dir / "__init__.py").is_file()


class TestOrchestratorSkillMd:
    """Tests for SKILL.md content."""

    def test_has_yaml_frontmatter(self):
        """SKILL.md has YAML frontmatter with required fields."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert content.startswith("---")
        # Check required frontmatter fields
        assert "name: workflow-orchestrator" in content
        assert "version:" in content
        assert "description:" in content

    def test_has_quick_reference(self):
        """SKILL.md has Quick Reference section."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "## Quick Reference" in content

    def test_has_context_detection(self):
        """SKILL.md documents the context detection algorithm."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "detect_context" in content or "Context Detection" in content
