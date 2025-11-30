#!/usr/bin/env python3
"""Integration tests for git-workflow-manager create_worktree.py.

These tests verify the full workflow of worktree creation with
planning document verification using real git repositories.
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
    """Integration tests for worktree creation with planning verification."""

    def test_full_workflow_with_committed_planning(self, git_repo_with_remote):
        """Should create worktree when planning docs committed and pushed."""
        from create_worktree import create_worktree

        local_path = git_repo_with_remote

        # Create and commit planning directory
        planning_dir = local_path / "planning" / "test-feature"
        planning_dir.mkdir(parents=True)
        (planning_dir / "requirements.md").write_text("# Requirements\n\nTest feature requirements.")
        (planning_dir / "architecture.md").write_text("# Architecture\n\nTest feature architecture.")
        (planning_dir / "epics.md").write_text("# Epics\n\nE-001: Core implementation")

        subprocess.run(["git", "add", "."], cwd=local_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "docs(planning): add planning for test-feature"],
            cwd=local_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push"],
            cwd=local_path,
            check=True,
            capture_output=True,
        )

        # Change to repo directory for create_worktree
        original_cwd = os.getcwd()
        try:
            os.chdir(local_path)

            # This should succeed
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

    def test_full_workflow_fails_uncommitted_planning(self, git_repo_with_remote):
        """Should fail worktree creation when planning docs not committed."""
        from create_worktree import create_worktree

        local_path = git_repo_with_remote

        # Create planning directory but DON'T commit
        planning_dir = local_path / "planning" / "uncommitted-feature"
        planning_dir.mkdir(parents=True)
        (planning_dir / "requirements.md").write_text("# Requirements\n\nUncommitted.")

        # Change to repo directory for create_worktree
        original_cwd = os.getcwd()
        try:
            os.chdir(local_path)

            # This should fail with clear error message
            with pytest.raises(ValueError) as exc_info:
                create_worktree("feature", "uncommitted-feature", "contrib/testuser")

            error_msg = str(exc_info.value)
            assert "Uncommitted changes detected" in error_msg
            assert "planning/uncommitted-feature/" in error_msg
        finally:
            os.chdir(original_cwd)

    def test_release_worktree_skips_planning_check(self, git_repo_with_remote):
        """Should allow release worktree creation without planning docs."""
        from create_worktree import create_worktree

        local_path = git_repo_with_remote

        # No planning directory - release should still work
        original_cwd = os.getcwd()
        try:
            os.chdir(local_path)

            # This should succeed (release doesn't need planning)
            # Note: slug validation doesn't allow dots, so use valid version slug
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
