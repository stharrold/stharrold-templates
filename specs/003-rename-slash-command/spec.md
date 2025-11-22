# Feature Specification: Namespace Slash Commands to workflow/

**Feature Branch**: `003-rename-slash-command`
**Created**: 2025-11-22
**Status**: Draft
**Input**: User description: "rename slash-command workflow to workflow/deploy using namespace scoping: all project slash-commands renamed to workflow/ scope with navigation descriptions"

---

## Quick Guidelines
-  Focus on WHAT users need and WHY
- Avoid HOW to implement (no tech stack, APIs, code structure)
- Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a developer using this repository's workflow automation, I want all slash commands organized under a `workflow/` namespace so that:
1. Commands are logically grouped by purpose (workflow automation)
2. The help output shows commands as "(project:workflow)" for clear categorization
3. Each command's description shows navigation flow to adjacent commands
4. A new `/4_implement` command automates task execution from tasks.md
5. The `/workflow` command is renamed to `/5_integrate` to handle PR deployment
6. Commands use numeric prefixes (0_, 1_, 2_, 3_, 4_) to indicate execution order

### Acceptance Scenarios

1. **Given** the existing `.claude/commands/` structure, **When** I list available commands with `/help`, **Then** all workflow commands show "(project:workflow)" organization tag

2. **Given** I invoke `/1_specify`, **When** I view its description, **Then** it shows navigation: "(start) → workflow/1_specify → workflow/2_plan"

3. **Given** I invoke `/2_plan`, **When** I view its description, **Then** it shows navigation: "workflow/1_specify → workflow/2_plan → workflow/3_tasks"

4. **Given** I invoke `/3_tasks`, **When** I view its description, **Then** it shows navigation: "workflow/2_plan → workflow/3_tasks → workflow/4_implement"

5. **Given** I invoke `/4_implement` (NEW), **When** I view its description, **Then** it shows navigation: "workflow/3_tasks → workflow/4_implement → workflow/5_integrate"

6. **Given** the `/4_implement` command is run, **When** tasks.md exists, **Then** it:
   - Loads tasks from tasks.md
   - Executes tasks automatically in dependency order
   - Tracks progress and marks tasks complete
   - Runs quality gates before completion
   - User can stop/rewind via Claude Code controls

7. **Given** I invoke `/5_integrate` (previously `/workflow`), **When** I view its description, **Then** it shows navigation: "workflow/4_implement → workflow/5_integrate → (end)"

8. **Given** the `/5_integrate` command is run, **When** following the full deployment flow, **Then** it executes: contrib PR → develop → release PR → main; release PR → develop; contrib rebase on develop

### Edge Cases
- What happens when user invokes old `/workflow` command? → Command no longer exists, user informed of new `/5_integrate` name
- What happens when user invokes old `/specify`, `/plan`, `/tasks` commands? → Commands no longer exist, user informed of new `/1_specify`, `/2_plan`, `/3_tasks` names
- How does system handle documentation references to old command names? → CLAUDE.md and related docs must be updated
- What if `/4_implement` is run without tasks.md? → Error with guidance to run `/3_tasks` first
- What if tasks fail during `/4_implement`? → User can stop, fix, and resume; progress is tracked

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST move all workflow slash commands into `workflow/` subdirectory with numeric prefixes
- **FR-002**: System MUST rename existing commands with numeric order prefixes:
  - `specify.md` → `workflow/1_specify.md` (command: `/1_specify`)
  - `plan.md` → `workflow/2_plan.md` (command: `/2_plan`)
  - `tasks.md` → `workflow/3_tasks.md` (command: `/3_tasks`)
  - `workflow.md` → `workflow/5_integrate.md` (command: `/5_integrate`)
- **FR-003**: System MUST create NEW command `workflow/4_implement.md` (command: `/4_implement`) that:
  - Loads tasks from `specs/{feature}/tasks.md`
  - Executes tasks automatically in dependency order
  - Uses TodoWrite to track progress
  - Supports parallel execution for [P] marked tasks
  - Runs quality gates before completion
  - Errors if tasks.md doesn't exist (guides user to run `/3_tasks` first)
- **FR-004**: Each command description MUST include navigation format: "workflow/<prev> → workflow/<current> → workflow/<next>"
- **FR-005**: Each existing command MUST retain its functionality unchanged
- **FR-006**: The `/5_integrate` command MUST handle the complete deployment flow:
  - Create PR from contrib → develop
  - Create release PR from develop → main
  - Create PR from release → develop (backport)
  - Rebase contrib branch on develop
- **FR-007**: System MUST update CLAUDE.md to reflect new command names and navigation
- **FR-008**: System MUST update all internal references to use new command names (`/1_specify`, `/2_plan`, `/3_tasks`, `/4_implement`, `/5_integrate`)
- **FR-009**: The `order` frontmatter field MUST be preserved for command sequencing
- **FR-010**: The `prev` and `next` frontmatter fields MUST be updated to reference new command paths

### Key Entities

- **Slash Command File**: Markdown file defining a Claude Code command, containing frontmatter (description, order, prev, next) and execution instructions
- **Namespace Subdirectory**: Folder under `.claude/commands/` that groups related commands and appears as "(project:workflow)" in help output
- **Navigation Description**: Standard format showing command flow in each command's description field

---

## Scope Boundaries

### In Scope
- Renaming and reorganizing 4 existing slash command files
- Creating 1 new slash command (`/4_implement`)
- Updating command descriptions with navigation flow
- Updating CLAUDE.md workflow documentation
- Updating frontmatter references

### Out of Scope
- Changing existing command functionality (behavior remains identical)
- Modifying underlying skill scripts (beyond what /4_implement needs)

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

## Technical Note

Per Claude Code documentation: Subdirectories create organizational namespaces that appear in help output as "(project:subdirectory)" but do not change the command invocation syntax. Commands are invoked by filename: `/1_specify`, `/2_plan`, `/3_tasks`, `/4_implement`, `/5_integrate`. The numeric prefixes ensure clear execution order.

**5-Command Workflow**:
```
/1_specify → /2_plan → /3_tasks → /4_implement → /5_integrate
   spec       design     tasks      execute        deploy
```
