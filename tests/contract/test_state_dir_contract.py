"""Contract tests for get_state_dir() function.

Tests the contract specified in specs/006-make-the-entire/contracts/worktree_context.md
"""

import sys
from pathlib import Path

# Add the worktree_context module to path
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent
        / '.claude/skills/workflow-utilities/scripts'
    ),
)

import pytest


class TestGetStateDirContract:
    """Contract tests for get_state_dir() function."""

    def test_returns_path_to_claude_state(self, tmp_path, monkeypatch):
        """Test: Returns Path to .claude-state/."""
        from worktree_context import get_state_dir

        result = get_state_dir()
        assert isinstance(result, Path)
        assert result.name == '.claude-state'

    def test_creates_directory_if_not_exists(self, tmp_path, monkeypatch):
        """Test: Creates directory if not exists."""
        from worktree_context import get_state_dir

        # Note: This test runs in the actual repo, so we just verify
        # the directory exists after calling get_state_dir()
        result = get_state_dir()
        assert result.exists()
        assert result.is_dir()

    def test_creates_gitignore_with_star(self, tmp_path, monkeypatch):
        """Test: Creates .gitignore with *."""
        from worktree_context import get_state_dir

        result = get_state_dir()
        gitignore = result / '.gitignore'
        assert gitignore.exists()
        content = gitignore.read_text()
        assert '*' in content

    def test_creates_worktree_id_file(self, tmp_path, monkeypatch):
        """Test: Creates .worktree-id file."""
        from worktree_context import get_state_dir

        result = get_state_dir()
        worktree_id_file = result / '.worktree-id'
        assert worktree_id_file.exists()
        content = worktree_id_file.read_text().strip()
        assert len(content) == 12
        # Validate it's a valid hex string
        int(content, 16)

    def test_idempotent_multiple_calls_return_same_path(self):
        """Test: Idempotent (multiple calls return same path)."""
        from worktree_context import get_state_dir

        result1 = get_state_dir()
        result2 = get_state_dir()
        result3 = get_state_dir()

        assert result1 == result2 == result3

    def test_raises_runtime_error_when_not_in_git_repo(self, tmp_path, monkeypatch):
        """Test: Raises RuntimeError when not in git repo."""
        from worktree_context import get_state_dir

        # Change to a non-git directory
        monkeypatch.chdir(tmp_path)

        with pytest.raises(RuntimeError):
            get_state_dir()
