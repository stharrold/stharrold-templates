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

**Workflow**: `/0_specify` → `/1_plan` → ... → `/N_final`

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
| `/0_specify` | 1 | (none) | `/1_plan` | Create feature spec |
| `/1_plan` | 2 | `/0_specify` | `/2_tasks` | Generate design artifacts |
| `/2_tasks` | 3 | `/1_plan` | `/3_implement` | Generate task list |
| `/3_implement` | 4 | `/2_tasks` | `/4_integrate` | Execute tasks |
| `/4_integrate` | 5 | `/3_implement` | `/5_release` | PR feature → contrib → develop |
| `/5_release` | 6 | `/4_integrate` | `/6_backmerge` | PR develop → release → main |
| `/6_backmerge` | 7 | `/5_release` | (end) | PR release → develop, rebase contrib |

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

**Workflow Order**: `/0_specify` → `/1_plan` → `/2_tasks` → `/3_implement` → `/4_integrate`

**Release Order**: `/5_release` → `/6_backmerge`

| Step | Command | Navigation | Purpose |
|------|---------|------------|---------|
| 1 | `/0_specify` | (start) → 0 → 1 | Create feature spec |
...
| 7 | `/6_backmerge` | 5 → 6 → (end) | Sync release to develop/contrib |
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
    ↓ /0_specify
[SPECIFIED] (spec.md exists)
    ↓ /1_plan
[PLANNED] (plan.md, research.md, data-model.md, contracts/, quickstart.md exist)
    ↓ /2_tasks
[TASKED] (tasks.md exists)
    ↓ /3_implement
[IMPLEMENTED] (tasks complete, quality gates pass)
    ↓ /4_integrate
[INTEGRATED] (PR merged to develop)
    ↓ (ready for release)
```

### Release Workflow State Machine

```
[INTEGRATED] (features merged to develop)
    ↓ /5_release
[RELEASED] (PR merged to main, tagged)
    ↓ /6_backmerge
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
