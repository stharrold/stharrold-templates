#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Apply workflow system from a cloned template repository to an existing repository.

This script is designed for the "clone and apply" use case:
1. User navigates to their existing repository
2. User clones stharrold-templates to .tmp/stharrold-templates
3. User tells Claude Code to apply the workflow

Usage:
    python apply_workflow.py <source-repo> <target-repo> [--force]

Arguments:
    source-repo: Path to cloned stharrold-templates (e.g., .tmp/stharrold-templates)
    target-repo: Path to existing repository (e.g., . or /path/to/my-repo)
    --force: Overwrite .claude/ directory without prompting

Example:
    cd my-repo
    mkdir -p .tmp
    git clone https://github.com/stharrold/stharrold-templates.git .tmp/stharrold-templates
    python .tmp/stharrold-templates/.claude/skills/initialize-repository/scripts/apply_workflow.py \\
      .tmp/stharrold-templates .

What it does:
1. Validates source has .claude/skills/ and .claude/commands/
2. Validates target is a git repository
3. Prompts before overwriting existing .claude/ (unless --force)
4. Copies .claude/skills/ (all skills)
5. Copies .claude/commands/ (v6 workflow commands)
6. Copies WORKFLOW.md, CONTRIBUTING.md
7. Merges pyproject.toml (adds dev dependencies, preserves existing)
8. Merges .gitignore (appends workflow patterns, deduplicates)
9. Prints summary with next steps

Exit codes:
    0: Success
    1: Source validation failed
    2: Target validation failed
    3: User cancelled (declined overwrite prompt)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Add workflow-utilities to path for safe_output
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "workflow-utilities" / "scripts"))
from safe_output import (
    SYMBOLS,
    print_error,
    print_info,
    print_success,
    print_warning,
)


def get_repo_root(path: Path) -> Path:
    """Get the repository root directory as an absolute path.

    Args:
        path: Any path within the repository

    Returns:
        Absolute path to repository root

    Raises:
        subprocess.CalledProcessError: If not a git repository
    """
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip()).resolve()


def validate_source(source_path: Path) -> tuple[bool, str]:
    """Validate source repository has workflow system.

    Args:
        source_path: Path to source repository

    Returns:
        Tuple of (is_valid, message)
    """
    if not source_path.exists():
        return False, f"Source path does not exist: {source_path}"

    if not source_path.is_dir():
        return False, f"Source path is not a directory: {source_path}"

    skills_dir = source_path / ".claude" / "skills"
    if not skills_dir.exists():
        return False, "Source missing .claude/skills/ directory"

    commands_dir = source_path / ".claude" / "commands"
    if not commands_dir.exists():
        return False, "Source missing .claude/commands/ directory"

    # Count skills
    skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]
    if len(skills) < 3:
        return False, f"Source has incomplete workflow system ({len(skills)} skills)"

    return True, f"Source validated ({len(skills)} skills found)"


def validate_target(target_path: Path) -> tuple[bool, str]:
    """Validate target is a git repository.

    Args:
        target_path: Path to target repository

    Returns:
        Tuple of (is_valid, message)
    """
    if not target_path.exists():
        return False, f"Target path does not exist: {target_path}"

    if not target_path.is_dir():
        return False, f"Target path is not a directory: {target_path}"

    # Check if it's a git repository
    git_dir = target_path / ".git"
    if not git_dir.exists():
        return False, "Target is not a git repository (no .git directory)"

    return True, "Target validated (git repository)"


def prompt_overwrite(target_path: Path) -> bool:
    """Prompt user before overwriting .claude/ directory.

    Args:
        target_path: Path to target repository

    Returns:
        True if user confirms, False otherwise
    """
    claude_dir = target_path / ".claude"
    if not claude_dir.exists():
        return True  # Nothing to overwrite

    print_warning("Target repository already has .claude/ directory")
    print_warning("Existing .claude/ will be replaced")

    response = input("\nProceed with workflow application? (y/N) ").strip().lower()
    return response in ["y", "yes"]


def copy_skills(source_path: Path, target_path: Path, force: bool) -> int:
    """Copy .claude/skills/ directory.

    Args:
        source_path: Path to source repository
        target_path: Path to target repository
        force: If True, delete existing before copying

    Returns:
        Number of skills copied
    """
    print_info("Copying .claude/skills/ directory...")

    source_skills = source_path / ".claude" / "skills"
    target_skills = target_path / ".claude" / "skills"

    if force and target_skills.exists():
        shutil.rmtree(target_skills)

    target_skills.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_skills, target_skills, dirs_exist_ok=True)

    # Count and report skills
    skills = [d.name for d in target_skills.iterdir() if d.is_dir()]
    for skill in sorted(skills):
        print_success(f"Copied skill: {skill}")

    print_success(f"Copied {len(skills)} skills")
    return len(skills)


