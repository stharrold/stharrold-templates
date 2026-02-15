#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for AgentDB symlink functionality in create_worktree.py."""

import os
import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent / ".claude/skills/git-workflow-manager/scripts"),
)

from create_worktree import setup_agentdb_symlink


class TestSetupAgentdbSymlink:
    """Tests for setup_agentdb_symlink function."""

    def test_creates_symlink_to_main_repo_db(self, tmp_path):
        """Should create symlink from worktree to main repo database."""
        # Setup
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        # Create state directories
        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        # Create main repo database
        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        # Call function
        result = setup_agentdb_symlink(worktree, main_repo)

        # Verify
        assert result is True
        worktree_db = worktree_state / "agentdb.duckdb"
        assert worktree_db.is_symlink()
        assert worktree_db.resolve() == main_db

    def test_creates_main_state_dir_if_missing(self, tmp_path):
        """Should create main repo .claude-state directory if it doesn't exist."""
        # Setup
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        # Call function
        result = setup_agentdb_symlink(worktree, main_repo)

        # Verify
        assert result is True
        main_state = main_repo / ".claude-state"
        assert main_state.exists()
        main_db = main_state / "agentdb.duckdb"
        assert main_db.exists()

    def test_creates_main_db_file_if_missing(self, tmp_path):
        """Should touch main repo database file if it doesn't exist."""
        # Setup
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        main_state = main_repo / ".claude-state"
        main_state.mkdir()

        worktree = tmp_path / "worktree"
        worktree.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        # Main DB doesn't exist yet
        main_db = main_state / "agentdb.duckdb"
        assert not main_db.exists()

        # Call function
        result = setup_agentdb_symlink(worktree, main_repo)

        # Verify main DB was created
        assert result is True
        assert main_db.exists()

    def test_idempotent_when_symlink_exists(self, tmp_path):
        """Should return True without changes if symlink already exists."""
        # Setup
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        worktree = tmp_path / "worktree"
        worktree.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        # Create symlink manually
        worktree_db = worktree_state / "agentdb.duckdb"
        relative_target = os.path.relpath(main_db, worktree_state)
        worktree_db.symlink_to(relative_target)

        # Call function again
        result = setup_agentdb_symlink(worktree, main_repo)

        # Verify no error
        assert result is True
        assert worktree_db.is_symlink()

    def test_idempotent_when_file_exists(self, tmp_path):
        """Should return True if regular file already exists (not overwrite)."""
        # Setup
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        worktree = tmp_path / "worktree"
        worktree.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        # Create regular file (not symlink)
        worktree_db = worktree_state / "agentdb.duckdb"
        worktree_db.write_text("existing database")

        # Call function
        result = setup_agentdb_symlink(worktree, main_repo)

        # Should return True (idempotent) and not overwrite
        assert result is True
        assert not worktree_db.is_symlink()
        assert worktree_db.read_text() == "existing database"

    def test_creates_relative_symlink(self, tmp_path):
        """Should create relative symlink for portability."""
        # Setup
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        worktree = tmp_path / "worktree"
        worktree.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        # Call function
        result = setup_agentdb_symlink(worktree, main_repo)

        # Verify symlink is relative
        assert result is True
        worktree_db = worktree_state / "agentdb.duckdb"
        symlink_target = os.readlink(worktree_db)
        assert not Path(symlink_target).is_absolute()
        # Should be something like "../../main_repo/.claude-state/agentdb.duckdb"
        assert ".." in symlink_target

    @pytest.mark.skipif(os.geteuid() == 0, reason="Root bypasses permission checks")
    def test_returns_false_on_permission_error(self, tmp_path):
        """Should return False and print warning on permission error."""
        # Setup - create read-only worktree state dir
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        worktree = tmp_path / "worktree"
        worktree.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        # Make worktree state read-only
        worktree_state.chmod(0o444)

        try:
            # Call function
            result = setup_agentdb_symlink(worktree, main_repo)

            # Should return False (permission denied)
            assert result is False
        finally:
            # Restore permissions for cleanup
            worktree_state.chmod(0o755)


class TestSymlinkIntegration:
    """Integration tests for symlink behavior with file operations."""

    def test_symlink_allows_shared_write(self, tmp_path):
        """Writing through symlink should update main repo database."""
        # Setup
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        # Create symlink
        setup_agentdb_symlink(worktree, main_repo)

        # Write through symlink
        worktree_db = worktree_state / "agentdb.duckdb"
        worktree_db.write_text("test data")

        # Verify main repo file has the data
        assert main_db.read_text() == "test data"

    def test_symlink_resolve_returns_main_path(self, tmp_path):
        """Resolving symlink should return main repo database path."""
        # Setup
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        # Create symlink
        setup_agentdb_symlink(worktree, main_repo)

        # Resolve should return main repo path
        worktree_db = worktree_state / "agentdb.duckdb"
        resolved = worktree_db.resolve()

        assert resolved == main_db


