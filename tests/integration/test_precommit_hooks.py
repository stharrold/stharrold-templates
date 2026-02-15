# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Integration tests for custom pre-commit hooks.

Tests each hook script by invoking it via subprocess against
temporary test fixtures.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-utilities" / "scripts"


class TestCheckClaudeMdFrontmatter:
    """Tests for check_claude_md_frontmatter.py hook."""

    def test_passes_with_valid_frontmatter(self, tmp_path, monkeypatch):
        """Hook passes when all CLAUDE.md files have YAML frontmatter."""
        monkeypatch.chdir(tmp_path)
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("---\ntype: claude-context\n---\n# Test\n")

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_claude_md_frontmatter.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_fails_without_frontmatter(self, tmp_path, monkeypatch):
        """Hook fails when CLAUDE.md is missing YAML frontmatter."""
        monkeypatch.chdir(tmp_path)
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test\nNo frontmatter here.\n")

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_claude_md_frontmatter.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "missing YAML frontmatter" in result.stdout

    def test_passes_with_no_claude_md_files(self, tmp_path, monkeypatch):
        """Hook passes when there are no CLAUDE.md files."""
        monkeypatch.chdir(tmp_path)

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_claude_md_frontmatter.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestCheckSkillStructure:
    """Tests for check_skill_structure.py hook."""

    def test_passes_with_valid_structure(self, tmp_path, monkeypatch):
        """Hook passes when skill directories have all required files."""
        monkeypatch.chdir(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "CLAUDE.md").write_text("---\ntype: claude-context\n---\n")
        (skill_dir / "README.md").write_text("# Test Skill\n")
        (skill_dir / "SKILL.md").write_text("---\nversion: 1.0.0\n---\n")

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_skill_structure.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_fails_with_missing_files(self, tmp_path, monkeypatch):
        """Hook fails when skill directory is missing required files."""
        monkeypatch.chdir(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        # Only create CLAUDE.md, missing README.md and SKILL.md

        (skill_dir / "CLAUDE.md").write_text("---\ntype: claude-context\n---\n")

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_skill_structure.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "missing" in result.stdout.lower()

    def test_passes_with_no_skills_directory(self, tmp_path, monkeypatch):
        """Hook passes when .claude/skills/ doesn't exist."""
        monkeypatch.chdir(tmp_path)

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_skill_structure.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestCheckSpdxHeaders:
    """Tests for check_spdx_headers.py hook."""

    def test_passes_with_valid_headers(self, tmp_path, monkeypatch):
        """Hook passes when Python files have SPDX headers."""
        monkeypatch.chdir(tmp_path)
        py_file = tmp_path / "test_script.py"
        py_file.write_text('# SPDX-FileCopyrightText: 2025 stharrold\n# SPDX-License-Identifier: Apache-2.0\n"""A test module."""\n')

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_spdx_headers.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_fails_without_headers(self, tmp_path, monkeypatch):
        """Hook fails when Python files are missing SPDX headers."""
        monkeypatch.chdir(tmp_path)
        py_file = tmp_path / "test_script.py"
        py_file.write_text('"""A module without SPDX headers."""\n\nprint("hello")\n')

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_spdx_headers.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "missing SPDX" in result.stdout


class TestCheckAsciiOnly:
    """Tests for check_ascii_only.py hook."""

    def test_passes_with_ascii_only(self, tmp_path):
        """Hook passes when Python files contain only ASCII."""
        py_file = tmp_path / "clean.py"
        py_file.write_text('# SPDX-FileCopyrightText: 2025 stharrold\n# SPDX-License-Identifier: Apache-2.0\nprint("hello world")\n')

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_ascii_only.py"), str(py_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_fails_with_non_ascii(self, tmp_path):
        """Hook fails when Python files contain non-ASCII characters."""
        py_file = tmp_path / "unicode.py"
        py_file.write_text('print("\u2713 done")\n')

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_ascii_only.py"), str(py_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Non-ASCII" in result.stdout
