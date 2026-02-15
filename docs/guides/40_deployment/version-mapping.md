# Version Mapping Guide

This document explains the version numbering schemes used in stharrold-templates and related projects.

## Version Schemes

### 1. Standard Workflow Version (v1.x.x)

**Purpose:** IU Health CBIA adaptation version
**Current:** v1.15.1
**Found in:**
- `D:\Projects\CLAUDE.md` (meta-repository)
- `D:\Projects\apply-workflow-batch.sh`
- `D:\Projects\templates\workflow-template\CLAUDE.md`
- Individual project CLAUDE.md files (workflow section)

**Example:**
```markdown
## Standard Workflow System
This repository uses **Standard Workflow v1.15.1** system...
```

**Semver Meaning:**
- Major (1.x.x): Breaking changes to skill interfaces
- Minor (x.15.x): New skills or commands added
- Patch (x.x.1): Bug fixes, documentation updates

### 2. German Workflow Version (v5.x.x)

**Purpose:** Original upstream workflow system version
**Current:** v5.3.0
**Source:** External repository (D:\Temp\standard\ or upstream)
**Found in:**
- `stharrold-templates/WORKFLOW.md` line 3: `Version: 5.3.0`
- `stharrold-templates/docs/reference/german-workflow-v5.3.0.md`
- `stharrold-templates/docs/reference/WORKFLOW-INIT-PROMPT.md`

**Example:**
```markdown
# Workflow Guide - Standard Language Learning Repository
**Version:** 5.3.0
```

**Relationship to Standard Workflow:**
- German Workflow is the **upstream source**
- Standard Workflow v1.x.x is the **CBIA adaptation**
- Updates flow: German v5.x.x → Standard v1.x.x

### 3. Package Version (pyproject.toml)

**Purpose:** Python package version for stharrold-templates
**Current:** 5.10.0
**Found in:** `stharrold-templates/pyproject.toml` line 6

**Example:**
```toml
[project]
name = "stharrold-templates"
version = "5.10.0"
```

**Note:** This version follows its own semver track and is not directly related to the workflow versions.

## Version Reference Table

| Location | Current Version | Meaning |
|----------|-----------------|---------|
| `apply-workflow-batch.sh` | v1.15.1 | What gets applied to CBIA projects |
| `WORKFLOW.md` header | v5.3.0 | German workflow source version |
| `pyproject.toml` | 5.10.0 | stharrold-templates package version |
| `CHANGELOG.md` | Various | Historical release versions |

## When to Update Versions

### Standard Workflow (v1.x.x)
Update when:
- Adding/removing skills → bump minor
- Breaking skill API changes → bump major
- Bug fixes → bump patch

Files to update:
1. `apply-workflow-batch.sh` line 2
2. `D:\Projects\CLAUDE.md` references
3. Each project's CLAUDE.md workflow section

### German Workflow (v5.x.x)
Update when:
- Syncing from upstream → match upstream version

Files to update:
1. `WORKFLOW.md` line 3
2. `docs/reference/german-workflow-v5.3.0.md` (rename if needed)

### Package Version (pyproject.toml)
Update when:
- Any release of stharrold-templates itself

## Version History

| Standard Workflow | German Workflow | Date | Notes |
|-------------------|-----------------|------|-------|
| v1.15.1 | v5.3.0 | 2025-11-24 | Current |
| v1.15.0 | v7x1.0 | 2025-11-19 | Added bmad-planner |
| v1.14.0 | v5.1.0 | 2025-11-15 | Added agentdb-state-manager |

## Recommended Practice

1. **For CBIA projects:** Reference Standard Workflow version (v1.x.x)
2. **For upstream sync:** Reference German Workflow version (v5.x.x)
3. **For package releases:** Use pyproject.toml version

**Example CLAUDE.md section:**
```markdown
## Standard Workflow System

This repository uses **Standard Workflow v1.15.1** (based on German Workflow v5.3.0).
```
