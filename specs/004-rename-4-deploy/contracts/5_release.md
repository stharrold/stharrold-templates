# Contract: /5_release Command

**Version**: 1.0.0 | **Date**: 2025-11-22

## Overview

The `/5_release` command creates a release from develop branch, runs quality gates, and creates a PR to main for production deployment.

## Frontmatter Contract

```yaml
---
description: "workflow/4_integrate → workflow/5_release → workflow/6_backmerge | Release to production"
order: 6
prev: /4_integrate
next: /6_backmerge
---
```

## Input Contract

**Prerequisites**:
- Current branch: `contrib/*` or `develop`
- Features integrated to develop (from `/4_integrate`)
- develop branch has commits since last release

**Arguments**:
- `<version>`: Semantic version (e.g., `v1.6.0`) - optional, auto-calculated if omitted

## Output Contract

**Artifacts Produced**:
- Branch: `release/<version>` created from develop
- PR: release → main (created)
- Tag: `<version>` on main (after PR merge)
- CHANGELOG.md updated (if exists)

**State After Execution**:
- Current branch: `contrib/<username>` (editable branch)
- release/* branch: exists until backmerge complete
- main branch: contains new release code
- Tag: release version tagged on main

## Workflow Steps

| Step | Command | Input | Output |
|------|---------|-------|--------|
| 1 | `create-release` | develop branch, version | release/<version> branch |
| 2 | `run-gates` | release branch | quality gates pass |
| 3 | `pr-main` | release branch | PR release → main |
| 4 | `tag-release` | main (after merge) | git tag <version> |

## Error Conditions

| Condition | Error | Recovery |
|-----------|-------|----------|
| No new commits on develop | Warning: "No changes since last release" | Abort or force continue |
| Quality gates fail | "Quality gates failed" | Fix issues on release branch |
| Release branch exists | "Release branch already exists" | Delete or use existing |
| PR already exists | Warning, continue | Merge existing PR |
| Tag already exists | "Tag already exists" | Bump version |

## Semantic Version Calculation

If version not provided:
1. Get latest tag from main
2. Analyze commits since tag
3. Calculate next version:
   - MAJOR: breaking changes
   - MINOR: new features
   - PATCH: bug fixes

## Navigation

```
/4_integrate → /5_release → /6_backmerge
```
