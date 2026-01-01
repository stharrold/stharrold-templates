# Research: Worktree-Aware Workflow and Skills System

**Feature Branch**: `006-make-the-entire`
**Date**: 2025-11-23

---

## Current State Analysis

### 1. AgentDB State Manager (DuckDB)

**Location**: `.gemini/skills/agentdb-state-manager/`

**Current Architecture**:
- Uses DuckDB with three core tables: `agent_synchronizations`, `sync_executions`, `sync_audit_trail`
- `worktree_path` field exists but is **optional** (VARCHAR nullable)
- No mandatory scoping by worktree - state is globally visible
- Single `agentdb.duckdb` file per session with 24-hour lifetime

**Key Files**:
- Schema: `.gemini/skills/agentdb-state-manager/schemas/agentdb_sync_schema.sql`
- Engine: `.gemini/skills/agentdb-state-manager/scripts/sync_engine.py`
- Init: `.gemini/skills/agentdb-state-manager/scripts/init_database.py`

### 2. TODO File Storage

**Current Storage**:
- Main manifest: `/TODO.md` (global)
- Per-feature: `/TODO_feature_*.md` (main repo root, shared across worktrees)
- Archived: `/docs/archived/TODO_*.md`

**Key Files**:
- Updater: `.gemini/skills/workflow-utilities/scripts/todo_updater.py`
- Registrar: `.gemini/skills/workflow-utilities/scripts/workflow_registrar.py`
- Archiver: `.gemini/skills/workflow-utilities/scripts/workflow_archiver.py`

### 3. Git Worktree Support

**Current Implementation**:
- Creates worktrees at: `{repo_parent}/{repo_name}_{workflow_type}_{timestamp}_{slug}`
- Worktree detection: Hardcoded directory pattern (`german_feature_*`)
- Flow token extraction: Directory name or git branch fallback

**Key Files**:
- Creator: `.gemini/skills/git-workflow-manager/scripts/create_worktree.py`
- Integration: `.gemini/skills/git-workflow-manager/scripts/worktree_agent_integration.py`

---

## Technical Research Findings

### Git Worktree Detection Methods

| Command | Output | Use Case |
|---------|--------|----------|
| `git rev-parse --show-toplevel` | Absolute repo root | Get current worktree root |
| `git rev-parse --git-dir` | `.git` or `.git/worktrees/{name}` | Detect if in worktree |
| `git rev-parse --git-common-dir` | Main repo `.git` path | Find shared git directory |
| `git worktree list --porcelain` | All worktrees with metadata | Enumerate worktrees |

**Detection Logic**:
```python
# If .git is a file (not directory), we're in a worktree
git_path = Path('.git')
if git_path.is_file():
    # Contains: gitdir: /path/to/main/.git/worktrees/{name}
    is_worktree = True
```

### State Scoping Options

| Scope | Current | Proposed |
|-------|---------|----------|
| Global | AgentDB session, TODO.md manifest | Unchanged (shared config) |
| Per-Branch | TODO_feature_*.md | Unchanged (git-tracked) |
| Per-Worktree | None | `.gemini-state/` directory |

---

## Design Decisions

### Decision 1: Worktree State Directory

**Chosen**: `.gemini-state/` directory within each worktree

**Rationale**:
- Mirrors `.gemini/` for skills (read-only) vs `.gemini-state/` for state (read-write)
- Automatically isolated per worktree
- Easy to `.gitignore` (mutable state shouldn't be committed)
- Convention follows existing patterns (`.git`, `.vscode`, etc.)

**Alternatives Rejected**:
- Storing in main repo `.git/worktrees/{name}/state/` - harder to access, git-internal
- Using environment variables - not persistent, requires manual setup

### Decision 2: Worktree Identifier

**Chosen**: Use `git rev-parse --show-toplevel` path hash

**Rationale**:
- Deterministic (same path = same ID)
- No additional state needed
- Works for both main repo and worktrees
- Survives session restarts

**Alternatives Rejected**:
- UUID per worktree - requires persistence mechanism
- Directory name parsing - fragile, depends on naming convention

### Decision 3: Skill Read vs. State Write Split

**Chosen**: Skills remain shared (`.gemini/skills/`), only state is worktree-local

**Rationale**:
- Skills are read-only definitions - no benefit to isolation
- Avoids duplication of skill code
- Changes to skills affect all worktrees consistently
- Only mutable state needs isolation

### Decision 4: Backward Compatibility

**Chosen**: Non-worktree repos auto-detect and use repo root

**Rationale**:
- `git rev-parse --show-toplevel` works in both cases
- State directory created on first write
- Existing repos continue working without changes
- No migration required

---

## Architecture Summary

### Before (Current)
```
repo/
├── .gemini/skills/          # Shared skill definitions
├── TODO.md                   # Global manifest
├── TODO_feature_*.md         # Per-feature (but globally stored)
├── agentdb.duckdb           # Session state (global)
└── ...
```

### After (Worktree-Aware)
```
repo/                         # Main working directory
├── .gemini/skills/          # Shared (read-only)
├── .gemini-state/           # Worktree-specific state
│   ├── agentdb.duckdb       # Per-worktree database
│   ├── workflow.json        # Workflow progress
│   └── .worktree-id         # Stable identifier
├── TODO.md                   # Git-tracked (per-branch)
└── ...

repo_feature_abc/            # Worktree for feature-abc
├── .gemini/skills/          # -> symlink or accessed from main
├── .gemini-state/           # Separate state directory
│   ├── agentdb.duckdb       # Independent database
│   ├── workflow.json        # Independent progress
│   └── .worktree-id         # Different identifier
└── ...
```

---

## Risk Analysis

| Risk | Mitigation |
|------|------------|
| Orphaned state on worktree removal | Cleanup utility in `git-workflow-manager` |
| Skills need state storage | Create `get_state_dir()` utility function |
| AgentDB schema changes | Backward-compatible migration in init script |
| TODO.md conflicts across worktrees | TODO.md stays git-tracked (per-branch) |

---

## Dependencies

- Python `pathlib` for path operations
- `subprocess` for git commands
- DuckDB Python driver (existing)
- No new external dependencies required

---
