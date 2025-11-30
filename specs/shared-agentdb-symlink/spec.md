# Specification: Shared AgentDB Symlink

**Type:** feature
**Slug:** shared-agentdb-symlink
**Date:** 2025-11-30
**Author:** stharrold

## Overview

This feature modifies worktree creation to symlink `agentdb.duckdb` to the main repository's database instead of creating isolated copies. This enables all Claude Code instances (main repo and worktrees) to share a unified view of workflow state, allowing cross-session visibility of running workflows.

## Implementation Context

**BMAD Planning:** See `planning/shared-agentdb-symlink/` for complete requirements and architecture.

**Implementation Preferences:**

- **Migration Strategy:** None (symlink-based, no schema changes)
- **Task Granularity:** Small tasks (1-2 hours each)
- **Follow Epic Order:** True

## Requirements Reference

See: `planning/shared-agentdb-symlink/requirements.md`

**Functional Requirements:**
- **FR-001:** Symlink AgentDB in worktrees (create symlink instead of new database file)
- **FR-002:** Main repo AgentDB as source of truth (canonical database location)
- **FR-003:** Cross-session visibility (query workflow state from all sessions)
- **FR-004:** Handle symlink in worktree_context (resolve symlinks correctly)

## Detailed Specification

### Component 1: create_worktree.py Modifications

**File:** `.claude/skills/git-workflow-manager/scripts/create_worktree.py`

**Purpose:** Modify worktree creation to symlink agentdb.duckdb instead of creating a new database.

**Changes Required:**

```python
# In create_worktree() function, after creating .claude-state/ directory:

def setup_agentdb_symlink(worktree_path: Path, main_repo_path: Path) -> None:
    """
    Create symlink from worktree's agentdb.duckdb to main repo's database.

    Args:
        worktree_path: Path to the newly created worktree
        main_repo_path: Path to the main repository (source of AgentDB)
    """
    worktree_state_dir = worktree_path / ".claude-state"
    main_db_path = main_repo_path / ".claude-state" / "agentdb.duckdb"
    worktree_db_path = worktree_state_dir / "agentdb.duckdb"

    # Ensure main repo database exists
    if not main_db_path.exists():
        # Initialize empty database in main repo if needed
        main_db_path.parent.mkdir(parents=True, exist_ok=True)
        main_db_path.touch()

    # Create symlink (relative path preferred for portability)
    if not worktree_db_path.exists():
        relative_target = os.path.relpath(main_db_path, worktree_state_dir)
        worktree_db_path.symlink_to(relative_target)
```

**Dependencies:**
- `pathlib` (standard library)
- `os` (standard library)

### Component 2: worktree_context.py Modifications

**File:** `.claude/skills/workflow-utilities/scripts/worktree_context.py`

**Purpose:** Ensure database path resolution works correctly with symlinks.

**Changes Required:**

```python
def get_agentdb_path() -> Path:
    """
    Get the path to the AgentDB database, resolving symlinks.

    Returns:
        Resolved absolute path to agentdb.duckdb
    """
    state_dir = get_state_dir()
    db_path = state_dir / "agentdb.duckdb"

    # Resolve symlink to get actual file path
    # This ensures DuckDB locks the correct file
    return db_path.resolve()


def get_main_repo_path() -> Path:
    """
    Get the path to the main repository (not worktree).

    Returns:
        Path to main repository root
    """
    git_dir = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True, text=True, check=True
    ).stdout.strip()

    # If in a worktree, git_dir is .git/worktrees/<name>
    # Main repo is ../../../ from there
    if "/worktrees/" in git_dir:
        # Extract main repo path from worktree git dir
        main_git_dir = Path(git_dir).parent.parent  # .git/
        return main_git_dir.parent
    else:
        # Already in main repo
        return Path(git_dir).parent
```

### Component 3: query_workflow_state.py Enhancements

**File:** `.claude/skills/agentdb-state-manager/scripts/query_workflow_state.py`

**Purpose:** Display workflow state from all sessions with worktree identification.

**Changes Required:**

```python
def query_all_sessions() -> list[dict]:
    """
    Query workflow state showing records from all worktrees.

    Returns:
        List of workflow records with worktree_id column
    """
    db_path = get_agentdb_path()  # Resolves symlink
    conn = duckdb.connect(str(db_path))

    # Query includes worktree_id to identify source
    result = conn.execute("""
        SELECT
            id,
            sync_type,
            pattern,
            source_path,
            target_path,
            worktree_id,
            created_at
        FROM workflow_syncs
        ORDER BY created_at DESC
        LIMIT 50
    """).fetchall()

    conn.close()
    return result


def format_output(records: list[dict]) -> str:
    """Format records showing which worktree each came from."""
    output = []
    for record in records:
        worktree = record["worktree_id"] or "main"
        output.append(f"[{worktree}] {record['pattern']} - {record['created_at']}")
    return "\n".join(output)
```

