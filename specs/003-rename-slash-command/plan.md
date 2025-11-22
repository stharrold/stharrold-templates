# Implementation Plan: Namespace Slash Commands

**Branch**: `003-rename-slash-command` | **Date**: 2025-11-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-rename-slash-command/spec.md`

## Summary

Reorganize project slash commands into `workflow/` namespace subdirectory with numeric prefixes (0_, 1_, 2_, 3_, 4_) for explicit execution order. Create new `/4_implement` command for automated task execution. Update all command descriptions to include navigation flow showing previous and next commands.

## Technical Context

**Language/Version**: Markdown (slash command files)
**Primary Dependencies**: Claude Code CLI
**Storage**: N/A (file-based configuration)
**Testing**: Manual verification via Claude Code CLI
**Target Platform**: Claude Code CLI (macOS/Linux/Windows)
**Project Type**: single (configuration files only)
**Performance Goals**: N/A
**Constraints**: N/A
**Scale/Scope**: 5 slash command files (4 existing + 1 new) + documentation

## Constitution Check

**Simplicity**:
- Projects: 0 (file reorganization only)
- Using framework directly? Yes (Claude Code slash commands)
- Single data model? Yes (markdown files with YAML frontmatter)
- Avoiding patterns? Yes (no abstractions needed)

**Architecture**:
- EVERY feature as library? N/A (configuration change)
- Libraries listed: None (no code)
- CLI per library: N/A
- Library docs: N/A

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? N/A (no code)
- Order: Manual verification via quickstart.md
- Integration tests: Verify commands work in Claude Code

**Observability**: N/A (configuration files)

**Versioning**: Inherits repository version

## Project Structure

### Documentation (this feature)
```
specs/003-rename-slash-command/
├── plan.md              # This file
├── research.md          # Phase 0 output ✓
├── data-model.md        # Phase 1 output ✓
├── quickstart.md        # Phase 1 output ✓
└── tasks.md             # Phase 2 output (/tasks command)
```

### Source Changes (repository)
```
.claude/commands/
├── specify.md     → REMOVE
├── plan.md        → REMOVE
├── tasks.md       → REMOVE
├── workflow.md    → REMOVE
└── workflow/      → CREATE
    ├── 0_specify.md
    ├── 1_plan.md
    ├── 2_tasks.md
    ├── 3_implement.md   ← NEW (automated task execution)
    └── 4_deploy.md

CLAUDE.md          → UPDATE (slash commands section)
```

**Structure Decision**: N/A - file reorganization only

## Phase 0: Research Complete ✓

See [research.md](./research.md) for:
- Claude Code namespace scoping documentation
- Frontmatter schema decisions
- Documentation update requirements

## Phase 1: Design Complete ✓

See [data-model.md](./data-model.md) for:
- Slash command file entity definition
- Directory structure before/after
- Frontmatter examples for each command

See [quickstart.md](./quickstart.md) for:
- Verification steps
- Success criteria checklist

**Note**: No API contracts needed - this is a file reorganization feature.

## Phase 2: Task Planning Approach

**Task Generation Strategy**:
- Create workflow/ directory
- Move and rename each existing command file (4 files)
- Create new /4_implement command file
- Update frontmatter in each file (descriptions with navigation)
- Update internal command references within each file
- Update CLAUDE.md documentation
- Remove old command files
- Verify via quickstart.md

**Ordering Strategy**:
1. Create directory structure first
2. Create new files with updated content [P] (parallel - independent files)
3. Create /4_implement.md (new command)
4. Update CLAUDE.md documentation
5. Remove old files (after new files verified)
6. Run verification

**Estimated Output**: 12-14 numbered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Complexity Tracking

*No violations - this is a simple file reorganization*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

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
- [x] Complexity deviations documented (none needed)

---
*Ready for /tasks command*