class TestWindowsHardLinkFallback:
    """Tests for Windows hard link fallback behavior."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only test")
    def test_uses_hardlink_when_symlink_fails_on_windows(self, tmp_path, monkeypatch):
        """On Windows, should fall back to hard link when symlink fails."""
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        main_db = main_state / "agentdb.duckdb"
        main_db.write_text("test database content")

        # Track calls
        symlink_called = False
        hardlink_called = False

        def mock_symlink_to(self, target):
            nonlocal symlink_called
            symlink_called = True
            raise OSError("Symlink requires admin privileges")

        original_link = os.link

        def mock_link(src, dst):
            nonlocal hardlink_called
            hardlink_called = True
            return original_link(src, dst)

        monkeypatch.setattr(Path, "symlink_to", mock_symlink_to)
        monkeypatch.setattr("os.link", mock_link)

        result = setup_agentdb_symlink(worktree, main_repo)

        assert result is True
        assert symlink_called is True
        assert hardlink_called is True
        worktree_db = worktree_state / "agentdb.duckdb"
        assert worktree_db.exists()
        assert worktree_db.read_text() == "test database content"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only test")
    def test_returns_false_when_both_link_types_fail_on_windows(self, tmp_path, monkeypatch):
        """On Windows, should return False if symlink and hard link both fail."""
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        def mock_symlink_to(self, target):
            raise OSError("No symlink")

        def mock_link(src, dst):
            raise OSError("No hard link")

        monkeypatch.setattr(Path, "symlink_to", mock_symlink_to)
        monkeypatch.setattr("os.link", mock_link)

        result = setup_agentdb_symlink(worktree, main_repo)

        assert result is False
        worktree_db = worktree_state / "agentdb.duckdb"
        assert not worktree_db.exists()


class TestCrossPlatformLinkBehavior:
    """Tests for cross-platform link behavior."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
    def test_symlink_used_on_unix(self, tmp_path, monkeypatch):
        """On Unix, should use symlink (not hard link)."""
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        # Track if hard link is called (it shouldn't be on Unix)
        hardlink_called = False
        original_link = os.link

        def mock_link(*args, **kwargs):
            nonlocal hardlink_called
            hardlink_called = True
            return original_link(*args, **kwargs)

        monkeypatch.setattr("os.link", mock_link)

        result = setup_agentdb_symlink(worktree, main_repo)

        assert result is True
        assert hardlink_called is False  # Hard link should not be called on Unix
        worktree_db = worktree_state / "agentdb.duckdb"
        assert worktree_db.is_symlink()

    def test_hardlink_writes_update_main_db(self, tmp_path):
        """Writes through hard link should update the main database."""
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        main_db = main_state / "agentdb.duckdb"
        main_db.write_text("initial content")

        # Create hard link directly (simulating Windows fallback)
        worktree_db = worktree_state / "agentdb.duckdb"
        os.link(main_db, worktree_db)

        # Write through worktree path
        worktree_db.write_text("updated content")

        # Verify main DB was updated
        assert main_db.read_text() == "updated content"


class TestPathResolution:
    """Tests for Path.resolve() usage with different link types."""

    def test_resolve_follows_symlink(self, tmp_path):
        """Path.resolve() should follow symlink to main database."""
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        # Create symlink
        worktree_db = worktree_state / "agentdb.duckdb"
        relative_target = os.path.relpath(main_db, worktree_state)
        worktree_db.symlink_to(relative_target)

        # Verify resolve() returns main DB path
        resolved = worktree_db.resolve()
        assert resolved == main_db.resolve()

    def test_resolve_works_with_hardlink(self, tmp_path):
        """Path.resolve() should work with hard link (returns own canonical path)."""
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        main_state = main_repo / ".claude-state"
        main_state.mkdir()
        worktree_state = worktree / ".claude-state"
        worktree_state.mkdir()

        main_db = main_state / "agentdb.duckdb"
        main_db.touch()

        # Create hard link
        worktree_db = worktree_state / "agentdb.duckdb"
        os.link(main_db, worktree_db)

        # Hard links share same inode - resolve() returns the canonical path of the file
        # (which is the path we asked for, since hard links are just additional names)
        resolved = worktree_db.resolve()
        assert resolved == worktree_db.resolve()  # Should be consistent
        assert resolved.exists()

        # Verify both point to same data
        main_db.write_text("shared content")
        assert worktree_db.read_text() == "shared content"
