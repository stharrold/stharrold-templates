# Tasks: Workflow Command Rename and Release Workflow

**Branch**: `004-rename-4-deploy` | **Date**: 2025-11-22
**Input**: Design documents from `/specs/004-rename-4-deploy/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 3.1: Setup (Command Rename)

- [ ] T001 Rename `.claude/commands/workflow/4_deploy.md` to `.claude/commands/workflow/5_integrate.md` using `git mv`
- [ ] T002 Update frontmatter in `.claude/commands/workflow/5_integrate.md`: change description to "workflow/4_implement → workflow/5_integrate → workflow/6_release | Integrate feature to develop", add `next: /6_release`
- [ ] T003 Update body content in `.claude/commands/workflow/5_integrate.md`: change "Step 5 of 5" to "Step 5 of 7", update workflow string to include all 7 commands, change "deploy" references to "integrate"

## Phase 3.2: New Command Files

- [ ] T004 [P] Create `.claude/commands/workflow/6_release.md` with frontmatter: description="workflow/5_integrate → workflow/6_release → workflow/7_backmerge | Release to production", order=6, prev=/5_integrate, next=/7_backmerge
- [ ] T005 [P] Create `.claude/commands/workflow/7_backmerge.md` with frontmatter: description="workflow/6_release → workflow/7_backmerge → (end) | Sync release to develop and contrib", order=7, prev=/6_release

## Phase 3.3: Update Existing Command Navigation

- [ ] T006 [P] Update `.claude/commands/workflow/1_specify.md`: change workflow string from 5 steps to 7 steps, update "Step 1 of 5" to "Step 1 of 7"
- [ ] T007 [P] Update `.claude/commands/workflow/2_plan.md`: change workflow string from 5 steps to 7 steps, update "Step 2 of 5" to "Step 2 of 7"
- [ ] T008 [P] Update `.claude/commands/workflow/3_tasks.md`: change workflow string from 5 steps to 7 steps, update "Step 3 of 5" to "Step 3 of 7"
- [ ] T009 [P] Update `.claude/commands/workflow/4_implement.md`: change description to "workflow/3_tasks → workflow/4_implement → workflow/5_integrate", change workflow string, update "Step 4 of 5" to "Step 4 of 7"

## Phase 3.4: Update Root Documentation

- [ ] T010 Update `CLAUDE.md` Slash Commands section: change table from 5 rows to 7 rows, rename `/4_deploy` to `/5_integrate`, add `/6_release` and `/7_backmerge` entries, update workflow order string
- [ ] T011 Run sync: copy `CLAUDE.md` to `AGENTS.md` (exact copy)
- [ ] T012 Run sync: copy `CLAUDE.md` to `.github/copilot-instructions.md` (exact copy)

## Phase 3.5: Create Supporting Python Scripts

- [ ] T013 Create `.claude/skills/git-workflow-manager/scripts/release_workflow.py` with steps: create-release (from develop), run-gates, pr-main, tag-release. Model after `pr_workflow.py` structure.
- [ ] T014 Create `.claude/skills/git-workflow-manager/scripts/backmerge_workflow.py` with steps: pr-develop, merge-pr, rebase-contrib, cleanup-release. Include `return_to_editable_branch()` at end.

## Phase 3.6: Populate New Command Content

- [ ] T015 Add body content to `.claude/commands/workflow/6_release.md`: Purpose, Prerequisites, Outputs, workflow steps (create-release, run-gates, pr-main, tag-release), usage examples referencing `release_workflow.py`
- [ ] T016 Add body content to `.claude/commands/workflow/7_backmerge.md`: Purpose, Prerequisites, Outputs, workflow steps (pr-develop, rebase-contrib, cleanup-release), usage examples referencing `backmerge_workflow.py`

## Phase 3.7: Validation

- [ ] T017 [P] Verify all `/5_integrate` references removed: run `grep -r "4_deploy" .claude/commands/` should return empty
- [ ] T018 [P] Verify CLAUDE.md synced: diff `CLAUDE.md` and `AGENTS.md` should be empty
- [ ] T019 Run quality gates: `podman-compose run --rm dev python .claude/skills/quality-enforcer/scripts/run_quality_gates.py`
- [ ] T020 Manual test: verify `/5_integrate` loads correctly in Claude Code
- [ ] T021 Manual test: verify `/6_release` loads correctly in Claude Code
- [ ] T022 Manual test: verify `/7_backmerge` loads correctly in Claude Code

---

## Dependencies

```
T001 → T002 → T003 (rename must complete before content update)
T003 → T004, T005 (4_integrate updated before creating 5,6)
T004, T005 → T015, T016 (files created before adding content)
T006-T009 can run in parallel (different files)
T010 → T011, T012 (CLAUDE.md updated before syncing)
T013, T014 can run in parallel (different script files)
T015, T016 depend on T013, T014 (scripts created before referencing)
T017-T022 run after all implementation complete
```

## Parallel Execution Examples

### Phase 3.2: New Commands (T004-T005)
```
# Launch in parallel - different files, no dependencies
Task: "Create .claude/commands/workflow/6_release.md with release workflow frontmatter"
Task: "Create .claude/commands/workflow/7_backmerge.md with backmerge workflow frontmatter"
```

### Phase 3.3: Navigation Updates (T006-T009)
```
# Launch in parallel - each modifies different file
Task: "Update 0_specify.md workflow string to 7 steps"
Task: "Update 1_plan.md workflow string to 7 steps"
Task: "Update 2_tasks.md workflow string to 7 steps"
Task: "Update 3_implement.md navigation to point to 4_integrate"
```

### Phase 3.5: Python Scripts (T013-T014)
```
# Launch in parallel - different script files
Task: "Create release_workflow.py with create-release, run-gates, pr-main, tag-release steps"
Task: "Create backmerge_workflow.py with pr-develop, rebase-contrib, cleanup-release steps"
```

### Phase 3.7: Validation (T017-T018)
```
# Launch in parallel - read-only verification
Task: "Verify all 4_deploy references removed from commands/"
Task: "Verify CLAUDE.md synced to AGENTS.md"
```

---

## Notes

- All file paths are relative to repository root
- Use `git mv` for rename (T001) to preserve history
- Python scripts should follow existing patterns in `pr_workflow.py`
- Sync tasks (T011, T012) are simple file copies
- Validation tasks (T017-T022) should run sequentially after T019 quality gates pass
- Commit after each logical group (Setup, New Commands, Navigation, Docs, Scripts, Validation)

## Validation Checklist

- [x] All contracts have corresponding implementation tasks (T004-T005, T015-T016)
- [x] All entities have tasks (slash commands, scripts, docs)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Dependencies documented
