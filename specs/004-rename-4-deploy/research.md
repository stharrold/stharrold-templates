# Research: Workflow Command Rename and Release Workflow

**Branch**: `004-rename-4-deploy` | **Date**: 2025-11-22

## Research Topic 1: Current `/4_deploy` Implementation and References

### Decision
Rename `/4_deploy` to `/4_integrate` and update all 16 files containing references.

### Findings

**Files containing `/4_deploy` references:**

| Category | Files | Action Required |
|----------|-------|-----------------|
| Command files | `0_specify.md`, `1_plan.md`, `2_tasks.md`, `3_implement.md`, `4_deploy.md` | Update navigation, rename `4_deploy.md` |
| Documentation | `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md` | Update references |
| Previous specs | `specs/003-rename-slash-command/*` | Already completed, no action |
| Current specs | `specs/004-rename-4-deploy/*` | N/A (this feature) |

**Current `/4_deploy` behavior:**
1. `finish-feature` - PR feature → contrib (runs quality gates)
2. `archive-todo` - Archive TODO files
3. `sync-agents` - Sync CLAUDE.md → AGENTS.md
4. `start-develop` - PR contrib → develop

### Rationale
- "Deploy" implies production deployment, but this command integrates to develop
- "Integrate" accurately describes merging feature work into shared branches
- All existing functionality preserved under new name

### Alternatives Considered
- `merge` - Too generic, unclear what's being merged
- `promote` - Decent, but less clear than integrate
- `submit` - Implies one-time action, but command has multiple steps

---

## Research Topic 2: Release Workflow Best Practices

### Decision
Implement `/5_release` with: develop → release/* branch → PR to main

### Findings

**Git-flow release pattern:**
```
develop (stable integration)
    ↓ create release/vX.Y.Z
release/vX.Y.Z (QA, version bumps, final fixes)
    ↓ PR + merge
main (production)
    ↓ tag vX.Y.Z
```

**Daily release workflow requirements:**
1. Create release branch from develop
2. Run quality gates on release branch
3. Version bump (semantic versioning)
4. Create PR to main
5. After merge: tag release on main

**Existing scripts available:**
- `create_release.py` - Creates release branch
- `tag_release.py` - Tags release on main
- `semantic_version.py` - Calculates version

### Rationale
- Release branch provides isolation for final QA
- PR to main ensures review before production
- Tag on main provides release tracking

### Alternatives Considered
- Direct develop → main PR (no release branch) - Rejected: no isolation for fixes
- Trunk-based (no release branch) - Rejected: doesn't fit existing git-flow hybrid

---

## Research Topic 3: Backmerge Patterns (PR + Rebase Hybrid)

### Decision
Implement `/6_backmerge` with: PR release → develop, then rebase contrib on develop

### Findings

**Two-step backmerge:**

| Step | Operation | Why |
|------|-----------|-----|
| 1. PR release → develop | Merge | Preserves release history, requires review, handles version bumps |
| 2. Rebase contrib on develop | Rebase | Keeps contrib linear, clean for next feature cycle |

**Why hybrid approach:**
- **PR for release → develop**: Release branches may have hotfixes, version bumps that need review
- **Rebase for contrib on develop**: Contrib is personal branch, rebase keeps it clean and linear

**Existing scripts available:**
- `backmerge_release.py` - Merges release to develop
- `daily_rebase.py` - Rebases contrib on develop

**Edge cases:**
- Merge conflicts during rebase: User must resolve manually
- No new commits since last release: `/5_release` should warn but allow

### Rationale
- PR preserves merge commit (traceable release integration)
- Rebase on contrib maintains clean history for feature development
- Matches existing `daily_rebase.py` pattern

### Alternatives Considered
- All PRs (release→develop, develop→contrib) - Rejected: contrib gets messy merge commits
- All rebases - Rejected: release integration loses merge commit traceability
- Skip backmerge (let daily rebase handle it) - Rejected: release branch must be explicitly merged

---

## Research Topic 4: Documentation Update Scope

### Decision
Update all documentation to reflect 7-step workflow with clear separation.

### Findings

**Documentation structure (current):**
```
Feature workflow (5 steps):
  /0_specify → /1_plan → /2_tasks → /3_implement → /4_deploy
```

**Documentation structure (proposed):**
```
Feature workflow (5 steps):
  /0_specify → /1_plan → /2_tasks → /3_implement → /4_integrate

Release workflow (2 steps):
  /5_release → /6_backmerge
```

**Files requiring updates:**

| File | Update Type |
|------|-------------|
| `CLAUDE.md` | Workflow table, slash commands section |
| `AGENTS.md` | Mirror of CLAUDE.md |
| `.github/copilot-instructions.md` | Mirror of CLAUDE.md |
| `WORKFLOW.md` | Full workflow documentation |
| Command files (0-4) | Navigation strings |
| Skill CLAUDE.md files | Any workflow references |

**Navigation string format:**
```yaml
# Current
description: "workflow/3_implement → workflow/4_deploy → (end)"

# Updated
description: "workflow/3_implement → workflow/4_integrate → workflow/5_release"
```

### Rationale
- Clear separation between feature and release workflows
- Consistent navigation across all commands
- Single source of truth (CLAUDE.md) syncs to mirrors

---

## Summary

| Topic | Decision |
|-------|----------|
| Rename | `/4_deploy` → `/4_integrate` |
| New command | `/5_release`: develop → release/* → main |
| New command | `/6_backmerge`: PR release→develop, rebase contrib on develop |
| Documentation | Update all 16 files with references |

**Ready for Phase 1: Design & Contracts**
