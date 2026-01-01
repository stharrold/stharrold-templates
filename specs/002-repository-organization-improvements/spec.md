# Feature Specification: Repository Organization Improvements

**Feature Branch**: `002-repository-organization-improvements`
**Created**: 2025-11-21
**Status**: Draft
**Input**: User description: "Repository organization improvements: add tests/ directory structure, add .DS_Store to gitignore, clean up .tmp/german/, consolidate TODO files, flatten draft hierarchy to docs/, add root README.md, reduce skill documentation redundancy"

---

## � Quick Guidelines
-  Focus on WHAT users need and WHY
- L Avoid HOW to implement (no tech stack, APIs, code structure)
- =e Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a developer or AI agent working with this repository, I want a clean, well-organized codebase with proper test structure, clear documentation entry points, and minimal redundancy so that I can navigate efficiently, run tests reliably, and understand the project structure quickly.

### Acceptance Scenarios
1. **Given** a fresh clone of the repository, **When** a developer looks for tests, **Then** they find a clear `tests/` directory at root level with organized test files
2. **Given** a macOS user working in the repository, **When** they run git status, **Then** no `.DS_Store` files appear in tracked or untracked lists
3. **Given** a developer exploring the repository root, **When** they look for project introduction, **Then** they find a `README.md` with quick start instructions
4. **Given** a developer needing to understand a skill, **When** they navigate to a skill directory, **Then** they find a single consolidated documentation file (not 3-4 separate files)
5. **Given** a developer looking for documentation, **When** they browse the `docs/` folder, **Then** they find a flat, intuitive structure without numeric prefixes
6. **Given** the repository after cleanup, **When** listing root-level TODO files, **Then** only a single `TODO.md` exists (or none if using GitHub Issues exclusively)

### Edge Cases
- What happens when tests reference paths that change during reorganization?
- How does the system handle existing links/references to old documentation paths?
- What happens to archived content that may still be referenced?

## Requirements *(mandatory)*

### Functional Requirements

#### Test Structure (High Priority)
- **FR-001**: Repository MUST have a `tests/` directory at root level
- **FR-002**: Test files MUST be organized to mirror source structure (e.g., `tests/skills/`, `tests/tools/`)
- **FR-003**: Existing test file `test_mcp_deduplication.py` MUST be moved into the new structure
- **FR-004**: Test configuration MUST work with `podman-compose run --rm dev pytest`

#### Gitignore Cleanup (High Priority)
- **FR-005**: `.gitignore` MUST include `.DS_Store` pattern
- **FR-006**: All existing `.DS_Store` files MUST be removed from tracking and filesystem

#### Temporary Directory Cleanup (High Priority)
- **FR-007**: `.tmp/german/` directory MUST be evaluated and either deleted, moved to a branch, or added to `.gitignore`
- **FR-008**: Decision on `.tmp/german/` MUST be documented (rationale preserved)

#### TODO Consolidation (Medium Priority)
- **FR-009**: Root-level TODO files MUST be consolidated into a single `TODO.md` or migrated to GitHub Issues
- **FR-010**: Issue-specific TODO files (`TODO_FOR_issue-*.md`) MUST be linked to their respective GitHub Issues or archived

#### Documentation Restructure (Medium Priority)
- **FR-011**: Draft folders (`00_draft-initial/`, `10_draft-merged/`) MUST be reorganized into `docs/` with clear subdirectories
- **FR-012**: Numeric prefixes MUST be removed from folder names
- **FR-013**: New structure MUST have intuitive names: `docs/guides/`, `docs/research/`, `docs/archived/`

#### Root README (Medium Priority)
- **FR-014**: Repository MUST have a `README.md` at root level
- **FR-015**: README.md MUST include: project description, prerequisites, quick start, link to CONTRIBUTING.md
- **FR-016**: README.md MUST be written for human developers (CLAUDE.md remains for AI agents)

#### Skill Documentation (Low Priority)
- **FR-017**: Each skill's documentation MUST be consolidated from multiple files (CLAUDE.md, README.md, SKILL.md) into a single file
- **FR-018**: Archived skill documentation in `ARCHIVED/` subdirectories MUST be compressed or removed if obsolete

### Key Entities

- **Test Suite**: Collection of pytest test files validating repository functionality
- **Documentation Set**: Markdown files providing guidance for humans and AI agents
- **Skill**: Self-contained module in `.gemini/skills/` with scripts and documentation
- **TODO Item**: Task or work item tracked for implementation

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
