---
type: claude-context
directory: .
purpose: Templates and utilities for MCP server configuration with containerized development (Podman + uv + Python 3.11)
parent: null
sibling_readme: README.md
children:
  - .claude/CLAUDE.md
  - docs/CLAUDE.md
  - tests/CLAUDE.md
---

# CLAUDE.md

## Status

Gemini Code to Claude Code migration complete (v8.0.0).
- `.gemini/` → `.claude/`, `GEMINI.md` → `CLAUDE.md` — done
- Secrets management aligned with `library` repo conventions
- pyproject.toml version: 8.7.0
- Workflow commands migrated from TOML to Markdown format (v8.2.0+)

## Gotchas

- `.claude/settings.local.json` is gitignored — do not commit (restrictive Bash allowlists break CI `claude-code-action` which needs unrestricted `gh` access)
- `release_workflow.py create-release` auto-calculates version from last git tag — override manually for major bumps
- Ruff auto-fixes import ordering on commit — re-stage if pre-commit hook modifies files
- All Python files require SPDX headers (`# SPDX-FileCopyrightText: 2025 stharrold` + `# SPDX-License-Identifier: Apache-2.0`) — pre-commit hook enforces this
- `docs/archived/` and `docs/reference/` preserve historical Gemini references intentionally — do not update
- `record_sync.py` auto-initializes AgentDB on first use — failures print `[WARN]` to stderr and exit 0 (non-blocking)
- AgentDB `init_database_if_needed` checks for `agent_synchronizations` table, not just file existence — pass `--db-path` to `init_database.py` for custom paths
- `backmerge_workflow.py cleanup-release` only prints instructions — run `git branch -d release/vX.Y.Z && git push origin --delete release/vX.Y.Z` manually
- Backmerge: always try `backmerge_workflow.py pr-develop` (release → develop) first so review comments can be fixed on the release branch — only fall back to PR `main` → `develop` if `gh pr create` returns "No commits between develop and release"
- `claude-code-review.yml` requires `claude_args: "--allowedTools Bash,WebFetch,WebSearch,Skill,Task"` (not `allowed_tools`), `id-token: write` (for OIDC auth), and `fetch-depth: 0` — without these, tool calls are denied and git diff can't reach the base branch
- `claude-code-review.yml` changes require reaching `main` before OIDC validates them — PRs with workflow edits will fail with "workflow file must have identical content to the version on the repository's default branch"
- `uv run` modifies `uv.lock` when `pyproject.toml` version changes — commit `uv.lock` after version bumps or rebase-contrib will fail with "Uncommitted changes detected"
- Git worktrees use a `.git` file (not directory) — use `.exists()` not `.is_dir()` when checking for git repos
- Slash commands use Markdown format (not TOML):
  - `description` → YAML frontmatter
  - `!{cmd}` → `` !`cmd` ``
  - `{{args}}` → `$ARGUMENTS`
- VCS wrapper functions: `from vcs import create_pr, get_contrib_branch, get_username` — NOT `get_vcs_adapter()` (removed in v8.5)
- VCS supports GitHub (`gh`) and Azure DevOps (`az`) — auto-detected from `git remote.origin.url`
- After deleting/renaming Python modules, grep all `*.md` files under `.claude/skills/` for stale references (CLAUDE.md, README.md, SKILL.md frontmatter)

## Branch Structure

`main` ← `develop` ← `contrib/stharrold` ← `feature/*`

## Commands

```bash
uv run pytest                              # All tests
uv run ruff check .                        # Lint
uv run pre-commit run --all-files          # Pre-commit hooks
uv run python .claude/skills/.../scripts/*.py  # Run skill scripts
```

## Bundles

This repo provides installable workflow bundles. See [BUNDLES.md](BUNDLES.md) for available bundles (git, secrets, ci, pipeline, graphrag, full) and usage.
- CLI: `python scripts/apply_bundle.py <source-repo> <target-repo> --bundle git [--bundle secrets] [--force] [--dry-run]`

## Key Context

- `claude-code-review.yml` prompt overrides macOS-only patterns (keyring, GITHUB_TOKEN) for Ubuntu CI — keep this prompt in sync if CLAUDE.md changes
- `library` repo (`../library/`) is the reference for secrets management patterns
- `synavistra` repo (`../synavistra/`) is the reference for `claude-code-review.yml` workflow
- `scripts/secrets_run.py` runs commands with secrets from OS keyring (#169)
- AgentDB state manager (`.claude/skills/agentdb-state-manager/`) has test coverage in `tests/skills/`
- `apply_workflow.py` was removed — use `scripts/apply_bundle.py` instead (see BUNDLES.md)
- Bundle integration tests are in `tests/integration/test_apply_bundle.py`, unit tests in `tests/unit/test_apply_bundle.py`
