---
type: directory-documentation
directory: .claude/skills/git-workflow-manager
title: Git Workflow Manager
sibling_claude: CLAUDE.md
parent: null
children:
  - ARCHIVED/README.md
---

# Git Workflow Manager

> **Automated git operations for the git-flow + GitHub-flow hybrid workflow with worktrees**

The Git Workflow Manager handles all git automation in the workflow system: branch creation, worktree management, commits, PRs, semantic versioning, and daily rebase operations. It implements a git-flow + GitHub-flow hybrid with isolated worktree development, designed for multi-contributor teams.

## Features

- ✅ **Automated worktree creation** - Isolated development environments per feature/release/hotfix
- ✅ **Semantic versioning** - Automatic version calculation from code changes (MAJOR.MINOR.PATCH)
- ✅ **GitHub integration** - PR creation and management via `gh` CLI
- ✅ **Timestamp-based naming** - Avoid shell escaping issues with compact ISO8601 format

## Quick Start

### Prerequisites

```bash
# Ensure you're in a git repository
git status

# Have GitHub CLI installed (for PR creation)
gh --version
```

### Create Feature Worktree

```bash
# From main repo on contrib/<gh-user> branch
python .claude/skills/git-workflow-manager/scripts/create_worktree.py \
  feature auth-system contrib/stharrold

# Output:
# ✓ State directory: ../german_feature_auth-system/.claude-state
# ✓ Worktree created: ../german_feature_auth-system
# ✓ Branch: feature/20251103T143000Z_auth-system
# {"worktree_path": "...", "branch_name": "...", "state_dir": "..."}
#
# Next steps:
#   cd ../german_feature_auth-system
#   python .claude/skills/speckit-author/scripts/create_specifications.py \
#     feature auth-system stharrold --todo-file ../TODO_feature_*.md
```

### Calculate Semantic Version

```bash
# From feature worktree (after implementation complete)
python .claude/skills/git-workflow-manager/scripts/semantic_version.py \
  develop v1.5.0

# Output: 1.6.0
#
# Logic:
# - Breaking changes (API changes, removed features) → MAJOR bump
# - New features (new files, new endpoints) → MINOR bump
# - Bug fixes, refactoring, docs, tests → PATCH bump
```

## Scripts Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `create_worktree.py` | Create isolated worktree for feature/release/hotfix | After planning |
| `cleanup_feature.py` | Archive TODO, remove worktree, print branch-delete commands | After PR merges |
| `semantic_version.py` | Calculate semantic version (shim → release_lib.semver) | Before release |

## Branch Structure

```
main                           ← Production (tagged vX.Y.Z)
  ↑                             ↑
release/vX.Y.Z                hotfix/vX.Y.Z-hotfix.N (worktree)
  ↑
develop                        ← Integration branch
  ↑
contrib/<gh-user>             ← Personal contribution (e.g., contrib/stharrold)
  ↑
feature/<timestamp>_<slug>    ← Isolated feature (worktree)
```

### Workflow Patterns

**Feature workflow:**
1. Main repo (contrib branch) → BMAD planning
2. Create feature worktree → SpecKit + Implementation
3. Quality gates → PR (feature → contrib)
4. Merge in GitHub UI → PR (contrib → develop)

**Release workflow (via release-pilot skill + gh CLI):**
1. Develop ready → create `release/vN.N.N` branch
2. Final QA + docs → PR (release → main), tag, backmerge

**Hotfix workflow:**
1. Bug in production → Create hotfix worktree from main
2. Minimal fix → PR (hotfix → main)
3. Tag on main → Back-merge to develop

## Examples

### Create Hotfix Worktree

```bash
# Hotfix for production bug
python .claude/skills/git-workflow-manager/scripts/create_worktree.py \
  hotfix security-patch main

# Output:
# ✓ Created worktree: ../german_hotfix_security-patch
# ✓ Created branch: hotfix/20251103T150000Z_security-patch
# ✓ Created TODO file: TODO_hotfix_20251103T150000Z_security-patch.md
```

### Create Release Worktree

```bash
# Release workflow
python .claude/skills/git-workflow-manager/scripts/create_worktree.py \
  release v1.6.0 develop

# Output:
# ✓ Created worktree: ../german_release_v1.6.0
# ✓ Created branch: release/v1.6.0
# ✓ Created TODO file: TODO_release_20251103T160000Z_v1.6.0.md
```

### Timestamp Format

