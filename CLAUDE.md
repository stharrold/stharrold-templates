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

Migration from Gemini Code to Claude Code conventions is in progress (tracked in #166).
- `.claude/` renamed to `.claude/`, `GEMINI.md` renamed to `CLAUDE.md`
- Next release: v8.0.0 (tracking issue #182)
- pyproject.toml version: 7.3.0 (aligned with CHANGELOG)

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

- `library` repo (`../library/`) is the reference for secrets management patterns
- `synavistra` repo (`../synavistra/`) is the reference for `claude-code-review.yml` workflow
- CI suppresses 5542 linting errors via `continue-on-error: true` in `tests.yml` (#177)
- AgentDB state manager (`.claude/skills/agentdb-state-manager/`) has 0% test coverage (#174)
- `scripts/run.py` is being renamed to `scripts/secrets_run.py` (#169)
