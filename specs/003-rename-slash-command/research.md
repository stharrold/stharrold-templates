# Research: Namespace Slash Commands

**Feature**: 003-rename-slash-command
**Date**: 2025-11-22

## Research Questions

### 1. Claude Code Slash Command Namespace Scoping

**Decision**: Use subdirectory structure `.claude/commands/workflow/` with numeric prefixes

**Rationale**:
- Per Claude Code documentation, subdirectories create organizational namespaces
- Commands in subdirectories appear as "(project:workflow)" in help output
- Actual command invocation uses filename only: `/1_specify`, `/2_plan`, etc.
- Numeric prefixes (0_, 1_, 2_, 3_, 4_) provide explicit execution order

**Alternatives Considered**:
- Flat structure with prefixes only → Rejected: loses namespace organization benefits
- Using slashes in filenames → Not supported by filesystem
- Relying on `order` frontmatter only → Less visible to users

### 2. Frontmatter Schema for Slash Commands

**Decision**: Preserve existing frontmatter fields, update navigation references

**Rationale**:
- `description`: Updated to include navigation flow
- `order`: Numeric order preserved (1, 2, 3, 4, 5)
- `prev`/`next`: Updated to reference new command names

**Schema**:
```yaml
---
description: "(start) → workflow/1_specify → workflow/2_plan | Create feature spec"
order: 1
next: /2_plan
---
```

### 3. Documentation Updates Required

**Decision**: Update CLAUDE.md and all internal command references

**Files to Update**:
1. `.claude/commands/workflow/*.md` - The command files themselves
2. `CLAUDE.md` - Slash commands section
3. Command internal references (`/specify` → `/1_specify`, etc.)

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| Command naming | `0_specify`, `1_plan`, `2_tasks`, `3_implement`, `4_deploy` |
| Directory structure | `.claude/commands/workflow/` |
| Navigation format | "workflow/<prev> → workflow/<current> → workflow/<next>" |