All branches use compact ISO8601 timestamps (`YYYYMMDDTHHMMSSZ`):

```bash
# Feature branch name
feature/20251103T143000Z_auth-system

# Rationale:
# - No colons/hyphens (avoids shell escaping issues)
# - Sortable chronologically
# - Parseable by underscores
# - Remains intact when parsed by scripts
```

### Semantic Versioning Examples

**Scenario 1: Bug fix**
```bash
# Changed: tests/test_auth.py (fixed test bug)
python .claude/skills/git-workflow-manager/scripts/semantic_version.py \
  develop v1.5.0

# Output: 1.5.1  (PATCH bump)
```

**Scenario 2: New feature**
```bash
# Changed: src/auth/oauth.py (new file - OAuth support)
python .claude/skills/git-workflow-manager/scripts/semantic_version.py \
  develop v1.5.1

# Output: 1.6.0  (MINOR bump)
```

**Scenario 3: Breaking change**
```bash
# Changed: src/api/routes.py (removed /old-endpoint)
python .claude/skills/git-workflow-manager/scripts/semantic_version.py \
  develop v1.6.0

# Output: 2.0.0  (MAJOR bump)
```

## Workflow Integration

### Phase 2: Implementation

```bash
# Create feature worktree after BMAD planning
cd ~/Code/german  # main repo
git checkout contrib/stharrold

python .claude/skills/git-workflow-manager/scripts/create_worktree.py \
  feature auth-system contrib/stharrold

# Move to worktree
cd ../german_feature_auth-system

# Create specifications
python .claude/skills/speckit-author/scripts/create_specifications.py \
  feature auth-system stharrold --todo-file ../TODO_feature_*.md

# Implement feature...
```

### Phase 3: Quality

```bash
# In feature worktree after implementation
python .claude/skills/quality-enforcer/scripts/run_quality_gates.py

# If passed, calculate version
python .claude/skills/git-workflow-manager/scripts/semantic_version.py \
  develop v1.5.0

# Output: 1.6.0
```

### Phase 4: Integration

```bash
# Create PR: feature → contrib (done via gh CLI)
gh pr create --base contrib/<user> --head <feature-branch> --title "feat: ..."

# After merge, rebase contrib onto develop
git fetch origin && git rebase origin/develop contrib/<user>

# Create PR: contrib → develop
gh pr create --base develop --head contrib/<user> --title "feat: ..."
```

### Phase 5: Release

See the `release-pilot` user skill and the `/workflow:s3-release` and
`/workflow:s4-backmerge` slash commands — release management now uses
`release_lib` helpers + `gh` CLI directly (scripts removed in #242).

## VCS Provider Support

Uses GitHub via `gh` CLI:

```bash
# GitHub repository
# Uses: gh pr create, gh pr view, gh issue create
gh auth status  # Must be authenticated
```

## Constants and Rationale

| Constant | Value | Rationale |
|----------|-------|-----------|
| TIMESTAMP_FORMAT | `YYYYMMDDTHHMMSSZ` | No colons/hyphens, sortable, parseable |
| VALID_WORKFLOW_TYPES | feature, release, hotfix | Covers all workflow phases |

## Troubleshooting

### Error: "Not in main repository"

```bash
✗ Error: Must run from main repository (not worktree)

Fix: cd to main repository before running script
```

### Error: "Branch already exists"

```bash
✗ Error: Branch feature/20251103T143000Z_auth already exists

Fix: Use different slug or delete existing branch:
  git branch -D feature/20251103T143000Z_auth
  git push origin --delete feature/20251103T143000Z_auth
```

## Related Documentation

- **[SKILL.md](SKILL.md)** - Complete technical documentation
- **[CLAUDE.md](CLAUDE.md)** - Claude Code integration guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

**See also:**
- [WORKFLOW.md](../../WORKFLOW.md) - Complete 6-phase workflow guide
- [workflow-utilities](../workflow-utilities/) - Shared utilities
- [quality-enforcer](../quality-enforcer/) - Quality gates

## Contributing

This skill is part of the workflow system. To update:

1. Modify scripts in `scripts/`
2. Update version in `SKILL.md` frontmatter
3. Document changes in `CHANGELOG.md`
4. Run validation: `python .claude/skills/workflow-utilities/scripts/validate_versions.py`
5. Sync documentation: `python .claude/skills/workflow-utilities/scripts/sync_skill_docs.py git-workflow-manager <version>`

## License

Part of the german repository workflow system.
