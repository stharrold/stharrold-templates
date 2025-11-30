# Technical Specification: Enforce Planning Commit Before Worktree

**Date:** 2025-11-30
**Author:** stharrold
**Status:** Draft
**Version:** 1.0.0

## Overview

This specification defines the implementation of planning document verification in `create_worktree.py`. The feature ensures that BMAD planning documents (`planning/{slug}/`) are committed and pushed before a feature worktree can be created, preventing worktrees that don't contain planning context.

## Problem Statement

Currently, `/1_specify` creates planning documents and then creates a git worktree, but there is no enforcement that planning documents are committed and pushed before the worktree is created. This can lead to:

1. Worktrees that don't contain the planning documents (they're only in uncommitted changes)
2. Lost planning context when the worktree is created from a base branch that doesn't have the planning docs
3. Confusion during `/2_plan` when `planning/{slug}/` is expected but missing

## Solution Design

### Approach

Add a verification step to `create_worktree.py` that runs **before** worktree creation for feature workflows. The verification performs three checks:

1. **Planning directory exists** - `planning/{slug}/` must exist in the repository
2. **No uncommitted changes** - Planning directory must have no staged or unstaged changes
3. **Branch is pushed** - Local branch must not be ahead of remote (changes are pushed)

### Scope

- **In scope:** Feature worktrees only (workflow_type == "feature")
- **Out of scope:** Release and hotfix worktrees (no planning docs required)

## Technical Design

### Function Signature

```python
def verify_planning_committed(slug: str) -> None:
    """
    Verify planning documents are committed and pushed before worktree creation.

    Args:
        slug: Feature slug (e.g., 'auth-system')

    Raises:
        ValueError: If planning directory doesn't exist
        ValueError: If uncommitted changes detected in planning directory
        ValueError: If local branch is ahead of remote

    Note:
        Only called for feature worktrees, not release/hotfix.
    """
```

### Implementation Location

File: `.claude/skills/git-workflow-manager/scripts/create_worktree.py`

Insert verification call after input validation, before worktree creation:

```python
def create_worktree(workflow_type, slug, base_branch, create_todo=False):
    # ... existing input validation ...

    # NEW: Verify planning committed (feature only)
    if workflow_type == "feature":
        verify_planning_committed(slug)

    # ... existing worktree creation ...
```

### Verification Logic

#### Check 1: Planning Directory Exists

```python
planning_dir = repo_root / "planning" / slug
if not planning_dir.exists():
    raise ValueError(
        f"Planning directory not found: planning/{slug}/\n"
        f"Resolution: Run /1_specify to create planning documents first.\n"
        f"Expected files:\n"
        f"  - planning/{slug}/requirements.md\n"
        f"  - planning/{slug}/architecture.md\n"
        f"  - planning/{slug}/epics.md"
    )
```

#### Check 2: No Uncommitted Changes

```python
# Check for uncommitted changes in planning directory
result = subprocess.run(
    ["git", "status", "--porcelain", f"planning/{slug}/"],
    capture_output=True,
    text=True,
    check=True
)
if result.stdout.strip():
    raise ValueError(
        f"Uncommitted changes detected in planning/{slug}/\n"
        f"Changed files:\n{result.stdout}\n"
        f"Resolution: Commit and push planning documents first:\n"
        f"  git add planning/{slug}/\n"
        f"  git commit -m 'docs(planning): add planning for {slug}'\n"
        f"  git push"
    )
```

#### Check 3: Branch is Pushed

```python
# Fetch remote to ensure we have latest
subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)

# Get current branch
result = subprocess.run(
    ["git", "branch", "--show-current"],
    capture_output=True,
    text=True,
    check=True
)
current_branch = result.stdout.strip()

# Check if local is ahead of remote
result = subprocess.run(
    ["git", "rev-list", "--count", f"origin/{current_branch}..HEAD"],
    capture_output=True,
    text=True
)
if result.returncode == 0 and int(result.stdout.strip()) > 0:
    ahead_count = result.stdout.strip()
    raise ValueError(
        f"Local branch is {ahead_count} commit(s) ahead of remote.\n"
        f"Resolution: Push your changes first:\n"
        f"  git push origin {current_branch}"
    )
```

