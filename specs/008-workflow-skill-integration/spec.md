# Feature Specification: Workflow Skill Integration

**Feature Branch**: `008-workflow-skill-integration`
**Created**: 2025-11-23
**Status**: Draft
**Input**: User description: "Integrate slash commands with skills system - replace .specify/ bash scripts with skill invocations (bmad-planner, speckit-author, git-workflow-manager, etc.), add AgentDB state tracking, use GitHub Issues for work item tracking"

## Execution Flow (main)
```
1. Parse user description from Input
   - Extracted: replace .specify/ scripts, integrate skills, add state tracking
2. Extract key concepts from description
   - Actors: developers, Claude Code, workflow orchestrator
   - Actions: invoke skills, track state, manage work items
   - Data: slash commands, skill scripts, AgentDB, GitHub Issues
   - Constraints: maintain workflow functionality, preserve existing skill APIs
3. For each unclear aspect:
   - None identified - comprehensive analysis completed in conversation
4. Fill User Scenarios & Testing section
   - Primary flow: developer runs /1_specify through /7_backmerge with skills
5. Generate Functional Requirements
   - 14 requirements identified, all testable
6. Identify Key Entities
   - Slash commands, skills, AgentDB, GitHub Issues
7. Run Review Checklist
   - All items pass
8. Return: SUCCESS (spec ready for planning)
```

---

## Quick Guidelines
- Focus on WHAT users need and WHY
- Avoid HOW to implement (no tech stack, APIs, code structure)
- Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a developer, I want the slash commands (/1_specify through /7_backmerge) to invoke the appropriate skills (bmad-planner, speckit-author, git-workflow-manager, etc.) so that I have a unified, state-tracked workflow instead of two disconnected systems (.specify/ and .claude/skills/).

### Acceptance Scenarios
1. **Given** a user runs `/1_specify "feature description"`, **When** the command executes, **Then** bmad-planner creates planning documents, git-workflow-manager creates a worktree, and AgentDB records the state transition
2. **Given** a user runs `/2_plan` in a worktree, **When** the command executes, **Then** speckit-author creates spec.md and plan.md with tasks, and AgentDB records the state
3. **Given** a user runs `/5_integrate`, **When** the PR is merged, **Then** git-workflow-manager cleans up the worktree without archiving TODO files (deprecated)
4. **Given** a user runs any slash command, **When** it completes, **Then** AgentDB contains a sync record for the workflow transition
5. **Given** .specify/ scripts exist, **When** the refactor is complete, **Then** .specify/ is archived and slash commands use skills directly

### Edge Cases
- What if bmad-planner is skipped (simple feature)? -> /1_specify has `--skip-planning` flag, proceeds directly to worktree creation
- What if user is not in a worktree for /2_plan? -> Error with instructions to run /1_specify first
- What if AgentDB is not initialized? -> Auto-initialize on first state write

---

## Requirements *(mandatory)*

### Functional Requirements

**Slash Command Updates:**
- **FR-001**: `/1_specify` MUST invoke bmad-planner for planning, git-workflow-manager for worktree creation, and record state in AgentDB
- **FR-002**: `/2_plan` MUST invoke tech-stack-adapter (if not cached), speckit-author for specifications, and record state in AgentDB
- **FR-003**: `/3_tasks` MUST validate task readiness from specs/*/plan.md and record state in AgentDB
- **FR-004**: `/4_implement` MUST use TodoWrite for execution, quality-enforcer for gates, and record state in AgentDB
- **FR-005**: `/5_integrate` MUST use git-workflow-manager for PR workflow, cleanup worktree without TODO archival, and record state in AgentDB
- **FR-006**: `/6_release` MUST use git-workflow-manager for release workflow and record state in AgentDB
- **FR-007**: `/7_backmerge` MUST use git-workflow-manager for backmerge workflow and record state in AgentDB

**Script Updates:**
- **FR-008**: `create_worktree.py` MUST have `--no-todo` flag (default=True) to skip TODO file creation
- **FR-009**: `cleanup_feature.py` MUST have `--no-archive` flag (default=True) to skip TODO archival
- **FR-010**: `create_specifications.py` MUST accept `--issue` flag for GitHub Issue linking (instead of `--todo-file`)

**State Tracking:**
- **FR-011**: AgentDB MUST have a `record_sync.py` script to record workflow transitions
- **FR-012**: AgentDB MUST have a `query_workflow_state.py` script to query current phase

**Deprecation:**
- **FR-013**: `.specify/` directory MUST be archived to `.specify/ARCHIVED/`
- **FR-014**: Scripts `sync_todo_to_db.py`, `todo_updater.py`, `workflow_archiver.py`, `workflow_registrar.py`, `sync_manifest.py` MUST be deprecated (moved to ARCHIVED/)

### Key Entities
- **Slash commands**: `/1_specify` through `/7_backmerge` in `.claude/commands/workflow/`
- **Skills**: bmad-planner, speckit-author, git-workflow-manager, quality-enforcer, tech-stack-adapter, workflow-utilities, agentdb-state-manager
- **AgentDB**: DuckDB database for workflow state tracking in `.claude-state/`
- **GitHub Issues**: Work item tracking (replaces TODO*.md)
- **.specify/**: Legacy bash scripts to be archived

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
