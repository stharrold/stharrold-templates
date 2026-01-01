# Research: Remove Redundant TODO*.md System

**Feature Branch**: `007-remove-redundant-todo`
**Date**: 2025-11-23
**Status**: Complete

---

## Research Questions

### RQ-001: What TODO*.md files currently exist?

**Decision**: Archive files in root directory, preserve templates

**Findings**:
- Root `TODO.md` - legacy manual task tracking file (last sync Sept 2025)
- `docs/archived/TODO_FOR_issue-*.md` - already archived, no action needed
- `.gemini/skills/workflow-orchestrator/templates/TODO_template.md` - template, preserve
- `.agents/workflow-orchestrator/templates/TODO_template.md` - synced template, preserve

**Rationale**: Only the root `TODO.md` needs archiving. Templates should be preserved for historical reference and potential future use.

---

### RQ-002: What scripts reference TODO*.md files?

**Decision**: Update or remove TODO-related code from 6 key scripts

**Findings** (from grep analysis):
1. **Quality gate script** - `.gemini/skills/quality-enforcer/scripts/run_quality_gates.py`
   - Contains `check_todo_frontmatter()` function (Gate #5)
   - References TODO*.md in quality gate results
   - **Action**: Remove Gate #5 entirely, renumber to 5 gates

2. **PR workflow script** - `.gemini/skills/git-workflow-manager/scripts/pr_workflow.py`
   - Has `archive-todo` step in workflow
   - **Action**: Remove or skip this step

3. **TODO updater script** - `.gemini/skills/workflow-utilities/scripts/todo_updater.py`
   - Dedicated script for TODO file management
   - **Action**: Deprecate (move to archived or delete)

4. **Sync TODO to DB** - `.gemini/skills/agentdb-state-manager/scripts/sync_todo_to_db.py`
   - Syncs TODO*.md content to DuckDB
   - **Action**: Deprecate or make optional

5. **Create worktree script** - `.gemini/skills/git-workflow-manager/scripts/create_worktree.py`
   - May create TODO files for new features
   - **Action**: Remove TODO creation logic

6. **Mirrored .agents/ scripts** - Same updates needed for mirrored copies

**Rationale**: Scripts must be updated to prevent runtime errors when TODO*.md files don't exist.

---

### RQ-003: What documentation references TODO*.md?

**Decision**: Update GEMINI.md, AGENTS.md, and related docs

**Findings**:
- `GEMINI.md` - Quality gates table mentions "TODO Frontmatter" gate
- `GEMINI.md` - "TODO*.md YAML Frontmatter (Required)" section
- `GEMINI.md` - PR workflow mentions `archive-todo` step
- `AGENTS.md` - Synced copy of GEMINI.md
- `.github/copilot-instructions.md` - May have synced content

**Sections to remove/update**:
1. Quality Gates table: Remove row for Gate 5, renumber Gate 6 → 5
2. "TODO*.md YAML Frontmatter (Required)" section: Delete entirely
3. PR Workflow steps: Remove `archive-todo` step
4. Sync changes to AGENTS.md

---

### RQ-004: What replaces TODO*.md functionality?

**Decision**: GitHub Issues + Speckit tasks.md (already in use)

**Comparison**:

| Capability | TODO*.md | GitHub Issues | Speckit tasks.md |
|------------|----------|---------------|------------------|
| Task list | Manual | Native | Generated from spec |
| Status tracking | YAML frontmatter | Issue state | Checkboxes |
| Branch linking | YAML field | Refs/labels | In spec folder |
| Discovery | Local grep | Web + CLI `gh issue` | Local files |
| Assignment | N/A | Native | N/A |
| Integration | Custom scripts | Native GH Actions | Via workflow |

**Rationale**: GitHub Issues provides superior external tracking. Speckit tasks.md provides superior local task breakdown with design artifact integration. TODO*.md adds no unique value.

---

### RQ-005: What is the migration/archive strategy?

**Decision**: Archive with date prefix, update docs, remove code

**Strategy**:
1. Archive `TODO.md` → `docs/archived/20251123T_TODO.md`
2. Update quality gates (remove gate #5)
3. Update GEMINI.md documentation
4. Run sync to update AGENTS.md
5. Update/deprecate TODO-related scripts
6. Verify quality gates pass

**Rationale**: Clean removal with historical preservation. No backward compatibility needed - this is a simplification.

---

## Technical Context Resolution

| Item | Resolution |
|------|------------|
| Language/Version | Python 3.11 (existing scripts) |
| Primary Dependencies | pathlib, shutil (file ops), subprocess (git) |
| Storage | N/A (filesystem archive) |
| Testing | pytest (verify gates pass) |
| Target Platform | Local filesystem |
| Project Type | Single (script updates) |
| Performance Goals | N/A (one-time cleanup) |
| Constraints | Must not break existing workflows |
| Scale/Scope | ~6 scripts, 2 docs, 1 file archive |

---

## Alternatives Considered

### Alternative 1: Keep TODO*.md as optional
**Rejected**: Adds complexity for no benefit. If optional, why maintain the code?

### Alternative 2: Convert TODO*.md to GitHub Issue sync
**Rejected**: Over-engineering. GitHub Issues already exist. Just use them directly.

### Alternative 3: Deprecation period with warnings
**Rejected**: Unnecessary. This is an internal tool change with no external users.

---

## Conclusion

Remove the TODO*.md system entirely:
1. Archive existing files (preserve history)
2. Remove quality gate validation
3. Update documentation
4. Deprecate related scripts
5. Rely on GitHub Issues + Speckit tasks.md going forward
