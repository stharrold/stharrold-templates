#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for apply_workflow.py functions."""

import sys
from pathlib import Path

# Add the scripts directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "initialize-repository" / "scripts"))

from apply_workflow import (
    extract_dev_deps_from_toml,
    merge_gitignore,
    merge_pyproject_toml,
    validate_source,
    validate_target,
)


class TestExtractDevDepsFromToml:
    """Tests for extract_dev_deps_from_toml()."""

    def test_extracts_from_dependency_groups(self):
        """Extracts dev deps from [dependency-groups].dev (PEP 735)."""
        toml_data = {
            "dependency-groups": {
                "dev": ["pytest>=8.0.0", "ruff>=0.1.0"],
            }
        }
        result = extract_dev_deps_from_toml(toml_data)
        assert result == ["pytest>=8.0.0", "ruff>=0.1.0"]

    def test_extracts_from_tool_uv(self):
        """Extracts dev deps from [tool.uv].dev-dependencies (older format)."""
        toml_data = {
            "tool": {
                "uv": {
                    "dev-dependencies": ["pytest>=7.0.0", "mypy>=1.0.0"],
                }
            }
        }
        result = extract_dev_deps_from_toml(toml_data)
        assert result == ["pytest>=7.0.0", "mypy>=1.0.0"]

    def test_extracts_from_optional_dependencies(self):
        """Extracts dev deps from [project.optional-dependencies].dev."""
        toml_data = {
            "project": {
                "optional-dependencies": {
                    "dev": ["pytest>=6.0.0", "black>=22.0.0"],
                }
            }
        }
        result = extract_dev_deps_from_toml(toml_data)
        assert result == ["pytest>=6.0.0", "black>=22.0.0"]

    def test_prefers_dependency_groups(self):
        """Prefers [dependency-groups].dev over other formats."""
        toml_data = {
            "dependency-groups": {
                "dev": ["preferred-dep"],
            },
            "tool": {
                "uv": {
                    "dev-dependencies": ["not-preferred"],
                }
            },
        }
        result = extract_dev_deps_from_toml(toml_data)
        assert result == ["preferred-dep"]

    def test_returns_empty_list_when_not_found(self):
        """Returns empty list when no dev deps found."""
        toml_data = {"project": {"name": "test"}}
        result = extract_dev_deps_from_toml(toml_data)
        assert result == []

    def test_returns_empty_list_for_empty_dev_section(self):
        """Returns empty list when dev section exists but is empty."""
        toml_data = {"dependency-groups": {"dev": []}}
        result = extract_dev_deps_from_toml(toml_data)
        assert result == []


class TestValidateSource:
    """Tests for validate_source()."""

    def test_fails_when_path_does_not_exist(self, tmp_path: Path):
        """Fails when source path doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        valid, message = validate_source(nonexistent)
        assert not valid
        assert "does not exist" in message

    def test_fails_when_path_is_file(self, tmp_path: Path):
        """Fails when source path is a file, not directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        valid, message = validate_source(file_path)
        assert not valid
        assert "not a directory" in message

    def test_fails_when_missing_skills_dir(self, tmp_path: Path):
        """Fails when .claude/skills/ directory is missing."""
        (tmp_path / ".claude" / "commands").mkdir(parents=True)
        valid, message = validate_source(tmp_path)
        assert not valid
        assert "missing .claude/skills/" in message

    def test_fails_when_missing_commands_dir(self, tmp_path: Path):
        """Fails when .claude/commands/ directory is missing."""
        (tmp_path / ".claude" / "skills" / "skill1").mkdir(parents=True)
        valid, message = validate_source(tmp_path)
        assert not valid
        assert "missing .claude/commands/" in message

    def test_fails_when_incomplete_skills(self, tmp_path: Path):
        """Fails when fewer than 3 skills exist."""
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "skill1").mkdir()
        (skills_dir / "skill2").mkdir()
        (tmp_path / ".claude" / "commands").mkdir()
        valid, message = validate_source(tmp_path)
        assert not valid
        assert "incomplete" in message

    def test_succeeds_with_complete_source(self, tmp_path: Path):
        """Succeeds when source has complete workflow system."""
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        for i in range(4):
            (skills_dir / f"skill{i}").mkdir()
        (tmp_path / ".claude" / "commands").mkdir()
        valid, message = validate_source(tmp_path)
        assert valid
        assert "4 skills found" in message


class TestValidateTarget:
    """Tests for validate_target()."""

    def test_fails_when_path_does_not_exist(self, tmp_path: Path):
        """Fails when target path doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        valid, message = validate_target(nonexistent)
        assert not valid
        assert "does not exist" in message

    def test_fails_when_path_is_file(self, tmp_path: Path):
        """Fails when target path is a file, not directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        valid, message = validate_target(file_path)
        assert not valid
        assert "not a directory" in message

    def test_fails_when_not_git_repo(self, tmp_path: Path):
        """Fails when target is not a git repository."""
        valid, message = validate_target(tmp_path)
        assert not valid
        assert "not a git repository" in message

    def test_succeeds_when_git_repo(self, tmp_path: Path):
        """Succeeds when target is a git repository."""
        (tmp_path / ".git").mkdir()
        valid, message = validate_target(tmp_path)
        assert valid
        assert "git repository" in message


