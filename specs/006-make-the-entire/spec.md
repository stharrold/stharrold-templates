# Feature Specification: Worktree-Aware Workflow and Skills System

**Feature Branch**: `006-make-the-entire`
**Created**: 2025-11-23
**Status**: Draft
**Input**: User description: "make the entire workflow and skills system worktree-aware"

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a developer running multiple Gemini Code instances concurrently, I want each instance working in a separate git worktree to have completely isolated state and context, so that multiple features can be developed in parallel without conflicts or interference.

### Acceptance Scenarios
1. **Given** a repository with the skills system, **When** a user creates two git worktrees for different features, **Then** each worktree maintains independent workflow state (TODO files, DuckDB state, progress tracking).

2. **Given** two Gemini Code instances running in separate worktrees, **When** both instances execute `/workflow/all`, **Then** each instance tracks only its own feature's progress without affecting the other.

3. **Given** a feature worktree with in-progress tasks, **When** the user switches to a different worktree, **Then** the original worktree's state is preserved and the new worktree has its own independent state.

4. **Given** worktree-specific state files, **When** the worktree is removed, **Then** only that worktree's state is cleaned up while the main repository and other worktrees remain unaffected.

5. **Given** shared skill definitions in `.gemini/skills/`, **When** accessed from any worktree, **Then** the skill code is read-only and shared, but any state the skill generates is worktree-specific.

### Edge Cases
- What happens when a worktree is created from a branch that already has state? State should be cloned or initialized fresh based on configuration.
- How does the system handle state when a worktree is pruned without cleanup? Orphaned state should be detectable and cleanable.
- What happens if two worktrees attempt to access shared resources simultaneously? Shared resources (skill definitions) should be read-only; state should be isolated.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect whether it is running in a git worktree or the main repository working directory.

- **FR-002**: System MUST store all mutable workflow state (DuckDB, progress files, TODO tracking) in a worktree-specific location rather than the shared repository root.

- **FR-003**: System MUST allow skill definitions (`.gemini/skills/`) to remain shared and read-only across all worktrees.

- **FR-004**: System MUST scope `agentdb-state-manager` DuckDB databases to the current worktree path.

- **FR-005**: System MUST ensure TODO*.md files are tracked per-worktree (or per-feature-branch) without collision.

- **FR-006**: System MUST provide a mechanism to detect and clean up orphaned worktree state when worktrees are removed.

- **FR-007**: System MUST maintain backward compatibility - repositories not using worktrees should function identically to current behavior.

- **FR-008**: System MUST document the worktree-aware architecture so users understand where state is stored.

- **FR-009**: System MUST ensure `/workflow/all` and all slash commands operate correctly when invoked from any worktree.

- **FR-010**: System MUST prevent workflow state conflicts when multiple Gemini Code instances run concurrently in different worktrees.

### Key Entities

- **Worktree Context**: The execution environment - either the main repository or a git worktree, identified by its filesystem path and associated git branch.

- **Workflow State**: Mutable data including DuckDB databases, TODO files, progress tracking, and any temporary artifacts generated during workflow execution.

- **Shared Skills**: Read-only skill definitions in `.gemini/skills/` that are shared across all worktrees without duplication.

- **Worktree State Directory**: A per-worktree location (e.g., `.gemini-state/` within each worktree) where all mutable state is stored.

---

## Review & Acceptance Checklist

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

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
