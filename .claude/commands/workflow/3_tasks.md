---
description: "workflow/2_plan → workflow/3_tasks → workflow/4_implement | Generate task list"
order: 3
prev: /2_plan
next: /4_implement
---

# /3_tasks - Step 3 of 7

**Workflow**: `/1_specify` → `/2_plan` → `/3_tasks` → `/4_implement` → `/5_integrate` → `/6_release` → `/7_backmerge`

**Purpose**: Validate task list from plan.md and prepare for implementation.

**Prerequisites**:
- Must be in feature worktree
- `specs/{slug}/plan.md` must exist with ## Tasks section (created by `/2_plan`)

**Outputs**: Validated task list ready for execution, AgentDB state record

**Next**: Run `/4_implement` to execute tasks automatically

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

3. **Check for spec/plan documents:**
   ```bash
   ls specs/{slug}/plan.md specs/{slug}/spec.md 2>/dev/null
   ```

4. **If spec documents missing, STOP and prompt user:**
   ```
   ❌ MISSING PREREQUISITES

   Could not find specs/{slug}/plan.md or specs/{slug}/spec.md

   The /3_tasks command requires specifications created by /2_plan.

   Options:
   1. Run /2_plan first to create specifications
   2. If you have a plan, I can help create specs/{slug}/plan.md manually

   Which would you like to do?
   ```

   **Do NOT proceed until user responds and artifacts exist.**

## Step 1: Verify Worktree Context

Confirm you are in a feature worktree (same as `/2_plan`).

## Step 2: Locate Plan File

Find the plan file at `specs/{slug}/plan.md` where `{slug}` is extracted from the current branch name.

## Step 3: Validate Task Structure

Read `specs/{slug}/plan.md` and verify it contains:
- A `## Tasks` or `## Task Breakdown` section
- Numbered tasks (T001, T002, etc. or similar format)
- Clear task descriptions with file paths

If tasks are missing or incomplete:
- Check `specs/{slug}/tasks.md` as an alternative location
- If no tasks found, prompt user to complete the plan first

## Step 4: Parse and Display Tasks

Parse the tasks from plan.md and display:
- Total task count
- Task categories (setup, implementation, testing, documentation)
- Parallel execution opportunities (tasks marked [P])
- Dependencies between tasks

## Step 5: Record State in AgentDB

Record the workflow transition:
```bash
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_3_tasks \
  --source "specs/{slug}/plan.md"
```

## Step 6: Report Readiness

Report to the user:
- Tasks validated and ready for execution
- Task summary (count, categories, parallel opportunities)
- Next step: Run `/4_implement` to execute tasks

**Important**: The task list must be complete and unambiguous before proceeding to implementation.
