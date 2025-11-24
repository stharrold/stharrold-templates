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
  - specs/CLAUDE.md
---

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

## Pre-commit Hooks

```bash
# Install hooks (one-time)
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

Hooks run automatically on commit:
- **sync-ai-config** - Syncs CLAUDE.md → AGENTS.md, .github/copilot-instructions.md, .agents/ (runs first)
- trailing whitespace, YAML/JSON validation
- ruff linting/formatting
- CLAUDE.md frontmatter check
- skill structure validation

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

## Test Organization

```
tests/
├── unit/           # Single component tests
├── contract/       # Interface compliance tests
├── integration/    # End-to-end scenarios
└── skills/         # Skill-specific tests (quality-enforcer, git-workflow-manager)
```

Run specific test categories:
```bash
uv run pytest tests/skills/ -v          # Skill tests only
uv run pytest tests/contract/ -v        # Contract tests only
```

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
| 2 | `/2_plan` | 1 → 2 → 3 | Generate specs via speckit-author |
| 3 | `/3_tasks` | 2 → 3 → 4 | Validate task list from plan.md |
| 4 | `/4_implement` | 3 → 4 → 5 | Execute tasks + run quality gates |
| 5 | `/5_integrate` | 4 → 5 → 6 | Create PRs, cleanup worktree |
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
| agentdb-state-manager | Workflow state tracking (AgentDB) |
| initialize-repository | Bootstrap new repos |

### Document Lifecycle

```
docs/research/ → docs/guides/ → docs/archived/
(research)       (production)   (compressed)
```

### AI Config Sync (Model-Agnostic)

CLAUDE.md automatically syncs to:
- `AGENTS.md` (cross-tool)
- `.github/copilot-instructions.md` (GitHub Copilot)
- `.agents/` (mirrored skills)

**Sync utility** (`sync_ai_config.py`):
```bash
# Manual sync
uv run python .claude/skills/workflow-utilities/scripts/sync_ai_config.py sync

# Verify files are in sync
uv run python .claude/skills/workflow-utilities/scripts/sync_ai_config.py verify

# Check if sync needed
uv run python .claude/skills/workflow-utilities/scripts/sync_ai_config.py check
```

**Automation**: Pre-commit hook syncs automatically when CLAUDE.md or .claude/ is modified.

## Git Workflow Commands

```bash
# Create feature worktree (no TODO file by default)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/create_worktree.py \
  feature my-feature contrib/stharrold --no-todo

# Semantic version calculation
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/semantic_version.py develop v5.0.0

# Archive management
podman-compose run --rm dev python .claude/skills/workflow-utilities/scripts/archive_manager.py list

# Release workflow (develop → release → main)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/release_workflow.py <step>
# Steps: create-release, run-gates, pr-main, tag-release, full, status

# Backmerge workflow (release → develop, rebase contrib)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/backmerge_workflow.py <step>
# Steps: pr-develop, rebase-contrib, cleanup-release, full, status

# ⚠️ CRITICAL: Backmerge direction
# CORRECT: release/vX.Y.Z → develop (use backmerge_release.py)
# WRONG:   main → develop (NEVER merge main to develop!)

# Cleanup feature worktree (no TODO archival by default)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/cleanup_feature.py \
  my-feature --no-archive
```

## Workflow State Tracking (AgentDB)

Workflow state is tracked in AgentDB (DuckDB) instead of TODO*.md files:

```bash
# Query current workflow phase
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/query_workflow_state.py

# Record workflow transition (called by slash commands)
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_1_specify \
  --source "planning/{slug}" \
  --target "worktree"
```

## Workflow Artifact Directories

**IMPORTANT**: Different workflow phases create artifacts in different locations:

| Directory | Created By | Purpose | Location |
|-----------|------------|---------|----------|
| `planning/{slug}/` | `/1_specify` | Initial requirements (BMAD docs) | Main repo |
| `specs/{slug}/` | `/2_plan` | Detailed specs and task lists | Feature worktree |

**Workflow artifact flow:**
```
/1_specify (main repo)     /2_plan (worktree)        /3_tasks (worktree)
        │                         │                         │
        ▼                         ▼                         ▼
