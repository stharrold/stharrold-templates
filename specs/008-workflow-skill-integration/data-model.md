# Data Model: Workflow Skill Integration

**Feature**: 008-workflow-skill-integration
**Date**: 2025-11-23

## Overview

This feature unifies two systems (`.specify/` and `.gemini/skills/`) into one. The data model focuses on:
1. Slash command → Skill mapping
2. AgentDB state records
3. Deprecated entities

## Entity: Slash Command

**Location**: `.gemini/commands/workflow/*.md`

| Field | Type | Description |
|-------|------|-------------|
| name | string | Command name (e.g., `1_specify`) |
| description | string | YAML frontmatter description |
| order | int | Workflow sequence (1-7) |
| prev | string | Previous command (nullable) |
| next | string | Next command (nullable) |
| skills_invoked | list[string] | Skills to load/invoke |
| state_pattern | string | AgentDB sync pattern |

**Relationships**:
- Invokes 1..n Skills
- Records 1 AgentDB sync per execution

## Entity: Skill

**Location**: `.gemini/skills/*/`

| Field | Type | Description |
|-------|------|-------------|
| name | string | Skill directory name |
| scripts | list[string] | Executable Python scripts |
| templates | list[string] | Template files (optional) |
| has_gemini_md | bool | Has GEMINI.md context file |
| has_skill_md | bool | Has SKILL.md documentation |

**Skills in scope**:
| Skill | Primary Scripts |
|-------|-----------------|
| tech-stack-adapter | `detect_stack.py` |
| bmad-planner | `create_planning.py` |
| speckit-author | `create_specifications.py`, `update_asbuilt.py` |
| git-workflow-manager | `create_worktree.py`, `cleanup_feature.py`, `pr_workflow.py`, `release_workflow.py`, `backmerge_workflow.py`, `semantic_version.py` |
| quality-enforcer | `run_quality_gates.py` |
| workflow-utilities | `deprecate_files.py`, `directory_structure.py` |
| agentdb-state-manager | `init_database.py`, `record_sync.py` (new), `query_workflow_state.py` (new) |

## Entity: AgentDB Sync Record

**Location**: `.gemini-state/agentdb.duckdb` → `agent_synchronizations` table

| Field | Type | Description |
|-------|------|-------------|
| sync_id | UUID | Unique identifier |
| agent_id | string | `gemini-code` |
| worktree_path | string | Git worktree path (nullable) |
| sync_type | enum | `workflow_transition`, `quality_gate`, `file_update` |
| source_location | string | Source (e.g., `planning/<slug>`) |
| target_location | string | Target (e.g., `specs/<slug>`) |
| pattern | string | Phase pattern (e.g., `phase_1_specify`) |
| status | enum | `pending`, `in_progress`, `completed`, `failed` |
| created_at | timestamp | Creation time |
| completed_at | timestamp | Completion time (nullable) |

**Workflow Patterns**:
| Pattern | Slash Command | Description |
|---------|---------------|-------------|
| `phase_1_specify` | `/1_specify` | Planning + worktree created |
| `phase_2_plan` | `/2_plan` | Specifications created |
| `phase_3_tasks` | `/3_tasks` | Tasks validated |
| `phase_4_implement` | `/4_implement` | Implementation + gates passed |
| `phase_5_integrate` | `/5_integrate` | PRs created + cleanup |
| `phase_6_release` | `/6_release` | Release created + tagged |
| `phase_7_backmerge` | `/7_backmerge` | Backmerge + cleanup |

## Entity: GitHub Issue (Work Item)

**Location**: GitHub repository issues

| Field | Type | Description |
|-------|------|-------------|
| number | int | Issue number |
| title | string | Feature description |
| labels | list[string] | `feature`, `pr-feedback`, etc. |
| state | enum | `open`, `closed` |
| linked_pr | int | Associated PR number (optional) |

**Replaces**: TODO*.md files for work item tracking

## Deprecated Entities

### .specify/ Directory
**Action**: Archive to `.specify/ARCHIVED/`

| File | Purpose (was) |
|------|---------------|
| `scripts/bash/create-new-feature.sh` | Create branch + spec template |
| `scripts/bash/setup-plan.sh` | Copy plan template |
| `scripts/bash/check-task-prerequisites.sh` | Validate plan exists |
| `scripts/bash/common.sh` | Shared bash functions |
| `scripts/bash/get-feature-paths.sh` | Path helpers |
| `templates/*.md` | Markdown templates |
| `memory/constitution.md` | Design rules |

### workflow-utilities Scripts
**Action**: Move to `ARCHIVED/`

| Script | Purpose (was) |
|--------|---------------|
| `sync_todo_to_db.py` | Sync TODO → AgentDB |
| `todo_updater.py` | Update TODO frontmatter |
| `workflow_archiver.py` | Archive completed TODO |
| `workflow_registrar.py` | Register in TODO.md manifest |
| `sync_manifest.py` | Sync manifest with filesystem |

## State Flow Diagram

```
GitHub Issue (created) ────────────────────────────────────────────────┐
                                                                       │
/1_specify ──────────────────────────────────────────────────────────┐ │
│ bmad-planner → planning/<slug>/                                    │ │
│ git-workflow-manager → worktree                                    │ │
│ AgentDB → phase_1_specify                                          │ │
└────────────────────────────────────────────────────────────────────┘ │
                           │                                           │
                           ▼                                           │
/2_plan ─────────────────────────────────────────────────────────────┐ │
│ speckit-author → specs/<slug>/spec.md, plan.md                     │ │
│ AgentDB → phase_2_plan                                             │ │
└────────────────────────────────────────────────────────────────────┘ │
                           │                                           │
                           ▼                                           │
/3_tasks ────────────────────────────────────────────────────────────┐ │
│ Validate specs/<slug>/plan.md has tasks                            │ │
│ AgentDB → phase_3_tasks                                            │ │
└────────────────────────────────────────────────────────────────────┘ │
                           │                                           │
                           ▼                                           │
/4_implement ────────────────────────────────────────────────────────┐ │
│ Execute tasks (TodoWrite)                                          │ │
│ quality-enforcer → gates                                           │ │
│ git-workflow-manager → version                                     │ │
│ AgentDB → phase_4_implement                                        │ │
└────────────────────────────────────────────────────────────────────┘ │
                           │                                           │
                           ▼                                           │
/5_integrate ────────────────────────────────────────────────────────┐ │
│ git-workflow-manager → PR, cleanup                                 │ │
│ Close GitHub Issue                                                 │◄┘
│ AgentDB → phase_5_integrate                                        │
└────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
/6_release ──────────────────────────────────────────────────────────┐
│ git-workflow-manager → release, tag                                │
│ AgentDB → phase_6_release                                          │
└────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
/7_backmerge ────────────────────────────────────────────────────────┐
│ git-workflow-manager → backmerge, cleanup                          │
│ AgentDB → phase_7_backmerge                                        │
└────────────────────────────────────────────────────────────────────┘
```
