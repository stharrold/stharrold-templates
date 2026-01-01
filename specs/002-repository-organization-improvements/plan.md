# Implementation Plan: Repository Organization Improvements

**Branch**: `002-repository-organization-improvements` | **Date**: 2025-11-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-repository-organization-improvements/spec.md`

## Summary

Reorganize repository structure for improved developer experience: create proper `tests/` directory, clean up gitignore, restructure documentation from numeric prefixes to intuitive names, consolidate TODO files, add README.md, and reduce skill documentation redundancy. This is a file organization task with no code changes.

## Technical Context

**Language/Version**: Python 3.11 (container)
**Primary Dependencies**: pytest, ruff, uv (existing)
**Storage**: Filesystem only (no database)
**Testing**: pytest with podman-compose
**Target Platform**: macOS/Linux development
**Project Type**: Single (Option 1 - utility/templates repository)
**Performance Goals**: N/A (file operations)
**Constraints**: Must preserve git history, quality gates must pass
**Scale/Scope**: ~100 files affected by reorganization

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (single repository)
- Using framework directly? Yes - standard Python tooling
- Single data model? Yes - filesystem structure
- Avoiding patterns? Yes - no abstractions needed

**Architecture**:
- EVERY feature as library? N/A - file reorganization, no new code
- Libraries listed: N/A
- CLI per library: N/A
- Library docs: N/A

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes - validation tests before changes
- Git commits show tests before implementation? Yes
- Order: Contract→Integration→E2E→Unit strictly followed? Yes - validation contract first
- Real dependencies used? Yes - actual filesystem
- Integration tests for: Structure validation
- FORBIDDEN: None applicable

**Observability**:
- Structured logging included? N/A
- Frontend logs → backend? N/A
- Error context sufficient? Yes - validation script output

**Versioning**:
- Version number assigned? Will increment patch version
- BUILD increments on every change? Yes
- Breaking changes handled? No breaking changes (internal reorganization)

## Project Structure

### Documentation (this feature)
```
specs/002-repository-organization-improvements/
├── spec.md              ✓ Created
├── plan.md              ✓ This file
├── research.md          ✓ Created
├── data-model.md        ✓ Created
├── quickstart.md        ✓ Created
├── contracts/           ✓ Created
│   └── validation-contract.md
└── tasks.md             ⏳ Created by /tasks command
```

### Source Code (repository root)
```
# Target structure after implementation:

tests/                   # NEW
├── __init__.py
├── conftest.py
├── test_mcp_deduplication.py  # Moved from root
└── skills/
    └── __init__.py

docs/                    # REORGANIZED
├── research/            # was 00_draft-initial/
├── guides/              # was 10_draft-merged/
└── archived/            # was ARCHIVED/

README.md                # NEW
.gitignore               # UPDATED
TODO.md                  # KEPT (others archived)
```

**Structure Decision**: Option 1 (Single project) - this is a templates/utilities repository

## Phase 0: Outline & Research ✓

**Completed**: See [research.md](./research.md)

Key decisions:
1. Test structure: `tests/` at root with subdirectories
2. `.tmp/german/`: Add to .gitignore (local-only)
3. Documentation: Rename to `docs/{research,guides,archived}/`
4. TODO files: Consolidate to single `TODO.md`
5. Skill docs: Single `SKILL.md` per skill
6. README vs GEMINI: Separate files for different audiences

**Output**: research.md with all decisions documented ✓

## Phase 1: Design & Contracts ✓

**Completed**: See [data-model.md](./data-model.md) and [contracts/](./contracts/)

1. **Data model**: File structure transformations documented
2. **Validation contract**: Post-condition checks defined
3. **Quickstart**: Validation steps documented

**Output**:
- data-model.md ✓
- contracts/validation-contract.md ✓
- quickstart.md ✓

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do*

**Task Generation Strategy**:
- Generate tasks from data-model.md transformations
- Each directory change → task
- Each file operation → task
- Validation tasks at end

**Ordering Strategy**:
- Preparation first (backup, gitignore)
- Structure changes (directories, moves)
- Content creation (README.md)
- Validation last (quality gates)
- Mark [P] for parallel operations on independent paths

**Estimated Output**: 15-20 ordered tasks

**IMPORTANT**: Ready for /tasks command

## Complexity Tracking

*No violations - simple file reorganization*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | - | - |

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
- [x] Complexity deviations documented (none)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
