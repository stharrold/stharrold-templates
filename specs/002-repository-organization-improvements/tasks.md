# Tasks: Repository Organization Improvements

**Input**: Design documents from `/specs/002-repository-organization-improvements/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files/directories, no dependencies)
- All paths are relative to repository root

---

## Phase 3.1: Setup & Preparation

- [ ] T001 Update `.gitignore` to add `.DS_Store` and `.tmp/` patterns
- [ ] T002 Remove all `.DS_Store` files from git tracking: `git rm --cached -r '*.DS_Store'`
- [ ] T003 Delete all `.DS_Store` files from filesystem: `find . -name ".DS_Store" -delete`

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: Validation tests MUST exist and document expected state before changes**

- [ ] T004 [P] Create `tests/__init__.py` (empty file)
- [ ] T005 [P] Create `tests/conftest.py` with shared pytest fixtures
- [ ] T006 [P] Create `tests/skills/__init__.py` (empty file for future skill tests)
- [ ] T007 Move `test_mcp_deduplication.py` to `tests/test_mcp_deduplication.py` using `git mv`
- [ ] T008 Verify pytest discovers tests: `podman-compose run --rm dev pytest --collect-only`

## Phase 3.3: Core Implementation - Directory Restructure

### 3.3.1: Documentation Directory Rename
- [ ] T009 Create `docs/` directory if not exists
- [ ] T010 Move `00_draft-initial/` to `docs/research/` using `git mv 00_draft-initial docs/research`
- [ ] T011 Move `10_draft-merged/` to `docs/guides/` using `git mv 10_draft-merged docs/guides`
- [ ] T012 Move `ARCHIVED/` to `docs/archived/` using `git mv ARCHIVED docs/archived`

### 3.3.2: TODO File Consolidation
- [ ] T013 [P] Archive `TODO_FOR_issue-13-merge-11-embedding.md` to `docs/archived/`
- [ ] T014 [P] Archive `TODO_FOR_issue-15-merge-12-baml.md` to `docs/archived/`
- [ ] T015 Update `TODO.md` with any active items from archived files (if applicable)

### 3.3.3: README Creation
- [ ] T016 Create `README.md` at repository root with:
  - Project title and description
  - Prerequisites (podman 4.0+, git, gh)
  - Quick Start (4 commands)
  - Links to GEMINI.md, WORKFLOW.md, CONTRIBUTING.md

## Phase 3.4: Integration - Link Updates

- [ ] T017 Search and update internal documentation links that reference old paths:
  - `00_draft-initial/` → `docs/research/`
  - `10_draft-merged/` → `docs/guides/`
  - `ARCHIVED/` → `docs/archived/`
- [ ] T018 Update any GEMINI.md references to old directory structure

## Phase 3.5: Polish & Validation

- [ ] T019 Run pytest to verify tests pass: `podman-compose run --rm dev pytest -v`
- [ ] T020 Run linting: `podman-compose run --rm dev ruff check .`
- [ ] T021 Run all 6 quality gates: `podman-compose run --rm dev python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py`
- [ ] T022 Execute quickstart.md validation steps manually
- [ ] T023 Commit changes with descriptive message

---

## Dependencies

```
T001 → T002 → T003 (gitignore before removal)
T004-T006 [parallel] → T007 → T008 (structure before move before verify)
T009 → T010, T011, T012 (docs/ before moves)
T010-T012 [sequential] (avoid conflicts)
T013-T014 [parallel] (independent files)
T015 → after T013, T014
T016 [independent]
T017 → after T010-T012
T019-T021 [sequential] → after all changes
```

## Parallel Execution Examples

### Batch 1: Test Directory Setup (T004-T006)
```bash
# Can run in parallel - different files
touch tests/__init__.py
touch tests/conftest.py
mkdir -p tests/skills && touch tests/skills/__init__.py
```

### Batch 2: TODO Archival (T013-T014)
```bash
# Can run in parallel - independent files
git mv TODO_FOR_issue-13-merge-11-embedding.md docs/archived/
git mv TODO_FOR_issue-15-merge-12-baml.md docs/archived/
```

## Notes

- Use `git mv` for all moves to preserve history
- Verify no broken links after directory renames
- Quality gates must pass before PR
- Commit frequently with clear messages

## Validation Checklist

- [x] All transformations from data-model.md have tasks
- [x] All validation contracts have corresponding test tasks
- [x] Tests/validation come before implementation changes
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path or command
- [x] No task modifies same file as another [P] task

---

## Execution Summary

| Phase | Tasks | Parallel? |
|-------|-------|-----------|
| 3.1 Setup | T001-T003 | Sequential |
| 3.2 Tests | T004-T008 | Partial [P] |
| 3.3.1 Docs | T009-T012 | Sequential |
| 3.3.2 TODOs | T013-T015 | Partial [P] |
| 3.3.3 README | T016 | Independent |
| 3.4 Links | T017-T018 | Sequential |
| 3.5 Polish | T019-T023 | Sequential |

**Total**: 23 tasks
**Estimated parallel batches**: 5-7 execution rounds
