# workflow-utilities (tactical notes)

Shared utility scripts used by all other workflow skills: VCS wrapper
(`gh`/`az`), directory structure creator, skill scaffolder, SPDX/ASCII
pre-commit hooks, and version validator. See [`SKILL.md`](SKILL.md) for
the canonical skill definition and per-script reference.

This file holds only gotchas that cost someone >30 minutes to
rediscover.

## Gotchas

### VCS wrapper (`vcs/operations.py`)

- **Import pattern**: `from vcs import create_pr, get_contrib_branch,
  get_username` -- these are plain wrapper functions, not methods on
  an adapter object. The old `GitHubAdapter` class and
  `get_vcs_adapter()` factory were removed in v8.5.
- **Auto-detection runs on every call.** Each wrapper function calls
  `_detect_provider()` which reads `git remote.origin.url` to pick
  `gh` vs `az`. The detection is cheap (one subprocess) but not
  cached -- if you're in a tight loop, cache the result yourself.
- **Azure DevOps support was added in v8.7.0** but the primary
  downstream (synavistra) uses only GitHub. Azure-specific bug tests
  are in `tests/unit/test_vcs.py::TestAzureDevOps`.
- **`get_contrib_branch(fallback="contrib/stharrold")`**: the
  fallback parameter was added in v8.7.0 to deduplicate three copies
  of the same detection logic scattered across workflow scripts.
  Always pass a fallback for robustness.

### Directory structure (`directory_structure.py`)

- **Does NOT create per-directory CLAUDE.md files.** The former
  `generate_claude_md.py` was removed in v8.9 (see `claude-md-hygiene`
  skill for the replacement discipline). If you need a CLAUDE.md in
  a new directory, write it by hand with real tactical content.
- **Creates directories even when empty.** Standard workflow layout:
  `.claude-state/`, `planning/`, `specs/`, `contracts/`. Git doesn't
  track empty dirs, so each gets a `.gitkeep`.

### Skill scaffolder (`create_skill.py`)

- **Generates a real `CLAUDE.md` for new skills** (not a stub). The
  template includes the rubric header from the root CLAUDE.md and
  placeholder sections for tactical notes. If you regenerate an
  existing skill's CLAUDE.md you'll lose your tactical content --
  back it up first.
- **Version starts at `1.0.0`** in the generated `SKILL.md`
  frontmatter and `CHANGELOG.md`. Do not bump to 0.1.0 "to match
  early development" -- skills follow semver from day one.

### Pre-commit hooks (`check_spdx_headers.py`, `check_ascii_only.py`, `check_skill_structure.py`)

- **`check_spdx_headers.py`** requires every `.py` file in the repo
  to start with:
  ```
  # SPDX-FileCopyrightText: 2025 stharrold
  # SPDX-License-Identifier: Apache-2.0
  ```
  Generated Python files via `create_skill.py` get the header
  automatically.
- **`check_ascii_only.py`** rejects em-dashes, smart quotes, and
  any non-ASCII character in `.py` files. Use `--` instead of `—`.
  Two pre-existing em-dash violations were found in the tree during
  the v8.9 cleanup (`scripts/run_entity_quality.py` and
  `data_catalog/services/grain_discovery.py`) -- fixed as a
  drive-by.
- **`check_skill_structure.py`** requires every `.claude/skills/*/`
  directory to contain `SKILL.md`, `README.md`, and `CLAUDE.md`.
  Hardcoded list; if you add a new required file, update
  `REQUIRED_FILES` in the script.
- **Removed in v8.9**: `check_claude_md_frontmatter.py` and
  `generate_claude_md.py`. They enforced/generated the Tier-B stub
  pattern that downstream experience (synavistra) proved harmful.
  Replacement: `claude-md-hygiene` skill.

### Version validation (`validate_versions.py`)

- **Checks that `pyproject.toml` version matches the last git tag
  plus an expected bump.** If you committed a version bump in a
  non-release commit, the validator will flag it.
- **Does NOT check `CHANGELOG.md`.** That check is in
  `scripts/pre_release_sanity.py::check_changelog()` (added v8.9).

## See also

- [`SKILL.md`](SKILL.md) -- canonical skill definition and per-script
  reference
- `git-workflow-manager` -- primary consumer of the VCS wrapper and
  archiver
- `claude-md-hygiene` -- the replacement for the deleted
  `generate_claude_md.py` stub factory
- Root [`CLAUDE.md`](../../../CLAUDE.md) "What goes here" rubric --
  the editorial policy that replaced the `claude-md-frontmatter`
  pre-commit hook