## Data Models

### Existing Schema (No Changes Required)

The existing AgentDB schema already includes `worktree_id` column:

```sql
CREATE TABLE IF NOT EXISTS workflow_syncs (
    id INTEGER PRIMARY KEY,
    sync_type VARCHAR NOT NULL,
    pattern VARCHAR NOT NULL,
    source_path VARCHAR,
    target_path VARCHAR,
    worktree_id VARCHAR,  -- Already exists for identification
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Point:** No schema migration needed. The symlink approach uses existing database structure.

## API Endpoints

**N/A** - This is a local file operation feature with no API component.

## Testing Requirements

### Unit Tests

**File:** `tests/skills/test_create_worktree_symlink.py`

```python
import pytest
from pathlib import Path
import tempfile
import os

def test_setup_agentdb_symlink_creates_symlink():
    """Test that symlink is created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        main_repo = Path(tmpdir) / "main"
        worktree = Path(tmpdir) / "worktree"

        # Setup directories
        (main_repo / ".claude-state").mkdir(parents=True)
        (main_repo / ".claude-state" / "agentdb.duckdb").touch()
        (worktree / ".claude-state").mkdir(parents=True)

        # Run function
        setup_agentdb_symlink(worktree, main_repo)

        # Verify
        symlink = worktree / ".claude-state" / "agentdb.duckdb"
        assert symlink.is_symlink()
        assert symlink.resolve() == main_repo / ".claude-state" / "agentdb.duckdb"


def test_symlink_allows_shared_writes():
    """Test that writes through symlink are visible in main repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        main_repo = Path(tmpdir) / "main"
        worktree = Path(tmpdir) / "worktree"

        # Setup
        (main_repo / ".claude-state").mkdir(parents=True)
        (worktree / ".claude-state").mkdir(parents=True)
        main_db = main_repo / ".claude-state" / "agentdb.duckdb"

        setup_agentdb_symlink(worktree, main_repo)

        # Write through worktree symlink
        worktree_db = worktree / ".claude-state" / "agentdb.duckdb"
        import duckdb
        conn = duckdb.connect(str(worktree_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.execute("INSERT INTO test VALUES (1)")
        conn.close()

        # Read from main repo
        conn = duckdb.connect(str(main_db))
        result = conn.execute("SELECT * FROM test").fetchall()
        conn.close()

        assert result == [(1,)]
```

### Integration Tests

**File:** `tests/integration/test_worktree_symlink_integration.py`

```python
def test_worktree_creation_with_symlink(tmp_git_repo):
    """Test full worktree creation creates symlink."""
    # Create worktree using create_worktree.py
    result = subprocess.run([
        "uv", "run", "python",
        ".claude/skills/git-workflow-manager/scripts/create_worktree.py",
        "feature", "test-feature", "contrib/stharrold", "--no-todo"
    ], capture_output=True, text=True)

    assert result.returncode == 0

    # Verify symlink exists
    worktree_path = Path("../repo_feature_test-feature")
    db_symlink = worktree_path / ".claude-state" / "agentdb.duckdb"
    assert db_symlink.is_symlink()
```

## Quality Gates

- [ ] Test coverage ≥ 80%
- [ ] All tests passing
- [ ] Linting clean (ruff check)
- [ ] Symlink creation verified on macOS and Linux
- [ ] DuckDB concurrent access tested

## Container Specifications

**N/A** - No container changes required. This feature operates on local filesystem.

## Dependencies

**No new dependencies required.** Uses existing:
- `pathlib` (standard library)
- `os` (standard library)
- `duckdb` (already in pyproject.toml)

## Implementation Notes

### Key Considerations

- **Relative symlinks preferred:** Use relative paths for portability when moving directories
- **DuckDB locking:** DuckDB handles concurrent access via file locks on the resolved path
- **Worktree cleanup:** When removing worktree, symlink is automatically removed (just a file)

### Error Handling

- **Main DB doesn't exist:** Create empty database before creating symlink
- **Symlink already exists:** Skip creation (idempotent)
- **Permission errors:** Log warning and fall back to isolated database

### Edge Cases

- **Nested worktrees:** Not supported (git limitation)
- **Cross-filesystem symlinks:** May not work on some systems; document as limitation
- **Windows:** Use `os.symlink()` which requires admin privileges or developer mode

## References

- [DuckDB Concurrency Documentation](https://duckdb.org/docs/connect/concurrency)
- [Python pathlib.Path.symlink_to](https://docs.python.org/3/library/pathlib.html#pathlib.Path.symlink_to)
- Planning: `planning/shared-agentdb-symlink/requirements.md`
