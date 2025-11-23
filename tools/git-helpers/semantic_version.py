#!/usr/bin/env python3
"""Calculate semantic version based on component changes."""

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
        result = subprocess.check_output(
            ['git', 'diff', '--name-only', f'{base_branch}...HEAD'],
            text=True
        )
        return [f for f in result.strip().split('\n') if f]
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
        # Core tools changes - conservative approach
        if file.startswith('mcp_manager.py') or file.startswith('tools/'):
            # Assume breaking if removing files or changing core APIs
            # For templates repo, most changes are additive (features) or fixes
            if Path(file).exists():
                # File still exists = likely feature or fix, not breaking
                # Conservative: treat as feature unless it's a test
                if not file.startswith('test_'):
                    has_feature = True
                else:
                    has_fix = True
            else:
                # File removed = potentially breaking
                has_breaking = True

        # Documentation changes are patches
        elif any(file.startswith(prefix) for prefix in ['10_draft-merged/', '00_draft-initial/', 'docs/', 'CLAUDE.md', 'README.md', 'CONTRIBUTING.md']):
            has_fix = True

        # Test files are patches
        elif file.startswith('test_') or file.startswith('tests/'):
            has_fix = True

        # Configuration changes
        elif file in ['pyproject.toml', 'requirements.txt', 'uv.lock', '.gitignore', '.python-version']:
            has_fix = True

        # CI/CD changes
        elif file.startswith('.github/') or file == 'azure-pipelines.yml':
            has_fix = True

        # New files in root (like new tools) are features
        elif file.endswith('.py') or file.endswith('.sh'):
            has_feature = True

    # Determine bump type (priority: major > minor > patch)
    if has_breaking:
        return 'major'
    elif has_feature:
        return 'minor'
    elif has_fix:
        return 'patch'
    else:
        return 'patch'  # Default to patch if unsure

def bump_version(current_version, bump_type):
    """Increment version based on bump type."""
    # Parse version (handle vX.Y.Z or X.Y.Z format)
    match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', current_version)
    if not match:
        print(f"Warning: Invalid version format '{current_version}', defaulting to v1.0.0")
        return 'v1.0.0'

    major, minor, patch = map(int, match.groups())

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f'v{major}.{minor}.{patch}'

def calculate_semantic_version(base_branch, current_version):
    """Calculate next semantic version based on changes."""
    changed_files = get_changed_files(base_branch)

    if not changed_files:
        print('No changed files detected')
        return current_version

    bump_type = analyze_changes(changed_files)
    new_version = bump_version(current_version, bump_type)

    print(f'Changed files: {len(changed_files)}', file=sys.stderr)
    print(f'Bump type: {bump_type}', file=sys.stderr)
    print(f'Current version: {current_version}', file=sys.stderr)
    print(f'New version: {new_version}', file=sys.stderr)

    return new_version

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: semantic_version.py <base_branch> <current_version>')
        print('Example: semantic_version.py develop v1.0.0')
        sys.exit(1)

    new_version = calculate_semantic_version(sys.argv[1], sys.argv[2])
    print(new_version)