planning/{slug}/           specs/{slug}/              specs/{slug}/
├── requirements.md        ├── spec.md                ├── plan.md (validated)
├── architecture.md        ├── plan.md                └── tasks.md
└── epics.md               └── CLAUDE.md
```

**Key rule**: `/4_implement` reads from `specs/{slug}/`, NOT `planning/{slug}/`.

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
python3 --version         # 3.11+ (container uses 3.11)

# VCS Provider CLI (one of):
gh --version              # GitHub CLI (for GitHub repos)
# OR
az --version              # Azure CLI (for Azure DevOps repos)
az extension add --name azure-devops  # Required extension
```

## VCS Provider Configuration

The workflow **auto-detects** GitHub or Azure DevOps from your git remote URL:
- `github.com` → GitHub adapter (uses `gh` CLI)
- `dev.azure.com`, `*.visualstudio.com` → Azure DevOps adapter (uses `az` CLI)

For explicit configuration (or when auto-detection fails), create `.vcs_config.yaml`:

```yaml
# GitHub (usually auto-detected)
vcs_provider: github

# OR Azure DevOps
vcs_provider: azure_devops
azure_devops:
  organization: "https://dev.azure.com/myorg"
  project: "MyProject"
  repository: "MyRepo"  # Optional, defaults to project name
```

**VCS abstraction layer:** `.claude/skills/workflow-utilities/scripts/vcs/`
- `provider.py` - Auto-detection from git remote
- `github_adapter.py` - GitHub CLI operations
- `azure_adapter.py` - Azure DevOps CLI operations
- `config.py` - Configuration file loader

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
| pytest not found in container | Use `podman-compose run --rm dev uv run pytest` (inside container) or `uv run pytest` (outside container) |
| Import errors | Use `podman-compose run --rm dev python` |
| Platform not found | `mcp_manager.py --status` to check |
| Worktree conflicts | `git worktree remove` + `git worktree prune` |
| Ended on wrong branch | `git checkout contrib/stharrold` |
| Orphaned state dirs | Run `cleanup_orphaned_state()` from worktree_context |

## Branch Cleanup

```bash
# List stale feature branches (numbered prefixes from old specs)
git branch --list '[0-9][0-9][0-9]-*'

# Delete merged local branches
git branch -d <branch-name>

# Delete remote tracking branches
git push origin --delete <branch-name>

# Prune stale remote-tracking references
git fetch --prune
```

## Apply This Workflow to Another Repository (Phase 0)

This repository can bootstrap new projects with the full workflow system:

```bash
# From any location with stharrold-templates available:
python stharrold-templates/.claude/skills/initialize-repository/scripts/initialize_repository.py \
  stharrold-templates /path/to/target-repo
```

**Interactive 4-phase Q&A:**
1. **Configuration** - Project name, description, VCS provider (GitHub/Azure DevOps)
2. **Component selection** - Which skills to include
3. **File generation** - Creates pyproject.toml, README.md, CLAUDE.md, etc.
4. **Git initialization** - Sets up main/develop/contrib branch structure

**Requirements for target repo:**
- Python 3.11+ with `uv`
- `pytest` for testing
- `ruff` + `mypy` for linting
- Podman for containerization
- GitHub (`gh`) OR Azure DevOps (`az`) CLI

**See:** `.claude/skills/initialize-repository/CLAUDE.md` for full documentation.

## Reference Documentation

- `WORKFLOW.md` - Workflow overview (14KB) with phase index
- `docs/reference/workflow-*.md` - Phase-specific workflow docs (≤20KB each)
- `ARCHITECTURE.md` - System architecture analysis
- `CHANGELOG.md` - Version history
- `specs/` - Feature specifications with design artifacts
- `specs/STATUS.md` - Specification status tracking (completed/active/paused/abandoned)

Archive completed specs:
```bash
uv run python .claude/skills/git-workflow-manager/scripts/archive_spec.py <spec-id>
```

## CLAUDE.md Hierarchy

Every directory has a CLAUDE.md with YAML frontmatter for AI navigation:
- `parent` - Link to parent directory's CLAUDE.md
- `children` - Links to child directories' CLAUDE.md files
- `sibling_readme` - Link to same-level README.md

```bash
# Generate missing CLAUDE.md files
podman-compose run --rm dev python .claude/skills/workflow-utilities/scripts/generate_claude_md.py

# Update children references in existing CLAUDE.md files
podman-compose run --rm dev python .claude/skills/workflow-utilities/scripts/update_claude_md_refs.py
```