def copy_commands(source_path: Path, target_path: Path, force: bool) -> int:
    """Copy .claude/commands/ directory.

    Args:
        source_path: Path to source repository
        target_path: Path to target repository
        force: If True, delete existing before copying

    Returns:
        Number of commands copied
    """
    print_info("Copying .claude/commands/ directory...")

    source_commands = source_path / ".claude" / "commands"
    target_commands = target_path / ".claude" / "commands"

    if not source_commands.exists():
        print_warning("Source has no .claude/commands/ directory")
        return 0

    if force and target_commands.exists():
        shutil.rmtree(target_commands)

    target_commands.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_commands, target_commands, dirs_exist_ok=True)

    # Count command files (*.md in workflow/)
    workflow_dir = target_commands / "workflow"
    if not workflow_dir.exists():
        print_warning("Workflow directory not found after copying commands")
        return 0

    commands = list(workflow_dir.glob("v6_*.md"))
    if not commands:
        print_warning("No v6_* workflow commands found in commands/workflow/")
        return 0

    for cmd in sorted(commands):
        print_success(f"Copied command: {cmd.stem}")
    print_success(f"Copied {len(commands)} workflow commands")
    return len(commands)


def copy_documentation(source_path: Path, target_path: Path) -> list[str]:
    """Copy workflow documentation files.

    Args:
        source_path: Path to source repository
        target_path: Path to target repository

    Returns:
        List of copied file names
    """
    print_info("Copying workflow documentation...")

    docs = ["WORKFLOW.md", "CONTRIBUTING.md"]
    copied = []

    for doc in docs:
        source_file = source_path / doc
        if source_file.exists():
            target_file = target_path / doc
            shutil.copy2(source_file, target_file)
            print_success(f"Copied {doc}")
            copied.append(doc)

    return copied


def merge_pyproject_toml(source_path: Path, target_path: Path) -> bool:
    """Merge dev dependencies into target pyproject.toml.

    Args:
        source_path: Path to source repository
        target_path: Path to target repository

    Returns:
        True if merged, False if skipped
    """
    print_info("Merging pyproject.toml...")

    source_file = source_path / "pyproject.toml"
    target_file = target_path / "pyproject.toml"

    if not source_file.exists():
        print_warning("Source has no pyproject.toml")
        return False

    # Read source to extract dev dependencies
    source_content = source_file.read_text()

    # Extract dev dependencies from source (simple parsing)
    dev_deps = []
    in_dev_section = False
    for line in source_content.split("\n"):
        if "[dependency-groups]" in line or "[project.optional-dependencies]" in line:
            in_dev_section = True
            continue
        if in_dev_section and line.startswith("["):
            in_dev_section = False
        if in_dev_section and line.strip().startswith('"'):
            dep = line.strip().strip('",')
            if dep:
                dev_deps.append(dep)

    if not dev_deps:
        # Fallback: use standard dev deps
        dev_deps = [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "ruff>=0.1.0",
            "pre-commit>=3.6.0",
        ]

    if not target_file.exists():
        # Create minimal pyproject.toml
        target_name = target_path.name
        content = f'''[project]
name = "{target_name}"
version = "0.1.0"
description = ""
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "pre-commit>=3.6.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 170
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "UP"]
'''
        target_file.write_text(content)
        print_success("Created pyproject.toml with dev dependencies")
        return True

    # Read existing target
    target_content = target_file.read_text()

    # Check if dev section exists
    if "[dependency-groups]" not in target_content and "[project.optional-dependencies]" not in target_content:
        # Append dev section
        dev_section = """
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "pre-commit>=3.6.0",
]
"""
        target_file.write_text(target_content + dev_section)
        print_success("Added dev dependencies to pyproject.toml")
        return True

    print_success("pyproject.toml already has dev dependencies (preserved)")
    return True


