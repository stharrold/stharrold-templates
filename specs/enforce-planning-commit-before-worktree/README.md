# Enforce Planning Commit Before Worktree

## Overview

This specification defines a verification mechanism for `create_worktree.py` that ensures BMAD planning documents are committed and pushed before a feature worktree can be created.

## Problem

The `/1_specify` workflow step creates planning documents and then creates a git worktree, but there is no enforcement that the planning documents are committed and pushed first. This can lead to worktrees that don't contain the planning context.

## Solution

Add three verification checks before feature worktree creation:

1. **Planning directory exists** - `planning/{slug}/` must exist
2. **No uncommitted changes** - Planning directory must be clean
3. **Branch is pushed** - Local commits must be pushed to remote

## Scope

- **Applies to:** Feature worktrees only
- **Skipped for:** Release and hotfix worktrees

## Files

| File | Description |
|------|-------------|
| `spec.md` | Technical specification with implementation details |
| `plan.md` | Implementation plan with task breakdown |
| `CLAUDE.md` | AI navigation context |

## Quick Start

After reviewing these specifications, run `/3_tasks` to validate the task list and proceed to implementation.

## References

- [Planning Documents](../../planning/enforce-planning-commit-before-worktree/)
- [Target Script](../../.claude/skills/git-workflow-manager/scripts/create_worktree.py)
