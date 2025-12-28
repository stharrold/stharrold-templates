#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for archive_manager.py create_archive() function."""

import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the scripts directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / "workflow-utilities" / "scripts"))

from archive_manager import create_archive, ensure_archived_directory, get_repo_root


class TestGetRepoRoot:
    """Tests for get_repo_root()."""

    def test_returns_absolute_path(self):
        """get_repo_root() returns an absolute path."""
        root = get_repo_root()
        assert root.is_absolute()

    def test_returns_valid_directory(self):
        """get_repo_root() returns an existing directory."""
        root = get_repo_root()
        assert root.is_dir()


class TestEnsureArchivedDirectory:
    """Tests for ensure_archived_directory()."""

    def test_creates_directory_if_missing(self, tmp_path: Path):
        """Creates ARCHIVED directory if it doesn't exist."""
        archived_dir = tmp_path / "ARCHIVED"
        assert not archived_dir.exists()

        result = ensure_archived_directory(archived_dir)

        assert result == archived_dir
        assert archived_dir.exists()

    def test_creates_claude_md(self, tmp_path: Path):
        """Creates CLAUDE.md in ARCHIVED directory."""
        archived_dir = tmp_path / "ARCHIVED"
        ensure_archived_directory(archived_dir)

        claude_md = archived_dir / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "Claude Code Context" in content
        assert "deprecated" in content.lower()

    def test_creates_readme_md(self, tmp_path: Path):
        """Creates README.md in ARCHIVED directory."""
        archived_dir = tmp_path / "ARCHIVED"
        ensure_archived_directory(archived_dir)

        readme = archived_dir / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "Archived Files" in content

    def test_idempotent(self, tmp_path: Path):
        """Running twice doesn't modify existing files."""
        archived_dir = tmp_path / "ARCHIVED"
        ensure_archived_directory(archived_dir)

        # Modify files
        (archived_dir / "CLAUDE.md").write_text("Custom content")
        (archived_dir / "README.md").write_text("Custom readme")

        # Run again
        ensure_archived_directory(archived_dir)

        # Files should not be overwritten
        assert (archived_dir / "CLAUDE.md").read_text() == "Custom content"
        assert (archived_dir / "README.md").read_text() == "Custom readme"


