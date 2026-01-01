# Requirements: Enforce Planning Commit Before Worktree

**Date:** 2025-11-30
**Author:** stharrold
**Status:** Draft

## Business Context

### Problem Statement

The /1_specify workflow step creates planning documents and then creates a git worktree,
but there is no enforcement that the planning documents are committed and pushed before
the worktree is created. This can lead to worktrees that don't contain the planning docs.


### Success Criteria

- [ ] Worktree creation fails with clear error if planning docs not committed and pushed


### Stakeholders

- **Primary:** Gemini Code users running the workflow, developers using the workflow automation

- **Secondary:** [Who else is impacted? Other teams, systems, users?]

## Functional Requirements


### FR-001: Verify planning directory exists

**Priority:** High
**Description:** Check that planning/{slug}/ directory exists in the repository before creating worktree

**Acceptance Criteria:**
- [ ] create_worktree.py checks for planning/{slug}/ directory for feature worktrees
- [ ] Returns clear error message if directory does not exist
- [ ] Includes resolution guidance in error message


### FR-002: Verify no uncommitted changes

**Priority:** High
**Description:** Check that planning directory has no staged or unstaged changes

**Acceptance Criteria:**
- [ ] create_worktree.py runs git status on planning/{slug}/
- [ ] Returns error if any uncommitted changes detected
- [ ] Error message includes git commands to resolve


### FR-003: Verify branch is pushed

**Priority:** High
**Description:** Ensure local branch is not ahead of remote (changes are pushed)

**Acceptance Criteria:**
- [ ] create_worktree.py compares local and remote branch
- [ ] Returns error if local is ahead of remote
- [ ] Error message suggests git push command


### FR-004: Feature-only enforcement

**Priority:** Medium
**Description:** Only apply checks for feature worktrees, not release or hotfix

**Acceptance Criteria:**
- [ ] Checks are skipped for workflow_type release and hotfix
- [ ] Feature worktrees always run verification


## Non-Functional Requirements

### Performance

- Performance: Minimal overhead - 3 git commands max
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
