# Critical Assessment: stharrold-templates v8.1.0

**Date:** 2026-01-31
**Assessor:** Claude Code (automated)
**Scope:** Full repository audit across 5 dimensions
**Branch:** contrib/stharrold (at v8.1.0)

---

## Dimension 1: Migration Completeness (Gemini -> Claude)

**Rating: Incomplete** -- The v8.0.0 migration addressed directory/file renames (`.gemini/` -> `.claude/`, `GEMINI.md` -> `CLAUDE.md`) but left significant textual references to "Gemini" in active documentation and configuration.

### Active documentation with stale references

| File | Line(s) | Issue |
|------|---------|-------|
| `WORKFLOW.md` | 5, 11, 81, 85, 89, 169, 172 | "Gemini CLI tools" referenced as current platform |
| `CONTRIBUTING.md` | 80 | "built-in Gemini CLI tools" in contributor instructions |
| `.github/copilot-instructions.md` | 79 | "Gemini's feature-dev plugin" in active config |
| `.gitignore` | 49-51 | Gemini-specific ignore rules still present |

### Configuration with stale references

| File | Line(s) | Issue |
|------|---------|-------|
| `.claude/skills/workflow-orchestrator/SKILL.md` | Multiple | Describes "Gemini's behavior" as current |
| `.claude/skills/initialize-repository/CLAUDE.md` | 155+ | "Co-Authored-By: Gemini" in templates |
| `.claude/skills/tech-stack-adapter/CLAUDE.md` | 137 | "Gemini needs to understand project" |
| `.claude/skills/agentdb-state-manager/SKILL.md` | 97-98 | docs.gemini.com URLs |
| `.claude/skills/UPDATE_CHECKLIST.md` | 219-285 | Multiple docs.gemini.com URLs and "Co-Authored-By: Gemini" |

### Intentionally preserved (per CLAUDE.md gotchas)

- `docs/archived/` -- historical references OK
- `docs/reference/` -- historical references OK
- `ARCHIVED/` -- compressed archives OK
- `CHANGELOG.md` -- version history OK

---

## Dimension 2: Dead References and Orphaned Artifacts

**Rating: Multiple issues found**

### Dead skill links

| File | Line(s) | Issue |
|------|---------|-------|
| `.claude/skills/CLAUDE.md` | 42 | Link to `bmad-planner/CLAUDE.md` -- directory archived |
| `.claude/skills/CLAUDE.md` | 22-25 | Lists archived skills without noting links are dead |

### Dead skill references in code

| File | Line(s) | Issue |
|------|---------|-------|
| `.claude/skills/initialize-repository/scripts/initialize_repository.py` | 55-57, 494-612 | References `bmad-planner`, `speckit-author`, `quality-enforcer` scripts |
| `.claude/skills/git-workflow-manager/scripts/pr_workflow.py` | 97 | Path to `quality-enforcer/scripts/run_quality_gates.py` |
| `.claude/skills/git-workflow-manager/scripts/release_workflow.py` | 106 | Path to `quality-enforcer/scripts/run_quality_gates.py` |
| `.claude/skills/git-workflow-manager/scripts/create_release.py` | 260 | Print references `quality-enforcer` script |
| `.claude/skills/workflow-utilities/scripts/validate_versions.py` | 41-43 | Skills list includes archived skills |

### Non-existent directory reference

| File | Line | Issue |
|------|------|-------|
| `pyproject.toml` | 44 | `"tools/**/*.py"` per-file-ignores -- no `tools/` directory exists |

### Orphaned directory

| Path | Issue |
|------|-------|
| `.gemini-state/` | Legacy state directory (16MB DuckDB + metadata). Should be archived. |

---

## Dimension 3: Portability and Hardcoded Values

**Rating: Multiple hardcoded user-specific values**

### Hardcoded paths (`/Users/stharrold`)

| File | Line(s) | Context |
|------|---------|---------|
| `.claude/skills/initialize-repository/CLAUDE.md` | 66-67 | Example paths in documentation |
| `.claude/skills/initialize-repository/CLAUDE.md` | 804-805 | Example source/target paths |
| `.claude/skills/tech-stack-adapter/CLAUDE.md` | 60 | Example `repo_root` value |
| `.claude/skills/tech-stack-adapter/README.md` | 40 | Example `repo_root` value |
| `docs/guides/10_mcp/11_setup.md` | 124, 140 | MCP setup example paths |

### Hardcoded branch names

| File | Line(s) | Value |
|------|---------|-------|
| `.claude/commands/workflow/v7x1_1-worktree.toml` | 15 | `contrib/stharrold` hardcoded in script invocation |
| `.claude/commands/workflow/v7x1_2-integrate.toml` | 12, 21 | `contrib/stharrold` hardcoded in PR targets |

---

## Dimension 4: Documentation Quality

**Rating: Functional but inconsistent**

### Missing Quick Reference sections

All 6 SKILL.md files lack a Quick Reference section at the top for fast lookup:
- `.claude/skills/agentdb-state-manager/SKILL.md`
- `.claude/skills/git-workflow-manager/SKILL.md`
- `.claude/skills/initialize-repository/SKILL.md`
- `.claude/skills/tech-stack-adapter/SKILL.md`
- `.claude/skills/workflow-orchestrator/SKILL.md`
- `.claude/skills/workflow-utilities/SKILL.md`

### Missing error recovery documentation

All 4 workflow command .toml files lack error recovery guidance:
- `.claude/commands/workflow/v7x1_1-worktree.toml`
- `.claude/commands/workflow/v7x1_2-integrate.toml`
- `.claude/commands/workflow/v7x1_3-release.toml`
- `.claude/commands/workflow/v7x1_4-backmerge.toml`

---

## Dimension 5: Test Coverage

**Rating: 67% skill coverage (4/6 skills tested)**

### Skills with tests

| Skill | Test Directory | Test Count |
|-------|---------------|------------|
| agentdb-state-manager | `tests/skills/agentdb-state-manager/` | 3 files |
| git-workflow-manager | `tests/skills/git-workflow-manager/` | 5 files |
| initialize-repository | `tests/skills/initialize-repository/` | 1 file |
| workflow-utilities | `tests/skills/workflow-utilities/` | 3 files |

### Skills without tests

| Skill | Key Scripts | Risk |
|-------|------------|------|
| tech-stack-adapter | `scripts/detect_stack.py` | Medium -- stack detection affects all workflow phases |
| workflow-orchestrator | (conceptual skill, no scripts) | Low -- orchestration is primarily documentation |

---

## Summary

| Dimension | Rating | Issues |
|-----------|--------|--------|
| Migration completeness | Incomplete | ~15 active files with stale Gemini refs |
| Dead references | Multiple issues | 3 archived skills referenced in code, dead links, orphaned dir |
| Portability | Multiple hardcoded values | ~6 files with user-specific paths, 2 files with hardcoded branch |
| Documentation quality | Inconsistent | 6 SKILL.md missing Quick Reference, 4 .toml missing error recovery |
| Test coverage | 67% | 2 skills untested |

**Recommended action:** Address all findings as release v8.2.0 (minor bump, no breaking changes).
