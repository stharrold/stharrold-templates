# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

**Templates and utilities for MCP (Model Context Protocol) server configuration:**
- Multi-platform MCP manager (`mcp_manager.py`) for Claude Code CLI, VS Code, and Claude Desktop
- Modular documentation guides (≤30KB per file for AI context optimization)
- Workflow automation tools (git helpers, archive management, semantic versioning)
- **Containerized development** - Podman + uv + Python 3.11 for consistent dev/CI environments

**Key Principle**: All development uses Podman containers with uv-managed Python 3.11. Testing with pytest, linting with ruff.

## Repository Structure

```
stharrold-templates/
├── mcp_manager.py              # Main: Multi-platform MCP server manager
├── test_mcp_deduplication.py   # MCP deduplication tests
├── validate_documentation.sh   # Validation orchestrator (runs 5 test_*.sh scripts)
├── test_*.sh                   # file_size, cross_references, content_duplication, command_syntax, yaml_structure
├── .claude/skills/             # Full german-workflow v1.15.1 skills integration (9 skills)
│   ├── agentdb-state-manager/ # State management with DuckDB synchronization
│   ├── bmad-planner/          # BMAD planning (requirements + architecture)
│   ├── git-workflow-manager/  # Git worktree and release management
│   ├── initialize-repository/ # Repository initialization
│   ├── quality-enforcer/      # Quality gates (tests, coverage, linting)
│   ├── speckit-author/        # SpecKit specifications (spec + plan)
│   ├── tech-stack-adapter/    # Python/uv/Podman stack detection
│   ├── workflow-orchestrator/ # Main workflow coordinator
│   └── workflow-utilities/    # Archive, directory structure, version validation
├── tools/                      # Workflow automation (german-workflow v1.15.1 scripts)
│   ├── git-helpers/           # create_worktree.py, semantic_version.py
│   └── workflow-utilities/    # archive_manager.py, directory_structure.py, validate_versions.py
├── 00_draft-initial/          # New content awaiting integration
├── 10_draft-merged/           # Production guides (≤30KB, modular CLAUDE.md hierarchy)
│   ├── CLAUDE.md             # Orchestrator for subdirectories
│   ├── 10_mcp/               # MCP server configuration
│   ├── 20_credentials/       # Security and credential management
│   └── 30_implementation/    # Development patterns and workflows
├── ARCHIVED/                  # Compressed date-based archives (YYYYMMDD.tar.gz)
├── TODO.md                    # GitHub issues tracker (#3-#44, 31 open, 1 closed)
├── CONTRIBUTING.md            # Contributor guidelines and quality standards
└── docs/reference/            # german-workflow-v5.3.0.md, WORKFLOW-INIT-PROMPT.md
```

## Core Architecture

### Document Lifecycle
```
Research → Integration → Archive
   ↓           ↓          ↓
00_draft-   10_draft-   ARCHIVED/
initial/    merged/     (YYYYMMDD.tar.gz)
```

**Integration Pipeline**: TODO.md tracks 22 GitHub issues → Planning docs → Worktrees → 10_draft-merged/

### MCP Manager Architecture

**Platform Detection** (`mcp_manager.py`):
- Auto-detects first available: claude-code → vscode → claude-desktop
- Platform-specific schemas: `"mcpServers": {}` (Claude) vs `"servers": {}` (VS Code)
- Config paths: `~/.claude.json` (CLI), platform-specific for VS Code/Desktop

**Key Classes & Functions**:
- `MCPConfig(platform, config_path)` - Platform-specific configuration handler (mcp_manager.py:97)
- `select_target_platform()` - Returns first available platform (mcp_manager.py:74)
- `deduplicate_servers()` - Preserves DISABLED_ prefixed versions (mcp_manager.py:432)
- `validate_credentials()` - Checks keychain/env for tokens (mcp_manager.py:44)
- `get_platform_config_paths()` - Returns OS-specific paths (mcp_manager.py:19)

**Server Management Pattern**:
- Active: Normal names (e.g., "github")
- Disabled: DISABLED_ prefix (e.g., "DISABLED_github")
- Deduplication preserves DISABLED_ versions during cleanup

### Modular CLAUDE.md Navigation

Hierarchical orchestration pattern:
1. Main CLAUDE.md (this file) → Repository overview
2. 10_draft-merged/CLAUDE.md → Subdirectory orchestrator
3. 10_draft-merged/{subdirectory}/CLAUDE.md → Domain-specific context
4. Individual guide files → Detailed implementation

**30KB Context Optimization**: Cross-references without loading full content.

## Essential Commands

### Container Environment

```bash
# Build container (first time or after Containerfile changes)
podman-compose build

# Run commands
podman-compose run --rm dev <command>

# Interactive shell
podman-compose run --rm dev bash

# Background container (optional)
podman-compose up -d              # Start dev container
podman-compose exec dev bash      # Shell into running container
podman-compose down               # Stop container
```

