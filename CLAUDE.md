# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

**Templates and utilities for MCP (Model Context Protocol) server configuration:**
- Multi-platform MCP manager (`mcp_manager.py`) for Claude Code CLI, VS Code, and Claude Desktop
- Modular documentation guides (≤30KB per file for AI context optimization)
- Workflow automation tools (git helpers, archive management, semantic versioning)
- **NOT a Python package** - Collection of standalone stdlib-only tools and templates

**Key Principle**: Core tools use stdlib only. Development tools (pytest, ruff, mypy) are optional via uv.

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
├── tools/                      # Workflow automation (german-workflow v1.15.1 stdlib-only scripts)
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

### MCP Manager Operations

```bash
# Status and platform detection
/usr/bin/python3 mcp_manager.py --status           # Show all platforms and servers
/usr/bin/python3 mcp_manager.py --check-credentials # Validate tokens

# Interactive management (auto-detects platform)
/usr/bin/python3 mcp_manager.py --add              # Add server
/usr/bin/python3 mcp_manager.py --remove           # Remove server
/usr/bin/python3 mcp_manager.py --disable          # Disable (DISABLED_ prefix)
/usr/bin/python3 mcp_manager.py --enable           # Re-enable

# Platform-specific operations
/usr/bin/python3 mcp_manager.py --platform claude-code --list
/usr/bin/python3 mcp_manager.py --platform vscode --add

# Maintenance
/usr/bin/python3 mcp_manager.py --deduplicate      # Remove duplicates
/usr/bin/python3 mcp_manager.py --backup-only      # Create backups
```

### Validation & Testing

```bash
# Documentation validation (run before committing docs)
./validate_documentation.sh                        # All 5 tests (orchestrator)
./test_file_size.sh                               # 30KB limit check
./test_cross_references.sh                        # Internal links
./test_content_duplication.sh                     # Duplicate detection
./test_command_syntax.sh                          # Bash command validation
./test_yaml_structure.sh                          # YAML frontmatter

# MCP functionality tests
/usr/bin/python3 test_mcp_deduplication.py        # Deduplication logic

# Test specific directory
./test_file_size.sh 10_draft-merged/30_implementation/
```

### Quality Assurance

```bash
# Linting and type checking (requires uv sync)
uv run ruff check .                               # All files
uv run ruff check --fix .                         # Auto-fix issues
uv run mypy mcp_manager.py                        # Type checking

# Codacy analysis (8 tools: pylint, bandit, ruff, mypy, prospector, flake8, pydocstyle, pycodestyle)
./.codacy/cli.sh analyze mcp_manager.py           # Analyze file
./.codacy/cli.sh analyze --tool pylint .          # Specific tool
./.codacy/cli.sh analyze --tool bandit --format json  # Security scan
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
python3 tools/git-helpers/semantic_version.py develop v5.0.0

# Archive management
python3 tools/workflow-utilities/archive_manager.py list
python3 tools/workflow-utilities/archive_manager.py create path/to/file

# Directory structure validation
python3 tools/workflow-utilities/directory_structure.py 10_draft-merged/

# Version consistency
python3 tools/workflow-utilities/validate_versions.py
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
python3 --version     # Python 3.12+ (for dev tools and CI/CD)
git --version         # Version control
gh --version          # GitHub CLI (for PR management)

# Optional (for development tools)
uv --version          # Python package manager
```

### Setup

```bash
# Fork and clone
gh repo fork stharrold/stharrold-templates --clone
cd stharrold-templates

# Install development dependencies (optional)
uv sync               # Installs pytest, ruff, mypy

# Test MCP manager
/usr/bin/python3 mcp_manager.py --status

# Validate documentation
./validate_documentation.sh
```

### Virtual Environment (Optional)

```bash
# Create and activate
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
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
- **Test before committing**: Run `./validate_documentation.sh` for docs, linting for code
- **Follow document lifecycle**: 00_draft-initial → 10_draft-merged → ARCHIVED
- **Use modular navigation**: Start with CLAUDE.md orchestrators, follow hierarchy
- **Platform-specific approach**: No cross-platform MCP sync (manage each platform separately)
- **Archive completed tasks**: Keep repository clean with compressed archives
- **Stdlib-only for core tools**: Dev tools (pytest, ruff, mypy) are optional

## Common Issues

### MCP Manager
- **Permission errors**: Use `/usr/bin/python3 mcp_manager.py` or `chmod +x mcp_manager.py`
- **Platform not found**: Use `--status` to see available platforms
- **Auto-detection issues**: Explicitly specify `--platform <name>`

### Shell Scripts
- **Permission denied**: Run `chmod +x *.sh test_*.sh validate_documentation.sh`
- **Validation failures**: Check specific test output for details

### Development
- **Import errors**: Use `/usr/bin/python3` for system Python
- **Configuration not found**: Check platform-specific paths with `--status`
- **Worktree conflicts**: Remove old worktrees with `git worktree remove` and `git worktree prune`

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
- ✅ CI/CD Pipelines (GitHub Actions + Azure Pipelines)
- ✅ Workflow Tools (tools/ directory - stdlib only scripts)
- ✅ CONTRIBUTING.md (quality standards, PR process)
- ✅ Enhanced .gitignore (comprehensive Python exclusions)
- ✅ pyproject.toml with uv dependency management (dev tools)
- ✅ Reference documentation (docs/reference/)

**Usage**:
- Skills provide progressive disclosure workflow for complex tasks
- Use BMAD for planning, SpecKit for specifications, quality-enforcer for gates
- AgentDB provides state management across worktrees (optional)

See `docs/reference/german-workflow-v5.3.0.md` for workflow reference (v5.3.0 documentation snapshot). Latest workflow version in `.tmp/german/` is v1.15.1 (2025-11-18).
