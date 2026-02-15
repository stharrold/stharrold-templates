# Workflow Guide: Operations & Maintenance

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Version:** 6.0.0

This document covers workflow state management, maintenance tasks, and cross-tool configuration.

---

## State Tracking (AgentDB)

Legacy `TODO_*.md` files have been replaced by **AgentDB**, a persistent DuckDB database that tracks workflow transitions and analytics.

**File:** `.claude-state/agentdb.duckdb`

### Common Commands

**Query Workflow State:**
```bash
uv run python .claude/skills/agentdb-state-manager/scripts/query_workflow_state.py
```

**Record Workflow Transition:**
```bash
uv run python .claude/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_v7x1_2_integrate
```

**Analyze Metrics:**
```bash
uv run python .claude/skills/agentdb-state-manager/scripts/analyze_metrics.py
```

---

## AI Configuration Sync

This repository follows a **Gemini-first** model but maintains compatibility with other tools like GitHub Copilot, Cursor, and Windsurf.

**Primary Source**: `.claude/`
**Mirrored Target**: `.agents/` (Follows the emerging [agents.md spec](https://github.com/openai/agents.md))

### Manual Sync
If instructions in `CLAUDE.md` or skills in `.claude/skills/` are updated, sync them to other tools:

```bash
# Sync CLAUDE.md to GitHub Copilot instructions
cp CLAUDE.md .github/copilot-instructions.md

# Sync CLAUDE.md to industry standard AGENTS.md
cp CLAUDE.md AGENTS.md

# Mirror skills to .agents/ directory
mkdir -p .agents && cp -r .claude/skills/* .agents/
```

---

## Maintenance Tasks

### Daily Rebase
To keep your `contrib` branch in sync with the integration branch:

```bash
uv run python .claude/skills/git-workflow-manager/scripts/daily_rebase.py contrib/stharrold
```

### Archive Management
Archive deprecated files with timestamps to maintain a clean repository while preserving history:

```bash
uv run python .claude/skills/workflow-utilities/scripts/deprecate_files.py \
  "description" file1.py file2.py
```

Result: `ARCHIVED/YYYYMMDDTHHMMSSZ_description.zip`

### Worktree Cleanup
If a worktree was not cleaned up automatically by `/workflow:v7x1_2-integrate`:

```bash
uv run python .claude/skills/git-workflow-manager/scripts/cleanup_feature.py slug
```

---

## Common Commands Reference

### Testing & Quality
```bash
# Run tests
uv run pytest

# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Git Operations
```bash
# List worktrees
git worktree list

# Prune stale worktrees
git worktree prune

# Delete branch
git branch -D branch-name
```

---

## Context Management

Claude Code has an effective context capacity of ~136K tokens.

**Warning Threshold**: 80K tokens.
**Checkpoint Threshold**: 100K tokens.

**At 100K tokens:**
1. Record current state in AgentDB.
2. Run `/init` to update persistent memory.
3. Run `/compact` to clear the active buffer.
4. Continue working.

```
