---
version: 1.0
last_updated: 2025-01-27T00:00:00Z
agent_context:
  project: "PROJECT_NAME"
  primary_language: "python"
  tech_stack: []
  environment: "development"
auto_compact_at: 95
---

# TODO-FOR-AI

## 🔴 Critical Priority
<!-- Security issues, production bugs, data loss risks -->

### TASK-001: [Example - Replace with actual task]
- **Status**: pending
- **Created**: 2025-01-27
- **Context**: [Describe the problem and why it's critical]
- **Files**: `path/to/relevant/files`
- **Acceptance Criteria**:
  - [ ] First requirement
  - [ ] Second requirement
  - [ ] Tests pass
- **Notes**: [Any additional context or constraints]

## 🟡 High Priority
<!-- Feature blocking, performance issues, user-facing bugs -->

### TASK-002: [Example task title]
- **Status**: pending
- **Created**: 2025-01-27
- **Dependencies**: None
- **Context**: [Why this needs attention soon]
- **Files**: `src/`, `tests/`
- **Acceptance Criteria**:
  - [ ] Implementation complete
  - [ ] Tests written
  - [ ] Documentation updated
- **Estimated Tokens**: 5000

## 🟢 Normal Priority
<!-- Regular development tasks, refactoring, improvements -->

### TASK-003: [Example task]
- **Status**: pending
- **Created**: 2025-01-27
- **Context**: [Standard development work]
- **Acceptance Criteria**:
  - [ ] Feature implemented
  - [ ] Code reviewed
  - [ ] Deployed to staging

## 🔵 Low Priority / Backlog
<!-- Nice-to-have features, minor improvements, technical debt -->

### TASK-004: [Example enhancement]
- **Status**: pending
- **Created**: 2025-01-27
- **Type**: enhancement
- **Context**: [Why this would be beneficial]

## 🚧 In Progress
<!-- Tasks currently being worked on - agents move items here when starting -->

<!-- Move active tasks here with:
- **Started**: 2025-01-27T10:30:00Z
- **Session**: [session-id or agent-id]
-->

## ⏸️ Blocked
<!-- Tasks that cannot proceed due to external dependencies -->

<!-- Example:
### TASK-XXX: [Blocked task]
- **Status**: blocked
- **Blocker**: [What's blocking this task]
- **Created**: 2025-01-27
- **Context**: [Original context]
-->

---

## Completed Tasks Archive

<details>
<summary>View completed tasks (0)</summary>

<!-- Completed tasks move here with metrics:
### ✅ TASK-000: Initial setup
- **Completed**: 2025-01-27
- **Time Taken**: 2 hours
- **Token Usage**: 12,500
- **Result**: [Brief outcome summary]
- **Lessons**: [Any insights for future tasks]
-->

</details>

---

## Agent Instructions

When processing this TODO list:

1. **At Session Start**:
   - Review all sections in priority order
   - Check for blocked tasks that may be unblocked
   - Move any abandoned "In Progress" tasks back to appropriate priority

2. **When Starting a Task**:
   - Move task to "🚧 In Progress" section
   - Add started timestamp and session ID
   - Update status to `in_progress`

3. **During Task Execution**:
   - Check off completed acceptance criteria
   - Update notes with discoveries or blockers
   - Reference task ID in commit messages

4. **When Completing a Task**:
   - Move to "Completed Tasks Archive"
   - Record time taken and token usage
   - Add brief result summary
   - Update any dependent tasks

5. **When Blocked**:
   - Move task to "⏸️ Blocked" section
   - Clearly document the blocker
   - Create new task for blocker if needed

6. **Maintenance**:
   - Archive completed tasks to `TODO-ARCHIVE.md` when > 20 items
   - Update `last_updated` timestamp in frontmatter
   - Compact descriptions that exceed 500 tokens

## Task Status Definitions

- **pending**: Not started, available for work
- **in_progress**: Currently being worked on
- **blocked**: Cannot proceed due to dependency
- **completed**: All acceptance criteria met
- **cancelled**: No longer needed (archive with reason)

## Priority Guidelines

- **🔴 Critical**: Fix within 24 hours - security, data loss, production down
- **🟡 High**: Fix within 3 days - blocking features, degraded performance  
- **🟢 Normal**: Fix within sprint - standard development work
- **🔵 Low**: Fix when convenient - improvements, nice-to-haves

## Token Budget Guidelines

- Small task: < 5,000 tokens
- Medium task: 5,000 - 20,000 tokens  
- Large task: 20,000 - 50,000 tokens
- Epic: > 50,000 tokens (consider breaking down)

---

## Notes for Humans

- This file is optimized for AI agents but remains human-readable
- Commit this file after AI sessions to track progress
- Use task IDs (TASK-XXX) in related commits and PRs
- Consider integrating with your issue tracker via GitHub Actions or webhooks