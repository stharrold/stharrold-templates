# Implementation Plan: Shared AgentDB Symlink

**Type:** feature
**Slug:** shared-agentdb-symlink
**Date:** 2025-11-30

## Task Breakdown

### Phase 1: Core Symlink Implementation

#### Task impl_001: Add get_main_repo_path() to worktree_context.py

**Priority:** High

**Files:**
- `.claude/skills/workflow-utilities/scripts/worktree_context.py`
- `tests/skills/test_worktree_context.py`

**Description:**
Add a function to detect and return the main repository path from any worktree.

**Steps:**
1. Add `get_main_repo_path()` function using `git rev-parse --git-dir`
2. Handle both main repo and worktree cases
3. Add unit tests for both scenarios

**Acceptance Criteria:**
- [ ] Function returns main repo path when called from worktree
- [ ] Function returns current repo path when called from main repo
- [ ] Unit tests cover both cases

**Verification:**
```bash
uv run pytest tests/skills/test_worktree_context.py -v -k "main_repo"
```

**Dependencies:**
- None

---

#### Task impl_002: Add setup_agentdb_symlink() function

**Priority:** High

**Files:**
- `.claude/skills/git-workflow-manager/scripts/create_worktree.py`
- `tests/skills/test_create_worktree.py`

**Description:**
Add function to create symlink from worktree's agentdb.duckdb to main repo's database.

**Steps:**
1. Add `setup_agentdb_symlink(worktree_path, main_repo_path)` function
2. Use relative symlinks for portability
3. Handle case where main DB doesn't exist yet
4. Make symlink creation idempotent

**Acceptance Criteria:**
- [ ] Symlink created correctly pointing to main repo database
- [ ] Uses relative path for portability
- [ ] Creates main DB if it doesn't exist
- [ ] Skips if symlink already exists (idempotent)

**Verification:**
```bash
uv run pytest tests/skills/test_create_worktree.py -v -k "symlink"
```

**Dependencies:**
- impl_001

---

#### Task impl_003: Integrate symlink creation into worktree creation flow

**Priority:** High

**Files:**
- `.claude/skills/git-workflow-manager/scripts/create_worktree.py`

**Description:**
Call `setup_agentdb_symlink()` during worktree creation after `.claude-state/` is created.

**Steps:**
1. Locate the worktree creation flow in `create_worktree()`
2. Add call to `setup_agentdb_symlink()` after state dir creation
3. Add error handling with graceful fallback to isolated DB

**Acceptance Criteria:**
- [ ] New worktrees have symlinked agentdb.duckdb
- [ ] Existing worktree creation flow unchanged except for symlink
- [ ] Graceful fallback if symlink fails

**Verification:**
```bash
# Manual test: Create a test worktree and verify symlink
uv run python .claude/skills/git-workflow-manager/scripts/create_worktree.py feature test-symlink contrib/stharrold --no-todo
ls -la ../stharrold-templates_feature_*_test-symlink/.claude-state/
```

**Dependencies:**
- impl_002

---

### Phase 2: Query Enhancements

#### Task impl_004: Update get_agentdb_path() to resolve symlinks

**Priority:** High

**Files:**
- `.claude/skills/workflow-utilities/scripts/worktree_context.py`

**Description:**
Ensure `get_agentdb_path()` resolves symlinks for proper DuckDB locking.

**Steps:**
1. Add `.resolve()` call to return actual file path
2. Update docstring to document symlink behavior
3. Verify DuckDB connections work through symlink

**Acceptance Criteria:**
- [ ] Function returns resolved (not symlink) path
- [ ] DuckDB can read/write through resolved path
- [ ] File locking works correctly

**Verification:**
```bash
uv run python -c "from worktree_context import get_agentdb_path; print(get_agentdb_path())"
```

**Dependencies:**
- impl_001

---

#### Task impl_005: Enhance query_workflow_state.py output

**Priority:** Medium

**Files:**
- `.claude/skills/agentdb-state-manager/scripts/query_workflow_state.py`

**Description:**
Update query output to clearly show which worktree each record came from.

**Steps:**
1. Add worktree_id to query output
2. Format output to show `[worktree_id]` prefix
3. Show "main" for records with null worktree_id

**Acceptance Criteria:**
- [ ] Output shows worktree source for each record
- [ ] Null worktree_id displayed as "main"
- [ ] Output is human-readable

**Verification:**
```bash
uv run python .claude/skills/agentdb-state-manager/scripts/query_workflow_state.py
```

**Dependencies:**
- impl_004

---

### Phase 3: Testing

#### Task test_001: Unit tests for symlink creation

**Priority:** High

**Files:**
- `tests/skills/test_create_worktree_symlink.py`

