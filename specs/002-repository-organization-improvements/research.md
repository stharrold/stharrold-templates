# Research: Repository Organization Improvements

**Feature**: 002-repository-organization-improvements
**Date**: 2025-11-21

## Research Questions

### RQ-1: Test Directory Structure Best Practices

**Decision**: Use flat `tests/` at root with subdirectories mirroring source

**Rationale**:
- pytest convention expects `tests/` at root
- pyproject.toml already configured with `testpaths = ["tests"]`
- Subdirectories (e.g., `tests/skills/`, `tests/tools/`) provide organization without complexity

**Alternatives Considered**:
- `src/tests/` - Rejected: Non-standard for Python projects
- Co-located tests (e.g., `skills/*/tests/`) - Rejected: Scattered, harder to run together

### RQ-2: .tmp/german/ Directory Purpose

**Decision**: Add to `.gitignore` (local-only working directory)

**Rationale**:
- Contains work-in-progress files that appear to be local development
- Duplicates much of `.gemini/skills/` structure
- Size is significant (~100+ files)
- Should not be committed or shared

**Alternatives Considered**:
- Delete entirely - Rejected: May contain useful local work
- Move to branch - Rejected: Creates noise in git history
- Keep tracked - Rejected: Adds confusion and duplication

### RQ-3: Documentation Restructure Strategy

**Decision**: Rename folders with intuitive names, preserve content

**Rationale**:
- Numeric prefixes (`00_`, `10_`, `30_`) add cognitive load
- Content is valuable and should be preserved
- Simple rename maintains git history

**New Structure**:
```
docs/
├── research/     # was 00_draft-initial/
├── guides/       # was 10_draft-merged/
└── archived/     # was ARCHIVED/
```

**Alternatives Considered**:
- Flatten all into `docs/` - Rejected: Loses categorization
- Keep numeric prefixes - Rejected: Non-intuitive for humans
- Delete old content - Rejected: Valuable reference material

### RQ-4: TODO File Consolidation Approach

**Decision**: Archive issue-specific TODOs, keep single TODO.md

**Rationale**:
- Multiple TODO files at root creates clutter
- Issue-specific TODOs duplicate GitHub Issue content
- Single TODO.md is standard convention

**Migration**:
1. `TODO_FOR_issue-*.md` → Archive to `ARCHIVED/`
2. `TODO.md` → Keep as primary
3. Update TODO.md with any active items from archived files

### RQ-5: Skill Documentation Standard

**Decision**: Consolidate to single `SKILL.md` per skill

**Rationale**:
- Current: GEMINI.md + README.md + SKILL.md + CHANGELOG.md = 4 files
- Redundancy increases maintenance burden
- Single file reduces cognitive load

**New Standard**:
```
.gemini/skills/{skill-name}/
├── SKILL.md        # Consolidated: purpose, usage, changelog
├── scripts/        # Implementation
└── ARCHIVED/       # Old versions (optional, compressed)
```

### RQ-6: README.md vs GEMINI.md Separation

**Decision**: Create README.md for humans, keep GEMINI.md for AI

**Rationale**:
- README.md is universal convention for human developers
- GEMINI.md contains AI-specific instructions and context
- Different audiences need different information density

**README.md Content**:
- Project description (1 paragraph)
- Prerequisites
- Quick start (3-5 commands)
- Links to detailed docs
- Contributing link

---

## Resolved Unknowns

| Unknown | Resolution |
|---------|------------|
| Test structure | `tests/` at root with subdirectories |
| .tmp/german/ | Add to .gitignore |
| Draft folders | Rename to docs/{research,guides,archived}/ |
| TODO files | Consolidate to single TODO.md |
| Skill docs | Single SKILL.md per skill |
| README vs GEMINI | Separate files for different audiences |

---

## Technical Decisions Summary

1. **No code changes required** - This is a file organization task
2. **Git history preserved** - Use `git mv` for renames
3. **Backwards compatibility** - Update any internal references
4. **Quality gates** - Must still pass after reorganization
