---
type: claude-context
directory: planning/shared-agentdb-symlink
purpose: BMAD planning documents for shared-agentdb-symlink feature
parent: ../CLAUDE.md
sibling_readme: README.md
children:
  - ARCHIVED/CLAUDE.md
---

# Claude Code Context: shared-agentdb-symlink Planning

## Purpose

BMAD planning documents for the shared-agentdb-symlink feature. Created during Phase 1 (Planning) in main repository on contrib branch.

## Directory Structure

```
planning/shared-agentdb-symlink/
├── requirements.md    # Business requirements (Analyst)
├── architecture.md    # Technical architecture (Architect)
├── epics.md          # Epic breakdown (PM)
├── CLAUDE.md         # This file
├── README.md         # Human-readable overview
└── ARCHIVED/         # Deprecated planning documents
```

## Files in This Directory

**requirements.md:**
- Problem statement and business context
- Functional requirements (FR-001, FR-002, ...)
- Non-functional requirements (performance, security, scalability)
- User stories and acceptance criteria
- Success criteria and constraints

**architecture.md:**
- System architecture and component design
- Technology stack with justifications
- Data models and API contracts
- Container architecture
- Security, error handling, testing strategies
- Deployment and observability

**epics.md:**
- Epic breakdown (E-001, E-002, ...)
- Epic scope, complexity, and priorities
- Dependencies between epics
- Implementation timeline and effort estimates

## Usage by SpecKit

These planning documents are used as input context by SpecKit (Phase 2) when creating specifications in feature worktrees:

1. SpecKit auto-detects this planning directory: `../planning/shared-agentdb-symlink/`
2. SpecKit reads requirements.md, architecture.md, epics.md
3. SpecKit conducts adaptive Q&A (5-8 questions vs 10-15 without BMAD)
4. SpecKit generates spec.md and plan.md aligned with this planning

**Token savings:** ~1,700-2,700 tokens per feature by reusing planning context

## Workflow Integration

**Phase 1 (BMAD Planning):** This directory created via create_planning.py
**Phase 2 (SpecKit):** Specifications reference this planning
**Phase 4 (As-Built):** update_asbuilt.py adds "As-Built" sections to these docs

## Related Documentation

- **[README.md](README.md)** - Human-readable overview of shared-agentdb-symlink planning

**Child Directories:**
- **[ARCHIVED/CLAUDE.md](ARCHIVED/CLAUDE.md)** - Archived planning documents

## Related Skills

- workflow-orchestrator
- bmad-planner (created this directory)
- speckit-author (consumes this planning)
- workflow-utilities
