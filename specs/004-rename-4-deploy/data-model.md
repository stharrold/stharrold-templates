# Data Model: Workflow Command Rename and Release Workflow

**Branch**: `004-rename-4-deploy` | **Date**: 2025-11-22

## Entities

### 1. Slash Command File

**Description**: Markdown file defining a workflow step in `.claude/commands/workflow/`

**Structure**:
```yaml
---
description: "prev_command → this_command → next_command | Short description"
order: <number>
prev: /<prev_command>
next: /<next_command>  # optional, for non-terminal commands
---

# /<command_name> - Step X of Y

**Workflow**: `/1_specify` → `/2_plan` → ... → `/N_final`

**Purpose**: <what this step does>

**Prerequisites**: <required state/artifacts from previous steps>

**Outputs**: <artifacts/state produced>

---

<command instructions>
```

**Validation Rules**:
- YAML frontmatter required
- `description` must show navigation: `prev → this → next`
- `order` must be sequential (1-based)
- `prev` must reference valid command or be omitted for first command
- Workflow string must be accurate and complete

**Instances**:

| Command | Order | Prev | Next | Description |
|---------|-------|------|------|-------------|
| `/1_specify` | 1 | (none) | `/2_plan` | Create feature spec |
| `/2_plan` | 2 | `/1_specify` | `/3_tasks` | Generate design artifacts |
| `/3_tasks` | 3 | `/2_plan` | `/4_implement` | Generate task list |
| `/4_implement` | 4 | `/3_tasks` | `/5_integrate` | Execute tasks |
| `/5_integrate` | 5 | `/4_implement` | `/6_release` | PR feature → contrib → develop |
| `/6_release` | 6 | `/5_integrate` | `/7_backmerge` | PR develop → release → main |
| `/7_backmerge` | 7 | `/6_release` | (end) | PR release → develop, rebase contrib |

---

### 2. Workflow Script

**Description**: Python script in `.claude/skills/git-workflow-manager/scripts/` that automates git operations

**Structure**:
```python
#!/usr/bin/env python3
"""
<Script Name>

<Description of what script does>

Usage:
    podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/<script>.py <args>

Steps:
    <numbered list of operations>
"""

import argparse
import subprocess
# ...

def step_<name>() -> bool:
    """Step description."""
    # Implementation
    return success

def main():
    parser = argparse.ArgumentParser(...)
    # ...
```

**Validation Rules**:
- Must be executable (`#!/usr/bin/env python3`)
- Must have docstring with usage
- Must return exit code (0=success, 1=failure)
- Must use `run_cmd()` for shell commands
- Must have `--help` support via argparse

**Instances**:

| Script | Purpose | Commands |
|--------|---------|----------|
| `pr_workflow.py` | Feature integration | finish-feature, archive-todo, sync-agents, start-develop |
| `release_workflow.py` | Release to production | create-release, run-gates, pr-main |
| `backmerge_workflow.py` | Sync release back | pr-develop, rebase-contrib |

---

### 3. Documentation File

**Description**: Markdown file documenting workflow (CLAUDE.md, WORKFLOW.md, etc.)

**CLAUDE.md Slash Commands Section**:
```markdown
## Slash Commands

**Workflow Order**: `/1_specify` → `/2_plan` → `/3_tasks` → `/4_implement` → `/5_integrate`

**Release Order**: `/6_release` → `/7_backmerge`

| Step | Command | Navigation | Purpose |
|------|---------|------------|---------|
| 1 | `/1_specify` | (start) → 0 → 1 | Create feature spec |
...
| 7 | `/7_backmerge` | 5 → 6 → (end) | Sync release to develop/contrib |
```

**Validation Rules**:
- Must be synced: CLAUDE.md → AGENTS.md → .github/copilot-instructions.md
- Navigation must match actual command frontmatter
- All 7 commands must be listed

---

## State Transitions

### Feature Workflow State Machine

```
[START]
    ↓ /1_specify
[SPECIFIED] (spec.md exists)
    ↓ /2_plan
[PLANNED] (plan.md, research.md, data-model.md, contracts/, quickstart.md exist)
    ↓ /3_tasks
[TASKED] (tasks.md exists)
    ↓ /4_implement
[IMPLEMENTED] (tasks complete, quality gates pass)
    ↓ /5_integrate
[INTEGRATED] (PR merged to develop)
    ↓ (ready for release)
```

### Release Workflow State Machine

```
[INTEGRATED] (features merged to develop)
    ↓ /6_release
[RELEASED] (PR merged to main, tagged)
    ↓ /7_backmerge
[SYNCED] (release merged to develop, contrib rebased)
    ↓ (ready for next feature)
[START]
```

---

## Relationships

```
Slash Command (1) ──executes──→ (0..1) Workflow Script
     │
     └──updates──→ (0..*) Documentation File

Feature Workflow (1) ──leads-to──→ (1) Release Workflow
     │
     └──produces──→ (1..*) Spec Artifacts
```

---

## File Locations

| Entity Type | Location Pattern |
|-------------|------------------|
| Slash Commands | `.claude/commands/workflow/<N>_<name>.md` |
| Workflow Scripts | `.claude/skills/git-workflow-manager/scripts/<name>.py` |
| Documentation | Root: `CLAUDE.md`, `AGENTS.md`, `WORKFLOW.md` |
| Spec Artifacts | `specs/<NNN>-<feature>/` |
