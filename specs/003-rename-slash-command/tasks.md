# Tasks: Namespace Slash Commands

**Input**: Design documents from `/specs/003-rename-slash-command/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓

## Summary

Reorganize 4 existing slash commands into `workflow/` namespace with numeric prefixes and navigation descriptions. Create 1 new `/4_implement` command for automated task execution.

## Phase 3.1: Setup

- [ ] T001 Create directory `.gemini/commands/workflow/`

## Phase 3.2: Core Implementation (Existing Commands)

**Note**: All [P] tasks create independent files and can run in parallel.

- [ ] T002 [P] Create `.gemini/commands/workflow/1_specify.md` with:
  - Copy content from `.gemini/commands/specify.md`
  - Update frontmatter description: `"(start) → workflow/1_specify → workflow/2_plan | Create feature spec"`
  - Update frontmatter: `order: 1`, `next: /2_plan` (remove `prev`)
  - Update internal references: `/specify` → `/1_specify`, `/plan` → `/2_plan`, `/tasks` → `/3_tasks`, `/workflow` → `/5_integrate`
  - Update workflow header: `**Workflow**: \`/1_specify\` → \`/2_plan\` → \`/3_tasks\` → \`/4_implement\` → \`/5_integrate\``

- [ ] T003 [P] Create `.gemini/commands/workflow/2_plan.md` with:
  - Copy content from `.gemini/commands/plan.md`
  - Update frontmatter description: `"workflow/1_specify → workflow/2_plan → workflow/3_tasks | Generate design artifacts"`
  - Update frontmatter: `order: 2`, `prev: /1_specify`, `next: /3_tasks`
  - Update internal references: `/specify` → `/1_specify`, `/plan` → `/2_plan`, `/tasks` → `/3_tasks`, `/workflow` → `/5_integrate`
  - Update workflow header: `**Workflow**: \`/1_specify\` → \`/2_plan\` → \`/3_tasks\` → \`/4_implement\` → \`/5_integrate\``

- [ ] T004 [P] Create `.gemini/commands/workflow/3_tasks.md` with:
  - Copy content from `.gemini/commands/tasks.md`
  - Update frontmatter description: `"workflow/2_plan → workflow/3_tasks → workflow/4_implement | Generate task list"`
  - Update frontmatter: `order: 3`, `prev: /2_plan`, `next: /4_implement`
  - Update internal references: `/specify` → `/1_specify`, `/plan` → `/2_plan`, `/tasks` → `/3_tasks`, `/workflow` → `/5_integrate`
  - Update workflow header: `**Workflow**: \`/1_specify\` → \`/2_plan\` → \`/3_tasks\` → \`/4_implement\` → \`/5_integrate\``

- [ ] T005 [P] Create `.gemini/commands/workflow/5_integrate.md` with:
  - Copy content from `.gemini/commands/workflow.md`
  - Update frontmatter description: `"workflow/4_implement → workflow/5_integrate → (end) | Execute PR workflow"`
  - Update frontmatter: `order: 5`, `prev: /4_implement` (remove `next`)
  - Update internal references: `/specify` → `/1_specify`, `/plan` → `/2_plan`, `/tasks` → `/3_tasks`, `/workflow` → `/5_integrate`
  - Update workflow header: `**Workflow**: \`/1_specify\` → \`/2_plan\` → \`/3_tasks\` → \`/4_implement\` → \`/5_integrate\``

## Phase 3.3: New Command (3_implement)

- [ ] T006 Create NEW `.gemini/commands/workflow/4_implement.md` with:
  - Frontmatter:
    ```yaml
    ---
    description: "workflow/3_tasks → workflow/4_implement → workflow/5_integrate | Execute tasks automatically"
    order: 4
    prev: /3_tasks
    next: /5_integrate
    ---
    ```
  - Title: `# /4_implement - Step 4 of 5`
  - Workflow header: `**Workflow**: \`/1_specify\` → \`/2_plan\` → \`/3_tasks\` → \`/4_implement\` → \`/5_integrate\``
  - Purpose: Execute tasks from tasks.md automatically
  - Prerequisites: `tasks.md` must exist (created by `/3_tasks`)
  - Behavior:
    1. Run `.specify/scripts/bash/check-task-prerequisites.sh --json` to get FEATURE_DIR
    2. Load and parse `FEATURE_DIR/tasks.md`
    3. Use TodoWrite to track all tasks
    4. Execute tasks in dependency order (setup → tests → core → integration → polish)
    5. Run [P] marked tasks in parallel using Task tool
    6. Mark tasks complete as they finish
    7. Run quality gates before completion
    8. Report completion and readiness for `/5_integrate`

## Phase 3.4: Documentation Update

- [ ] T007 Update `GEMINI.md` slash commands section:
  - Change workflow order to: `/1_specify` → `/2_plan` → `/3_tasks` → `/4_implement` → `/5_integrate`
  - Update table with 5 commands and navigation descriptions
  - Update any other references to old command names

## Phase 3.5: Cleanup (AFTER verifying new files work)

- [ ] T008 [P] Remove `.gemini/commands/specify.md`
- [ ] T009 [P] Remove `.gemini/commands/plan.md`
- [ ] T010 [P] Remove `.gemini/commands/tasks.md`
- [ ] T011 [P] Remove `.gemini/commands/workflow.md`

## Phase 3.6: Verification

- [ ] T012 Run quickstart.md verification steps:
  - Verify all 5 files exist in workflow/ directory
  - Verify old files are removed
  - Verify frontmatter has correct navigation
  - Verify GEMINI.md is updated

## Dependencies

```
T001 (create dir) → T002-T006 (create files) → T007 (update docs) → T008-T011 (remove old) → T012 (verify)
```

- T001 blocks all file creation (T002-T006)
- T002-T005 can run in parallel (different files, existing commands)
- T006 creates new /4_implement (can run parallel with T002-T005)
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