### Error Messages

All error messages follow this pattern:
1. Clear description of what failed
2. Specific details (file paths, counts)
3. Resolution guidance with exact commands

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Release worktree | Skip verification (no planning docs required) |
| Hotfix worktree | Skip verification (no planning docs required) |
| Planning dir exists but empty | Pass (directory exists, files not required) |
| Remote branch doesn't exist | Pass (can't be ahead of non-existent remote) |
| Working offline | Fetch fails, verification continues with local state only |

## Testing Strategy

### Unit Tests

File: `tests/skills/git-workflow-manager/test_create_worktree.py`

```python
class TestVerifyPlanningCommitted:
    """Tests for verify_planning_committed function."""

    def test_planning_dir_exists_passes(self, tmp_git_repo):
        """Should pass when planning directory exists."""

    def test_planning_dir_missing_fails(self, tmp_git_repo):
        """Should fail with clear error when planning directory missing."""

    def test_uncommitted_changes_fails(self, tmp_git_repo):
        """Should fail when planning directory has uncommitted changes."""

    def test_unpushed_commits_fails(self, tmp_git_repo):
        """Should fail when local branch is ahead of remote."""

    def test_feature_worktree_runs_verification(self, tmp_git_repo):
        """Should run verification for feature worktrees."""

    def test_release_worktree_skips_verification(self, tmp_git_repo):
        """Should skip verification for release worktrees."""

    def test_hotfix_worktree_skips_verification(self, tmp_git_repo):
        """Should skip verification for hotfix worktrees."""
```

### Integration Tests

File: `tests/skills/git-workflow-manager/test_create_worktree_integration.py`

```python
class TestCreateWorktreeWithPlanningVerification:
    """Integration tests for worktree creation with planning verification."""

    def test_full_workflow_with_planning(self, tmp_git_repo_with_remote):
        """Should create worktree when planning docs committed and pushed."""

    def test_full_workflow_fails_without_planning(self, tmp_git_repo_with_remote):
        """Should fail worktree creation when planning docs missing."""
```

## Acceptance Criteria

- [ ] FR-001: `create_worktree.py` checks for `planning/{slug}/` directory for feature worktrees
- [ ] FR-001: Returns clear error message if directory does not exist
- [ ] FR-001: Error message includes resolution guidance
- [ ] FR-002: `create_worktree.py` runs `git status` on `planning/{slug}/`
- [ ] FR-002: Returns error if any uncommitted changes detected
- [ ] FR-002: Error message includes git commands to resolve
- [ ] FR-003: `create_worktree.py` compares local and remote branch
- [ ] FR-003: Returns error if local is ahead of remote
- [ ] FR-003: Error message suggests `git push` command
- [ ] FR-004: Checks are skipped for workflow_type release
- [ ] FR-004: Checks are skipped for workflow_type hotfix
- [ ] FR-004: Feature worktrees always run verification

## Dependencies

- Python 3.11+
- Git CLI
- Existing `create_worktree.py` implementation

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing workflows | Feature-only scope limits impact |
| Fetch failures in offline mode | Graceful degradation to local-only checks |
| Performance impact from fetch | Single fetch per worktree creation (~1s) |

## References

- [Requirements](../../planning/enforce-planning-commit-before-worktree/requirements.md)
- [Architecture](../../planning/enforce-planning-commit-before-worktree/architecture.md)
- [Epics](../../planning/enforce-planning-commit-before-worktree/epics.md)
- [create_worktree.py](../../.claude/skills/git-workflow-manager/scripts/create_worktree.py)
