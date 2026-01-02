# Workflow Guide - v6 (Implementation)

**Version:** 6.0.0
**Date:** 2026-01-01
**Architecture:** 4-phase workflow using built-in Gemini CLI tools

## Overview

This repository uses a streamlined 4-phase workflow for Python development:
- **Git-flow hybrid** with worktrees for isolation
- **Built-in Gemini CLI tools** for planning, architecture, and implementation
- **No separate manual quality gates** (Gemini Code Review automated via GitHub Actions)

## Prerequisites

Required tools:
- **VCS CLI** - GitHub (`gh`) OR Azure DevOps (`az`) for PR operations
- **uv** - Python package manager
- **git** - Version control with worktree support
- **Python 3.11+** - Language runtime
- **Gemini Code** - AI development assistant

Verify prerequisites:
```bash
# VCS Provider (one of):
gh auth status          # GitHub: Must be authenticated
# OR
az account show         # Azure DevOps: Must be logged in

uv --version            # Must be installed
python3 --version       # Must be 3.11+
```

## v6 Workflow

```
/worktree "feature description"
    | creates worktree, user implements feature in worktree
    v
/integrate "feature/YYYYMMDDTHHMMSSZ_slug"
    | PR feature->contrib->develop
    v
/release
    | create release, PR to main, tag
    v
/backmerge
    | PR release->develop, rebase contrib, cleanup
```

### Step 1: Create Worktree (`/worktree`)

Creates isolated git worktree for feature development.

```bash
/worktree "add user authentication"
```

**Output:**
- Branch: `feature/{timestamp}_{slug}`
- Worktree: `../{project}_feature_{timestamp}_{slug}/`

**Next steps displayed:** Navigate to worktree and implement the feature.

### Step 2: Feature Implementation

Run in the feature worktree (not main repo) using built-in Gemini CLI tools:

```bash
cd <worktree-path>
# Then just chat with Gemini:
"Implement user authentication with JWT tokens"
```

**Gemini handles:**
- Understanding the codebase
- Planning the implementation
- Writing code and tests
- Refinement

No separate planning documents needed.

### Step 3: Integrate (`/integrate`)

From main repo, after implementation is complete:

```bash
/integrate "feature/20251229T120000Z_add-user-auth"
```

**Two modes:**
- **Full mode** (with branch arg): PR feature->contrib, cleanup worktree, PR contrib->develop
- **Contrib-only mode** (no arg): PR contrib->develop only

**Manual gates:** PRs require approval in GitHub/Azure DevOps UI.

### Step 4: Release (`/release`)

Creates release from develop:

```bash
/release           # Auto-calculate version
/release v1.2.0    # Explicit version
```

**Creates:**
- Branch: `release/{version}` from develop
- PR to main (requires approval)
- Tag on main after merge

### Step 5: Backmerge (`/backmerge`)

Syncs release changes back:

```bash
/backmerge
```

**Actions:**
- PR release->develop (requires approval)
- Rebases contrib on develop
- Deletes release branch

## Branch Structure

```
main                           <- Production (tagged vX.Y.Z)
  ^
release/vX.Y.Z                <- Release candidate (ephemeral)
  ^
develop                        <- Integration branch
  ^
contrib/<gh-user>             <- Personal contribution (contrib/stharrold)
  ^
feature/<timestamp>_<slug>    <- Isolated feature (worktree)
```

### Branch Protection

**Protected branches (PR-only):**
- `main` - Production
- `develop` - Integration

**Editable branches:**
- `contrib/*` - Personal contribution
- `feature/*` - Feature development

**Ephemeral branches:**
- `release/*` - Created in `/release`, deleted in `/backmerge`

## Key Differences from v1-v7

| Aspect | v1-v7 | v6 |
|--------|-------|-----|
| Planning | BMAD documents + SpecKit specs | Built-in Gemini tools |
| Quality gates | 5 separate gates | Gemini Code Review |
| Steps | 7 phases | 4 steps |
| Artifacts | requirements.md, architecture.md, spec.md, plan.md | None (Gemini handles internally) |

## Skills System

| Skill | Purpose |
|-------|---------|
| workflow-orchestrator | Main coordinator, templates |
| git-workflow-manager | Worktrees, PRs, semantic versioning |
| tech-stack-adapter | Python/uv detection |
| workflow-utilities | Archive, directory structure |
| agentdb-state-manager | Workflow state tracking |
| initialize-repository | Bootstrap new repos |

**Archived skills** (see `ARCHIVED/`):
- bmad-planner
- speckit-author
- quality-enforcer

## Related Documentation

- **[GEMINI.md](GEMINI.md)** - Main AI context file
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
