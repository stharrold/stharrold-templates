# Implementation Plan: Worktree-Aware Workflow and Skills System

**Branch**: `006-make-the-entire` | **Date**: 2025-11-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-make-the-entire/spec.md`

## Summary

Enable multiple Claude Code instances to work on different features concurrently in separate git worktrees without state conflicts. The solution creates a `.claude-state/` directory within each worktree to store mutable workflow state (DuckDB, workflow progress) while keeping skill definitions (`.claude/skills/`) shared and read-only.

## Technical Context

**Language/Version**: Python 3.11 (existing stack)
**Primary Dependencies**: DuckDB, pathlib, subprocess (existing)
**Storage**: DuckDB (per-worktree), JSON (workflow progress), filesystem
**Testing**: pytest with contract and integration tests
**Target Platform**: macOS/Linux (Podman container)
**Project Type**: Single project (Option 1)
**Performance Goals**: No measurable overhead (<10ms for worktree detection)
**Constraints**: Backward compatible with non-worktree repos
**Scale/Scope**: 2-10 concurrent worktrees per developer

## Constitution Check

**Simplicity**:
- Projects: 1 (existing skills system, no new projects)
- Using framework directly: Yes (git CLI, pathlib, DuckDB)
- Single data model: Yes (WorktreeContext dataclass)
- Avoiding patterns: Yes (no Repository/UoW, direct file access)

**Architecture**:
- EVERY feature as library: Yes (new module in workflow-utilities)
- Libraries: `worktree_context.py` - worktree detection and state management
- CLI: Integrated into existing skill scripts
- Library docs: Updated CLAUDE.md

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor: Yes
- Order: Contract tests → Integration tests → Unit tests
- Real dependencies: Yes (actual git commands, real filesystem)
- Integration tests for: worktree_context module, state directory creation

**Observability**:
- Structured logging: Via existing skill logging
- Error context: Include worktree_id in all errors

**Versioning**:
- Version: Minor version bump (adds feature, backward compatible)
- Breaking changes: None (new optional functionality)

## Project Structure

### Documentation (this feature)
```
specs/006-make-the-entire/
├── plan.md              # This file
├── research.md          # ✓ Complete
├── data-model.md        # ✓ Complete
├── quickstart.md        # ✓ Complete
├── contracts/           # ✓ Complete
│   ├── worktree_context.md
│   └── state_integration.md
└── tasks.md             # Phase 2 output (/tasks command)
```

### Source Code Changes
```
.claude/skills/workflow-utilities/scripts/
├── worktree_context.py      # NEW: Core detection module
└── workflow_progress.py     # NEW: Progress tracking in state dir

.claude/skills/agentdb-state-manager/scripts/
├── init_database.py         # UPDATE: Use state dir for DB
└── sync_engine.py           # UPDATE: Add worktree_id

.claude/skills/git-workflow-manager/scripts/
├── create_worktree.py       # UPDATE: Init state dir on create
└── worktree_agent_integration.py  # UPDATE: Use worktree_context

tests/
├── contract/
│   └── test_worktree_context_contract.py   # NEW
├── integration/
│   └── test_worktree_isolation.py          # NEW
└── unit/
    └── test_worktree_context.py            # NEW
```

## Phase 2: Task Planning Approach

**Task Generation Strategy**:
- Generate tasks from contracts (worktree_context.md, state_integration.md)
- Each contract function → contract test task [P]
- Each entity (WorktreeContext, StateDirectory) → model creation task [P]
- Each integration point → update task
- Implementation tasks to make tests pass

**Ordering Strategy**:
1. Contract tests for worktree_context module (fail first)
2. Implement worktree_context.py (make tests pass)
3. Integration tests for state directory isolation
4. Update dependent skills (agentdb, git-workflow-manager)
5. End-to-end validation via quickstart

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
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none needed)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