def merge_gitignore(source_path: Path, target_path: Path) -> bool:
    """Append workflow patterns to .gitignore, deduplicate.

    Args:
        source_path: Path to source repository
        target_path: Path to target repository

    Returns:
        True if merged, False if skipped
    """
    print_info("Merging .gitignore...")

    source_file = source_path / ".gitignore"
    target_file = target_path / ".gitignore"

    # Workflow-specific patterns to add
    workflow_patterns = [
        "",
        "# Workflow system",
        ".claude-state/",
        ".tmp/",
        "*.duckdb",
        "*.duckdb.wal",
    ]

    if not target_file.exists():
        # Create .gitignore with workflow patterns
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            print_success("Copied .gitignore from source")
        else:
            target_file.write_text("\n".join(workflow_patterns) + "\n")
            print_success("Created .gitignore with workflow patterns")
        return True

    # Read existing
    existing_lines = target_file.read_text().split("\n")

    # Add workflow patterns if not present
    added = []
    for pattern in workflow_patterns:
        if pattern and pattern not in existing_lines:
            existing_lines.append(pattern)
            if pattern and not pattern.startswith("#"):
                added.append(pattern)

    # Deduplicate while preserving order
    seen = set()
    unique_lines = []
    for line in existing_lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    # Write back
    target_file.write_text("\n".join(unique_lines))

    if added:
        print_success(f"Added {len(added)} workflow patterns to .gitignore")
    else:
        print_success(".gitignore already has workflow patterns (preserved)")

    return True


def print_summary(
    target_path: Path,
    skills_count: int,
    commands_count: int,
    docs_copied: list[str],
) -> None:
    """Print summary of what was applied.

    Args:
        target_path: Path to target repository
        skills_count: Number of skills copied
        commands_count: Number of commands copied
        docs_copied: List of documentation files copied
    """
    print("\n" + "=" * 50)
    print_success("Workflow Application Complete")
    print("=" * 50 + "\n")

    print(f"Target: {target_path.resolve()}\n")

    ok = SYMBOLS["checkmark"]
    print("Applied:")
    print(f"  {ok} {skills_count} workflow skills (.claude/skills/)")
    print(f"  {ok} {commands_count} workflow commands (.claude/commands/)")
    for doc in docs_copied:
        print(f"  {ok} {doc}")
    print(f"  {ok} pyproject.toml (merged dev dependencies)")
    print(f"  {ok} .gitignore (merged workflow patterns)")

    print("\nNext Steps:")
    print("  1. Review changes: git status")
    print("  2. Install dependencies: uv sync")
    print("  3. Run tests: uv run pytest")
    print('  4. Start v6 workflow: /workflow:v6_1_worktree "feature description"')
    print("  5. Optional cleanup: rm -rf .tmp/")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0=success, 1=source error, 2=target error, 3=cancelled)
    """
    parser = argparse.ArgumentParser(
        description="Apply workflow system from cloned template to existing repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  cd my-repo
  mkdir -p .tmp
  git clone https://github.com/stharrold/stharrold-templates.git .tmp/stharrold-templates
  python .tmp/stharrold-templates/.claude/skills/initialize-repository/scripts/apply_workflow.py \\
    .tmp/stharrold-templates .
""",
    )

    parser.add_argument(
        "source_repo",
        type=Path,
        help="Path to cloned stharrold-templates",
    )
    parser.add_argument(
        "target_repo",
        type=Path,
        help="Path to existing repository",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite .claude/ directory without prompting",
    )

    args = parser.parse_args()

    # Resolve paths
    source_path = args.source_repo.resolve()
    target_path = args.target_repo.resolve()

    print("\n" + "=" * 50)
    print("Apply Workflow System")
    print("=" * 50 + "\n")

    # Validate source
    print_info(f"Validating source: {source_path}")
    valid, message = validate_source(source_path)
    if not valid:
        print_error(message)
        return 1
    print_success(message)

    # Validate target
    print_info(f"Validating target: {target_path}")
    valid, message = validate_target(target_path)
    if not valid:
        print_error(message)
        return 2
    print_success(message)

    # Prompt for overwrite (unless --force)
    if not args.force:
        if not prompt_overwrite(target_path):
            print_warning("Cancelled by user")
            return 3

    print()  # Blank line before operations

    # Copy operations
    skills_count = copy_skills(source_path, target_path, args.force)
    commands_count = copy_commands(source_path, target_path, args.force)
    docs_copied = copy_documentation(source_path, target_path)

    # Merge operations (always merge, never overwrite)
    merge_pyproject_toml(source_path, target_path)
    merge_gitignore(source_path, target_path)

    # Summary
    print_summary(target_path, skills_count, commands_count, docs_copied)

    return 0


if __name__ == "__main__":
    sys.exit(main())
