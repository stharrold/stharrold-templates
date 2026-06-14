---
name: git-workflow-manager
version: 5.1.0
description: |
  Manages git operations: worktree creation, branch management, commits,
  PRs, and semantic versioning (shim over release_lib.semver).

  Use when: Creating branches/worktrees, committing, pushing, versioning

  Triggers: create worktree, commit, push, rebase, version, PR
---

## Quick Reference

```bash
# Create feature worktree
uv run python .claude/skills/git-workflow-manager/scripts/create_worktree.py \
  feature <slug> contrib/<user>

# Semantic version (shim -> release_lib.semver)
uv run python .claude/skills/git-workflow-manager/scripts/semantic_version.py develop <current-version>
```

# Git Workflow Manager

## Purpose

Handles all git operations following git-flow + GitHub-flow hybrid model.

## Branch Structure

```
main                           ← Production (tagged vX.Y.Z)
  ↑
release/vX.Y.Z                ← Release candidate
  ↑
develop                        ← Integration branch
  ↑
contrib/<gh-user>             ← Personal contribution branch
  ↑
feature/<timestamp>_<slug>    ← Isolated feature (worktree)
hotfix/vX.Y.Z-hotfix.N       ← Production hotfix (worktree)
```

### Protected Branch Policy

**CRITICAL:** This skill manages git operations and MUST enforce branch protection rules.

**Protected branches (NEVER delete, NEVER commit directly):**
- `main` - Production branch (tagged releases only)
- `develop` - Integration branch (PR merges only)

**All scripts in this skill comply with:**
1. No direct commits to `main` (except tag operations)
2. No direct commits to `develop`
3. All merges via pull requests (user merges in GitHub UI)

**Script validation:**
- All scripts in `scripts/` directory are validated for compliance
- Test: `tests/test_branch_protection.py` verifies no unintended main/develop commits
- See WORKFLOW.md "Branch Protection Policy" for complete rules

## Scripts

### create_worktree.py

Creates feature/release/hotfix worktree.

```bash
python .claude/skills/git-workflow-manager/scripts/create_worktree.py \
  <feature|release|hotfix> <slug> <base_branch>
```

**Arguments:**
- `workflow_type`: feature, release, or hotfix
- `slug`: Short descriptive name (e.g., 'json-validator')
- `base_branch`: Branch to create from (e.g., 'contrib/username')

### cleanup_feature.py

Archives TODO file, removes worktree, prints branch-deletion commands.

```bash
python .claude/skills/git-workflow-manager/scripts/cleanup_feature.py <slug>
```

### semantic_version.py

Backward-compat shim that re-exports from `release_lib.semver` (issue #240).

```bash
python .claude/skills/git-workflow-manager/scripts/semantic_version.py \
  <base_branch> <current_version>
```

**Version bump logic:**
- **MAJOR**: Breaking changes (API changes, removed features)
- **MINOR**: New features (new files, new functions)
- **PATCH**: Bug fixes, refactoring, docs

Removed in #242 (superseded by `release-pilot` skill + `release_lib`):
`create_release.py`, `tag_release.py`, `backmerge_workflow.py`,
`cleanup_release.py`, `daily_rebase.py`, `generate_work_items_from_pr.py`,
`release_workflow.py`, `pr_workflow.py`.

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Example:**
```
feat(validator): add JSON schema validation endpoint

Implements REST API endpoint for validating JSON against schemas.
Uses jsonschema library for validation logic.

Implements: impl_003
Spec: specs/json-validator/spec.md
Tests: tests/test_validator.py
Coverage: 85%

Refs: TODO_feature_20251022T143022Z_json-validator.md
```

## PR Creation

```bash
# Feature → contrib/<gh-user>
gh pr create \
  --base "contrib/<gh-user>" \
  --head "<feature-branch>" \
  --title "feat: <description>" \
  --body "See TODO_feature_*.md for details"

# After user merges in GitHub UI:
# Contrib → develop
gh pr create \
  --base "develop" \
  --head "contrib/<gh-user>" \
  --title "feat: <description>" \
  --body "Completed feature: <name>"
```

## Integration with Other Skills

Other skills call these scripts:

```python
import subprocess

# Create worktree
result = subprocess.run([
    'python',
    '.claude/skills/git-workflow-manager/scripts/create_worktree.py',
    'feature', 'my-feature', 'contrib/user'
], capture_output=True, text=True)

# Calculate version
result = subprocess.run([
    'python',
    '.claude/skills/git-workflow-manager/scripts/semantic_version.py',
    'develop', 'v1.0.0'
], capture_output=True, text=True)

new_version = result.stdout.strip()
```
