# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

**Templates and utilities for MCP (Model Context Protocol) server configuration:**
- Multi-platform MCP manager (`mcp_manager.py`) for Claude Code CLI, VS Code, and Claude Desktop
- Modular documentation guides (≤30KB per file for AI context optimization)
- Workflow automation tools (git helpers, archive management, semantic versioning)
- **Containerized development** - Podman + uv + Python 3.11 for consistent dev/CI environments

**Key Principle**: All development uses `podman-compose run --rm dev <command>`. One way to run everything.

## Essential Commands

```bash
# Build container (once)
podman-compose build

# Run any command (containerized - preferred)
podman-compose run --rm dev <command>

# Alternative: Run directly with uv (when podman unavailable)
uv run <command>

# Common operations
podman-compose run --rm dev pytest                    # Run tests
podman-compose run --rm dev pytest -v -k test_name    # Single test
podman-compose run --rm dev ruff check .              # Lint
podman-compose run --rm dev ruff check --fix .        # Auto-fix
podman-compose run --rm dev python mcp_manager.py --status

# Or without container:
uv run pytest
uv run pytest -v -k test_name
uv run ruff check .
```

## Quality Gates (5 gates, all must pass before PR)

```bash
podman-compose run --rm dev python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
```

| Gate | Description |
|------|-------------|
| 1. Coverage | ≥80% test coverage |
| 2. Tests | All pytest tests pass |
| 3. Build | `uv build` succeeds |
| 4. Linting | `ruff check .` clean |
| 5. AI Config Sync | CLAUDE.md → AGENTS.md synced |

## PR Workflow (Enforced Sequence)

```bash
# Step 1: PR feature → contrib (runs quality gates)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py finish-feature

# Step 2: Sync CLAUDE.md → AGENTS.md
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents

# Step 3: PR contrib → develop
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py start-develop

# Or run all steps
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py full
```

## Slash Commands

**Orchestrator**: `/workflow/all` - Run complete workflow with auto-detection and manual gate pauses

**Feature Workflow**: `/1_specify` → `/2_plan` → `/3_tasks` → `/4_implement` → `/5_integrate`

**Release Workflow**: `/6_release` → `/7_backmerge`

| Command | Purpose |
|---------|---------|
| `/workflow/all` | Orchestrate full workflow (auto-detect state, pause at PR gates) |
| `/workflow/all new "desc"` | Start new feature from scratch |
| `/workflow/all release` | Run release workflow (steps 6-7) |
| `/workflow/all continue` | Resume after PR merge |

| Step | Command | Navigation | Purpose |
|------|---------|------------|---------|
| 1 | `/1_specify` | (start) → 1 → 2 | Create feature branch and specification |
| 2 | `/2_plan` | 1 → 2 → 3 | Generate design artifacts (research, data model, contracts) |
| 3 | `/3_tasks` | 2 → 3 → 4 | Generate ordered task list from design artifacts |
| 4 | `/4_implement` | 3 → 4 → 5 | Execute tasks automatically with progress tracking |
| 5 | `/5_integrate` | 4 → 5 → 6 | Create PRs (feature→contrib→develop) |
| 6 | `/6_release` | 5 → 6 → 7 | Create release (develop→release→main) |
| 7 | `/7_backmerge` | 6 → 7 → (end) | Sync release (PR to develop, rebase contrib) |

## Core Architecture

### MCP Manager (`mcp_manager.py`)

**Platform Detection**: Auto-detects claude-code → vscode → claude-desktop

**Key Functions**:
- `MCPConfig(platform, config_path)` - Platform-specific handler
- `select_target_platform()` - Returns first available platform
- `deduplicate_servers()` - Preserves DISABLED_ prefixed versions

**Schema Differences**:
- Claude Code & Desktop: `"mcpServers": {}`
- VS Code: `"servers": {}`

### Branch Structure

```
main (production) ← develop (integration) ← contrib/stharrold (active) ← feature/*
```

**PR Flow**: feature → contrib → develop → main

**Branch Editability:**
| Branch | Editable | Direct Commits |
|--------|----------|----------------|
| `feature/*` | Yes | Yes |
| `contrib/*` | Yes | Yes |
| `develop` | No | PRs only |
| `main` | No | PRs only |
| `release/*` | Ephemeral | Deleted after merge |

