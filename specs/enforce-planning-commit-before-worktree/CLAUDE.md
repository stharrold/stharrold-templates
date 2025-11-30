---
type: claude-context
directory: specs/enforce-planning-commit-before-worktree
purpose: Specifications for enforcing planning document commit before worktree creation
parent: specs/CLAUDE.md
sibling_readme: README.md
children: []
---

# Claude Code Context: enforce-planning-commit-before-worktree Specifications

## Purpose

Technical specifications and implementation plan for the enforce-planning-commit-before-worktree feature. This feature ensures BMAD planning documents are committed and pushed before a feature worktree can be created.

## Directory Structure

```
specs/enforce-planning-commit-before-worktree/
├── spec.md           # Technical specification
├── plan.md           # Implementation plan with tasks
├── CLAUDE.md         # This file
└── README.md         # Human-readable overview
```

## Key Files

**spec.md:**
- Problem statement and solution design
- Technical implementation details
- Function signatures and logic
- Error handling patterns
- Testing strategy
- Acceptance criteria

**plan.md:**
- Task breakdown with estimates
- Implementation order
- Success criteria
- Rollback plan

## Implementation Summary

Add verification to `create_worktree.py` that checks:
1. `planning/{slug}/` directory exists
2. No uncommitted changes in planning directory
3. Local branch is pushed to remote

Only applies to feature worktrees (not release/hotfix).

## Related Documentation

- **Planning:** [../../planning/enforce-planning-commit-before-worktree/](../../planning/enforce-planning-commit-before-worktree/CLAUDE.md)
- **Target File:** [../../.claude/skills/git-workflow-manager/scripts/create_worktree.py](../../.claude/skills/git-workflow-manager/scripts/create_worktree.py)

## Related Skills

- git-workflow-manager (target skill for changes)
- workflow-orchestrator (uses create_worktree.py)
- quality-enforcer (validates implementation)