class TestMergeGitignore:
    """Tests for merge_gitignore()."""

    def test_creates_gitignore_when_missing(self, tmp_path: Path):
        """Creates .gitignore when it doesn't exist (no source)."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        result = merge_gitignore(source, target)

        assert result is True
        gitignore = target / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".claude-state/" in content
        assert ".tmp/" in content

    def test_copies_source_gitignore(self, tmp_path: Path):
        """Copies source .gitignore when target doesn't have one."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        source_gitignore = source / ".gitignore"
        source_gitignore.write_text("*.pyc\n__pycache__/\n")

        result = merge_gitignore(source, target)

        assert result is True
        content = (target / ".gitignore").read_text()
        assert "*.pyc" in content
        assert "__pycache__/" in content

    def test_adds_workflow_patterns_to_existing(self, tmp_path: Path):
        """Adds workflow patterns to existing .gitignore."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        (target / ".gitignore").write_text("*.pyc\n__pycache__/\n")

        result = merge_gitignore(source, target)

        assert result is True
        content = (target / ".gitignore").read_text()
        assert "*.pyc" in content
        assert ".claude-state/" in content
        assert ".tmp/" in content

    def test_deduplicates_non_blank_lines(self, tmp_path: Path):
        """Deduplicates non-blank lines."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        (target / ".gitignore").write_text(".claude-state/\n.tmp/\n*.pyc\n")

        merge_gitignore(source, target)

        content = (target / ".gitignore").read_text()
        # Count occurrences
        assert content.count(".claude-state/") == 1
        assert content.count(".tmp/") == 1

    def test_preserves_single_blank_lines(self, tmp_path: Path):
        """Preserves blank lines but collapses consecutive ones."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        (target / ".gitignore").write_text("*.pyc\n\n\n__pycache__/\n")

        merge_gitignore(source, target)

        content = (target / ".gitignore").read_text()
        # Consecutive blank lines should be collapsed
        assert "\n\n\n" not in content
        # But single blank lines are preserved
        assert "\n\n" in content  # One blank line remains


class TestMergePyprojectToml:
    """Tests for merge_pyproject_toml()."""

    def test_warns_when_source_missing(self, tmp_path: Path):
        """Returns False when source has no pyproject.toml."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        result = merge_pyproject_toml(source, target)

        assert result is False

    def test_creates_pyproject_when_target_missing(self, tmp_path: Path):
        """Creates pyproject.toml when target doesn't have one."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        source_toml = source / "pyproject.toml"
        source_toml.write_text("""
[project]
name = "source-project"

[dependency-groups]
dev = ["pytest>=8.0.0"]
""")

        result = merge_pyproject_toml(source, target)

        assert result is True
        target_toml = target / "pyproject.toml"
        assert target_toml.exists()
        content = target_toml.read_text()
        assert "[dependency-groups]" in content
        assert "pytest>=8.0.0" in content

    def test_uses_fallback_deps_when_source_has_none(self, tmp_path: Path):
        """Uses fallback dev deps when source has no dev section."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        source_toml = source / "pyproject.toml"
        source_toml.write_text("""
[project]
name = "source-project"
""")

        result = merge_pyproject_toml(source, target)

        assert result is True
        content = (target / "pyproject.toml").read_text()
        assert "pytest" in content
        assert "ruff" in content

    def test_preserves_existing_dev_deps(self, tmp_path: Path):
        """Preserves existing dev dependencies in target."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        (source / "pyproject.toml").write_text("""
[project]
name = "source"

[dependency-groups]
dev = ["pytest>=8.0.0"]
""")
        (target / "pyproject.toml").write_text("""
[project]
name = "target"

[dependency-groups]
dev = ["custom-dep>=1.0.0"]
""")

        result = merge_pyproject_toml(source, target)

        assert result is True
        content = (target / "pyproject.toml").read_text()
        # Target's existing deps should be preserved
        assert "custom-dep>=1.0.0" in content

    def test_adds_dev_section_when_missing(self, tmp_path: Path):
        """Adds dev section when target has pyproject but no dev deps."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        (source / "pyproject.toml").write_text("""
[project]
name = "source"

[dependency-groups]
dev = ["pytest>=8.0.0"]
""")
        (target / "pyproject.toml").write_text("""
[project]
name = "target"
version = "1.0.0"
""")

        result = merge_pyproject_toml(source, target)

        assert result is True
        content = (target / "pyproject.toml").read_text()
        assert "[dependency-groups]" in content
        assert "pytest>=8.0.0" in content
        # Original content preserved
        assert 'name = "target"' in content
        assert 'version = "1.0.0"' in content

    def test_handles_invalid_source_toml(self, tmp_path: Path):
        """Returns False when source TOML is invalid."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        (source / "pyproject.toml").write_text("invalid [ toml =")

        result = merge_pyproject_toml(source, target)

        assert result is False

    def test_handles_invalid_target_toml(self, tmp_path: Path):
        """Preserves invalid target TOML as-is with warning."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        (source / "pyproject.toml").write_text("""
[project]
name = "source"

[dependency-groups]
dev = ["pytest>=8.0.0"]
""")
        original_content = "invalid [ toml ="
        (target / "pyproject.toml").write_text(original_content)

        result = merge_pyproject_toml(source, target)

        # Should return True (preserved as-is)
        assert result is True
        # Content should be unchanged
        assert (target / "pyproject.toml").read_text() == original_content
