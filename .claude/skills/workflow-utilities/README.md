---
type: directory-documentation
directory: .claude/skills/workflow-utilities
title: Workflow Utilities
sibling_claude: CLAUDE.md
parent: null
children:
  - ARCHIVED/README.md
---

# Workflow Utilities

> **Shared utilities for all workflow skills -- VCS abstraction, file deprecation, pre-commit hooks, version validation, and skill scaffolding**

## Quick Start

```bash
# Archive deprecated files
uv run python .claude/skills/workflow-utilities/scripts/deprecate_files.py <desc> <files...>

# List/extract archives
uv run python .claude/skills/workflow-utilities/scripts/archive_manager.py list
uv run python .claude/skills/workflow-utilities/scripts/archive_manager.py extract <archive>

# Validate version consistency across SKILL.md files
uv run python .claude/skills/workflow-utilities/scripts/validate_versions.py
```

## Features

- **File deprecation** -- Archive old files (never delete directly)
- **Directory standards** -- Create standard `CLAUDE.md` / `README.md` / `ARCHIVED/` structure
- **Archive management** -- List and extract timestamped archives
- **VCS abstraction** -- `gh`/`az` wrapper functions (shim over `release_lib.vcs`)
- **Pre-commit hooks** -- SPDX headers, ASCII-only, skill structure validation
- **Version validation** -- `validate_versions.py` checks all SKILL.md semver frontmatter
- **Skill scaffolding** -- `create_skill.py` bootstraps a new skill directory

## Scripts Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `deprecate_files.py` | Timestamp-archive files into `ARCHIVED/` | Replacing old implementations |
| `directory_structure.py` | Create standard dir (`CLAUDE.md`, `README.md`, `ARCHIVED/`) | Creating `planning/`, `specs/` |
| `archive_manager.py` | List and extract archives | Inspecting / recovering archived files |
| `validate_versions.py` | Validate SKILL.md semver + WORKFLOW.md version | Before committing skill changes |
| `create_skill.py` | Scaffold a new skill directory | Adding a new skill (rare) |
| `check_spdx_headers.py` | Pre-commit: enforce Apache-2.0 SPDX headers | Run by pre-commit automatically |
| `check_ascii_only.py` | Pre-commit: reject non-ASCII chars in `.py` files | Run by pre-commit automatically |
| `check_skill_structure.py` | Pre-commit: require `SKILL.md`/`README.md`/`CLAUDE.md` per skill | Run by pre-commit automatically |

## VCS Layer

A backward-compat shim over `release_lib.vcs` (extracted in issue #240).
**New code should import from `release_lib.vcs` directly.**

```python
from release_lib.vcs import create_pr, get_contrib_branch, get_username

branch = get_contrib_branch()   # auto-detects provider (gh / az)
username = get_username()

pr_url = create_pr(
    base=branch,
    head="release/20251103T143000Z_auth",
    title="feat: auth system",
    body="PR body",
)
```

## Best Practices

**File deprecation:**
- Never delete files directly
- Use `deprecate_files.py` to archive with a timestamp

**Directory creation:**
- Use `directory_structure.py` for consistency (creates required `CLAUDE.md` / `README.md` / `ARCHIVED/`)

**Documentation maintenance:**
- Run `validate_versions.py` before committing skill changes
- SKILL.md is the canonical definition; README.md is the quick-start summary

## Integration

Skills that use workflow-utilities:

- **git-workflow-manager** -- VCS abstraction (`vcs/` shim)
- **initialize-repository** -- `directory_structure.py`, `create_skill.py`

## Related Documentation

- **[SKILL.md](SKILL.md)** -- canonical skill definition and per-script reference
- **[CLAUDE.md](CLAUDE.md)** -- gotchas and tactical notes
- **[WORKFLOW.md](../../WORKFLOW.md)** -- three-tier workflow guide
