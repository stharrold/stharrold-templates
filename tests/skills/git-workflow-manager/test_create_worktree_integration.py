#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Integration tests for git-workflow-manager create_worktree.py.

These tests verify the full workflow of worktree creation using real git repositories.
Note: v6 workflow removed planning verification (Gemini handles planning).
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / ".claude/skills/git-workflow-manager/scripts"),
)


@pytest.fixture
def git_repo_with_remote(tmp_path):
    """Create a temporary git repository with a mock remote.

    Sets up:
    - A "remote" bare repository
    - A "local" repository cloned from the remote
    - A contrib/testuser branch
    """
    # Create bare "remote" repository
    remote_path = tmp_path / "remote.git"
    remote_path.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=remote_path, check=True, capture_output=True)

    # Create local repository
    local_path = tmp_path / "local"
    subprocess.run(
        ["git", "clone", str(remote_path), str(local_path)],
        check=True,
        capture_output=True,
    )

    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit on main
    (local_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=local_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    # Rename branch to 'main' (may be 'master' depending on git config)
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    # Create contrib/testuser branch
    subprocess.run(
        ["git", "checkout", "-b", "contrib/testuser"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "contrib/testuser"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    return local_path


class TestCreateWorktreeIntegration:
    """Integration tests for worktree creation (v6 workflow)."""

    def test_feature_worktree_creation(self, git_repo_with_remote):
        """Should create feature worktree without planning verification (v6 workflow)."""
        from create_worktree import create_worktree

        local_path = git_repo_with_remote

        # Change to repo directory for create_worktree
        original_cwd = os.getcwd()
        try:
            os.chdir(local_path)

            # v6: This should succeed without planning docs
            result = create_worktree("feature", "test-feature", "contrib/testuser")

            assert "worktree_path" in result
            assert "branch_name" in result
            assert "test-feature" in result["branch_name"]
            assert Path(result["worktree_path"]).exists()

            # Cleanup: remove worktree
            subprocess.run(
                ["git", "worktree", "remove", result["worktree_path"], "--force"],
                cwd=local_path,
                check=False,
                capture_output=True,
            )
        finally:
            os.chdir(original_cwd)

    def test_feature_worktree_no_planning_required(self, git_repo_with_remote):
        """v6 workflow: feature worktree creation does NOT require planning docs."""
        from create_worktree import create_worktree

        local_path = git_repo_with_remote

        # No planning directory - should still work (v6 uses Gemini tools for planning).
        original_cwd = os.getcwd()
        try:
            os.chdir(local_path)

            # This should succeed (v6 workflow removed planning verification)
            result = create_worktree("feature", "no-planning-feature", "contrib/testuser")

            assert "worktree_path" in result
            assert "no-planning-feature" in result["branch_name"]
            assert Path(result["worktree_path"]).exists()

            # Cleanup: remove worktree
            subprocess.run(
                ["git", "worktree", "remove", result["worktree_path"], "--force"],
                cwd=local_path,
                check=False,
                capture_output=True,
            )
        finally:
            os.chdir(original_cwd)

    def test_release_worktree_creation(self, git_repo_with_remote):
        """Should allow release worktree creation."""
        from create_worktree import create_worktree

        local_path = git_repo_with_remote

        original_cwd = os.getcwd()
        try:
            os.chdir(local_path)

            # Release worktrees should work
            result = create_worktree("release", "v1-0-0", "contrib/testuser")

            assert "worktree_path" in result
            assert "release" in result["branch_name"]

            # Cleanup: remove worktree
            subprocess.run(
                ["git", "worktree", "remove", result["worktree_path"], "--force"],
                cwd=local_path,
                check=False,
                capture_output=True,
            )
        finally:
            os.chdir(original_cwd)

    def test_worktree_creates_state_directory(self, git_repo_with_remote):
        """Should create .claude-state directory in worktree."""
        from create_worktree import create_worktree

        local_path = git_repo_with_remote

        original_cwd = os.getcwd()
        try:
            os.chdir(local_path)

            result = create_worktree("feature", "state-test", "contrib/testuser")

            worktree_path = Path(result["worktree_path"])
            state_dir = worktree_path / ".claude-state"
            assert state_dir.exists()
            assert (state_dir / ".gitignore").exists()
            assert (state_dir / ".worktree-id").exists()

            # Cleanup: remove worktree
            subprocess.run(
                ["git", "worktree", "remove", result["worktree_path"], "--force"],
                cwd=local_path,
                check=False,
                capture_output=True,
            )
        finally:
            os.chdir(original_cwd)
