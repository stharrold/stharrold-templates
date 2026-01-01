# Feature Specification: Remove Redundant TODO*.md System

**Feature Branch**: `007-remove-redundant-todo`
**Created**: 2025-11-23
**Status**: Draft
**Input**: User description: "Remove redundant TODO*.md system - archive existing files, update quality gates, and update GEMINI.md since GitHub Issues and Speckit tasks.md now provide superior task tracking"

## Execution Flow (main)
```
1. Parse user description from Input
   - Extracted: remove TODO*.md files, archive them, update quality gates, update docs
2. Extract key concepts from description
   - Actors: developers, CI/CD pipeline, Gemini Code
   - Actions: archive files, update quality gate, update documentation
   - Data: TODO*.md files, GEMINI.md, quality gate scripts
   - Constraints: maintain backward compatibility during transition
3. For each unclear aspect:
   - None identified - feature is well-defined cleanup task
4. Fill User Scenarios & Testing section
   - Primary flow: developer runs quality gates without TODO*.md requirement
5. Generate Functional Requirements
   - 7 requirements identified, all testable
6. Identify Key Entities
   - TODO*.md files, quality gate configuration, documentation
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
As a developer, I want the TODO*.md system removed from quality gates and documentation so that I can use GitHub Issues and Speckit tasks.md for task tracking without maintaining redundant TODO files with YAML frontmatter.

### Acceptance Scenarios
1. **Given** a repository with no TODO*.md files, **When** quality gates run, **Then** all gates pass without warnings about missing TODO files
2. **Given** existing TODO*.md files in the repository, **When** the cleanup is complete, **Then** they are archived to `docs/archived/` with date prefix
3. **Given** GEMINI.md references TODO*.md requirements, **When** the update is complete, **Then** no references to TODO*.md frontmatter requirements remain
4. **Given** a developer creates a new feature, **When** they follow the documented workflow, **Then** they use GitHub Issues and Speckit instead of TODO*.md files

### Edge Cases
- What happens when archived TODO files already exist in `docs/archived/`? -> Use timestamped prefix to avoid collisions
- How does system handle worktrees with local TODO*.md files? -> Each worktree archives independently

---

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST archive all existing TODO*.md files (excluding templates) to `docs/archived/` with date prefix
- **FR-002**: System MUST remove quality gate #5 (TODO frontmatter validation) from `run_quality_gates.py`
- **FR-003**: System MUST update GEMINI.md to remove all references to TODO*.md requirements
- **FR-004**: System MUST update AGENTS.md (synced copy) to reflect GEMINI.md changes
- **FR-005**: System MUST preserve TODO template files in `.gemini/skills/workflow-orchestrator/templates/` for historical reference or future use
- **FR-006**: System MUST update workflow scripts that reference TODO*.md to remove or skip those operations
- **FR-007**: Quality gates MUST pass after all changes are complete

### Key Entities
- **TODO*.md files**: Legacy task tracking files with YAML frontmatter (status, feature, branch) - being archived
- **Quality Gate #5**: The "TODO Frontmatter" validation in `run_quality_gates.py` - being removed
- **GEMINI.md / AGENTS.md**: AI assistant configuration files - being updated
- **Speckit tasks.md**: The replacement task tracking system in `specs/*/tasks.md` - already in use

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