class TestCreateArchive:
    """Tests for create_archive() function."""

    def test_creates_archive_with_single_file(self, tmp_path: Path):
        """Creates archive containing a single file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        archived_dir = tmp_path / "ARCHIVED"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="test-archive",
                files=[str(test_file)],
                archived_dir=archived_dir,
                timestamp="20251228T120000Z",
            )

        # Verify archive was created
        assert Path(result).exists()
        assert result.endswith(".zip")
        assert "test-archive" in result
        assert "20251228T120000Z" in result
        assert failed_files == []

        # Verify contents
        with zipfile.ZipFile(result, "r") as zipf:
            names = zipf.namelist()
            assert "test.txt" in names

    def test_creates_archive_with_multiple_files(self, tmp_path: Path):
        """Creates archive containing multiple files."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        archived_dir = tmp_path / "ARCHIVED"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="multi-file",
                files=[str(file1), str(file2)],
                archived_dir=archived_dir,
                timestamp="20251228T120000Z",
            )

        # Verify contents
        assert failed_files == []
        with zipfile.ZipFile(result, "r") as zipf:
            names = zipf.namelist()
            assert "file1.txt" in names
            assert "file2.txt" in names

    def test_preserves_paths_when_enabled(self, tmp_path: Path):
        """Preserves directory structure when preserve_paths=True."""
        # Create nested test file
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "nested.txt"
        test_file.write_text("nested content")

        archived_dir = tmp_path / "ARCHIVED"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="preserve-test",
                files=[str(test_file)],
                archived_dir=archived_dir,
                preserve_paths=True,
                timestamp="20251228T120000Z",
            )

        # Verify path is preserved in archive
        assert failed_files == []
        with zipfile.ZipFile(result, "r") as zipf:
            names = zipf.namelist()
            assert "subdir/nested.txt" in names

    def test_deletes_originals_when_enabled(self, tmp_path: Path):
        """Deletes source files when delete_originals=True."""
        # Create test file
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("delete me")
        assert test_file.exists()

        archived_dir = tmp_path / "ARCHIVED"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="delete-test",
                files=[str(test_file)],
                archived_dir=archived_dir,
                delete_originals=True,
                timestamp="20251228T120000Z",
            )

        # Verify file was deleted
        assert not test_file.exists()
        assert failed_files == []

    def test_keeps_originals_by_default(self, tmp_path: Path):
        """Keeps source files by default (delete_originals=False)."""
        # Create test file
        test_file = tmp_path / "keep_me.txt"
        test_file.write_text("keep me")

        archived_dir = tmp_path / "ARCHIVED"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="keep-test",
                files=[str(test_file)],
                archived_dir=archived_dir,
                timestamp="20251228T120000Z",
            )

        # Verify file still exists
        assert test_file.exists()
        assert failed_files == []

    def test_raises_error_for_no_valid_files(self, tmp_path: Path):
        """Raises ValueError when no valid files are provided."""
        archived_dir = tmp_path / "ARCHIVED"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            with pytest.raises(ValueError, match="No valid files were archived"):
                create_archive(
                    description="empty-test",
                    files=["nonexistent.txt"],
                    archived_dir=archived_dir,
                    timestamp="20251228T120000Z",
                )

    def test_skips_missing_files_with_warning(self, tmp_path: Path, capsys):
        """Skips missing files but archives valid ones."""
        # Create one valid file
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("valid content")

        archived_dir = tmp_path / "ARCHIVED"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="partial-test",
                files=[str(valid_file), "nonexistent.txt"],
                archived_dir=archived_dir,
                timestamp="20251228T120000Z",
            )

        # Verify archive was created with valid file
        assert Path(result).exists()
        with zipfile.ZipFile(result, "r") as zipf:
            names = zipf.namelist()
            assert "valid.txt" in names
            assert "nonexistent.txt" not in names

        # Verify failed files list contains the missing file
        assert len(failed_files) == 1
        assert "nonexistent.txt" in failed_files[0][0]
        assert failed_files[0][1] == "File not found"

        # Verify warning was printed (uses format_warning from safe_output)
        captured = capsys.readouterr()
        assert "[WARN]" in captured.err

    def test_uses_custom_output_directory(self, tmp_path: Path):
        """Uses custom output directory."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        custom_dir = tmp_path / "custom_archive"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="custom-dir",
                files=[str(test_file)],
                archived_dir=custom_dir,
                timestamp="20251228T120000Z",
            )

        assert str(custom_dir) in result
        assert Path(result).exists()
        assert failed_files == []

    def test_creates_archived_structure_by_default(self, tmp_path: Path):
        """Creates CLAUDE.md and README.md in archive directory by default."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        archived_dir = tmp_path / "ARCHIVED"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="structure-test",
                files=[str(test_file)],
                archived_dir=archived_dir,
                timestamp="20251228T120000Z",
            )

        assert (archived_dir / "CLAUDE.md").exists()
        assert (archived_dir / "README.md").exists()
        assert failed_files == []

    def test_skips_archived_structure_when_disabled(self, tmp_path: Path):
        """Skips CLAUDE.md and README.md when ensure_archived_structure=False."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        archived_dir = tmp_path / "plain_archive"

        with patch("archive_manager.get_repo_root", return_value=tmp_path):
            result, failed_files = create_archive(
                description="no-structure",
                files=[str(test_file)],
                archived_dir=archived_dir,
                ensure_archived_structure=False,
                timestamp="20251228T120000Z",
            )

        assert not (archived_dir / "CLAUDE.md").exists()
        assert not (archived_dir / "README.md").exists()
        assert failed_files == []

    @pytest.mark.skipif(os.geteuid() == 0, reason="Root can read files regardless of permissions")
    def test_handles_permission_error_on_archive(self, tmp_path: Path, capsys):
        """Handles files that can't be read due to permissions."""
        # Create test files - one readable, one not
        readable_file = tmp_path / "readable.txt"
        readable_file.write_text("readable content")

        unreadable_file = tmp_path / "unreadable.txt"
        unreadable_file.write_text("secret content")
        unreadable_file.chmod(0o000)

        archived_dir = tmp_path / "ARCHIVED"

        try:
            with patch("archive_manager.get_repo_root", return_value=tmp_path):
                result, failed_files = create_archive(
                    description="perm-test",
                    files=[str(readable_file), str(unreadable_file)],
                    archived_dir=archived_dir,
                    timestamp="20251228T120000Z",
                )

            # Verify archive was created with readable file only
            assert Path(result).exists()
            with zipfile.ZipFile(result, "r") as zipf:
                names = zipf.namelist()
                assert "readable.txt" in names
                assert "unreadable.txt" not in names

            # Verify failed files list contains the permission error
            assert len(failed_files) == 1
            assert "unreadable.txt" in failed_files[0][0]

            # Verify warning was printed
            captured = capsys.readouterr()
            assert "[WARN]" in captured.err
        finally:
            unreadable_file.chmod(0o644)  # Restore permissions for cleanup
