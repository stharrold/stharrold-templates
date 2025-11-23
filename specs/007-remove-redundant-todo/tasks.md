# Tasks: Remove Redundant TODO*.md System

**Input**: Design documents from `/specs/007-remove-redundant-todo/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → SUCCESS: Implementation plan loaded
   → Extracted: Python 3.11, pathlib/shutil, single project structure
2. Load optional design documents:
   → data-model.md: Entities to remove/modify identified
   → contracts/: quality-gates.md, documentation.md loaded
   → research.md: 5 research questions resolved
3. Generate tasks by category:
   → Setup: None (existing project)
   → Tests: Verify existing quality gates pass
   → Core: Archive file, update script, update docs
   → Integration: Sync AGENTS.md
   → Polish: Verify quality gates, cleanup
4. Apply task rules:
   → Most tasks sequential (dependencies between them)
   → Some verification tasks can be parallel [P]
5. Number tasks sequentially (T001-T011)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 3.1: Archive Files

- [ ] T001 Archive `TODO.md` to `docs/archived/20251123T000000Z_TODO.md`
  - Move file with timestamp prefix
  - Verify source file removed from root
  - Verify archived file exists

---

## Phase 3.2: Update Quality Gates Script

- [ ] T002 Remove `check_todo_frontmatter()` function from `.claude/skills/quality-enforcer/scripts/run_quality_gates.py`
  - Delete the entire function (~50 lines)
  - Remove function call in `run_all_gates()`
  - Remove from imports if separate

- [ ] T003 Update gate numbering in `.claude/skills/quality-enforcer/scripts/run_quality_gates.py`
  - Change `[5/6]` to `[5/5]` for AI Config Sync gate
  - Change `[X/6]` to `[X/5]` for all gates (1-5)
  - Update any gate count variables

- [ ] T004 Remove `todo_frontmatter` from results dict in `.claude/skills/quality-enforcer/scripts/run_quality_gates.py`
  - Remove `'todo_frontmatter_passed'` key from results
  - Remove from any summary output

---

## Phase 3.3: Update Documentation

- [ ] T005 Update quality gates table in `CLAUDE.md`
  - Remove row: `| 5. TODO Frontmatter | All TODO*.md have valid YAML frontmatter |`
  - Renumber: `| 6. AI Config Sync |` → `| 5. AI Config Sync |`
  - Update header if mentions "6 gates" → "5 gates"

- [ ] T006 Remove TODO frontmatter section from `CLAUDE.md`
  - Delete entire section: `## TODO*.md YAML Frontmatter (Required)`
  - Including the YAML code block example

- [ ] T007 Update PR workflow in `CLAUDE.md`
  - Remove `archive-todo` step and its comment
  - Renumber remaining steps (Step 3 → Step 2, Step 4 → Step 3)
  - Update `# Or run all steps` if needed

- [ ] T008 Remove TODO reference from critical guidelines in `CLAUDE.md`
  - Delete line: `- **TODO files require YAML frontmatter**: status, feature, branch fields`

---

## Phase 3.4: Sync and Verify

- [ ] T009 Sync `AGENTS.md` from `CLAUDE.md`
  ```bash
  podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents
  ```

- [ ] T010 [P] Run quality gates to verify all pass
  ```bash
  podman-compose run --rm dev python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
  ```
  - Expected: 5/5 gates pass
  - Expected: No TODO-related output

- [ ] T011 [P] Verify no TODO references remain in documentation
  ```bash
  grep -rn "TODO Frontmatter" CLAUDE.md AGENTS.md
  grep -rn "archive-todo" CLAUDE.md AGENTS.md
  ```
  - Expected: No matches

---

## Dependencies

```
T001 (archive) → T002-T004 (script) → T005-T008 (docs) → T009 (sync) → T010-T011 (verify)

Detailed:
- T001 must complete first (removes TODO.md that would fail old gates)
- T002 blocks T003, T004 (same file, logical order)
- T005 blocks T006, T007, T008 (same file, logical order)
- T009 requires T005-T008 complete (syncs final CLAUDE.md)
- T010, T011 can run in parallel [P] after T009
```

---

## Parallel Execution Examples

### Phase 3.4: Verification tasks in parallel
```bash
# Launch T010-T011 together (2 agents):
# Agent 1:
podman-compose run --rm dev python .claude/skills/quality-enforcer/scripts/run_quality_gates.py

# Agent 2:
grep -rn "TODO Frontmatter" CLAUDE.md AGENTS.md && \
grep -rn "archive-todo" CLAUDE.md AGENTS.md
```

---

## Validation Checklist

- [x] All contracts have corresponding tests (N/A - cleanup task)
- [x] All entities have model tasks (N/A - removal only)
- [x] All tests come before implementation (using existing quality gates)
- [x] Parallel tasks truly independent (T010, T011 verify different things)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

---

## Notes

- This is a cleanup/removal feature, so task count is low (11 tasks)
- Most tasks are sequential due to file dependencies
- Verification tasks (T010-T011) can run in parallel
- No new tests needed - existing quality gates verify the changes
- Commit after each phase completes for easy rollback
