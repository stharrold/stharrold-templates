---
description: Show sN workflow overview and status
---

# /workflow:status - sN workflow

**Current State**: !`python3 .claude/skills/agentdb-state-manager/scripts/query_workflow_state.py`

**Branch**: !`git branch --show-current`

## Commands
- `/workflow:s1-worktree "desc"` - Step 1
- `/workflow:s2-integrate ["branch"]` - Step 2
- `/workflow:s3-release` - Step 3
- `/workflow:s4-backmerge` - Step 4
