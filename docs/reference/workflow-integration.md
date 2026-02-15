# Workflow Guide: Integration & Release (Step 3-4)

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Previous:** [Planning & Implementation (Step 1-2)](workflow-planning.md)
**Version:** 6.0.0

This document covers the synchronization and deployment steps of the v7x1 workflow.

---

### Step 3: Integrate Feature

**Location:** Main repository
**Branch:** `contrib/<gh-user>`
**Command:** `/workflow:v7x1_2-integrate ["feature/branch-name"]`

After completing development in the worktree, you must integrate the changes back into the main development line.

#### Full Integration (Feature Branch)
If you provide the branch name, `/workflow:v7x1_2-integrate` will:
1. Push the feature branch to origin.
2. Create a Pull Request from **feature** → **contrib**.
3. **Manual Gate**: You merge the PR in the GitHub UI.
4. Clean up the feature worktree and branches.
5. Create a Pull Request from **contrib** → **develop**.

#### Contrib-Only Integration
If you omit the branch name, it assumes you've already merged your feature into `contrib` and just want to sync with `develop`.

**Manual Gate:** All PRs require manual approval and merge in the VCS web portal.

---

### Step 4: Release & Backmerge

**Location:** Main repository
**Branch:** `develop` → `release/vX.Y.Z` → `main`

#### 4.1: Release to Production
**Command:** `/workflow:v7x1_3-release [version]`

When `develop` is ready for production:
1. Creates a `release/vX.Y.Z` branch from `develop`.
2. Creates a Pull Request from **release** → **main**.
3. **Manual Gate**: You merge the PR in the GitHub UI.
4. Tags the release on `main` automatically after merge.

#### 4.2: Backmerge to Develop
**Command:** `/workflow:v7x1_4-backmerge`

After tagging the release, you must sync those changes back to the integration branch:
1. Creates a Pull Request from **release** → **develop**.
2. **Manual Gate**: You merge the PR in the GitHub UI.
3. Rebases your `contrib` branch onto the updated `develop`.
4. Deletes the ephemeral release branch.

---

## Semantic Versioning

The `/workflow:v7x1_3-release` command uses semantic versioning (`vMAJOR.MINOR.PATCH`):
- **MAJOR**: Breaking changes.
- **MINOR**: New features.
- **PATCH**: Bug fixes.

If no version is provided, the system defaults to a **MINOR** bump from the latest tag.

---

## Branch Protection

**Protected branches (PR-only):**
- **`main`**: Production (immutable history).
- **`develop`**: Integration (shared history).

**Editable branches:**
- **`contrib/*`**: Your personal workspace.
- **`feature/*`**: Isolated feature development.

**Rule**: Always use Pull Requests to merge into `main` or `develop`. Direct commits are forbidden.

---

**Next:** [Operations & Maintenance](workflow-operations.md)
