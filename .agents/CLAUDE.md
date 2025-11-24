---
type: claude-context
directory: .agents
purpose: Auto-synced mirror of .claude/skills/ for cross-tool AI compatibility. Do not edit directly.
parent: ../CLAUDE.md
sibling_readme: null
children:
  - agentdb-state-manager/CLAUDE.md
  - bmad-planner/CLAUDE.md
  - commands/CLAUDE.md
  - git-workflow-manager/CLAUDE.md
  - initialize-repository/CLAUDE.md
  - quality-enforcer/CLAUDE.md
  - speckit-author/CLAUDE.md
  - tech-stack-adapter/CLAUDE.md
  - workflow-orchestrator/CLAUDE.md
  - workflow-utilities/CLAUDE.md
---

# Claude Code Context: .agents

## Purpose

Auto-synced mirror of `.claude/skills/` for cross-tool AI compatibility.

**WARNING: Do not edit files in this directory directly. Changes will be overwritten.**

## Relationship with .claude/skills/

| Directory | Purpose | Editable |
|-----------|---------|----------|
| `.claude/skills/` | **Primary source** - All skill implementations | Yes |
| `.agents/` | **Mirror** - For GitHub Copilot, Cursor, and other AI tools | No |

### Sync Mechanism

The sync is performed by the PR workflow:
```bash
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents
```

This copies:
- All skill directories and their contents
- CLAUDE.md, README.md, SKILL.md files
- Scripts and templates

### When Sync Happens

- Automatically during `/5_integrate` workflow step
- Manually via `pr_workflow.py sync-agents`
- Before any PR from contrib to develop

## Contents

Mirrors the 9 skills from `.claude/skills/`:

| Skill | Purpose |
|-------|---------|
| agentdb-state-manager | Workflow state tracking (AgentDB) |
| bmad-planner | Requirements + architecture |
| git-workflow-manager | Worktrees, PRs, semantic versioning |
| initialize-repository | Bootstrap new repos |
| quality-enforcer | Quality gates (5 gates) |
| speckit-author | Specifications |
| tech-stack-adapter | Python/uv/Podman detection |
| workflow-orchestrator | Main coordinator, templates |
| workflow-utilities | Archive, directory structure |

## Related

- **Primary Source**: [.claude/skills/](../.claude/skills/CLAUDE.md)
- **Sync Script**: `.claude/skills/git-workflow-manager/scripts/pr_workflow.py`
- **Parent**: [Repository Root](../CLAUDE.md)
