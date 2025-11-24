# Quickstart: Workflow Skill Integration

**Feature**: 008-workflow-skill-integration
**Date**: 2025-11-23

## Validation Scenarios

### Scenario 1: New Feature Workflow (End-to-End)

**Goal**: Verify all 7 slash commands invoke skills and record state correctly.

```bash
# 1. Start new feature
/workflow/all new "test feature for validation"

# Expected:
# - bmad-planner creates planning/test-feature/
# - git-workflow-manager creates worktree
# - AgentDB has phase_1_specify record
# - User prompted to cd to worktree

# 2. In worktree, create specs
/2_plan

# Expected:
# - speckit-author creates specs/test-feature/spec.md, plan.md
# - AgentDB has phase_2_plan record

# 3. Validate tasks
/3_tasks

# Expected:
# - Tasks parsed from plan.md
# - AgentDB has phase_3_tasks record

# 4. Implement
/4_implement

# Expected:
# - Tasks executed
# - Quality gates pass (5/5)
# - AgentDB has phase_4_implement record

# 5. Integrate
/5_integrate

# Expected:
# - PR feature→contrib created
# - After merge: worktree deleted (no TODO archived)
# - AgentDB has phase_5_integrate record
```

### Scenario 2: Script Flag Verification

**Goal**: Verify new script flags work correctly.

```bash
# Test create_worktree.py --no-todo
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/create_worktree.py \
  feature test-no-todo contrib/stharrold --no-todo

# Expected:
# - Worktree created
# - NO TODO_feature_*.md file created

# Verify no TODO file
ls TODO_feature_*test-no-todo*.md 2>/dev/null && echo "FAIL: TODO exists" || echo "PASS: No TODO"

# Cleanup
git worktree remove ../stharrold-templates_feature_test-no-todo
git branch -D feature/*_test-no-todo
```

```bash
# Test cleanup_feature.py --no-archive
# (Requires existing worktree)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/cleanup_feature.py \
  test-slug --no-archive

# Expected:
# - Worktree deleted
# - Branch deleted
# - NO archival operation attempted
```

### Scenario 3: AgentDB State Tracking

**Goal**: Verify state is recorded and queryable.

```bash
# Initialize AgentDB
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/init_database.py

# Record a test sync
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_1_specify \
  --source "planning/test" \
  --target "worktree"

# Expected: "✓ Recorded sync: <uuid>"

# Query state
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/query_workflow_state.py \
  --format json

# Expected: JSON with phase=1, pattern=phase_1_specify
```

### Scenario 4: .specify/ Archived

**Goal**: Verify .specify/ is no longer used.

```bash
# Check .specify/ is archived
ls -la .specify/ARCHIVED/ 2>/dev/null && echo "PASS: Archived" || echo "CHECK: May not be archived yet"

# Verify slash commands don't reference .specify/
grep -r "\.specify/" .claude/commands/workflow/

# Expected: No matches (all references removed)
```

### Scenario 5: Deprecated Scripts Archived

**Goal**: Verify workflow-utilities scripts are deprecated.

```bash
# Check deprecated scripts moved to ARCHIVED/
ls .claude/skills/workflow-utilities/ARCHIVED/

# Expected files:
# - sync_todo_to_db.py
# - todo_updater.py
# - workflow_archiver.py
# - workflow_registrar.py
# - sync_manifest.py
```

## Verification Checklist

| Test | Command | Expected |
|------|---------|----------|
| Skills invoked | `/1_specify "test"` | bmad-planner + git-workflow-manager called |
| No TODO created | `ls TODO_*.md` | No new TODO files |
| State recorded | `query_workflow_state.py` | Returns current phase |
| .specify/ archived | `ls .specify/ARCHIVED/` | Contains bash scripts |
| Gates pass | `run_quality_gates.py` | 5/5 gates pass |
| Workflow complete | `/workflow/all` | All 7 phases executable |

## Rollback Plan

If issues arise, revert to previous behavior:

```bash
# Restore .specify/
mv .specify/ARCHIVED/* .specify/

# Restore workflow-utilities scripts
mv .claude/skills/workflow-utilities/ARCHIVED/*.py .claude/skills/workflow-utilities/scripts/

# Revert slash commands (git)
git checkout HEAD~1 -- .claude/commands/workflow/

# Revert script changes
git checkout HEAD~1 -- .claude/skills/git-workflow-manager/scripts/create_worktree.py
git checkout HEAD~1 -- .claude/skills/git-workflow-manager/scripts/cleanup_feature.py
```
