# Research: Workflow Skill Integration

**Feature**: 008-workflow-skill-integration
**Date**: 2025-11-23
**Input**: Comprehensive conversation analysis of current vs intended architecture

## Research Questions

### RQ-001: What does each slash command currently call?

**Finding**: Current slash commands use `.specify/` bash scripts:

| Command | Current Script | Location |
|---------|---------------|----------|
| `/1_specify` | `create-new-feature.sh` | `.specify/scripts/bash/` |
| `/2_plan` | `setup-plan.sh` | `.specify/scripts/bash/` |
| `/3_tasks` | `check-task-prerequisites.sh` | `.specify/scripts/bash/` |
| `/4_implement` | TodoWrite + quality-enforcer | Mixed |
| `/5_integrate` | `pr_workflow.py` | `.gemini/skills/git-workflow-manager/` |
| `/6_release` | `release_workflow.py` | `.gemini/skills/git-workflow-manager/` |
| `/7_backmerge` | `backmerge_workflow.py` | `.gemini/skills/git-workflow-manager/` |

**Gap**: Steps 1-3 use `.specify/` (disconnected from skills), steps 4-7 partially use skills.

### RQ-002: What skills should each slash command invoke?

**Finding**: Based on workflow-orchestrator/SKILL.md and other skill documentation:

| Command | Intended Skills | Scripts |
|---------|-----------------|---------|
| `/1_specify` | tech-stack-adapter, bmad-planner, git-workflow-manager | `detect_stack.py`, `create_planning.py`, `create_worktree.py` |
| `/2_plan` | tech-stack-adapter, speckit-author | `detect_stack.py`, `create_specifications.py` |
| `/3_tasks` | workflow-utilities | Task validation from `specs/*/plan.md` |
| `/4_implement` | quality-enforcer, git-workflow-manager | `run_quality_gates.py`, `semantic_version.py` |
| `/5_integrate` | git-workflow-manager | `pr_workflow.py`, `cleanup_feature.py` |
| `/6_release` | git-workflow-manager, quality-enforcer | `release_workflow.py` |
| `/7_backmerge` | git-workflow-manager | `backmerge_workflow.py` |

### RQ-003: What scripts need flag additions?

**Finding**: Three scripts need updates to skip deprecated TODO operations:

| Script | New Flag | Default | Purpose |
|--------|----------|---------|---------|
| `create_worktree.py` | `--no-todo` | `True` | Skip TODO file creation |
| `cleanup_feature.py` | `--no-archive` | `True` | Skip TODO archival |
| `create_specifications.py` | `--issue` | None | Link to GitHub Issue |

### RQ-004: What new AgentDB scripts are needed?

**Finding**: Two new scripts for state tracking:

| Script | Purpose | Inputs |
|--------|---------|--------|
| `record_sync.py` | Record workflow transitions | `--sync-type`, `--pattern`, `--source`, `--target` |
| `query_workflow_state.py` | Query current phase | `--worktree` (optional) |

### RQ-005: What needs to be deprecated?

**Finding**: Two categories of deprecation:

**.specify/ directory** (archive entirely):
- `create-new-feature.sh`
- `setup-plan.sh`
- `check-task-prerequisites.sh`
- `common.sh`
- `get-feature-paths.sh`
- `update-agent-context.sh`
- `templates/` (spec-template.md, plan-template.md, tasks-template.md, agent-file-template.md)
- `memory/` (constitution.md, constitution_update_checklist.md)

**workflow-utilities scripts** (move to ARCHIVED/):
- `sync_todo_to_db.py`
- `todo_updater.py`
- `workflow_archiver.py`
- `workflow_registrar.py`
- `sync_manifest.py`

## Key Insights

1. **Two disconnected systems exist**: `.specify/` (bash) and `.gemini/skills/` (Python). The intended design uses only skills.

2. **State tracking evolution**: TODO*.md → AgentDB. The schema already supports workflow transitions via `agent_synchronizations` table.

3. **Work item evolution**: TODO*.md → GitHub Issues. The `generate_work_items_from_pr.py` script already creates GitHub Issues from PR feedback.

4. **Slash commands are prompts, not executables**: They provide instructions to Gemini Code, which then calls the appropriate scripts.

5. **Graceful migration**: Add flags to existing scripts (backward compatible), then update slash commands to use new defaults.

## References

- `workflow-orchestrator/SKILL.md` - Phase map and skill loading logic
- `workflow-orchestrator/GEMINI.md` - Context detection algorithm
- `agentdb-state-manager/schemas/agentdb_sync_schema.sql` - State schema
- `git-workflow-manager/GEMINI.md` - Script documentation
- Conversation analysis (2025-11-23) - Comprehensive architecture review
