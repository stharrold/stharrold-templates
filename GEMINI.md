---
type: gemini-context
directory: .
purpose: Templates and utilities for MCP server configuration with containerized development (Podman + uv + Python 3.11)
parent: null
sibling_readme: README.md
children:
  - .gemini/GEMINI.md
  - docs/GEMINI.md
  - tests/GEMINI.md
---

# GEMINI.md

This file provides guidance to Gemini Code (gemini.ai/code) when working with code in this repository.

## What This Repository Is

**Templates and utilities for MCP (Model Context Protocol) server configuration:**
- Modular documentation guides (≤30KB per file for AI context optimization)
- Workflow automation tools (git helpers, archive management, semantic versioning)
- **Containerized development** - Podman + uv + Python 3.11 for consistent dev/CI environments

**Key Principle**: Workflow commands use `uv run <command>` directly. Package testing uses containers (CI/CD).

## Essential Commands

```bash
# Workflow commands (run directly with uv)
uv run <command>

# Common operations
uv run pytest                              # Run tests
uv run pytest -v -k test_name              # Single test
uv run ruff check .                        # Lint
uv run ruff check --fix .                  # Auto-fix

# Package testing (containerized - for CI/CD)
podman-compose build                       # Build container
podman-compose run --rm dev uv run pytest  # Run tests in container
```

## Pre-commit Hooks

```bash
# Install hooks (one-time)
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

Hooks run automatically on commit:
- trailing whitespace, YAML/JSON validation
- ruff linting/formatting (v0.14.8)
- GEMINI.md frontmatter check
- skill structure validation
- **SPDX license headers** - Validates Apache 2.0 headers on all Python files

## Test Organization

```
tests/
├── unit/           # Single component tests
├── contract/       # Interface compliance tests
├── integration/    # End-to-end scenarios
└── skills/         # Skill-specific tests (git-workflow-manager, workflow-utilities)
```

Run specific test categories:
```bash
uv run pytest tests/skills/ -v          # Skill tests only
uv run pytest tests/contract/ -v        # Contract tests only
uv run pytest -m "not integration and not benchmark"  # Exclude slow tests (default in quality gates)
```

## v7x1 Workflow (Implementation)

Streamlined 4-phase workflow using built-in Gemini CLI tools:

```
/workflow:v7x1_1-worktree "feature description"
    | creates worktree, user implements feature in worktree
    v
/workflow:v7x1_2-integrate "feature/YYYYMMDDTHHMMSSZ_slug"
    | PR feature->contrib->develop
    v
/workflow:v7x1_3-release
    | create release, PR to main, tag
    v
/workflow:v7x1_4-backmerge
    | PR release->develop, rebase contrib, cleanup