### Skills System (9 skills in `.claude/skills/`)

| Skill | Purpose |
|-------|---------|
| workflow-orchestrator | Main coordinator, templates |
| git-workflow-manager | Worktrees, PRs, semantic versioning |
| quality-enforcer | Quality gates (5 gates) |
| bmad-planner | Requirements + architecture |
| speckit-author | Specifications |
| tech-stack-adapter | Python/uv/Podman detection |
| workflow-utilities | Archive, directory structure |
| agentdb-state-manager | DuckDB state sync |
| initialize-repository | Bootstrap new repos |

### Document Lifecycle

```
docs/research/ → docs/guides/ → docs/archived/
(research)       (production)   (compressed)
```

### AI Config Sync

CLAUDE.md automatically syncs to:
- `AGENTS.md` (cross-tool)
- `.github/copilot-instructions.md` (GitHub Copilot)
- `.agents/` (mirrored skills)

## Git Workflow Commands

```bash
# Create feature worktree
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/create_worktree.py feature my-feature contrib/stharrold

# Semantic version calculation
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/semantic_version.py develop v5.0.0

# Archive management
podman-compose run --rm dev python tools/workflow-utilities/archive_manager.py list

# Release workflow (develop → release → main)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/release_workflow.py <step>
# Steps: create-release, run-gates, pr-main, tag-release, full, status

# Backmerge workflow (release → develop, rebase contrib)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/backmerge_workflow.py <step>
# Steps: pr-develop, rebase-contrib, cleanup-release, full, status

# ⚠️ CRITICAL: Backmerge direction
# CORRECT: release/vX.Y.Z → develop (use backmerge_release.py)
# WRONG:   main → develop (NEVER merge main to develop!)
```

## MCP Configuration Paths

| Platform | macOS | Windows | Linux |
|----------|-------|---------|-------|
| Claude Code | `~/.claude.json` | `~/.claude.json` | `~/.claude.json` |
| VS Code | `~/Library/.../mcp.json` | `~/AppData/.../mcp.json` | `~/.config/.../mcp.json` |
| Claude Desktop | `~/Library/.../config.json` | `~/AppData/.../config.json` | `~/.config/.../config.json` |

## Prerequisites

```bash
podman --version          # 4.0+
podman-compose --version
git --version
gh --version              # GitHub CLI
```

## Critical Guidelines

- **One way to run**: Always use `podman-compose run --rm dev <command>`
- **End on editable branch**: All workflows must end on `contrib/*` (never `develop` or `main`)
- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** unless explicitly requested
- **Follow PR workflow sequence**: finish-feature → sync-agents → start-develop
- **Quality gates must pass** before creating any PR

## Worktree State Isolation

Multiple Claude Code instances can work on different features concurrently using git worktrees. Each worktree has isolated state in `.claude-state/`:

```
repo/                         # Main repository
├── .claude/skills/          # Shared (read-only)
├── .claude-state/           # Per-worktree state
│   ├── agentdb.duckdb       # Isolated database
│   ├── workflow.json        # Workflow progress
│   └── .worktree-id         # Stable identifier
└── ...

repo_feature_abc/            # Feature worktree
├── .claude-state/           # Separate state
│   └── ...                  # Independent from main
└── ...
```

**Key utilities**:
- `from worktree_context import get_state_dir` - Get worktree-specific state directory
- `from worktree_context import get_worktree_id` - Get stable worktree identifier
- State automatically isolated when using worktrees

## Common Issues

| Issue | Solution |
|-------|----------|
| Container not building | `podman info` to verify Podman running |
| Import errors | Use `podman-compose run --rm dev python` |
| Platform not found | `mcp_manager.py --status` to check |
| Worktree conflicts | `git worktree remove` + `git worktree prune` |
| Ended on wrong branch | `git checkout contrib/stharrold` |
| Orphaned state dirs | Run `cleanup_orphaned_state()` from worktree_context |

## Reference Documentation

- `WORKFLOW.md` - Complete 7-phase workflow guide
- `ARCHITECTURE.md` - System architecture analysis
- `CHANGELOG.md` - Version history (current: v5.9.0)
- `docs/reference/` - Workflow reference docs
- `specs/` - Feature specifications with design artifacts
