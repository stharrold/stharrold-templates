---
description: Show sN workflow overview and status
---

# /workflow:status - sN workflow

**Branch**: !`git branch --show-current`

**Open PRs**: !`gh pr list --state open`

**Worktrees**: !`git worktree list`

## Commands
- `/workflow:s1-worktree "desc"` - Step 1
- `/workflow:s2-integrate ["branch"]` - Step 2
- `/workflow:s3-release` - Step 3
- `/workflow:s4-backmerge` - Step 4
