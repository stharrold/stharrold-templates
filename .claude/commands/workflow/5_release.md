---
description: "workflow/4_integrate → workflow/5_release → workflow/6_backmerge | Release to production"
order: 6
prev: /4_integrate
next: /6_backmerge
---

# /5_release - Step 6 of 7

**Workflow**: `/0_specify` → `/1_plan` → `/2_tasks` → `/3_implement` → `/4_integrate` → `/5_release` → `/6_backmerge`

**Purpose**: Create release from develop, run quality gates, and create PR to main for production deployment.

**Prerequisites**: Features integrated to develop (from `/4_integrate`), develop has commits since last release

**Outputs**: Release branch created, PR to main, tag on main after merge

**Next**: Run `/6_backmerge` after release PR is merged to main

---

# Release Workflow Command

Create a release and deploy to production.

## Workflow Steps (in order)

1. **create-release** - Create release branch from develop
2. **run-gates** - Run quality gates on release branch
3. **pr-main** - Create PR from release to main
4. **tag-release** - Tag release on main after PR merge

## Usage

Run workflow step:
```bash
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/release_workflow.py <step>
```

## Available Steps

- `create-release` - Create release/<version> branch from develop
- `run-gates` - Run quality gates on release branch
- `pr-main` - Create PR from release to main
- `tag-release` - Tag the release on main after merge
- `full` - Run all steps in sequence
- `status` - Show current release status

## Example Session

```bash
# 1. Create release branch (auto-calculates version)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/release_workflow.py create-release

# 2. Run quality gates on release branch
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/release_workflow.py run-gates

# 3. Create PR to main
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/release_workflow.py pr-main

# 4. After PR merged, tag the release
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/release_workflow.py tag-release
```

## Semantic Versioning

Version is auto-calculated if not provided:
- **MAJOR**: Breaking changes detected
- **MINOR**: New features added
- **PATCH**: Bug fixes only

## Quality Gates

The `run-gates` step runs quality gates:
- Test coverage (≥80%)
- All tests passing
- Build successful
- Linting clean

## Notes

- Release branch is ephemeral (deleted after backmerge)
- Tag is created on main after PR merge
- CHANGELOG.md is updated automatically if present
