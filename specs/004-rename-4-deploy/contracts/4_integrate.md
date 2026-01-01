# Contract: /5_integrate Command

**Version**: 1.0.0 | **Date**: 2025-11-22

## Overview

The `/5_integrate` command (renamed from `/4_deploy`) integrates completed feature work into shared branches via PRs.

## Frontmatter Contract

```yaml
---
description: "workflow/4_implement → workflow/5_integrate → workflow/6_release | Integrate feature to develop"
order: 5
prev: /4_implement
next: /6_release
---
```

## Input Contract

**Prerequisites**:
- Current branch: `feature/*` (for finish-feature step)
- Implementation complete (from `/4_implement`)
- All tasks marked complete
- Quality gates passing

## Output Contract

**Artifacts Produced**:
- PR: feature → contrib (created and merged)
- TODO files archived to `ARCHIVED/`
- GEMINI.md synced to AGENTS.md, .github/copilot-instructions.md
- PR: contrib → develop (created)

**State After Execution**:
- Current branch: `contrib/<username>` (editable branch)
- Feature branch: deleted (after PR merge)
- develop branch: contains new feature code

## Workflow Steps

| Step | Command | Input | Output |
|------|---------|-------|--------|
| 1 | `finish-feature` | feature/* branch, passing quality gates | PR feature → contrib |
| 2 | `archive-todo` | TODO*.md files | `ARCHIVED/<timestamp>_TODO*.md` |
| 3 | `sync-agents` | GEMINI.md | AGENTS.md, .github/copilot-instructions.md |
| 4 | `start-develop` | contrib/* branch | PR contrib → develop |

## Error Conditions

| Condition | Error | Recovery |
|-----------|-------|----------|
| Not on feature branch | "Must be on feature branch" | `git checkout feature/*` |
| Quality gates fail | "Quality gates failed" | Fix issues, re-run |
| PR already exists | Warning, continue | Merge existing PR |
| Push fails | "Push failed" | Check remote access |

## Navigation

```
/4_implement → /5_integrate → /6_release
```
