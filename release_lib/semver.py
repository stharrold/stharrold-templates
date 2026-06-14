#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Deterministic semantic-version math for the release pilot.

Canonical home (moved from .claude/skills/git-workflow-manager/scripts/
semantic_version.py in issue #240). The release-pilot skill's promotion
step calls next_version_from_tag() so the version is computed, never
guessed.

Bump type is inferred from changed file paths (file-pattern heuristic),
not from commit messages or code analysis.
"""

import re
import subprocess
import sys
from pathlib import Path


def get_changed_files(base_branch):
    """Get list of changed files compared to base.

    Uses three-dot diff (base_branch...HEAD) to compare the current branch
    against the merge-base with base_branch. This ensures we detect all changes
    that will be included in a PR/merge, not just uncommitted working directory changes.
    """
    try:
        result = subprocess.check_output(["git", "diff", "--name-only", f"{base_branch}...HEAD"], text=True)
        return [f for f in result.strip().split("\n") if f]
    except subprocess.CalledProcessError:
        return []


def analyze_changes(changed_files):
    """
    Determine version bump type based on changed files.

    Returns:
        'major' | 'minor' | 'patch'

    Rules:
    - MAJOR: Breaking changes (API changes, removed features)
    - MINOR: New features (new files in src/, new endpoints)
    - PATCH: Bug fixes, refactoring, docs, tests
    """
    has_breaking = False
    has_feature = False
    has_fix = False

    for file in changed_files:
        # API changes are potentially breaking
        if file.startswith("src/api/") or file.startswith("src/*/api/"):
            # Check if file existed before (new = feature, modified = potentially breaking)
            if Path(file).exists():
                has_breaking = True

        # New Python files in src/ are features
        elif file.startswith("src/") and file.endswith(".py"):
            if Path(file).exists():
                has_feature = True

        # Tests, docs, config are patches
        elif any(file.startswith(prefix) for prefix in ["tests/", "docs/", "resources/"]):
            has_fix = True

        # Configuration changes
        elif file in ["pyproject.toml", "requirements.txt", "uv.lock"]:
            has_fix = True

    # Determine bump type (priority: major > minor > patch)
    if has_breaking:
        return "major"
    elif has_feature:
        return "minor"
    elif has_fix:
        return "patch"
    else:
        return "patch"  # Default to patch if unsure


def bump_version(current_version, bump_type):
    """Increment version based on bump type."""
    # Parse version (handle vX.Y.Z or X.Y.Z format)
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", current_version)
    if not match:
        print(f"Warning: Invalid version format '{current_version}', defaulting to v1.0.0")
        return "v1.0.0"

    major, minor, patch = map(int, match.groups())

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"v{major}.{minor}.{patch}"


def get_last_tag(ref=None):
    """Return the most recent annotated tag (e.g. 'v9.0.0'), or None.

    Mirrors the `git describe --tags --abbrev=0` lookup that
    create_release.py and backmerge_workflow.py do inline. Pass ref
    (e.g. 'origin/main') to scope the lookup to a branch's history;
    omit it to use the current HEAD's reachable tags.
    """
    cmd = ["git", "describe", "--tags", "--abbrev=0"]
    if ref:
        cmd.append(ref)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def calculate_semantic_version(base_branch, current_version):
    """Calculate next semantic version based on changes."""
    changed_files = get_changed_files(base_branch)

    if not changed_files:
        print("No changed files detected")
        return current_version

    bump_type = analyze_changes(changed_files)
    new_version = bump_version(current_version, bump_type)

    print(f"Changed files: {len(changed_files)}", file=sys.stderr)
    print(f"Bump type: {bump_type}", file=sys.stderr)
    print(f"Current version: {current_version}", file=sys.stderr)
    print(f"New version: {new_version}", file=sys.stderr)

    return new_version


def next_version_from_tag(base_branch="develop", ref=None):
    """Compute the next version end to end: last tag -> bumped version.

    This is the deterministic helper the release-pilot skill calls at the
    promotion gate. Falls back to v0.0.0 as the seed when no tag exists
    (so a first release becomes v0.0.1 / v0.1.0 / v1.0.0 per the change
    analysis).
    """
    current = get_last_tag(ref) or "v0.0.0"
    return calculate_semantic_version(base_branch, current)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: semver.py <base_branch> <current_version>")
        print("Example: semver.py develop v1.0.0")
        sys.exit(1)

    print(calculate_semantic_version(sys.argv[1], sys.argv[2]))
