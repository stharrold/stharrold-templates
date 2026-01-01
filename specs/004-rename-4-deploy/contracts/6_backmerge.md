# Contract: /7_backmerge Command

**Version**: 1.0.0 | **Date**: 2025-11-22

## Overview

The `/7_backmerge` command syncs release changes back to development branches: PR release to develop, then rebase contrib on develop.

## Frontmatter Contract

```yaml
---
description: "workflow/6_release → workflow/7_backmerge → (end) | Sync release to develop and contrib"
order: 7
prev: /6_release
next: (none - end of workflow)
---
```

## Input Contract

**Prerequisites**:
- Release PR merged to main (from `/6_release`)
- release/* branch still exists
- Tag created on main

**Arguments**:
- `<version>`: Release version to backmerge (e.g., `v1.6.0`)

## Output Contract

**Artifacts Produced**:
- PR: release → develop (created and merged)
- contrib/* branch rebased on develop
- release/* branch deleted (cleanup)

**State After Execution**:
- Current branch: `contrib/<username>` (editable branch)
- develop branch: contains release changes
- contrib/* branch: rebased on develop, ready for new features
- release/* branch: deleted

## Workflow Steps

| Step | Command | Input | Output |
|------|---------|-------|--------|
| 1 | `pr-develop` | release/* branch | PR release → develop |
| 2 | *(Manual GitHub PR merge)* | PR approval | develop updated |
| 3 | `rebase-contrib` | contrib/* branch | contrib rebased on develop |
| 4 | `cleanup-release` | release/* branch | branch deleted |

## Two-Phase Sync Strategy

### Phase 1: PR release → develop (Merge)

**Why PR (not direct merge)**:
- Requires review for release changes (version bumps, hotfixes)
- Preserves merge commit for traceability
- Handles potential conflicts with develop

**Operation**:
```bash
gh pr create --base develop --head release/<version>
# After approval and merge
```

### Phase 2: Rebase contrib on develop

**Why Rebase (not merge)**:
- Keeps contrib branch linear and clean
- Avoids merge commits in personal branch
- Matches daily_rebase.py pattern

**Operation**:
```bash
git checkout contrib/<username>
git fetch origin
git rebase origin/develop
git push --force-with-lease
```

## Error Conditions

| Condition | Error | Recovery |
|-----------|-------|----------|
| Release branch not found | "Release branch does not exist" | Check version, may already be cleaned up |
| Release not merged to main | "Release not yet merged" | Complete `/6_release` first |
| Rebase conflicts | "Conflicts during rebase" | Resolve manually, continue rebase |
| Force push rejected | "Push rejected" | Check branch protection, use --force-with-lease |

## Conflict Resolution

If rebase conflicts occur:
1. Script pauses with conflict message
2. User resolves conflicts manually
3. User runs `git rebase --continue`
4. Script resumes cleanup

## Navigation

```
/6_release → /7_backmerge → (end)
```

## Workflow Completion

After `/7_backmerge`:
- All branches synced
- Ready for new feature cycle
- Return to `/1_specify` for next feature
