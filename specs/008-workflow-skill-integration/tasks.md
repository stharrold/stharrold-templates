# Tasks: Workflow Skill Integration

**Input**: Design documents from `/specs/008-workflow-skill-integration/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → SUCCESS: Implementation plan loaded
   → Extracted: Python 3.11, single project, slash commands + scripts
2. Load optional design documents:
   → data-model.md: Entity mappings loaded
   → contracts/: slash-commands.md, state-tracking.md loaded
   → research.md: 5 research questions resolved
3. Generate tasks by category:
   → Setup: None (existing project)
   → Scripts: Flag additions, new AgentDB scripts
   → Slash Commands: Rewrite 7 commands
   → Deprecation: Archive .specify/, move scripts
   → Verification: Test workflow
4. Apply task rules:
   → Script tasks can be parallel [P] (different files)
   → Slash command tasks sequential (test each)
5. Number tasks sequentially (T001-T028)
6. Generate dependency graph
7. Validate task completeness
8. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 3.1: Create New AgentDB Scripts

- [ ] T001 [P] Create `record_sync.py` in `.claude/skills/agentdb-state-manager/scripts/`
  - Implement CLI with argparse: `--sync-type`, `--pattern`, `--source`, `--target`, `--worktree`, `--metadata`
  - Connect to AgentDB, insert into `agent_synchronizations`
  - Insert audit record into `sync_audit_trail`
  - Print success message with sync_id
  - See contract: `contracts/state-tracking.md`

- [ ] T002 [P] Create `query_workflow_state.py` in `.claude/skills/agentdb-state-manager/scripts/`
  - Implement CLI with argparse: `--worktree`, `--format`
  - Query latest sync for worktree from `agent_synchronizations`
  - Parse phase number from pattern (e.g., `phase_2_plan` → 2)
  - Output text or JSON format
  - See contract: `contracts/state-tracking.md`

---

## Phase 3.2: Add Script Flags

- [ ] T003 [P] Add `--no-todo` flag to `.claude/skills/git-workflow-manager/scripts/create_worktree.py`
  - Add argparse argument: `--no-todo` (default=True, action='store_false' for `create_todo`)
  - Wrap TODO creation in `if create_todo:` block
  - Update docstring and help text
  - Maintain backward compatibility (flag skips by default)

- [ ] T004 [P] Add `--no-archive` flag to `.claude/skills/git-workflow-manager/scripts/cleanup_feature.py`
  - Add argparse argument: `--no-archive` (default=True, action='store_false' for `archive_todo`)
  - Wrap TODO archival in `if archive_todo:` block
  - Remove `--summary` and `--version` as required when `--no-archive`
  - Update docstring and help text

- [ ] T005 [P] Add `--issue` flag to `.claude/skills/speckit-author/scripts/create_specifications.py`
  - Add argparse argument: `--issue` (optional int)
  - Remove `--todo-file` argument (deprecated)
  - Store issue number in spec metadata
  - Update docstring and help text

---

## Phase 3.3: Rewrite Slash Commands

- [ ] T006 Rewrite `/1_specify` in `.claude/commands/workflow/1_specify.md`
  - Remove reference to `.specify/scripts/bash/create-new-feature.sh`
  - Add invocations for:
    1. `tech-stack-adapter/scripts/detect_stack.py` (if not cached)
    2. `gh issue create` (optional)
    3. `bmad-planner/scripts/create_planning.py`
    4. `git-workflow-manager/scripts/create_worktree.py --no-todo`
    5. `agentdb-state-manager/scripts/record_sync.py --pattern phase_1_specify`
  - Update prerequisites and outputs
  - See contract: `contracts/slash-commands.md`

- [ ] T007 Rewrite `/2_plan` in `.claude/commands/workflow/2_plan.md`
  - Remove reference to `.specify/scripts/bash/setup-plan.sh`
  - Add invocations for:
    1. `speckit-author/scripts/create_specifications.py --issue`
    2. `agentdb-state-manager/scripts/record_sync.py --pattern phase_2_plan`
  - Add precondition: must be in worktree
  - Update prerequisites and outputs
  - See contract: `contracts/slash-commands.md`

- [ ] T008 Rewrite `/3_tasks` in `.claude/commands/workflow/3_tasks.md`
  - Remove reference to `.specify/scripts/bash/check-task-prerequisites.sh`
  - Add validation: check `specs/*/plan.md` has ## Tasks section
  - Add invocation for:
    1. `agentdb-state-manager/scripts/record_sync.py --pattern phase_3_tasks`
  - Update prerequisites and outputs
  - See contract: `contracts/slash-commands.md`

- [ ] T009 Update `/4_implement` in `.claude/commands/workflow/4_implement.md`
  - Add invocation for:
    1. `agentdb-state-manager/scripts/record_sync.py --pattern phase_4_implement`
  - Keep existing TodoWrite and quality-enforcer invocations
  - Update outputs to mention AgentDB state

- [ ] T010 Update `/5_integrate` in `.claude/commands/workflow/5_integrate.md`
  - Add invocation for:
    1. `git-workflow-manager/scripts/cleanup_feature.py --no-archive`
    2. `gh issue close` (after PR merge)
    3. `agentdb-state-manager/scripts/record_sync.py --pattern phase_5_integrate`
  - Remove `archive-todo` step reference
  - Update outputs to mention cleanup without archival

- [ ] T011 Update `/6_release` in `.claude/commands/workflow/6_release.md`
  - Add invocation for:
    1. `agentdb-state-manager/scripts/record_sync.py --pattern phase_6_release`
  - Keep existing release_workflow.py invocations
  - Update outputs to mention AgentDB state

- [ ] T012 Update `/7_backmerge` in `.claude/commands/workflow/7_backmerge.md`
  - Add invocation for:
    1. `agentdb-state-manager/scripts/record_sync.py --pattern phase_7_backmerge`
  - Keep existing backmerge_workflow.py invocations
  - Update outputs to mention AgentDB state

---

## Phase 3.4: Update /workflow/all Orchestrator

- [ ] T013 Update `/workflow/all` in `.claude/commands/workflow/all.md`
  - Add state detection using `query_workflow_state.py`
  - Update MODE=default to query AgentDB for current phase
  - Update MODE=continue to check AgentDB state
  - Add AgentDB initialization check at start

---

## Phase 3.5: Archive .specify/ Directory

- [ ] T014 Create `.specify/ARCHIVED/` directory
  ```bash
  mkdir -p .specify/ARCHIVED
  ```

- [ ] T015 Move `.specify/scripts/` to `.specify/ARCHIVED/scripts/`
  ```bash
  mv .specify/scripts .specify/ARCHIVED/
  ```

- [ ] T016 Move `.specify/templates/` to `.specify/ARCHIVED/templates/`
  ```bash
  mv .specify/templates .specify/ARCHIVED/
  ```

- [ ] T017 Move `.specify/memory/` to `.specify/ARCHIVED/memory/`
  ```bash
  mv .specify/memory .specify/ARCHIVED/
  ```

- [ ] T018 Create `.specify/README.md` explaining deprecation
  - Note: "This directory is deprecated. See .claude/skills/ for workflow automation."
  - Link to: workflow-orchestrator, bmad-planner, speckit-author

---

## Phase 3.6: Deprecate workflow-utilities Scripts

- [ ] T019 [P] Move `sync_todo_to_db.py` to `ARCHIVED/` in workflow-utilities
  ```bash
  mv .claude/skills/workflow-utilities/scripts/sync_todo_to_db.py \
     .claude/skills/workflow-utilities/ARCHIVED/
  ```

- [ ] T020 [P] Move `todo_updater.py` to `ARCHIVED/` in workflow-utilities
  ```bash
  mv .claude/skills/workflow-utilities/scripts/todo_updater.py \
     .claude/skills/workflow-utilities/ARCHIVED/
  ```

- [ ] T021 [P] Move `workflow_archiver.py` to `ARCHIVED/` in workflow-utilities
  ```bash
  mv .claude/skills/workflow-utilities/scripts/workflow_archiver.py \
     .claude/skills/workflow-utilities/ARCHIVED/
  ```

- [ ] T022 [P] Move `workflow_registrar.py` to `ARCHIVED/` in workflow-utilities
  ```bash
  mv .claude/skills/workflow-utilities/scripts/workflow_registrar.py \
     .claude/skills/workflow-utilities/ARCHIVED/
  ```

- [ ] T023 [P] Move `sync_manifest.py` to `ARCHIVED/` in workflow-utilities
  ```bash
  mv .claude/skills/workflow-utilities/scripts/sync_manifest.py \
     .claude/skills/workflow-utilities/ARCHIVED/
  ```

---

## Phase 3.7: Update Documentation

- [ ] T024 Update `CLAUDE.md` to reflect new workflow
  - Update slash command descriptions
  - Remove references to .specify/
  - Add note about AgentDB state tracking
  - Update PR workflow section (no archive-todo step)

- [ ] T025 Update `.claude/skills/workflow-orchestrator/CLAUDE.md`
  - Add references to new AgentDB scripts
  - Update skill loading logic description
  - Remove TODO file references

- [ ] T026 Update `.claude/skills/agentdb-state-manager/CLAUDE.md`
  - Add documentation for `record_sync.py`
  - Add documentation for `query_workflow_state.py`
  - Update workflow integration section

---

## Phase 3.8: Verification

- [ ] T027 [P] Run quality gates to verify all pass
  ```bash
  podman-compose run --rm dev python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
  ```
  - Expected: 5/5 gates pass

- [ ] T028 [P] Verify no .specify/ references in slash commands
  ```bash
  grep -r "\.specify/" .claude/commands/workflow/ && echo "FAIL" || echo "PASS"
  ```
  - Expected: No matches

---

## Dependencies

```
T001, T002 (AgentDB scripts) ─┬─→ T006-T013 (slash commands)
T003, T004, T005 (flags) ─────┘
                              │
                              ↓
T006-T013 (slash commands) ───→ T014-T018 (.specify/ archive)
                              │
                              ↓
T014-T018 (.specify/) ────────→ T019-T023 (deprecate scripts)
                              │
                              ↓
T019-T023 (deprecate) ────────→ T024-T026 (documentation)
                              │
                              ↓
T024-T026 (docs) ─────────────→ T027-T028 (verification)

Parallel groups:
- T001, T002 can run together (different files)
- T003, T004, T005 can run together (different files)
- T019-T023 can run together (different files, same action)
- T027, T028 can run together (verification)
```

---

## Parallel Execution Examples

### Phase 3.1-3.2: Scripts in parallel
```bash
# Launch T001-T005 together (5 agents):
# Each agent works on one script file independently
```

### Phase 3.6: Deprecation in parallel
```bash
# Launch T019-T023 together (5 agents):
# Each agent moves one script to ARCHIVED/
```

### Phase 3.8: Verification in parallel
```bash
# Launch T027-T028 together (2 agents):
# Agent 1: Run quality gates
# Agent 2: Grep for .specify/ references
```

---

## Validation Checklist

- [x] All contracts have corresponding implementation tasks
- [x] All entities have related tasks
- [x] Script tasks before slash command tasks (dependencies)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Verification tasks at end

---

## Notes

- Total: 28 tasks
- Parallel opportunities: T001-T002, T003-T005, T019-T023, T027-T028
- Sequential phases: Scripts → Slash Commands → Archive → Deprecate → Docs → Verify
- Estimated effort: Medium (mostly slash command rewrites, minimal new code)
- Risk: Low (graceful deprecation, backward compatible flags)
