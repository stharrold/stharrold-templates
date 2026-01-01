# Implementation Plan: Remove Redundant TODO*.md System

**Branch**: `007-remove-redundant-todo` | **Date**: 2025-11-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-remove-redundant-todo/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → SUCCESS: Spec loaded from specs/007-remove-redundant-todo/spec.md
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → SUCCESS: No clarifications needed (simple cleanup task)
   → Project Type: single (script updates only)
3. Evaluate Constitution Check section below
   → SUCCESS: No violations (simplification, not addition)
   → Update Progress Tracking: Initial Constitution Check ✓
4. Execute Phase 0 → research.md
   → SUCCESS: research.md generated with 5 research questions resolved
5. Execute Phase 1 → contracts, data-model.md, quickstart.md
   → SUCCESS: All Phase 1 artifacts generated
6. Re-evaluate Constitution Check section
   → SUCCESS: Design is simpler than before (removes complexity)
   → Update Progress Tracking: Post-Design Constitution Check ✓
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → SUCCESS: Task approach documented below
8. STOP - Ready for /tasks command
```

## Summary

Remove the redundant TODO*.md task tracking system since GitHub Issues and Speckit tasks.md now provide superior functionality. Archive existing files, remove quality gate #5 (TODO frontmatter validation), and update documentation to reflect the simplified workflow with 5 quality gates instead of 6.

## Technical Context
**Language/Version**: Python 3.11 (existing scripts)
**Primary Dependencies**: pathlib, shutil (file operations)
**Storage**: N/A (filesystem archive only)
**Testing**: pytest (verify quality gates pass)
**Target Platform**: Local filesystem
**Project Type**: single (script modifications)
**Performance Goals**: N/A (one-time cleanup)
**Constraints**: Must not break existing workflows
**Scale/Scope**: ~6 scripts, 2 docs, 1 file archive

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 0 new (removing complexity, not adding)
- Using framework directly? Yes - standard Python file operations
- Single data model? N/A - no new data models
- Avoiding patterns? Yes - direct file/string operations

**Architecture**:
- EVERY feature as library? N/A - modifying existing scripts
- Libraries listed: None new
- CLI per library: N/A
- Library docs: N/A

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes - verify gates pass after changes
- Git commits show tests before implementation? Yes - run existing tests
- Order: Contract→Integration→E2E→Unit strictly followed? N/A - using existing tests
- Real dependencies used? Yes - actual file system
- Integration tests for: Existing quality gate tests cover this
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? N/A - using existing logging
- Frontend logs → backend? N/A
- Error context sufficient? N/A

**Versioning**:
- Version number assigned? Will increment via release workflow
- BUILD increments on every change? Yes
- Breaking changes handled? Yes - this is a simplification, not breaking change

## Project Structure

### Documentation (this feature)
```
specs/007-remove-redundant-todo/
├── plan.md              # This file ✓
├── research.md          # Phase 0 output ✓
├── data-model.md        # Phase 1 output ✓
├── quickstart.md        # Phase 1 output ✓
├── contracts/           # Phase 1 output ✓
│   ├── quality-gates.md
│   └── documentation.md
└── tasks.md             # Phase 2 output (/tasks command)
```

### Source Code Changes (repository root)
```
Files to modify:
├── GEMINI.md                                              # Remove TODO references
├── AGENTS.md                                              # Sync from GEMINI.md
├── TODO.md → docs/archived/                               # Archive
└── .gemini/skills/quality-enforcer/scripts/
    └── run_quality_gates.py                               # Remove Gate 5
```

**Structure Decision**: Single project (script modifications only)

## Phase 0: Outline & Research
✓ COMPLETE - See [research.md](./research.md)

Key findings:
- 1 file to archive: `TODO.md`
- 6 scripts reference TODO*.md (identified in research)
- Quality gate #5 to remove
- GEMINI.md sections to update documented

## Phase 1: Design & Contracts
✓ COMPLETE - See artifacts:
- [data-model.md](./data-model.md) - Entities being removed/modified
- [contracts/quality-gates.md](./contracts/quality-gates.md) - Gate behavior contract
- [contracts/documentation.md](./contracts/documentation.md) - Documentation contract
- [quickstart.md](./quickstart.md) - Validation scenarios

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Simple linear workflow (archive → update code → update docs → verify)
- ~10-12 tasks expected (not 25-30, this is a cleanup)
- Most tasks can run sequentially (dependencies between them)

**Ordering Strategy**:
1. Archive TODO.md first (prerequisite for clean test run)
2. Update quality gates script (core change)
3. Update GEMINI.md documentation
4. Sync AGENTS.md
5. Run quality gates to verify
6. Optional: Clean up other TODO-related scripts

**Estimated Output**: 10-12 ordered tasks in tasks.md

## Complexity Tracking
*No complexity violations - this feature REMOVES complexity*

| Aspect | Before | After |
|--------|--------|-------|
| Quality gates | 6 gates | 5 gates |
| TODO tracking systems | 3 (TODO.md, Issues, tasks.md) | 2 (Issues, tasks.md) |
| Required YAML frontmatter | Yes | No |

## Progress Tracking

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (N/A - simplification)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
