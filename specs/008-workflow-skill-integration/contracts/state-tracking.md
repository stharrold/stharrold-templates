# Contract: State Tracking

**Feature**: 008-workflow-skill-integration
**Date**: 2025-11-23

## Overview

AgentDB provides workflow state tracking via the `agent_synchronizations` table. Two new scripts enable recording and querying state.

---

## record_sync.py Contract

**Location**: `.claude/skills/agentdb-state-manager/scripts/record_sync.py`

**Purpose**: Record workflow transitions in AgentDB

**Interface**:
```bash
python .claude/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type <type> \
  --pattern <pattern> \
  [--source <source>] \
  [--target <target>] \
  [--worktree <path>] \
  [--metadata <json>]
```

**Arguments**:
| Argument | Required | Description |
|----------|----------|-------------|
| `--sync-type` | Yes | One of: `workflow_transition`, `quality_gate`, `file_update` |
| `--pattern` | Yes | Phase pattern (e.g., `phase_1_specify`) |
| `--source` | No | Source location (e.g., `planning/my-feature`) |
| `--target` | No | Target location (e.g., `specs/my-feature`) |
| `--worktree` | No | Worktree path (auto-detected if in worktree) |
| `--metadata` | No | Additional JSON metadata |

**Behavior**:
1. Initialize AgentDB if not exists
2. Generate UUID for sync_id
3. Detect worktree path if not provided
4. Insert record into `agent_synchronizations` with status `completed`
5. Insert audit record into `sync_audit_trail`
6. Print sync_id on success

**Output**:
```
✓ Recorded sync: <sync_id>
  Type: workflow_transition
  Pattern: phase_1_specify
  Source: planning/my-feature
  Target: worktree
```

**Errors**:
- `ERROR: Invalid sync-type` - sync_type not in allowed list
- `ERROR: AgentDB initialization failed` - database error

---

## query_workflow_state.py Contract

**Location**: `.claude/skills/agentdb-state-manager/scripts/query_workflow_state.py`

**Purpose**: Query current workflow phase from AgentDB

**Interface**:
```bash
python .claude/skills/agentdb-state-manager/scripts/query_workflow_state.py \
  [--worktree <path>] \
  [--format <format>]
```

**Arguments**:
| Argument | Required | Description |
|----------|----------|-------------|
| `--worktree` | No | Worktree path (auto-detected) |
| `--format` | No | Output format: `text` (default), `json` |

**Behavior**:
1. Connect to AgentDB
2. Query latest sync record for current worktree
3. Determine current phase from pattern
4. Return phase information

**Output (text)**:
```
Current Workflow State:
  Worktree: /path/to/feature_my-feature
  Phase: 2 (plan)
  Last Sync: 2025-11-23T10:30:00Z
  Pattern: phase_2_plan
  Next: /3_tasks
```

**Output (json)**:
```json
{
  "worktree": "/path/to/feature_my-feature",
  "phase": 2,
  "phase_name": "plan",
  "last_sync": "2025-11-23T10:30:00Z",
  "pattern": "phase_2_plan",
  "next_command": "/3_tasks"
}
```

**Errors**:
- `ERROR: No workflow state found` - no syncs for this worktree
- `ERROR: Not in a git repository` - cannot detect worktree

---

## State Patterns

**Workflow Transition Patterns**:
| Pattern | Phase | Description |
|---------|-------|-------------|
| `phase_1_specify` | 1 | Planning + worktree created |
| `phase_2_plan` | 2 | Specifications created |
| `phase_3_tasks` | 3 | Tasks validated |
| `phase_4_implement` | 4 | Implementation complete |
| `phase_5_integrate` | 5 | Integration complete |
| `phase_6_release` | 6 | Release created |
| `phase_7_backmerge` | 7 | Backmerge complete |

**Quality Gate Pattern**:
| Pattern | Description |
|---------|-------------|
| `quality_gate_passed` | All 5 gates passed |
| `quality_gate_failed` | One or more gates failed |

---

## Database Schema Reference

Uses existing `agent_synchronizations` table from `agentdb_sync_schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS agent_synchronizations (
    sync_id VARCHAR PRIMARY KEY,
    agent_id VARCHAR NOT NULL,          -- 'claude-code'
    worktree_path VARCHAR,              -- Git worktree path
    sync_type VARCHAR NOT NULL,         -- workflow_transition, quality_gate, file_update
    source_location VARCHAR NOT NULL,
    target_location VARCHAR NOT NULL,
    pattern VARCHAR NOT NULL,           -- phase_1_specify, etc.
    status VARCHAR NOT NULL,            -- pending, in_progress, completed, failed
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    created_by VARCHAR NOT NULL,
    metadata JSON
);
```

---

## Integration with Slash Commands

Each slash command calls `record_sync.py` after completing its primary operations:

```bash
# Example: /2_plan records state after speckit-author completes
podman-compose run --rm dev python .claude/skills/speckit-author/scripts/create_specifications.py ...

# Then record the transition
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_2_plan \
  --source "../planning/{slug}" \
  --target "specs/{slug}"
```

The `/workflow/all` orchestrator can use `query_workflow_state.py` to detect current phase and continue from there.
