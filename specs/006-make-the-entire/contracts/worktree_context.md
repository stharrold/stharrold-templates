# Contract: WorktreeContext Module

**Feature Branch**: `006-make-the-entire`
**Date**: 2025-11-23
**Location**: `.gemini/skills/workflow-utilities/scripts/worktree_context.py`

---

## Purpose

Central utility module for worktree detection and state directory management. All skills that need worktree-aware state must import from this module.

---

## Public API

### `get_worktree_context() -> WorktreeContext`

Detect the current worktree context.

**Returns**: `WorktreeContext` dataclass with all detection results

**Behavior**:
1. Run `git rev-parse --show-toplevel` to get worktree root
2. Run `git rev-parse --git-common-dir` to get shared git directory
3. Check if `.git` is a file (worktree) or directory (main repo)
4. Generate stable worktree ID from path hash
5. Get current branch name

**Errors**:
- `RuntimeError`: Not in a git repository

### `get_state_dir() -> Path`

Get the worktree-specific state directory, creating if needed.

**Returns**: `Path` to `.gemini-state/` directory

**Behavior**:
1. Call `get_worktree_context()`
2. Construct path: `{worktree_root}/.gemini-state/`
3. Create directory if not exists
4. Create `.gitignore` file if not exists
5. Write `.worktree-id` file if not exists

**Errors**:
- `PermissionError`: Cannot create state directory
- `RuntimeError`: Not in a git repository

### `get_worktree_id() -> str`

Get the stable worktree identifier.

**Returns**: 12-character hex string (SHA-256 prefix)

**Behavior**:
1. Call `get_worktree_context()`
2. Return `worktree_id` field

### `cleanup_orphaned_state(repo_root: Path) -> list[Path]`

Find and optionally remove orphaned state directories.

**Args**:
- `repo_root`: Main repository root path

**Returns**: List of orphaned state directory paths

**Behavior**:
1. List all worktrees via `git worktree list --porcelain`
2. Find state directories in each worktree path
3. Compare against active worktree list
4. Return paths without active worktrees

---

## Data Structures

### WorktreeContext (dataclass)

```python
@dataclass
class WorktreeContext:
    worktree_root: Path
    git_common_dir: Path
    is_worktree: bool
    worktree_id: str
    branch_name: str

    @property
    def state_dir(self) -> Path:
        return self.worktree_root / ".gemini-state"
```

---

## Usage Examples

### In Skill Scripts

```python
from worktree_context import get_state_dir, get_worktree_id

# Get isolated state directory
state_dir = get_state_dir()
db_path = state_dir / "agentdb.duckdb"

# Include worktree_id in database records
worktree_id = get_worktree_id()
```

### In AgentDB Initialization

```python
from worktree_context import get_state_dir

def init_database():
    state_dir = get_state_dir()
    db_path = state_dir / "agentdb.duckdb"
    conn = duckdb.connect(str(db_path))
    # ...
```

---

## Test Scenarios

### Test 1: Main Repository Detection

**Given**: Running in main repository (not a worktree)
**When**: `get_worktree_context()` is called
**Then**:
- `is_worktree` is `False`
- `worktree_root` equals `git_common_dir` parent
- `worktree_id` is stable across calls

### Test 2: Worktree Detection

**Given**: Running in a git worktree
**When**: `get_worktree_context()` is called
**Then**:
- `is_worktree` is `True`
- `worktree_root` differs from main repo
- `worktree_id` is unique to this worktree

### Test 3: State Directory Creation

**Given**: State directory does not exist
**When**: `get_state_dir()` is called
**Then**:
- Directory is created at `.gemini-state/`
- `.gitignore` contains `*`
- `.worktree-id` contains the worktree ID

### Test 4: Idempotent State Directory

**Given**: State directory already exists
**When**: `get_state_dir()` is called multiple times
**Then**:
- Same path returned each time
- Existing files not modified

### Test 5: Orphaned State Detection

**Given**: A worktree was removed but `.gemini-state/` remains
**When**: `cleanup_orphaned_state()` is called
**Then**:
- Orphaned directory is identified
- Returned in list for cleanup decision

---
