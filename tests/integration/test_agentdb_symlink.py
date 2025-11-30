"""Integration test for shared AgentDB via symlink.

Tests that worktree AgentDB symlinks work correctly with the actual
worktree_context utilities and DuckDB operations.
"""

import sys
from pathlib import Path

# Add the worktree_context module to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / ".claude/skills/workflow-utilities/scripts"),
)


class TestGetAgentdbPath:
    """Integration tests for get_agentdb_path function."""

    def test_returns_path_object(self):
        """Given: get_agentdb_path() called.
        Then: Returns a Path object.
        """
        from worktree_context import get_agentdb_path

        db_path = get_agentdb_path()

        assert isinstance(db_path, Path)

    def test_path_is_resolved(self):
        """Given: get_agentdb_path() called.
        Then: Path is resolved (absolute, no symlinks).
        """
        from worktree_context import get_agentdb_path

        db_path = get_agentdb_path()

        # Resolved paths are absolute
        assert db_path.is_absolute()
        # Resolved paths have no .. components
        assert ".." not in str(db_path)

    def test_path_ends_with_agentdb_duckdb(self):
        """Given: get_agentdb_path() called.
        Then: Path ends with agentdb.duckdb.
        """
        from worktree_context import get_agentdb_path

        db_path = get_agentdb_path()

        assert db_path.name == "agentdb.duckdb"

    def test_path_parent_is_claude_state(self):
        """Given: get_agentdb_path() called.
        Then: Parent directory is .claude-state.
        """
        from worktree_context import get_agentdb_path

        db_path = get_agentdb_path()

        assert db_path.parent.name == ".claude-state"


class TestGetMainRepoPath:
    """Integration tests for get_main_repo_path function."""

    def test_returns_path_or_none(self):
        """Given: get_main_repo_path() called.
        Then: Returns Path or None depending on worktree status.
        """
        from worktree_context import get_main_repo_path, get_worktree_context

        main_repo = get_main_repo_path()
        ctx = get_worktree_context()

        if ctx.is_worktree:
            assert isinstance(main_repo, Path)
            assert main_repo.is_absolute()
        else:
            assert main_repo is None

    def test_main_repo_contains_git_dir(self):
        """Given: Running in a worktree and get_main_repo_path() called.
        Then: Main repo path contains .git directory.
        """
        from worktree_context import get_main_repo_path, get_worktree_context

        main_repo = get_main_repo_path()
        ctx = get_worktree_context()

        if ctx.is_worktree and main_repo is not None:
            git_dir = main_repo / ".git"
            assert git_dir.exists()
            assert git_dir.is_dir()


class TestSymlinkWithDuckDB:
    """Integration tests for symlinked AgentDB with DuckDB operations."""

    def test_can_connect_via_resolved_path(self):
        """Given: AgentDB path resolved.
        Then: DuckDB can connect to the database.
        """
        pytest = __import__("pytest")

        try:
            import duckdb
        except ImportError:
            pytest.skip("duckdb not installed")

        from worktree_context import get_agentdb_path

        db_path = get_agentdb_path()

        # Should be able to connect (creates file if needed)
        conn = duckdb.connect(str(db_path))
        # Basic query to verify connection
        result = conn.execute("SELECT 1").fetchone()
        conn.close()

        assert result == (1,)

    def test_resolved_path_locks_correct_file(self):
        """Given: AgentDB accessed via symlink.
        Then: Resolved path ensures correct file locking.
        """
        from worktree_context import get_agentdb_path, get_state_dir

        db_path = get_agentdb_path()
        state_dir = get_state_dir()
        symlink_path = state_dir / "agentdb.duckdb"

        # If symlink exists, resolved path should differ from symlink path
        if symlink_path.is_symlink():
            # Resolved path points to actual file
            assert db_path != symlink_path
            # But following the symlink should get to same place
            assert symlink_path.resolve() == db_path
        else:
            # Not a symlink - paths should match
            assert db_path == symlink_path.resolve()
