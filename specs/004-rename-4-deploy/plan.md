# Implementation Plan: Workflow Command Rename and Release Workflow

**Branch**: `004-rename-4-deploy` | **Date**: 2025-11-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-rename-4-deploy/spec.md`

## Summary

Rename `/4_deploy` to `/5_integrate` for semantic accuracy, and add `/6_release` and `/7_backmerge` commands to support daily release workflows. This separates the feature integration workflow (1-5) from the release workflow (6-7).

## Technical Context
**Language/Version**: Markdown (slash commands), Python 3.11 (pr_workflow.py)
**Primary Dependencies**: GitHub CLI (gh), git
**Storage**: N/A (file-based slash commands)
**Testing**: Manual workflow testing, quality gates
**Target Platform**: macOS/Linux (CLI)
**Project Type**: Single project (workflow automation)
**Performance Goals**: N/A (human-initiated commands)
**Constraints**: Must maintain backward compatibility during transition
**Scale/Scope**: 3 command files to modify, 2 new command files, documentation updates

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (workflow commands only)
- Using framework directly? Yes (Markdown + Python scripts)
- Single data model? Yes (slash command structure)
- Avoiding patterns? Yes (no abstractions needed)

**Architecture**:
- EVERY feature as library? N/A (workflow commands, not code library)
- Libraries listed: N/A
- CLI per library: N/A
- Library docs: N/A

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes (manual testing before/after)
- Git commits show tests before implementation? N/A (documentation change)
- Order: Contract->Integration->E2E->Unit strictly followed? N/A
- Real dependencies used? Yes (actual git operations)
- Integration tests for: N/A (documentation/workflow change)
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? Yes (pr_workflow.py has print statements)
- Frontend logs -> backend? N/A
- Error context sufficient? Yes

**Versioning**:
- Version number assigned? MINOR bump (new feature)
- BUILD increments on every change? Yes
- Breaking changes handled? Yes (rename with documentation update)

## Project Structure

### Documentation (this feature)
```
specs/004-rename-4-deploy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/tasks command)
```

### Source Code (repository root)
```
.claude/commands/workflow/
├── 0_specify.md         # Update workflow navigation
├── 1_plan.md            # Update workflow navigation
├── 2_tasks.md           # Update workflow navigation
├── 3_implement.md       # Update workflow navigation
├── 4_integrate.md       # RENAMED from 4_deploy.md
├── 5_release.md         # NEW
└── 6_backmerge.md       # NEW

.claude/skills/git-workflow-manager/scripts/
├── pr_workflow.py       # Existing (unchanged for /5_integrate)
├── release_workflow.py  # NEW (for /6_release)
└── backmerge_workflow.py # NEW (for /7_backmerge)
```

**Structure Decision**: Single project (Option 1)

## Phase 0: Outline & Research

**Research Topics**:
1. Current `/5_integrate` implementation and all references
2. Release workflow best practices (develop -> release -> main)
3. Backmerge patterns (PR + rebase hybrid)
4. Documentation update scope

**Output**: research.md with all findings consolidated

## Phase 1: Design & Contracts

**Entities**:
1. Slash Command files (Markdown with YAML frontmatter)
2. Python workflow scripts
3. Documentation files (CLAUDE.md, WORKFLOW.md, etc.)

**Contracts**:
1. `/5_integrate` - Same contract as current `/5_integrate`
2. `/6_release` - New contract for release workflow
3. `/7_backmerge` - New contract for backmerge workflow

**Output**: data-model.md, contracts/, quickstart.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Rename `/4_deploy.md` to `/5_integrate.md`
- Update content of `/5_integrate.md`
- Create `/6_release.md` with release workflow
- Create `/7_backmerge.md` with backmerge workflow
- Update navigation in commands 1-4
- Update all documentation references
- Create supporting Python scripts if needed

**Ordering Strategy**:
1. Rename command file (atomic operation)
2. Update renamed file content
3. Create new command files [P]
4. Update navigation in existing commands [P]
5. Update documentation files [P]
6. Test workflow end-to-end

**Estimated Output**: 15-20 numbered, ordered tasks in tasks.md

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Progress Tracking

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [x] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
