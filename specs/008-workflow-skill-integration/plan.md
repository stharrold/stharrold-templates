# Implementation Plan: Workflow Skill Integration

**Branch**: `008-workflow-skill-integration` | **Date**: 2025-11-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-workflow-skill-integration/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → SUCCESS: Spec loaded from specs/008-workflow-skill-integration/spec.md
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → SUCCESS: No clarifications needed (design analyzed in conversation)
   → Project Type: single (script updates + slash command rewrites)
3. Evaluate Constitution Check section below
   → SUCCESS: Simplification by unifying two systems into one
   → Update Progress Tracking: Initial Constitution Check ✓
4. Execute Phase 0 → research.md
   → SUCCESS: research.md generated with analysis from conversation
5. Execute Phase 1 → contracts, data-model.md, quickstart.md
   → SUCCESS: All Phase 1 artifacts generated
6. Re-evaluate Constitution Check section
   → SUCCESS: Design is simpler (one system instead of two)
   → Update Progress Tracking: Post-Design Constitution Check ✓
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → SUCCESS: Task approach documented below
8. STOP - Ready for /tasks command
```

## Summary

Integrate slash commands (/1_specify through /7_backmerge) with the skills system, replacing the disconnected .specify/ bash scripts with direct skill invocations. Add AgentDB state tracking for workflow transitions. Use GitHub Issues for work item tracking (TODO*.md already deprecated).

## Technical Context
**Language/Version**: Python 3.11 (existing scripts), Markdown (slash commands)
**Primary Dependencies**: Existing skills (bmad-planner, speckit-author, git-workflow-manager, etc.)
**Storage**: AgentDB (DuckDB) for state, GitHub Issues for work items
**Testing**: pytest (verify skills callable), manual (verify workflow)
**Target Platform**: Claude Code CLI
**Project Type**: single (slash command rewrites + script flag additions)
**Performance Goals**: N/A (workflow orchestration)
**Constraints**: Must not break existing skill APIs
**Scale/Scope**: 7 slash commands, ~5 script flag additions, 2 new AgentDB scripts

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 0 new (unifying existing systems)
- Using framework directly? Yes - existing skill scripts
- Single data model? Yes - AgentDB sync schema (already exists)
- Avoiding patterns? Yes - direct script calls

**Architecture**:
- EVERY feature as library? N/A - modifying existing skills
- Libraries listed: None new
- CLI per library: N/A
- Library docs: N/A

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes - verify skills callable first
- Git commits show tests before implementation? Yes - test skill invocations
- Order: Contract→Integration→E2E→Unit strictly followed? N/A - using existing tests
- Real dependencies used? Yes - actual skill scripts
- Integration tests for: Workflow flow tests exist
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? Yes - AgentDB audit trail
- Frontend logs → backend? N/A
- Error context sufficient? Yes - skill scripts have error handling

**Versioning**:
- Version number assigned? Will increment via release workflow
- BUILD increments on every change? Yes
- Breaking changes handled? Yes - graceful deprecation of .specify/

## Project Structure

### Documentation (this feature)
```
specs/008-workflow-skill-integration/
├── spec.md              # This file ✓
├── plan.md              # This file ✓
├── research.md          # Phase 0 output ✓
├── data-model.md        # Phase 1 output ✓
├── quickstart.md        # Phase 1 output ✓
├── contracts/           # Phase 1 output ✓
│   ├── slash-commands.md
│   └── state-tracking.md
└── tasks.md             # Phase 2 output (/tasks command)
```

### Source Code Changes
```
Files to modify:
├── .claude/commands/workflow/
│   ├── 1_specify.md                    # Rewrite to use skills
│   ├── 2_plan.md                       # Rewrite to use skills
│   ├── 3_tasks.md                      # Rewrite to use skills
│   ├── 4_implement.md                  # Add AgentDB recording
│   ├── 5_integrate.md                  # Add cleanup_feature.py call
│   ├── 6_release.md                    # Add AgentDB recording
│   └── 7_backmerge.md                  # Add AgentDB recording
├── .claude/skills/git-workflow-manager/scripts/
│   ├── create_worktree.py              # Add --no-todo flag
│   └── cleanup_feature.py              # Add --no-archive flag
├── .claude/skills/speckit-author/scripts/
│   └── create_specifications.py        # Add --issue flag, remove --todo-file
├── .claude/skills/agentdb-state-manager/scripts/
│   ├── record_sync.py                  # NEW: Record workflow transitions
│   └── query_workflow_state.py         # NEW: Query current phase
└── .specify/                           # Archive to ARCHIVED/
```

**Structure Decision**: Single project (script modifications + slash command rewrites)

## Phase 0: Outline & Research
✓ COMPLETE - See [research.md](./research.md)

Key findings:
- 7 slash commands to rewrite
- 3 scripts need flag additions
- 2 new AgentDB scripts needed
- .specify/ to archive (4 bash scripts, templates)
- 5 workflow-utilities scripts to deprecate

## Phase 1: Design & Contracts
✓ COMPLETE - See artifacts:
- [data-model.md](./data-model.md) - Skill invocation mapping
- [contracts/slash-commands.md](./contracts/slash-commands.md) - Slash command contracts
- [contracts/state-tracking.md](./contracts/state-tracking.md) - AgentDB contracts
- [quickstart.md](./quickstart.md) - Validation scenarios

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Group by: Slash commands (7), Script flags (3), New scripts (2), Deprecation (2)
- ~25-30 tasks expected (comprehensive refactor)
- Some tasks can run in parallel (different files)

**Ordering Strategy**:
1. Add script flags first (prerequisites for slash commands)
2. Create new AgentDB scripts (prerequisites for state tracking)
3. Rewrite slash commands (main work)
4. Archive .specify/ (cleanup)
5. Deprecate workflow-utilities scripts (cleanup)
6. Verify workflow end-to-end

**Estimated Output**: 25-30 ordered tasks in tasks.md

## Slash Command → Skill Mapping

| Command | Skills Invoked | State Record |
|---------|----------------|--------------|
| `/1_specify` | tech-stack-adapter, bmad-planner, git-workflow-manager | `phase_1_specify` |
| `/2_plan` | tech-stack-adapter, speckit-author | `phase_2_plan` |
| `/3_tasks` | workflow-utilities (validation only) | `phase_3_tasks` |
| `/4_implement` | quality-enforcer, git-workflow-manager | `phase_4_implement` |
| `/5_integrate` | git-workflow-manager, quality-enforcer | `phase_5_integrate` |
| `/6_release` | git-workflow-manager, quality-enforcer | `phase_6_release` |
| `/7_backmerge` | git-workflow-manager | `phase_7_backmerge` |

## Complexity Tracking
*This feature UNIFIES complexity (two systems → one)*

| Aspect | Before | After |
|--------|--------|-------|
| Specification systems | 2 (.specify/, skills) | 1 (skills only) |
| State tracking | TODO*.md + AgentDB | AgentDB only |
| Work item tracking | TODO*.md + GitHub Issues | GitHub Issues only |
| Bash scripts to maintain | 4 (.specify/) | 0 |

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
