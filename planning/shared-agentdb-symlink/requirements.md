# Requirements: Shared Agentdb Symlink

**Date:** 2025-11-30
**Author:** stharrold
**Status:** Draft

## Business Context

### Problem Statement

Each worktree has an isolated .claude-state/agentdb.duckdb that is independent from the main repo's AgentDB.
This means contrib cannot see what workflows are running in worktrees, worktrees cannot see each other's status,
and there is no unified view of workflow state across all Claude Code instances working on the same project.


### Success Criteria

- [ ] All Claude Code instances (contrib and worktrees) can query a unified AgentDB to see workflow state across all sessions


### Stakeholders

- **Primary:** Claude Code users running multiple concurrent sessions, developers using workflow automation with worktrees

- **Secondary:** [Who else is impacted? Other teams, systems, users?]

## Functional Requirements


### FR-001: Symlink AgentDB in worktrees

**Priority:** High
**Description:** When creating a worktree, create a symlink from worktree's agentdb.duckdb to main repo's agentdb.duckdb

**Acceptance Criteria:**
- [ ] create_worktree.py creates symlink instead of new database file
- [ ] Symlink points to main repo's .claude-state/agentdb.duckdb
- [ ] Worktree can read/write through symlink


### FR-002: Main repo AgentDB as source of truth

**Priority:** High
**Description:** The main repo (contrib) holds the canonical AgentDB that all worktrees link to

**Acceptance Criteria:**
- [ ] Main repo .claude-state/agentdb.duckdb is the primary database
- [ ] All workflow state from all sessions stored in this one database
- [ ] Database includes worktree_id column to identify source


### FR-003: Cross-session visibility

**Priority:** High
**Description:** Any session can query workflow state from all other sessions

**Acceptance Criteria:**
- [ ] query_workflow_state.py shows state from all worktrees
- [ ] Can filter by worktree_id if needed
- [ ] Status output indicates which worktree each record came from


### FR-004: Handle symlink in worktree_context

**Priority:** Medium
**Description:** worktree_context.py should resolve symlinks when getting database path

**Acceptance Criteria:**
- [ ] get_state_dir() works correctly with symlinks
- [ ] Database connections work through symlink
- [ ] No special handling needed by callers


## Non-Functional Requirements

### Performance

- Performance: No significant overhead - symlink resolution is fast
- Concurrency: [e.g., 100 simultaneous users]

### Security

- Authentication: [e.g., JWT tokens, OAuth 2.0]
- Authorization: [e.g., Role-based access control]
- Data encryption: [e.g., At rest and in transit]
- Input validation: [e.g., JSON schema validation]

### Scalability

- Horizontal scaling: [Yes/No, explain approach]
- Database sharding: [Required? Strategy?]
- Cache strategy: [e.g., Redis for session data]

### Reliability

- Uptime target: [e.g., 99.9%]
- Error handling: [Strategy for failures]
- Data backup: [Frequency, retention]

### Maintainability

- Code coverage: [e.g., ≥80%]
- Documentation: [API docs, architecture docs]
- Testing: [Unit, integration, e2e strategies]

## Constraints

### Technology

- Programming language: Python 3.11+
- Package manager: uv
- Framework: [e.g., FastAPI, Flask, Django]
- Database: [e.g., SQLite, PostgreSQL]
- Container: Podman

### Budget

[Any cost constraints or considerations]

### Timeline

- Target completion: [Date or duration]
- Milestones: [Key dates]

### Dependencies

- External systems: [APIs, services this depends on]
- Internal systems: [Other features, modules]
- Third-party libraries: [Key dependencies]

## Out of Scope

[Explicitly state what this feature will NOT include. This prevents scope creep.]

- [Feature or capability NOT in scope]
- [Future enhancement to consider later]
- [Related but separate concern]

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| [Risk description] | High/Med/Low | High/Med/Low | [How to prevent or handle] |
| [Risk description] | High/Med/Low | High/Med/Low | [How to prevent or handle] |

## Data Requirements

### Data Entities

[Describe the main data entities this feature will work with]

### Data Volume

[Expected data size, growth rate]

### Data Retention

[How long to keep data, archive strategy]

## User Stories

### As a [user type], I want [goal] so that [benefit]

**Scenario 1:** [Happy path]
- Given [context]
- When [action]
- Then [expected result]

**Scenario 2:** [Alternative path]
- Given [context]
- When [action]
- Then [expected result]

**Scenario 3:** [Error condition]
- Given [context]
- When [action]
- Then [expected error handling]

## Assumptions

[List any assumptions being made about users, systems, or environment]

- Assumption 1: [e.g., Users have modern browsers]
- Assumption 2: [e.g., Network connectivity is reliable]
- Assumption 3: [e.g., Input data follows expected format]

## Questions and Open Issues

- [ ] Question 1: [Unresolved question requiring input]
- [ ] Question 2: [Decision needed before implementation]

## Approval

- [ ] Product Owner review
- [ ] Technical Lead review
- [ ] Security review (if applicable)
- [ ] Ready for implementation
