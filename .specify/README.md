# .specify/ - DEPRECATED

This directory is deprecated as of v5.12.0.

## Migration

The workflow automation has been migrated to `.claude/skills/`:

| Old Location | New Location |
|--------------|--------------|
| `.specify/scripts/bash/` | `.claude/skills/git-workflow-manager/scripts/` |
| `.specify/templates/` | `.claude/skills/speckit-author/templates/` |
| `.specify/memory/` | `.claude/skills/workflow-orchestrator/templates/` |

## New Workflow

Use the following slash commands instead:

- `/1_specify` - Creates planning documents via `bmad-planner`
- `/2_plan` - Creates specifications via `speckit-author`
- `/3_tasks` - Validates task list from `plan.md`
- `/4_implement` - Executes tasks with `quality-enforcer`
- `/5_integrate` - Creates PRs via `git-workflow-manager`
- `/6_release` - Creates releases via `release_workflow.py`
- `/7_backmerge` - Syncs branches via `backmerge_workflow.py`

## State Tracking

Workflow state is now tracked in AgentDB (DuckDB) instead of TODO*.md files:

```bash
# Query current state
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/query_workflow_state.py
```

## Archived Contents

The original `.specify/` contents have been moved to `.specify/ARCHIVED/`:
- `scripts/` - Original bash scripts
- `templates/` - Original markdown templates
- `memory/` - Original constitution and memory files

## References

- `CLAUDE.md` - Main AI context file
- `.claude/skills/` - Active skill implementations
- `specs/008-workflow-skill-integration/` - Migration specification
