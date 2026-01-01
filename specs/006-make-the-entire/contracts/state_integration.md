# Contract: State Integration Updates

**Feature Branch**: `006-make-the-entire`
**Date**: 2025-11-23

---

## Purpose

Document changes required to existing skill scripts to integrate worktree-aware state management.

---

## AgentDB State Manager Updates

### File: `.gemini/skills/agentdb-state-manager/scripts/init_database.py`

**Current Behavior**:
- Creates `agentdb.duckdb` in current working directory or specified path
- No worktree awareness

**Required Changes**:
1. Import `get_state_dir()` from `worktree_context`
2. Default database path to `get_state_dir() / "agentdb.duckdb"`
3. Add `worktree_id` column to schema

**Contract**:
```python
def init_database(db_path: Path = None) -> duckdb.DuckDBPyConnection:
    """Initialize AgentDB with worktree-aware defaults."""
    if db_path is None:
        db_path = get_state_dir() / "agentdb.duckdb"
    # ... existing logic
```

### File: `.gemini/skills/agentdb-state-manager/scripts/sync_engine.py`

**Current Behavior**:
- `worktree_path` is optional parameter
- No automatic worktree detection

**Required Changes**:
1. Auto-detect worktree_id on engine initialization
2. Include worktree_id in all sync records
3. Filter queries by worktree_id by default

**Contract**:
```python
class SynchronizationEngine:
    def __init__(self, db_path: Path = None, worktree_id: str = None):
        self.worktree_id = worktree_id or get_worktree_id()
        self.db_path = db_path or get_state_dir() / "agentdb.duckdb"
```

---

## Git Workflow Manager Updates

### File: `.gemini/skills/git-workflow-manager/scripts/worktree_agent_integration.py`

**Current Behavior**:
- Hardcoded directory pattern detection (`german_feature_*`)
- Manual flow token extraction

**Required Changes**:
1. Replace hardcoded patterns with `get_worktree_context()`
2. Use `worktree_id` instead of directory name parsing

**Contract**:
```python
@staticmethod
def get_flow_token() -> str:
    """Get flow token using worktree context."""
    ctx = get_worktree_context()
    if ctx.branch_name.startswith(("feature/", "hotfix/")):
        return ctx.branch_name
    return f"worktree-{ctx.worktree_id}"
```

### File: `.gemini/skills/git-workflow-manager/scripts/create_worktree.py`

**Current Behavior**:
- Creates worktree at `{repo_parent}/{repo_name}_{type}_{timestamp}_{slug}`
- No state directory initialization

**Required Changes**:
1. Optionally initialize `.gemini-state/` in new worktree
2. Parameterize worktree path pattern via environment variable

**Contract**:
```python
def create_worktree(..., init_state: bool = True) -> Path:
    """Create worktree with optional state initialization."""
    # ... existing creation logic
    if init_state:
        state_dir = worktree_path / ".gemini-state"
        state_dir.mkdir(exist_ok=True)
        # Write initial files
```

---

## Workflow Utilities Updates

### File: `.gemini/skills/workflow-utilities/scripts/todo_updater.py`

**Current Behavior**:
- Updates TODO_feature_*.md in repository root
- No worktree awareness (files are git-tracked)

**Required Changes**:
- None - TODO files remain git-tracked per-branch
- Workflow progress (mutable state) moves to `.gemini-state/workflow.json`

### New File: `.gemini/skills/workflow-utilities/scripts/workflow_progress.py`

**Purpose**: Manage workflow progress in worktree state directory

**Contract**:
```python
def get_workflow_progress() -> dict:
    """Load workflow progress from state directory."""
    state_dir = get_state_dir()
    progress_file = state_dir / "workflow.json"
    if progress_file.exists():
        return json.loads(progress_file.read_text())
    return {"steps_completed": [], "current_step": 0}

def update_workflow_progress(step: int, artifact: str = None) -> None:
    """Update workflow progress in state directory."""
    progress = get_workflow_progress()
    progress["current_step"] = step
    if step not in progress["steps_completed"]:
        progress["steps_completed"].append(step)
    if artifact:
        progress.setdefault("artifacts", {})[f"step_{step}"] = artifact
    progress["last_updated"] = datetime.utcnow().isoformat() + "Z"

    state_dir = get_state_dir()
    (state_dir / "workflow.json").write_text(json.dumps(progress, indent=2))
```

---

## Quality Enforcer Updates

### File: `.gemini/skills/quality-enforcer/scripts/run_quality_gates.py`

**Current Behavior**:
- Runs quality gates against repository root
- No worktree awareness

**Required Changes**:
- Use `get_worktree_context().worktree_root` for repository root
- Log worktree_id in gate results

**Contract**:
```python
def run_gates() -> dict:
    ctx = get_worktree_context()
    results = {
        "worktree_id": ctx.worktree_id,
        "worktree_root": str(ctx.worktree_root),
        # ... existing gate results
    }
```

---

## Backward Compatibility

All changes must maintain backward compatibility:

1. **Non-worktree repos**: `is_worktree=False`, state in repo root `.gemini-state/`
2. **Existing skills**: Unchanged behavior unless explicitly updated
3. **AgentDB schema**: New column is nullable, existing records unaffected
4. **TODO files**: Continue using git-tracked files, no migration needed

---

## Test Scenarios

### Integration Test 1: Cross-Worktree Isolation

**Setup**: Two worktrees A and B from same repo
**Action**: Run workflow step in each worktree
**Verify**:
- Each has separate `.gemini-state/` directory
- Each has separate `agentdb.duckdb`
- Workflow progress is independent

### Integration Test 2: Main Repo Compatibility

**Setup**: Main repository (not worktree)
**Action**: Run existing workflow
**Verify**:
- State directory created at repo root
- All scripts continue functioning
- No behavioral changes from pre-update

### Integration Test 3: Orphaned State Cleanup

**Setup**: Create worktree, run workflow, remove worktree
**Action**: Run cleanup utility
**Verify**:
- Orphaned state identified
- Optional cleanup works correctly
- Main repo state unaffected

---
