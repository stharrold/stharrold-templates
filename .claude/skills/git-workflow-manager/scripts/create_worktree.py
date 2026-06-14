#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Create feature/release/hotfix worktree for isolated development.

Constants:
- TIMESTAMP_FORMAT: YYYYMMDDTHHMMSSZ (compact ISO8601)
  Rationale: Compact format that remains intact when branch names are parsed
  by underscores and hyphens. No colons/hyphens avoid shell escaping issues.

Note: TODO file generation is removed. Use GitHub Issues for task tracking.
"""

import argparse
import hashlib
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Constants with documented rationale
TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"  # Compact ISO8601 for filename/branch safety
VALID_WORKFLOW_TYPES = ["feature", "release", "hotfix"]  # Supported workflow types


def create_worktree(workflow_type, slug, base_branch):
    """
    Create a worktree for feature/release/hotfix development.

    Args:
        workflow_type: 'feature' | 'release' | 'hotfix'
        slug: Short descriptive name (e.g., 'json-validator')
        base_branch: Branch to create from (e.g., 'contrib/username')

    Returns:
        dict with worktree_path, branch_name, state_dir

    Raises:
        ValueError: If inputs are invalid
        subprocess.CalledProcessError: If git/gh commands fail
        FileNotFoundError: If required tools are missing
    """
    # Input validation
    if workflow_type not in VALID_WORKFLOW_TYPES:
        raise ValueError(f"Invalid workflow_type '{workflow_type}'. Must be one of: {', '.join(VALID_WORKFLOW_TYPES)}")

    if not slug or not slug.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"Invalid slug '{slug}'. Must contain only letters, numbers, hyphens, and underscores.")

    # Use timezone-aware datetime (datetime.utcnow() is deprecated in Python 3.12+)
    timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
    branch_name = f"{workflow_type}/{timestamp}_{slug}"

    # Get repository root
    try:
        repo_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.PIPE).strip())
    except subprocess.CalledProcessError as e:
        print("ERROR: Not in a git repository", file=sys.stderr)
        print(f"Git error: {e.stderr.strip()}", file=sys.stderr)
        raise

    # Verify base branch exists
    try:
        subprocess.run(["git", "rev-parse", "--verify", base_branch], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        print(f"ERROR: Base branch '{base_branch}' does not exist", file=sys.stderr)
        print("Available branches:", file=sys.stderr)
        subprocess.run(["git", "branch", "-a"], stderr=subprocess.DEVNULL)
        raise

    worktree_path = repo_root.parent / f"{repo_root.name}_{workflow_type}_{timestamp}_{slug}"

    # Check if worktree path already exists
    if worktree_path.exists():
        raise FileExistsError(f"Worktree path already exists: {worktree_path}\nRemove it first with: git worktree remove {worktree_path}")

    # Create worktree
    try:
        subprocess.run(["git", "worktree", "add", str(worktree_path), "-b", branch_name, base_branch], check=True, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        print("ERROR: Failed to create worktree", file=sys.stderr)
        print(f"Command: git worktree add {worktree_path} -b {branch_name} {base_branch}", file=sys.stderr)
        print(f"Git error: {e.stderr.strip()}", file=sys.stderr)
        raise

    # Initialize .claude-state/ directory in new worktree
    state_dir = worktree_path / ".claude-state"
    try:
        state_dir.mkdir(exist_ok=True)
        # Create .gitignore in state dir
        (state_dir / ".gitignore").write_text("# Ignore all files in state directory\n*\n")
        # Create .worktree-id with hash of worktree path
        worktree_id = hashlib.sha256(str(worktree_path).encode()).hexdigest()[:12]
        (state_dir / ".worktree-id").write_text(worktree_id)
        print(f"[OK] State directory: {state_dir}")
    except (OSError, PermissionError) as e:
        print(f"[WARN]  Could not create state directory: {e}", file=sys.stderr)

    print(f"[OK] Worktree created: {worktree_path}")
    print(f"[OK] Branch: {branch_name}")

    return {"worktree_path": str(worktree_path), "branch_name": branch_name, "state_dir": str(state_dir) if state_dir.exists() else None}


def main():
    """Main entry point with argparse."""
    parser = argparse.ArgumentParser(
        description="Create feature/release/hotfix worktree",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create feature worktree
  python create_worktree.py feature my-feature contrib/stharrold

  # Create release worktree
  python create_worktree.py release v1.6.0 develop
""",
    )

    parser.add_argument("workflow_type", choices=VALID_WORKFLOW_TYPES, help="Workflow type")
    parser.add_argument("slug", help="Short descriptive name (e.g., my-feature, v1.6.0)")
    parser.add_argument("base_branch", help="Branch to create from (e.g., contrib/username, develop)")

    args = parser.parse_args()

    try:
        result = create_worktree(args.workflow_type, args.slug, args.base_branch)

        import json

        print(json.dumps(result))
    except (ValueError, FileExistsError) as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Error already printed in function
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
