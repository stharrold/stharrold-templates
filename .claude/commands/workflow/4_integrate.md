---
description: "workflow/3_implement → workflow/4_integrate → workflow/5_release | Integrate feature to develop"
order: 5
prev: /3_implement
next: /5_release
---

# /4_integrate - Step 5 of 7

**Workflow**: `/0_specify` → `/1_plan` → `/2_tasks` → `/3_implement` → `/4_integrate` → `/5_release` → `/6_backmerge`

**Purpose**: Integrate completed feature work into shared branches (PR to contrib, archive, sync, PR to develop).

**Prerequisites**: Implementation complete, all tasks done, quality gates passed (from `/3_implement`)

**Outputs**: PR created, TODO archived, configs synced

**Next**: Run `/5_release` to release to production, then `/6_backmerge` to sync back

---

# Integration Workflow Command

Execute the required PR workflow sequence.

## Workflow Steps (in order)

1. **finish-feature** - PR feature → contrib (runs quality gates first)
2. **archive-todo** - Archive TODO files after PR merge
3. **sync-agents** - Sync CLAUDE.md → AGENTS.md and .agents/
4. **start-develop** - PR contrib → develop

## Usage

Run workflow step:
```bash
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py <step>
```

## Available Steps

- `finish-feature` - Create PR from feature to contrib branch
- `archive-todo` - Archive TODO*.md files to ARCHIVED/
- `sync-agents` - Sync CLAUDE.md to cross-tool formats
- `start-develop` - Create PR from contrib to develop
- `full` - Run all steps in sequence
- `status` - Show current workflow status

## Example Session

```bash
# 1. On feature branch, finish feature and create PR to contrib
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py finish-feature

# 2. After PR is merged, archive the TODO file
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py archive-todo

# 3. Sync CLAUDE.md to AGENTS.md
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents

# 4. Create PR from contrib to develop
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py start-develop
```

## Quality Gates

The `finish-feature` step automatically runs quality gates:
- Test coverage (≥80%)
- All tests passing
- Build successful
- Linting clean
- TODO*.md YAML frontmatter valid
- AI config sync

## TODO*.md Frontmatter Requirements

All TODO*.md files must have YAML frontmatter with:
```yaml
---
status: in_progress|completed|blocked
feature: feature-name
branch: feature/timestamp_slug
---
```