```

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `/workflow:v7x1_1-worktree "desc"` | Create worktree for isolated development |
| 2 | `/workflow:v7x1_2-integrate ["branch"]` | PR feature->contrib->develop |
| 3 | `/workflow:v7x1_3-release` | Create release (develop->release->main) |
| 4 | `/workflow:v7x1_4-backmerge` | Sync release (PR to develop, rebase contrib) |

**Detailed Guide**: See [WORKFLOW.md](WORKFLOW.md) for step-by-step instructions.

**Key differences from old v1-v7 workflow:**
- No BMAD planning or SpecKit specifications (Implementation uses built-in tools)
- No manual quality gates (Gemini Code Review automated via GitHub Actions)
- Simplified 4-step flow instead of 7 steps

## Core Architecture

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
| `release/*` | Ephemeral | `/workflow:v7x1_3-release` creates, `/workflow:v7x1_4-backmerge` deletes |
...
- **Follow v7x1 workflow sequence**: `/workflow:v7x1_1-worktree` -> Implementation -> `/workflow:v7x1_2-integrate` -> `/workflow:v7x1_3-release` -> `/workflow:v7x1_4-backmerge`

### Skills System (6 skills in `.gemini/skills/`)

| Skill | Purpose |
|-------|---------|
| workflow-orchestrator | Main coordinator, templates |
| git-workflow-manager | Worktrees, PRs, semantic versioning |
| tech-stack-adapter | Python/uv/Podman detection |
| workflow-utilities | Archive, directory structure |
| agentdb-state-manager | Workflow state tracking (AgentDB) |
| initialize-repository | Bootstrap new repos |

**Archived skills** (see `ARCHIVED/`):
- bmad-planner - Replaced by autonomous implementation
- speckit-author - Replaced by autonomous implementation
- quality-enforcer - Replaced by Gemini Code Review

### Document Lifecycle

```
docs/research/ → docs/guides/ → docs/archived/
(research)       (production)   (compressed)
```

## Git Workflow Commands

```bash
# Create feature worktree
uv run python .gemini/skills/git-workflow-manager/scripts/create_worktree.py \
  feature my-feature contrib/stharrold

# Semantic version calculation
uv run python .gemini/skills/git-workflow-manager/scripts/semantic_version.py develop v7x1.0

# Archive management
uv run python .gemini/skills/workflow-utilities/scripts/archive_manager.py list

# Release workflow (develop → release → main)
uv run python .gemini/skills/git-workflow-manager/scripts/release_workflow.py <step>
# Steps: create-release, run-gates, pr-main, tag-release, full, status

# Backmerge workflow (release → develop, rebase contrib)
# Pattern: release/vX.Y.Z ──PR──> develop (direct, no intermediate branch)
# Requires: release/* branch must exist when starting step 7
uv run python .gemini/skills/git-workflow-manager/scripts/backmerge_workflow.py <step>
# Steps: pr-develop, rebase-contrib, cleanup-release, full, status

# CRITICAL: Backmerge direction
# CORRECT: release/vX.Y.Z -> develop (direct PR from release branch)
# WRONG:   main -> develop (NEVER merge main to develop!)

# Cleanup feature worktree and branches
uv run python .gemini/skills/git-workflow-manager/scripts/cleanup_feature.py my-feature
```

## Workflow State Tracking (AgentDB)

Workflow state is tracked in AgentDB (DuckDB) instead of TODO*.md files:

```bash
# Query current workflow phase
uv run python .gemini/skills/agentdb-state-manager/scripts/query_workflow_state.py

# Record workflow transition (called by slash commands)
uv run python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern v7x1_1_worktree \
  --source "contrib/stharrold" \
  --target "feature/YYYYMMDDTHHMMSSZ_slug"
```

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

## Cross-Platform Compatibility

- Pre-commit hooks use `language: python` (no shebang scripts) - works on Git Bash for Windows
- All scripts invoked via `uv run python <script>` - no shell script dependencies
- ASCII-only characters in Python files ensures terminal compatibility across platforms

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

**VCS abstraction layer:** `.gemini/skills/workflow-utilities/scripts/vcs/`
- `provider.py` - Auto-detection from git remote
- `github_adapter.py` - GitHub CLI operations
- `azure_adapter.py` - Azure DevOps CLI operations
- `config.py` - Configuration file loader

## Critical Guidelines

- **One way to run**: Workflow commands use `uv run <command>` directly
- **End on editable branch**: All workflows must end on `contrib/*` (never `develop` or `main`)
- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** unless explicitly requested
- **Follow v7x1 workflow sequence**: `/workflow:v7x1_1-worktree` -> Implementation -> `/workflow:v7x1_2-integrate` -> `/workflow:v7x1_3-release` -> `/workflow:v7x1_4-backmerge`
- **SPDX headers required**: All Python files must have Apache 2.0 license headers
- **ASCII-only**: Use only ASCII characters in Python files (Issue #121)
- **Absolute paths**: Use dynamically populated absolute paths in scripts (Issue #122)
- **Use GitHub Issues**: Task tracking uses GitHub Issues/Azure DevOps work items (not TODO*.md files)

## ASCII-Only Characters (Issue #121)

All Python files must use only ASCII characters (0x00-0x7F). No Unicode symbols.

**Why**: Ensures compatibility across all platforms, terminals, and encoding configurations.

**Encoding**: Files are UTF-8 encoded (UTF-8 is ASCII-compatible for ASCII characters).

**Common replacements** (use `safe_output.py` functions):

| Unicode | ASCII | Function |
|---------|-------|----------|
| `[checkmark]` | `[OK]` | `format_check()` |
| `[cross]` | `[FAIL]` | `format_cross()` |
| `[warning]` | `[WARN]` | `format_warning()` |
| `[arrow]` | `->` | `format_arrow()` |

**Validation**: `uv run python .gemini/skills/workflow-utilities/scripts/check_ascii_only.py`

**Pre-commit**: Enforced automatically via `ascii-only` hook.

## Absolute Paths (Issue #122)

Scripts must use dynamically populated absolute paths, not relative paths.

**Why**: Relative paths break when scripts are called from different working directories.

**Pattern**:
```python
import subprocess
from pathlib import Path

def get_repo_root() -> Path:
    """Get the repository root directory as an absolute path."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(result.stdout.strip()).resolve()

# Use absolute paths
repo_root = get_repo_root()
archived_dir = repo_root / "ARCHIVED"
file_path = (repo_root / relative_path).resolve()
```

**Key rules**:
- Always resolve paths with `.resolve()` for absolute canonical form
- Derive paths from `git rev-parse --show-toplevel` for repo-relative paths
- Convert relative input paths to absolute before processing
- Store relative paths in archives for portability (use `relative_to(repo_root)`)

## SPDX License Headers

All Python files require SPDX headers for Apache 2.0 compliance:

```python
#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
```

**Validation**: `uv run python .gemini/skills/workflow-utilities/scripts/check_spdx_headers.py`

## Worktree State Isolation

Multiple Gemini Code instances can work on different features concurrently using git worktrees. Each worktree has isolated state in `.gemini-state/`:

```
repo/                         # Main repository
├── .gemini/skills/          # Shared (read-only)
├── .gemini-state/           # Per-worktree state
│   ├── agentdb.duckdb       # Isolated database
│   ├── workflow.json        # Workflow progress
│   └── .worktree-id         # Stable identifier
└── ...

repo_feature_abc/            # Feature worktree
├── .gemini-state/           # Separate state
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
| Container not building | `podman info` to verify Podman running (CI/CD only) |
| pytest not found | Use `uv run pytest` |
| Import errors | Use `uv run python` |
| Worktree conflicts | `git worktree remove` + `git worktree prune` |
| Ended on wrong branch | `git checkout contrib/stharrold` |
| Orphaned state dirs | Run `cleanup_orphaned_state()` from worktree_context |
| Branch divergence | See [Preventing Branch Divergence](#preventing-branch-divergence) section |
| DuckDB not found | Run `uv sync` to install duckdb Python package (CLI not required) |

## Quick Debugging

```bash
# Where am I in the workflow?
uv run python .gemini/skills/agentdb-state-manager/scripts/query_workflow_state.py

# Am I in the right context for this step?
uv run python .gemini/skills/workflow-utilities/scripts/verify_workflow_context.py --step <N>

# What branches exist?
git branch -a | grep -E "(feature|release|contrib)"

# What worktrees exist?
git worktree list

# What's the current branch?
git branch --show-current

# Is this a worktree or main repo?
git rev-parse --git-dir  # .git = main repo, .git/worktrees/* = worktree
```

## Preventing Branch Divergence

**Problem**: When multiple sessions run `rebase-contrib` or `daily_rebase.py`, local and remote branches can diverge with same content but different SHAs.

**Root cause**: Rebasing creates new commit SHAs. If session A rebases and pushes while session B has old history, session B's subsequent rebase creates parallel history.

**Built-in safeguards** (v5.16.0+):
- `backmerge_workflow.py` and `daily_rebase.py` now check for divergence before rebasing
- If divergence detected, scripts halt with resolution options
- If remote is ahead, scripts auto-pull before rebasing

**Manual detection**:
```bash
# Check for divergence
git fetch origin
git rev-list --left-right --count contrib/stharrold...origin/contrib/stharrold
# Output: "X Y" where X=local-only commits, Y=remote-only commits
# If both > 0: DIVERGED
```

**Resolution options**:
```bash
# Option 1: Accept remote (recommended if remote has newer work)
git reset --hard origin/contrib/stharrold

# Option 2: Force push local (if local has work you want to keep)
git push --force-with-lease origin contrib/stharrold

# Option 3: Merge (creates merge commit, less clean history)
git pull --no-rebase
```

**Best practices**:
1. Always push after running backmerge or daily rebase
2. Pull before starting new work in a session
3. Avoid running backmerge from multiple machines simultaneously
4. Use single source of truth for rebase operations

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
# From within stharrold-templates:
python .gemini/skills/initialize-repository/scripts/initialize_repository.py . /path/to/target-repo
```

**Interactive 4-phase Q&A:**
1. **Configuration** - Project name, description, VCS provider (GitHub/Azure DevOps)
2. **Component selection** - Which skills to include
3. **File generation** - Creates pyproject.toml, README.md, GEMINI.md, etc.
4. **Git initialization** - Sets up main/develop/contrib branch structure

**Requirements for target repo:**
- Python 3.11+ with `uv`
- `pytest` for testing
- `ruff` + `mypy` for linting
- Podman for containerization
- GitHub (`gh`) OR Azure DevOps (`az`) CLI

**See:** `.gemini/skills/initialize-repository/GEMINI.md` for full documentation.

## Reference Documentation

- `WORKFLOW.md` - Workflow overview (14KB) with phase index
- `docs/reference/workflow-*.md` - Phase-specific workflow docs (≤20KB each)
- `CHANGELOG.md` - Version history
- `ARCHIVED/` - Archived specs, planning docs, and deprecated skills (zipped)

## GEMINI.md Hierarchy

Every directory has a GEMINI.md with YAML frontmatter for AI navigation:
- `parent` - Link to parent directory's GEMINI.md
- `children` - Links to child directories' GEMINI.md files
- `sibling_readme` - Link to same-level README.md

```bash
# Generate missing GEMINI.md files
uv run python .gemini/skills/workflow-utilities/scripts/generate_gemini_md.py

# Update children references in existing GEMINI.md files
uv run python .gemini/skills/workflow-utilities/scripts/update_gemini_md_refs.py
```

## Related Documentation

- **[README.md](README.md)** - Human-readable documentation for this directory

**Child Directories:**
- **[ARCHIVED/GEMINI.md](ARCHIVED/GEMINI.md)** - Archived
- **[docs/GEMINI.md](docs/GEMINI.md)** - Docs
- **[tests/GEMINI.md](tests/GEMINI.md)** - Tests
