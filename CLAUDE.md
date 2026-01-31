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
- pyproject.toml version: 8.2.0
- Workflow commands migrated from TOML to Markdown format (v8.2.0+)

## Gotchas

- `.claude/settings.local.json` is gitignored — do not commit (restrictive Bash allowlists break CI `claude-code-action` which needs unrestricted `gh` access)
- `release_workflow.py create-release` auto-calculates version from last git tag — override manually for major bumps
- Ruff auto-fixes import ordering on commit — re-stage if pre-commit hook modifies files
- `docs/archived/` and `docs/reference/` preserve historical Gemini references intentionally — do not update
- `record_sync.py` auto-initializes AgentDB on first use — failures print `[WARN]` to stderr and exit 0 (non-blocking)
- AgentDB `init_database_if_needed` checks for `agent_synchronizations` table, not just file existence — pass `--db-path` to `init_database.py` for custom paths
- Slash commands use Markdown format (not TOML):
  - `description` → YAML frontmatter
  - `!{cmd}` → `` !`cmd` ``
  - `{{args}}` → `$ARGUMENTS`

## Branch Structure

`main` ← `develop` ← `contrib/stharrold` ← `feature/*`

## Commands

```bash
uv run pytest                              # All tests
uv run ruff check .                        # Lint
uv run pre-commit run --all-files          # Pre-commit hooks
uv run python .claude/skills/.../scripts/*.py  # Run skill scripts
```

## Key Context

- `claude-code-review.yml` prompt overrides macOS-only patterns (keyring, GITHUB_TOKEN) for Ubuntu CI — keep this prompt in sync if CLAUDE.md changes
- `library` repo (`../library/`) is the reference for secrets management patterns
- `synavistra` repo (`../synavistra/`) is the reference for `claude-code-review.yml` workflow
- `scripts/secrets_run.py` runs commands with secrets from OS keyring (#169)
- AgentDB state manager (`.claude/skills/agentdb-state-manager/`) has test coverage in `tests/skills/`
