# Data Model: Slash Command Files

**Feature**: 003-rename-slash-command
**Date**: 2025-11-22

## Entity: Slash Command File

A markdown file that defines a Claude Code slash command.

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Short description shown in `/help`, includes navigation |
| `order` | integer | Yes | Execution order (1-5) |
| `prev` | string | No | Previous command reference (empty for first) |
| `next` | string | No | Next command reference (empty for last) |
| `body` | markdown | Yes | Command instructions and documentation |

### File Naming Convention

```
{order}_{name}.md
```

- `order`: Single digit (0-4) indicating sequence
- `name`: Descriptive command name (specify, plan, tasks, implement, deploy)

### Directory Structure

**Before**:
```
.claude/commands/
├── specify.md     → /specify
├── plan.md        → /plan
├── tasks.md       → /tasks
└── workflow.md    → /workflow
```

**After**:
```
.claude/commands/
└── workflow/
    ├── 0_specify.md   → /1_specify (project:workflow)
    ├── 1_plan.md      → /2_plan (project:workflow)
    ├── 2_tasks.md     → /3_tasks (project:workflow)
    ├── 3_implement.md → /4_implement (project:workflow) ← NEW
    └── 4_deploy.md    → /5_integrate (project:workflow)
```

### Frontmatter Examples

**0_specify.md**:
```yaml
---
description: "(start) → workflow/1_specify → workflow/2_plan | Create feature spec"
order: 1
next: /2_plan
---
```

**1_plan.md**:
```yaml
---
description: "workflow/1_specify → workflow/2_plan → workflow/3_tasks | Generate design artifacts"
order: 2
prev: /1_specify
next: /3_tasks
---
```

**2_tasks.md**:
```yaml
---
description: "workflow/2_plan → workflow/3_tasks → workflow/4_implement | Generate task list"
order: 3
prev: /2_plan
next: /4_implement
---
```

**3_implement.md** (NEW):
```yaml
---
description: "workflow/3_tasks → workflow/4_implement → workflow/5_integrate | Execute tasks automatically"
order: 4
prev: /3_tasks
next: /5_integrate
---
```

**4_deploy.md**:
```yaml
---
description: "workflow/4_implement → workflow/5_integrate → (end) | Execute PR workflow"
order: 5
prev: /4_implement
---
```

## Relationships

```
0_specify → 1_plan → 2_tasks → 3_implement → 4_deploy
   ↓          ↓         ↓           ↓            ↓
 spec.md   plan.md  tasks.md    executed      PRs
                                  tasks
```

Each command produces artifacts consumed by the next command in sequence.

## /4_implement Behavior

The new `/4_implement` command:
1. Loads `specs/{feature}/tasks.md`
2. Parses tasks (T001, T002, etc.)
3. Executes tasks in dependency order
4. Runs [P] marked tasks in parallel
5. Uses TodoWrite to track progress
6. Runs quality gates before completion
7. User can stop/rewind via Claude Code controls