### MCP Manager Operations

```bash
# Status and platform detection
podman-compose run --rm dev python mcp_manager.py --status
podman-compose run --rm dev python mcp_manager.py --check-credentials

# Interactive management (auto-detects platform)
podman-compose run --rm dev python mcp_manager.py --add
podman-compose run --rm dev python mcp_manager.py --remove
podman-compose run --rm dev python mcp_manager.py --disable
podman-compose run --rm dev python mcp_manager.py --enable

# Platform-specific operations
podman-compose run --rm dev python mcp_manager.py --platform claude-code --list
podman-compose run --rm dev python mcp_manager.py --platform vscode --add

# Maintenance
podman-compose run --rm dev python mcp_manager.py --deduplicate
podman-compose run --rm dev python mcp_manager.py --backup-only
```

### Validation & Testing

```bash
# Documentation validation
podman-compose run --rm dev ./validate_documentation.sh
podman-compose run --rm dev ./test_file_size.sh
podman-compose run --rm dev ./test_cross_references.sh

# Run all tests with pytest
podman-compose run --rm dev pytest
podman-compose run --rm dev pytest test_mcp_deduplication.py -v

# Test specific directory
podman-compose run --rm dev ./test_file_size.sh 10_draft-merged/30_implementation/
```

### Quality Assurance

```bash
# Linting with ruff
podman-compose run --rm dev ruff check .
podman-compose run --rm dev ruff check --fix .
podman-compose run --rm dev ruff format .

# Testing with pytest
podman-compose run --rm dev pytest
podman-compose run --rm dev pytest --cov=. --cov-report=term
podman-compose run --rm dev pytest -v tests/
```

### Git Workflow

**Branch Structure**:
```
main (production)
  ↑
develop (integration)
  ↑
contrib/stharrold (active development - default branch)
  ↑
feature/* (via worktrees)
```

**PR Flow**: Feature → contrib/stharrold → develop → main

**Worktree Management**:
```bash
# Create feature worktree (using automation tool)
python3 tools/git-helpers/create_worktree.py feature my-feature contrib/stharrold

# Manual worktree creation
git worktree add ../stharrold-templates.worktrees/my-feature -b feat/my-feature

# List and cleanup
git worktree list
git worktree remove ../stharrold-templates.worktrees/my-feature
git worktree prune
```

**Commit Format**:
```bash
git commit -m "feat: descriptive message

Closes #123

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Types**: feat, fix, docs, style, refactor, test, chore

### Workflow Automation Tools

```bash
# Semantic versioning (customized for templates repo)
podman-compose run --rm dev python tools/git-helpers/semantic_version.py develop v5.0.0

# Archive management
podman-compose run --rm dev python tools/workflow-utilities/archive_manager.py list
podman-compose run --rm dev python tools/workflow-utilities/archive_manager.py create path/to/file

# Directory structure validation
podman-compose run --rm dev python tools/workflow-utilities/directory_structure.py 10_draft-merged/

# Version consistency
podman-compose run --rm dev python tools/workflow-utilities/validate_versions.py
```

## Platform-Specific MCP Configuration

### Configuration Paths (OS-specific)

**macOS**:
- Claude Code: `~/.claude.json`
- VS Code: `~/Library/Application Support/Code/User/mcp.json`
- Claude Desktop: `~/Library/Application Support/Claude/config.json`

**Windows**:
- Claude Code: `~/.claude.json`
- VS Code: `~/AppData/Roaming/Code/User/mcp.json`
- Claude Desktop: `~/AppData/Roaming/Claude/config.json`

**Linux**:
- Claude Code: `~/.claude.json`
- VS Code: `~/.config/Code/User/mcp.json`
- Claude Desktop: `~/.config/claude/config.json`

### Schema Differences

**Claude Code & Desktop** (`mcpServers` root key):
```json
{
  "mcpServers": {
    "server-name": {
      "command": "command",
      "args": ["arg1"],
      "env": {"ENV_VAR": "value"}
    }
  }
}
```

**VS Code** (`servers` root key):
```json
{
  "servers": {
    "server-name": {
      "command": "command",
      "args": ["arg1"],
      "env": {"ENV_VAR": "value"}
    }
  }
}
```

### Credential Management

**Common Tokens**: GITHUB_TOKEN, OPENAI_API_KEY, ANTHROPIC_API_KEY

**Storage**:
- macOS: Keychain
- Windows: Credential Manager
- Linux: Environment variables (or gnome-keyring)

**Validation**: `--check-credentials` checks keychain/env for tokens

## Development Environment

### Prerequisites

```bash
# Required
podman --version          # Container runtime (Podman 4.0+)
podman-compose --version  # Container orchestration
git --version             # Version control
gh --version              # GitHub CLI (for PR management)
```

### Setup

```bash
# Fork and clone
gh repo fork stharrold/stharrold-templates --clone
cd stharrold-templates

