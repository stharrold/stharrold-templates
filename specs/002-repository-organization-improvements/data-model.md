# Data Model: Repository Organization Improvements

**Feature**: 002-repository-organization-improvements
**Date**: 2025-11-21

## Overview

This feature involves file and directory reorganization. No database entities or application data models are required. The "data model" here describes the file structure transformations.

## File Structure Transformations

### Entity: Test Directory

**Current State**: No `tests/` directory; test file at root

| Attribute | Before | After |
|-----------|--------|-------|
| Location | `test_mcp_deduplication.py` (root) | `tests/test_mcp_deduplication.py` |
| Structure | Flat | Hierarchical with subdirectories |
| Config | `testpaths = ["tests"]` in pyproject.toml | Same (already configured) |

**Target Structure**:
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_mcp_deduplication.py
└── skills/                  # Future skill tests
    └── __init__.py
```

### Entity: Documentation Directory

**Current State**: Numeric-prefixed directories at root

| Attribute | Before | After |
|-----------|--------|-------|
| Research docs | `00_draft-initial/` | `docs/research/` |
| Guide docs | `10_draft-merged/` | `docs/guides/` |
| Archived docs | `ARCHIVED/` | `docs/archived/` |

**Target Structure**:
```
docs/
├── research/       # Exploratory documents
├── guides/         # Production documentation
│   ├── mcp/
│   ├── credentials/
│   └── implementation/
└── archived/       # Historical versions
```

### Entity: Gitignore Patterns

**Current State**: Missing common patterns

| Pattern | Status |
|---------|--------|
| `.DS_Store` | Missing → Add |
| `.tmp/` | Missing → Add |
| `__pycache__/` | Present |
| `.venv/` | Present |

### Entity: TODO Files

**Current State**: Multiple files at root

| File | Action |
|------|--------|
| `TODO.md` | Keep (primary) |
| `TODO_FOR_issue-13-*.md` | Archive |
| `TODO_FOR_issue-15-*.md` | Archive |

### Entity: Skill Documentation

**Current State**: Multiple docs per skill

| Current Files | Target |
|---------------|--------|
| `SKILL.md` | Keep (primary) |
| `README.md` | Merge into SKILL.md |
| `GEMINI.md` | Merge into SKILL.md |
| `CHANGELOG.md` | Append to SKILL.md |
| `ARCHIVED/` | Compress or delete |

### Entity: Root README

**Current State**: Missing

**Target**: New `README.md` at repository root

| Section | Content |
|---------|---------|
| Title | Project name + badges |
| Description | 1-paragraph overview |
| Prerequisites | podman, git, gh versions |
| Quick Start | 4 commands to get running |
| Documentation | Links to GEMINI.md, WORKFLOW.md |
| Contributing | Link to CONTRIBUTING.md |

## Validation Rules

1. **Test structure**: `pytest` must discover and run tests
2. **Documentation**: All internal links must resolve
3. **Gitignore**: No `.DS_Store` files in git status
4. **Quality gates**: All 6 gates must pass post-reorganization

## State Transitions

```
Current Repository State
         │
         ▼
┌─────────────────────┐
│ Add .gitignore      │
│ patterns            │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Create tests/       │
│ structure           │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Rename docs/        │
│ directories         │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Consolidate TODOs   │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Create README.md    │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Consolidate skill   │
│ documentation       │
└─────────────────────┘
         │
         ▼
Final Repository State
