# CLAUDE.md

## Status

This repo is migrating from Gemini Code to Claude Code conventions (tracked in #166).
- `.gemini/` → `.claude/`, `GEMINI.md` → `CLAUDE.md`
- Next release: v8.0.0 (tracking issue #182)
- Current pyproject.toml version is stale (7.2.0, should be 7.3.0 per CHANGELOG)

## Branch Structure

`main` ← `develop` ← `contrib/stharrold` ← `feature/*`

## Commands

```bash
uv run pytest                              # All tests
uv run ruff check .                        # Lint
uv run pre-commit run --all-files          # Pre-commit hooks
uv run python .gemini/skills/.../scripts/*.py  # Run skill scripts
```

## Key Context

- `library` repo (`../library/`) is the reference for secrets management patterns
- `synavistra` repo (`../synavistra/`) is the reference for `claude-code-review.yml` workflow
- CI suppresses 5542 linting errors via `continue-on-error: true` in `tests.yml` (#177)
- AgentDB state manager (`.gemini/skills/agentdb-state-manager/`) has 0% test coverage (#174)
- `scripts/run.py` is being renamed to `scripts/secrets_run.py` (#169)
