# Data Model: Remove Redundant TODO*.md System

**Feature Branch**: `007-remove-redundant-todo`
**Date**: 2025-11-23

---

## Overview

This feature is a **cleanup/removal** operation, not a new data system. The data model documents what is being removed and what remains.

---

## Entities Being Removed

### Entity: TODO File (DEPRECATED)

**Purpose**: Legacy per-feature task tracking file

**Structure** (for reference during removal):
```yaml
---
status: in_progress|completed|blocked
feature: feature-name
branch: feature/timestamp_slug
---
# TODO content (markdown task list)
```

**Files to Archive**:
| File | Location | Action |
|------|----------|--------|
| `TODO.md` | Root | Archive to `docs/archived/` |

**Files to Preserve** (templates):
| File | Location | Reason |
|------|----------|--------|
| `TODO_template.md` | `.gemini/skills/workflow-orchestrator/templates/` | Historical reference |
| `TODO_template.md` | `.agents/workflow-orchestrator/templates/` | Synced copy |

---

## Entities Being Modified

### Entity: Quality Gate Configuration

**Location**: `.gemini/skills/quality-enforcer/scripts/run_quality_gates.py`

**Before** (6 gates):
```
Gate 1: Coverage (≥80%)
Gate 2: Tests (pytest pass)
Gate 3: Build (uv build)
Gate 4: Linting (ruff check)
Gate 5: TODO Frontmatter (REMOVE)
Gate 6: AI Config Sync
```

**After** (5 gates):
```
Gate 1: Coverage (≥80%)
Gate 2: Tests (pytest pass)
Gate 3: Build (uv build)
Gate 4: Linting (ruff check)
Gate 5: AI Config Sync (renumbered from 6)
```

**Function to Remove**: `check_todo_frontmatter()`

---

### Entity: PR Workflow Steps

**Location**: `.gemini/skills/git-workflow-manager/scripts/pr_workflow.py`

**Before**:
```
1. finish-feature → PR feature → contrib
2. archive-todo → Archive TODO file (REMOVE)
3. sync-agents → Sync GEMINI.md → AGENTS.md
4. start-develop → PR contrib → develop
```

**After**:
```
1. finish-feature → PR feature → contrib
2. sync-agents → Sync GEMINI.md → AGENTS.md
3. start-develop → PR contrib → develop
```

---

### Entity: GEMINI.md Sections

**Sections to Remove**:
1. Quality Gates table row: `| 5. TODO Frontmatter | All TODO*.md have valid YAML frontmatter |`
2. Entire section: `## TODO*.md YAML Frontmatter (Required)`
3. PR Workflow step: `archive-todo` reference

**Sections to Update**:
1. Quality Gates table: Renumber Gate 6 → Gate 5
2. PR Workflow code block: Remove `archive-todo` line

---

## Entities Replacing TODO*.md

### Entity: GitHub Issue (External)

**Source**: GitHub Issues API / `gh issue` CLI
**Schema**: GitHub-native (title, body, labels, assignees, state)
**No local file storage** - accessed via API

### Entity: Speckit Tasks (Existing)

**Location**: `specs/{feature}/tasks.md`
**Schema**: Markdown with task checkboxes, dependencies, phases
**Already in use** - no changes needed

---

## State Transitions

```
┌─────────────────┐     Archive      ┌─────────────────┐
│  TODO.md exists │ ───────────────► │ docs/archived/  │
└─────────────────┘                  └─────────────────┘

┌─────────────────┐     Remove       ┌─────────────────┐
│ Gate 5 function │ ───────────────► │    (deleted)    │
└─────────────────┘                  └─────────────────┘

┌─────────────────┐     Update       ┌─────────────────┐
│  GEMINI.md v1   │ ───────────────► │  GEMINI.md v2   │
│ (6 gates, TODO) │                  │ (5 gates, no    │
│                 │                  │  TODO section)  │
└─────────────────┘                  └─────────────────┘
```

---

## Validation Rules

### Pre-Implementation Checks
- [ ] `TODO.md` exists in root (to archive)
- [ ] `check_todo_frontmatter()` exists in quality gates (to remove)
- [ ] GEMINI.md contains TODO references (to update)

### Post-Implementation Checks
- [ ] No `TODO*.md` in root (except templates in subdirs)
- [ ] Quality gates pass (5 gates, not 6)
- [ ] GEMINI.md has no TODO*.md references
- [ ] AGENTS.md synced with GEMINI.md