**Description:**
Comprehensive unit tests for symlink functionality.

**Steps:**
1. Create test file with fixtures using tempfile
2. Test symlink creation
3. Test idempotent behavior
4. Test shared writes through symlink
5. Test error handling

**Acceptance Criteria:**
- [ ] Test symlink is created correctly
- [ ] Test relative path is used
- [ ] Test writes through symlink visible in main DB
- [ ] Test graceful handling of missing main repo

**Verification:**
```bash
uv run pytest tests/skills/test_create_worktree_symlink.py -v
```

**Dependencies:**
- impl_002

---

#### Task test_002: Integration test for worktree with symlink

**Priority:** High

**Files:**
- `tests/integration/test_worktree_symlink_integration.py`

**Description:**
End-to-end test of worktree creation with AgentDB symlink.

**Steps:**
1. Create test that runs full worktree creation
2. Verify symlink exists and points correctly
3. Test workflow state written from worktree visible in main repo
4. Clean up test worktree

**Acceptance Criteria:**
- [ ] Full worktree creation tested
- [ ] Symlink verified
- [ ] Cross-session visibility tested

**Verification:**
```bash
uv run pytest tests/integration/test_worktree_symlink_integration.py -v
```

**Dependencies:**
- impl_003, test_001

---

### Phase 4: Quality & Documentation

#### Task qa_001: Run quality gates

**Priority:** High

**Files:**
- All modified files

**Description:**
Run all quality gates and fix any issues.

**Steps:**
1. Run ruff check and fix linting issues
2. Run pytest with coverage
3. Verify ≥80% coverage on new code
4. Run full quality gates script

**Acceptance Criteria:**
- [ ] All 5 quality gates pass
- [ ] Coverage ≥80%
- [ ] No linting errors

**Verification:**
```bash
uv run python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
```

**Dependencies:**
- test_001, test_002

---

## Task Summary

| Task ID | Name | Priority | Dependencies |
|---------|------|----------|--------------|
| impl_001 | Add get_main_repo_path() | High | None |
| impl_002 | Add setup_agentdb_symlink() | High | impl_001 |
| impl_003 | Integrate into worktree creation | High | impl_002 |
| impl_004 | Update get_agentdb_path() | High | impl_001 |
| impl_005 | Enhance query output | Medium | impl_004 |
| test_001 | Unit tests for symlink | High | impl_002 |
| test_002 | Integration test | High | impl_003, test_001 |
| qa_001 | Run quality gates | High | test_001, test_002 |

## Task Dependencies Graph

```
impl_001 ─┬─> impl_002 ─> impl_003 ─┐
          │                          │
          └─> impl_004 ─> impl_005   │
                                     ├─> test_002 ─> qa_001
test_001 ────────────────────────────┘
```

## Critical Path

1. impl_001 (get_main_repo_path)
2. impl_002 (setup_agentdb_symlink)
3. impl_003 (integrate into create_worktree)
4. test_001 (unit tests) - can parallel with impl_003
5. test_002 (integration tests)
6. qa_001 (quality gates)

## Parallel Work Opportunities

- impl_004 can be done in parallel with impl_002/impl_003
- test_001 can be started after impl_002, in parallel with impl_003
- impl_005 can be done in parallel with testing phase

## Quality Checklist

Before considering this feature complete:

- [ ] All tasks marked as complete
- [ ] Test coverage ≥ 80%
- [ ] All tests passing (unit + integration)
- [ ] Linting clean (`uv run ruff check .`)
- [ ] New worktrees have symlinked AgentDB
- [ ] Cross-session visibility verified manually
- [ ] Code reviewed

## Risk Assessment

### Low Risk

- **impl_001-003**: Straightforward file operations
  - Well-understood Python standard library

### Medium Risk

- **DuckDB concurrent access**: Multiple processes accessing same DB
  - Mitigation: DuckDB handles this natively with file locks
  - Test with concurrent writes in integration tests

- **Cross-platform symlinks**: Windows requires special permissions
  - Mitigation: Document Windows limitation; most development on Unix

## Implementation Notes

### Key Design Decisions

1. **Relative symlinks**: More portable than absolute paths
2. **Graceful fallback**: If symlink fails, fall back to isolated DB
3. **No schema changes**: Reuse existing worktree_id column

### Common Pitfalls

- Don't use absolute paths for symlinks (breaks if repo moves)
- Always resolve symlink before DuckDB connect (for proper locking)
- Don't assume main repo DB exists (create if needed)

### Resources

- [DuckDB Concurrency](https://duckdb.org/docs/connect/concurrency)
- [Python pathlib symlink_to](https://docs.python.org/3/library/pathlib.html#pathlib.Path.symlink_to)
- Planning: `planning/shared-agentdb-symlink/`
