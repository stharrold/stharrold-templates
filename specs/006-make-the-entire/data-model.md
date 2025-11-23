# Data Model: Worktree-Aware State

**Feature Branch**: `006-make-the-entire`
**Date**: 2025-11-23

---

## Entities

### WorktreeContext

Represents the execution context for worktree detection and state scoping.

| Field | Type | Description |
|-------|------|-------------|
| `worktree_root` | `Path` | Absolute path to worktree/repo root |
| `git_common_dir` | `Path` | Path to shared `.git` directory |
| `is_worktree` | `bool` | True if running in a git worktree |
| `worktree_id` | `str` | Stable hash of `worktree_root` |
| `branch_name` | `str` | Current git branch |
| `state_dir` | `Path` | Path to `.claude-state/` directory |

**Derivation Rules**:
- `worktree_root` = `git rev-parse --show-toplevel`
- `git_common_dir` = `git rev-parse --git-common-dir`
- `is_worktree` = `.git` is a file (not directory)
- `worktree_id` = `sha256(worktree_root)[:12]`
- `state_dir` = `worktree_root / ".claude-state"`

### StateDirectory

Represents the per-worktree mutable state storage.

| Field | Type | Description |
|-------|------|-------------|
| `path` | `Path` | `.claude-state/` absolute path |
| `worktree_id` | `str` | Identifier linking to WorktreeContext |
| `created_at` | `datetime` | Directory creation timestamp |

**Contents**:
```
.claude-state/
├── agentdb.duckdb       # Per-worktree DuckDB database
├── workflow.json        # Workflow progress tracking
├── .worktree-id         # Stable identifier file
└── .gitignore           # Auto-created to ignore directory
```

### WorkflowProgress

JSON structure stored in `.claude-state/workflow.json`.

```json
{
  "worktree_id": "a1b2c3d4e5f6",
  "feature_branch": "006-make-the-entire",
  "current_step": 2,
  "steps_completed": [1],
  "artifacts": {
    "spec": "specs/006-make-the-entire/spec.md",
    "research": "specs/006-make-the-entire/research.md"
  },
  "last_updated": "2025-11-23T12:00:00Z",
  "session_id": "uuid-here"
}
```

---

## State Transitions

### Worktree Lifecycle

```
[Created] --> [Active] --> [Merged] --> [Removed]
     │            │            │            │
     └── init     └── work     └── PR       └── cleanup
         state        in           merged       orphaned
                      state                     state
```

### State Directory Lifecycle

1. **Creation**: On first skill execution in worktree
2. **Active**: Read/write during workflow execution
3. **Orphaned**: Worktree removed but state remains
4. **Cleanup**: Explicit cleanup command or auto-detection

---

## Integration Points

### Skill Scripts

All skill scripts that store state must use:

```python
from worktree_context import get_state_dir

state_dir = get_state_dir()
db_path = state_dir / "agentdb.duckdb"
```

### AgentDB Schema Updates

**New column in `agent_synchronizations`**:

```sql
ALTER TABLE agent_synchronizations
ADD COLUMN worktree_id VARCHAR(12);

CREATE INDEX idx_sync_worktree
ON agent_synchronizations(worktree_id);
```

### TODO File Handling

- TODO.md: Git-tracked (per-branch), no change needed
- TODO_feature_*.md: Git-tracked (per-branch), no change needed
- Workflow progress: Stored in `.claude-state/workflow.json`

---

## Validation Rules

1. `worktree_root` must be a valid git repository
2. `state_dir` must be writable (create if not exists)
3. `worktree_id` must be consistent across invocations
4. AgentDB queries should filter by `worktree_id` for isolation

---
