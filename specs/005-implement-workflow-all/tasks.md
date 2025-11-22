# Tasks: /workflow/all Command

**Input**: Design documents from `/specs/005-implement-workflow-all/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/all.md, quickstart.md

---

## Phase 3.1: Setup

- [ ] T001 Create `.claude/commands/workflow/all.md` with YAML frontmatter containing description and order fields

## Phase 3.2: Core Implementation

- [ ] T002 Add state detection section to `all.md`: get current branch via `git branch --show-current`, determine branch type (feature/contrib/develop/release/main), and report detected state

- [ ] T003 Add artifact detection section to `all.md`: check for spec.md, research.md, tasks.md existence in specs/{feature}/ directory to determine workflow progress

- [ ] T004 Add mode parsing section to `all.md`: parse $ARGUMENTS for "new", "release", "continue" modes or default to auto-detect

- [ ] T005 Add "new" mode handler to `all.md`: validate description not empty, invoke /workflow:0_specify with description, then continue through steps 1-4

- [ ] T006 Add "release" mode handler to `all.md`: validate branch is contrib/* or develop, invoke /workflow:5_release, pause for PR merge, then /workflow:6_backmerge

- [ ] T007 Add default mode handler to `all.md`: use state detection to determine starting step, execute steps in sequence until manual gate or completion

- [ ] T008 Add manual gate detection to `all.md`: after /5_integrate and /6_release, pause execution and display PR URLs with resume instructions

- [ ] T009 Add "continue" mode handler to `all.md`: check PR merge status via `gh pr list`, if merged continue to next step, otherwise report waiting status

- [ ] T010 Add progress output formatting to `all.md`: use [▶], [✓], [✗] indicators for step status, show detected state summary at start

- [ ] T011 Add error handling to `all.md`: on step failure, stop execution, report which step failed with error message, suggest retry command

## Phase 3.3: Documentation Updates

- [ ] T012 Update CLAUDE.md Slash Commands section to include `/workflow/all` with description of modes (new, release, continue, default)

- [ ] T013 [P] Sync CLAUDE.md updates to AGENTS.md

- [ ] T014 [P] Sync CLAUDE.md updates to .github/copilot-instructions.md

## Phase 3.4: Validation

- [ ] T015 Test "new" mode: run `/workflow/all new "test feature"` and verify it creates spec and continues through workflow

- [ ] T016 Test default mode: on feature branch with existing artifacts, verify correct starting step detection

- [ ] T017 Test manual gate pause: verify command pauses after /5_integrate and shows PR URLs

- [ ] T018 Test "release" mode: from contrib branch, verify /6_release and /7_backmerge execution

---

## Dependencies

```
T001 → T002-T011 (frontmatter before content)
T002, T003 → T004, T007 (detection before mode handlers)
T004 → T005, T006, T007, T009 (parsing before handlers)
T005, T006, T007 → T008 (handlers before gate detection)
T008 → T009 (gate detection before continue mode)
T002-T011 → T012 (implementation before docs)
T012 → T013, T014 (CLAUDE.md before sync)
T001-T014 → T015-T018 (implementation before testing)
```

## Parallel Execution

```
# T013-T014 can run in parallel (different files):
Task: "Sync CLAUDE.md updates to AGENTS.md"
Task: "Sync CLAUDE.md updates to .github/copilot-instructions.md"
```

## Notes

- Single file implementation (all.md) - most tasks are sequential
- Testing is manual via command execution
- No Python script needed - pure slash command orchestration
- Verify each mode works independently before integration testing