# Build container
podman-compose build

# Test MCP manager
podman-compose run --rm dev python mcp_manager.py --status

# Validate documentation
podman-compose run --rm dev ./validate_documentation.sh
```

## CI/CD Integration

**GitHub Actions** (`.github/workflows/tests.yml`):
- Runs on: push/PR to main, develop, contrib/stharrold
- Tests: documentation validation, MCP manager, deduplication, linting, type checking

**Azure Pipelines** (`azure-pipelines.yml`):
- Alternative CI/CD platform
- Same test suite as GitHub Actions

## Issue Integration Architecture

**GitHub Issues → Implementation Pipeline**:

1. **GitHub Issues**: #3-#24, #31-#44 (tracked in TODO.md)
2. **Planning**: `TODO_FOR_issue-{number}-{approach}.md`
3. **Worktrees**: `../stharrold-templates.worktrees/issue/{number}-{approach}`
4. **Document Order**: Files numbered by source (09_, 11_, 12_) integrate sequentially
5. **Multi-Approach**: Single issue can have multiple worktrees (claude, bmad, speckit, flow)

**Current Priorities** (from TODO.md):
1. Code review feedback (#31-35, #38-39, #41-44)
2. 🔴 **TOP**: Issue #13 (Document #11 - embedding model integration)
3. Core technical docs (#15-16, #22-23)
4. Security enhancements (#3-5)
5. Infrastructure (#8-11)

## Critical Guidelines

- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** unless explicitly requested
- **Test before committing**: Run `podman-compose run --rm dev pytest` and `podman-compose run --rm dev ruff check .`
- **Follow document lifecycle**: 00_draft-initial → 10_draft-merged → ARCHIVED
- **Use modular navigation**: Start with CLAUDE.md orchestrators, follow hierarchy
- **Platform-specific approach**: No cross-platform MCP sync (manage each platform separately)
- **Archive completed tasks**: Keep repository clean with compressed archives
- **Use Podman containers**: Same container for dev and CI/CD ensures consistency

## Common Issues

### MCP Manager
- **Permission errors**: Use `podman-compose run --rm dev python mcp_manager.py`
- **Platform not found**: Use `--status` to see available platforms
- **Auto-detection issues**: Explicitly specify `--platform <name>`

### Shell Scripts
- **Permission denied**: Run `chmod +x *.sh test_*.sh validate_documentation.sh`
- **Validation failures**: Check specific test output for details

### Development
- **Import errors**: Use `podman-compose run --rm dev python`
- **Configuration not found**: Check platform-specific paths with `--status`
- **Worktree conflicts**: Remove old worktrees with `git worktree remove` and `git worktree prune`
- **Container not building**: Run `podman info` to verify Podman is running

## German Workflow System Integration (Full)

Integrated from german workflow v1.15.1 (updated 2025-11-20):

**Skills** (`.claude/skills/` - 9 skills):
- ✅ **workflow-orchestrator** - Main coordinator (~300 lines) with TODO, WORKFLOW, CLAUDE templates
- ✅ **tech-stack-adapter** - Detects Python/uv/Podman (~200 lines)
- ✅ **git-workflow-manager** - Git operations (~500 lines): worktree, release, semantic version
- ✅ **bmad-planner** - BMAD planning (requirements + architecture)
- ✅ **speckit-author** - SpecKit specifications (spec + plan)
- ✅ **quality-enforcer** - Quality gates (≥80% coverage, tests, linting)
- ✅ **agentdb-state-manager** - DuckDB state synchronization (MIT Agent Pattern)
- ✅ **initialize-repository** - Repository initialization
- ✅ **workflow-utilities** - Archive, directory structure, version validation

**Infrastructure**:
- ✅ CI/CD Pipelines (GitHub Actions + Azure Pipelines with Podman)
- ✅ Workflow Tools (tools/ directory)
- ✅ CONTRIBUTING.md (quality standards, PR process)
- ✅ Enhanced .gitignore (comprehensive Python exclusions)
- ✅ pyproject.toml with uv dependency management
- ✅ Containerfile + podman-compose.yml for dev/CI consistency
- ✅ Reference documentation (docs/reference/)

**Usage**:
- Skills provide progressive disclosure workflow for complex tasks
- Use BMAD for planning, SpecKit for specifications, quality-enforcer for gates
- AgentDB provides state management across worktrees (optional)

See `docs/reference/german-workflow-v5.3.0.md` for workflow reference (v5.3.0 documentation snapshot). Latest workflow version in `.tmp/german/` is v1.15.1 (2025-11-18).
