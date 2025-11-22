# Tasks: Namespace Slash Commands

**Input**: Design documents from `/specs/003-rename-slash-command/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓

## Summary

Reorganize 4 existing slash commands into `workflow/` namespace with numeric prefixes and navigation descriptions. Create 1 new `/3_implement` command for automated task execution.

## Phase 3.1: Setup

- [ ] T001 Create directory `.claude/commands/workflow/`

## Phase 3.2: Core Implementation (Existing Commands)

**Note**: All [P] tasks create independent files and can run in parallel.

- [ ] T002 [P] Create `.claude/commands/workflow/0_specify.md` with:
  - Copy content from `.claude/commands/specify.md`
  - Update frontmatter description: `"(start) → workflow/0_specify → workflow/1_plan | Create feature spec"`
  - Update frontmatter: `order: 1`, `next: /1_plan` (remove `prev`)
  - Update internal references: `/specify` → `/0_specify`, `/plan` → `/1_plan`, `/tasks` → `/2_tasks`, `/workflow` → `/4_deploy`
  - Update workflow header: `**Workflow**: \`/0_specify\` → \`/1_plan\` → \`/2_tasks\` → \`/3_implement\` → \`/4_deploy\``

- [ ] T003 [P] Create `.claude/commands/workflow/1_plan.md` with:
  - Copy content from `.claude/commands/plan.md`
  - Update frontmatter description: `"workflow/0_specify → workflow/1_plan → workflow/2_tasks | Generate design artifacts"`
  - Update frontmatter: `order: 2`, `prev: /0_specify`, `next: /2_tasks`
  - Update internal references: `/specify` → `/0_specify`, `/plan` → `/1_plan`, `/tasks` → `/2_tasks`, `/workflow` → `/4_deploy`
  - Update workflow header: `**Workflow**: \`/0_specify\` → \`/1_plan\` → \`/2_tasks\` → \`/3_implement\` → \`/4_deploy\``

- [ ] T004 [P] Create `.claude/commands/workflow/2_tasks.md` with:
  - Copy content from `.claude/commands/tasks.md`
  - Update frontmatter description: `"workflow/1_plan → workflow/2_tasks → workflow/3_implement | Generate task list"`
  - Update frontmatter: `order: 3`, `prev: /1_plan`, `next: /3_implement`
  - Update internal references: `/specify` → `/0_specify`, `/plan` → `/1_plan`, `/tasks` → `/2_tasks`, `/workflow` → `/4_deploy`
  - Update workflow header: `**Workflow**: \`/0_specify\` → \`/1_plan\` → \`/2_tasks\` → \`/3_implement\` → \`/4_deploy\``

- [ ] T005 [P] Create `.claude/commands/workflow/4_deploy.md` with:
  - Copy content from `.claude/commands/workflow.md`
  - Update frontmatter description: `"workflow/3_implement → workflow/4_deploy → (end) | Execute PR workflow"`
  - Update frontmatter: `order: 5`, `prev: /3_implement` (remove `next`)
  - Update internal references: `/specify` → `/0_specify`, `/plan` → `/1_plan`, `/tasks` → `/2_tasks`, `/workflow` → `/4_deploy`
  - Update workflow header: `**Workflow**: \`/0_specify\` → \`/1_plan\` → \`/2_tasks\` → \`/3_implement\` → \`/4_deploy\``

## Phase 3.3: New Command (3_implement)

- [ ] T006 Create NEW `.claude/commands/workflow/3_implement.md` with:
  - Frontmatter:
    ```yaml
    ---
    description: "workflow/2_tasks → workflow/3_implement → workflow/4_deploy | Execute tasks automatically"
    order: 4
    prev: /2_tasks
    next: /4_deploy
    ---
    ```
  - Title: `# /3_implement - Step 4 of 5`
  - Workflow header: `**Workflow**: \`/0_specify\` → \`/1_plan\` → \`/2_tasks\` → \`/3_implement\` → \`/4_deploy\``
  - Purpose: Execute tasks from tasks.md automatically
  - Prerequisites: `tasks.md` must exist (created by `/2_tasks`)
  - Behavior:
    1. Run `.specify/scripts/bash/check-task-prerequisites.sh --json` to get FEATURE_DIR
    2. Load and parse `FEATURE_DIR/tasks.md`
    3. Use TodoWrite to track all tasks
    4. Execute tasks in dependency order (setup → tests → core → integration → polish)
    5. Run [P] marked tasks in parallel using Task tool
    6. Mark tasks complete as they finish
    7. Run quality gates before completion
    8. Report completion and readiness for `/4_deploy`

## Phase 3.4: Documentation Update

- [ ] T007 Update `CLAUDE.md` slash commands section:
  - Change workflow order to: `/0_specify` → `/1_plan` → `/2_tasks` → `/3_implement` → `/4_deploy`
  - Update table with 5 commands and navigation descriptions
  - Update any other references to old command names

## Phase 3.5: Cleanup (AFTER verifying new files work)

- [ ] T008 [P] Remove `.claude/commands/specify.md`
- [ ] T009 [P] Remove `.claude/commands/plan.md`
- [ ] T010 [P] Remove `.claude/commands/tasks.md`
- [ ] T011 [P] Remove `.claude/commands/workflow.md`

## Phase 3.6: Verification

- [ ] T012 Run quickstart.md verification steps:
  - Verify all 5 files exist in workflow/ directory
  - Verify old files are removed
  - Verify frontmatter has correct navigation
  - Verify CLAUDE.md is updated

## Dependencies

```
T001 (create dir) → T002-T006 (create files) → T007 (update docs) → T008-T011 (remove old) → T012 (verify)
```

- T001 blocks all file creation (T002-T006)
- T002-T005 can run in parallel (different files, existing commands)
- T006 creates new /3_implement (can run parallel with T002-T005)
- T007 depends on T002-T006 completion
- T008-T011 depend on T007 (verify before delete)
- T008-T011 can run in parallel (different files)
- T012 depends on all previous tasks

## Parallel Execution Example

```bash
# After T001, launch T002-T006 together:
# These create independent files and can run in parallel

# After T007, launch T008-T011 together:
# These remove independent files and can run in parallel
```

## Validation Checklist

- [x] All 5 command files have creation tasks (4 existing + 1 new)
- [x] All 4 old files have removal tasks
- [x] Setup (T001) before file creation (T002-T006)
- [x] File creation before documentation (T007)
- [x] Documentation before cleanup (T008-T011)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
