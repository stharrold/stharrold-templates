# Tasks: Worktree-Aware Workflow and Skills System

**Input**: Design documents from `/specs/006-make-the-entire/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/

---

## Phase 3.1: Setup

- [ ] T001 Create test directory structure at `tests/contract/` and `tests/integration/`
- [ ] T002 Add `.gemini-state/` to root `.gitignore` (append if not present)

## Phase 3.2: Tests First (TDD) - MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (worktree_context module)

- [ ] T003 [P] Contract test `get_worktree_context()` in `tests/contract/test_worktree_context_contract.py`
  - Test: Returns WorktreeContext dataclass
  - Test: `worktree_root` is valid Path
  - Test: `worktree_id` is 12-char hex string
  - Test: `is_worktree` is boolean
  - Test: Raises RuntimeError when not in git repo

- [ ] T004 [P] Contract test `get_state_dir()` in `tests/contract/test_state_dir_contract.py`
  - Test: Returns Path to `.gemini-state/`
  - Test: Creates directory if not exists
  - Test: Creates `.gitignore` with `*`
  - Test: Creates `.worktree-id` file
  - Test: Idempotent (multiple calls return same path)

- [ ] T005 [P] Contract test `get_worktree_id()` in `tests/contract/test_worktree_id_contract.py`
  - Test: Returns 12-char hex string
  - Test: Stable across multiple calls
  - Test: Different for different paths

- [ ] T006 [P] Contract test `cleanup_orphaned_state()` in `tests/contract/test_cleanup_contract.py`
  - Test: Returns list of Path objects
  - Test: Identifies orphaned directories
  - Test: Does not include active worktrees

### Integration Tests

- [ ] T007 [P] Integration test main repo detection in `tests/integration/test_main_repo_detection.py`
  - Given: Running in main repository
  - When: `get_worktree_context()` called
  - Then: `is_worktree=False`, stable ID

- [ ] T008 [P] Integration test state directory creation in `tests/integration/test_state_directory.py`
  - Given: No `.gemini-state/` exists
  - When: `get_state_dir()` called
  - Then: Directory created with correct files

- [ ] T009 Integration test backward compatibility in `tests/integration/test_backward_compat.py`
  - Given: Main repository (not worktree)
  - When: All worktree functions called
  - Then: Works identically to expected non-worktree behavior

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### WorktreeContext Module (NEW)

- [ ] T010 Implement `WorktreeContext` dataclass in `.gemini/skills/workflow-utilities/scripts/worktree_context.py`
  - Fields: worktree_root, git_common_dir, is_worktree, worktree_id, branch_name
  - Property: state_dir

- [ ] T011 Implement `get_worktree_context()` in `.gemini/skills/workflow-utilities/scripts/worktree_context.py`
  - Run git commands: `rev-parse --show-toplevel`, `--git-common-dir`
  - Check `.git` is file vs directory
  - Generate worktree_id from SHA-256 hash

- [ ] T012 Implement `get_state_dir()` in `.gemini/skills/workflow-utilities/scripts/worktree_context.py`
  - Create `.gemini-state/` directory
  - Write `.gitignore` with `*`
  - Write `.worktree-id` file

- [ ] T013 Implement `get_worktree_id()` in `.gemini/skills/workflow-utilities/scripts/worktree_context.py`
  - Call get_worktree_context()
  - Return worktree_id field

- [ ] T014 Implement `cleanup_orphaned_state()` in `.gemini/skills/workflow-utilities/scripts/worktree_context.py`
  - Run `git worktree list --porcelain`
  - Find `.gemini-state/` in each path
  - Compare against active list

### WorkflowProgress Module (NEW)

- [ ] T015 [P] Implement `workflow_progress.py` in `.gemini/skills/workflow-utilities/scripts/workflow_progress.py`
  - `get_workflow_progress()` - load from workflow.json
  - `update_workflow_progress()` - save to workflow.json
  - Uses `get_state_dir()` for path

## Phase 3.4: Integration Updates

### AgentDB State Manager

- [ ] T016 Update `init_database.py` in `.gemini/skills/agentdb-state-manager/scripts/init_database.py`
  - Import `get_state_dir` from worktree_context
  - Default db_path to `get_state_dir() / "agentdb.duckdb"`
  - Maintain backward compat with explicit path parameter

- [ ] T017 Update `sync_engine.py` in `.gemini/skills/agentdb-state-manager/scripts/sync_engine.py`
  - Import `get_worktree_id, get_state_dir`
  - Auto-detect worktree_id in `__init__`
  - Default db_path to state directory

### Git Workflow Manager

- [ ] T018 Update `worktree_agent_integration.py` in `.gemini/skills/git-workflow-manager/scripts/worktree_agent_integration.py`
  - Import `get_worktree_context`
  - Replace hardcoded pattern detection with worktree_context
  - Update `get_flow_token()` to use branch_name from context

- [ ] T019 Update `create_worktree.py` in `.gemini/skills/git-workflow-manager/scripts/create_worktree.py`
  - Add optional `init_state: bool = True` parameter
  - Create `.gemini-state/` in new worktree if init_state=True

### Quality Enforcer

- [ ] T020 Update `run_quality_gates.py` in `.gemini/skills/quality-enforcer/scripts/run_quality_gates.py`
  - Import `get_worktree_context`
  - Use `worktree_root` for repository root detection
  - Include `worktree_id` in gate results

## Phase 3.5: Polish

- [ ] T021 [P] Add unit tests for edge cases in `tests/unit/test_worktree_context.py`
  - Empty git repository
  - Deeply nested worktree paths
  - Special characters in paths

- [ ] T022 [P] Update GEMINI.md with worktree documentation
  - Add `.gemini-state/` description
  - Document worktree isolation behavior
  - Add troubleshooting for orphaned state

- [ ] T023 Run quickstart.md validation scenarios
  - Test worktree detection
  - Test state directory creation
  - Test concurrent worktree isolation

- [ ] T024 Run quality gates to verify all pass
  - `podman-compose run --rm dev python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py`

---

## Dependencies

```
T001, T002 (setup) → T003-T009 (tests) → T010-T015 (core) → T016-T020 (integration) → T021-T024 (polish)

