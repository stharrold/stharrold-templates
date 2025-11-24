---
description: "workflow/1_specify → workflow/2_plan → workflow/3_tasks | Generate design artifacts"
order: 2
prev: /1_specify
next: /3_tasks
---

# /2_plan - Step 2 of 7

**Workflow**: `/1_specify` → `/2_plan` → `/3_tasks` → `/4_implement` → `/5_integrate` → `/6_release` → `/7_backmerge`

**Purpose**: Generate specifications (spec.md, plan.md) from planning documents.

**Prerequisites**:
- Must be in feature worktree (created by `/1_specify`)
- `../planning/{slug}/` must exist with BMAD documents

**Outputs**: `specs/{slug}/spec.md`, `specs/{slug}/plan.md`, AgentDB state record

---

Given the feature context, do this:

## Step 0: Verify Prerequisites (REQUIRED)

**IMPORTANT: Always run these checks before proceeding.**

1. **Verify feature branch:**
   ```bash
   git branch --show-current
   ```
   Must start with `feature/`. If not, STOP and tell user to switch to feature worktree.

2. **Extract slug from branch name:**
   Branch format: `feature/{timestamp}_{slug}`
   Example: `feature/20251124T111020Z_ai-config-architecture-docs` → slug = `ai-config-architecture-docs`

3. **Check for planning documents in MAIN repo:**
   The planning directory is in the main repository, not the worktree:
   ```bash
   ls ../stharrold-templates/planning/{slug}/requirements.md 2>/dev/null || \
   ls ../planning/{slug}/requirements.md 2>/dev/null
   ```

4. **If planning documents missing, STOP and prompt user:**
   ```
   ❌ MISSING PREREQUISITES

   Could not find planning/{slug}/requirements.md

   The /2_plan command requires planning documents created by /1_specify.

   Options:
   1. Run /1_specify first to create planning documents
   2. If you have requirements, I can help create planning/{slug}/requirements.md manually

   Which would you like to do?
   ```

   **Do NOT proceed until user responds and artifacts exist.**

## Step 1: Verify Worktree Context

Confirm you are in a feature worktree:
- Current directory should be `../{project}_feature_{timestamp}_{slug}/`
- Not the main repository root

If not in worktree, prompt user to `cd` to the worktree first.

## Step 2: Detect Feature Slug

Extract the slug from the current branch name:
```bash
git branch --show-current
```
Branch format: `feature/{timestamp}_{slug}` → extract `{slug}`

## Step 3: Verify Planning Documents

Check that BMAD planning documents exist:
- `../planning/{slug}/requirements.md`
- `../planning/{slug}/architecture.md`
- `../planning/{slug}/epics.md`

If missing, prompt user to run `/1_specify` first.

## Step 4: Create Specifications

Run the SpecKit author to create specifications:
```bash
podman-compose run --rm dev python .claude/skills/speckit-author/scripts/create_specifications.py \
  feature {slug} stharrold \
  --issue {issue-number}
```

This creates `specs/{slug}/` with:
- `spec.md` - Technical specification
- `plan.md` - Implementation plan with tasks
- `CLAUDE.md` - AI context
- `README.md` - Overview

## Step 5: Record State in AgentDB

Record the workflow transition:
```bash
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_2_plan \
  --source "../planning/{slug}" \
  --target "specs/{slug}"
```

## Step 6: Report Completion

Report to the user:
- Specifications created at `specs/{slug}/`
- Planning documents referenced from `../planning/{slug}/`
- Next step: Run `/3_tasks` to validate task list

**Important**: Verify `specs/{slug}/plan.md` has a valid task breakdown before proceeding.
