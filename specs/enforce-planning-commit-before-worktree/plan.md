# Implementation Plan: Enforce Planning Commit Before Worktree

**Date:** 2025-11-30
**Author:** stharrold
**Status:** Draft
**Estimated Effort:** 2-3 hours

## Overview

This plan outlines the implementation steps for adding planning document verification to `create_worktree.py`. The implementation is straightforward as it adds a single verification function called before worktree creation.

## Prerequisites

- [x] Planning documents exist in `planning/enforce-planning-commit-before-worktree/`
- [x] Specification reviewed in `specs/enforce-planning-commit-before-worktree/spec.md`
- [x] Understanding of existing `create_worktree.py` implementation

## Task Breakdown

### Task 1: Implement verify_planning_committed Function

**File:** `.claude/skills/git-workflow-manager/scripts/create_worktree.py`

**Changes:**
1. Add new function `verify_planning_committed(slug: str) -> None`
2. Implement Check 1: Planning directory exists
3. Implement Check 2: No uncommitted changes (git status --porcelain)
4. Implement Check 3: Branch is pushed (git rev-list comparison)
5. Each check raises `ValueError` with actionable error message

**Implementation notes:**
- Function should be pure (no side effects except git fetch)
- Error messages must include exact commands for resolution
- Handle edge case where remote branch doesn't exist

**Estimated time:** 30 minutes

---

### Task 2: Integrate Verification into create_worktree

**File:** `.claude/skills/git-workflow-manager/scripts/create_worktree.py`

**Changes:**
1. Call `verify_planning_committed(slug)` after input validation
2. Only call for `workflow_type == "feature"`
3. Skip for release and hotfix workflow types

**Integration point (after line ~52):**
```python
# After: if not slug or not slug.replace("-", "").replace("_", "").isalnum():
#     raise ValueError(...)

# NEW: Verify planning committed (feature only)
if workflow_type == "feature":
    verify_planning_committed(slug)

# Before: timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
```

**Estimated time:** 10 minutes

---

### Task 3: Write Unit Tests

**File:** `tests/skills/git-workflow-manager/test_create_worktree.py`

**Test cases:**
1. `test_verify_planning_dir_exists_passes` - Planning dir exists → passes
2. `test_verify_planning_dir_missing_fails` - Planning dir missing → ValueError
3. `test_verify_uncommitted_changes_fails` - Uncommitted changes → ValueError
4. `test_verify_unpushed_commits_fails` - Local ahead of remote → ValueError
5. `test_feature_worktree_runs_verification` - Feature type triggers verification
6. `test_release_worktree_skips_verification` - Release type skips verification
7. `test_hotfix_worktree_skips_verification` - Hotfix type skips verification

**Test fixtures needed:**
- `tmp_git_repo` - Temporary git repository with planning directory
- `tmp_git_repo_with_remote` - Temporary repo with mock remote

**Estimated time:** 45 minutes

---

### Task 4: Write Integration Test

**File:** `tests/skills/git-workflow-manager/test_create_worktree_integration.py`

**Test cases:**
1. `test_full_workflow_with_committed_planning` - End-to-end success path
2. `test_full_workflow_fails_uncommitted_planning` - End-to-end failure path

**Estimated time:** 30 minutes

---

### Task 5: Update Documentation

**Files:**
1. `.claude/skills/git-workflow-manager/CLAUDE.md` - Add verification details to create_worktree.py section
2. `.claude/skills/git-workflow-manager/CHANGELOG.md` - Add entry for new feature

**Estimated time:** 15 minutes

---

### Task 6: Run Quality Gates

**Commands:**
```bash
# Run tests with coverage
uv run pytest tests/skills/git-workflow-manager/ -v --cov

# Run linting
uv run ruff check .

# Run full quality gates
uv run python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
```

**Estimated time:** 15 minutes

---

## Implementation Order

```
Task 1 (verify_planning_committed)
    ↓
Task 2 (integrate into create_worktree)
    ↓
Task 3 (unit tests) ──┬──> Task 6 (quality gates)
    ↓                 │
Task 4 (integration)──┘
    ↓
Task 5 (documentation)
```

## Success Criteria

- [ ] All 7 unit tests pass
- [ ] All 2 integration tests pass
- [ ] Coverage ≥80% for create_worktree.py
- [ ] Ruff linting clean
- [ ] All 5 quality gates pass
- [ ] Documentation updated

## Rollback Plan

If issues arise:
1. Verification is isolated to one function - easy to disable
2. Feature-only scope limits blast radius
3. Can add `--skip-planning-check` flag if needed (not recommended)

## Notes

- Implementation is backward-compatible (release/hotfix unchanged)
- Error messages prioritize user experience with exact commands
- Single git fetch per worktree creation is acceptable overhead (~1s)