Detailed:
- T003-T006 can run in parallel [P]
- T007-T008 can run in parallel [P]
- T010 blocks T011-T014 (dataclass needed first)
- T011 blocks T012, T013 (context needed)
- T012 blocks T015 (get_state_dir needed)
- T010-T014 block T016-T020 (core module needed)
- T015 [P] independent of T016-T020
```

## Parallel Execution Examples

### Phase 3.2: Run all contract tests in parallel
```bash
# Launch T003-T006 together (4 agents):
podman-compose run --rm dev pytest tests/contract/test_worktree_context_contract.py -v
podman-compose run --rm dev pytest tests/contract/test_state_dir_contract.py -v
podman-compose run --rm dev pytest tests/contract/test_worktree_id_contract.py -v
podman-compose run --rm dev pytest tests/contract/test_cleanup_contract.py -v
```

### Phase 3.2: Run integration tests in parallel
```bash
# Launch T007-T008 together (2 agents):
podman-compose run --rm dev pytest tests/integration/test_main_repo_detection.py -v
podman-compose run --rm dev pytest tests/integration/test_state_directory.py -v
```

### Phase 3.5: Run polish tasks in parallel
```bash
# Launch T021-T022 together (2 agents):
podman-compose run --rm dev pytest tests/unit/test_worktree_context.py -v
# (T022 is documentation update, no test command)
```

---

## Validation Checklist

- [x] All contracts have corresponding tests (T003-T006)
- [x] All entities have model tasks (T010 WorktreeContext)
- [x] All tests come before implementation (T003-T009 before T010-T015)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

---

## Notes

- Test files should import from relative path: `sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".gemini/skills/workflow-utilities/scripts"))`
- All tests must fail first (TDD red phase) before implementation
- Commit after each task completion
- Use `podman-compose run --rm dev pytest tests/ -v` to run all tests
