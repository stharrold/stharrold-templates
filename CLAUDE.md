# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Latest Update (2025-09-14)**: Enhanced with comprehensive MCP security patterns including OAuth 2.1 implementation, production security tools (mcp-secrets-plugin, mcpauth, Auth0), layered storage architecture, and Trail of Bits vulnerability mitigations. See feature/08_merge branch for detailed security enhancements.

## Repository Architecture

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and agentic development workflows. The repository provides cross-platform tools, comprehensive modular guides, and automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

**Current MCP State**: All MCP servers have been removed from all platforms (as of 2025-09-12). This provides a clean slate for selective server management using the platform-specific approach.

**Repository Configuration**: Default working branch is `contrib/stharrold` for active development. GitHub repository configured with minimal branch protection (deletion prevention only).

### Core Architecture

The repository follows a **platform-specific management approach** with a structured document lifecycle:

**Management Tool Architecture:**
1. **`mcp_manager.py`** - Central platform-targeted management tool with auto-detection
   - Single-platform operations (not cross-platform synchronization)
   - MCPConfig class handles individual platform operations
   - Platform selection via `select_target_platform()` with auto-detection
   - Disable/enable servers via `DISABLED_` prefix renaming

**Document Lifecycle System:**
2. **Research Phase** (`00_draft-initial/`) - Raw research and analysis awaiting integration
3. **Modular Guides** (`10_draft-merged/`) - Hierarchical documentation with YAML frontmatter and 30KB file limits
4. **Archive System** (`ARCHIVED/`) - Historical documents with UTC timestamps (`YYYYMMDDTHHMMSSZ_filename.ext`)

### Modular Guide Structure
The `10_draft-merged/` directory contains a hierarchical documentation system:
- **`CLAUDE.md`** - Project Context Orchestrator with 30KB file constraints
- **`10_mcp/`** - MCP server configuration and setup guides
- **`20_credentials/`** - Security and credential management guides
- **`30_implementation/`** - Development strategy, workflow patterns, and testing standards
  - **Multi-agent orchestration subcategories**:
    - `38a_enterprise-migration-timeline.md` - 9-week enterprise migration plan
    - `39a_langgraph-orchestration.md` - LangGraph TypeScript implementation (18KB)
    - `39b_state-management.md` - Redis Cluster, Celery, CQRS patterns (12KB)
    - `39c_workflow-implementation.md` - Complete w00.0-w09.0 workflows (23KB)

Each directory has its own `CLAUDE.md` orchestrator and numbered guide files for systematic navigation.

### Key Components

- **Platform-Specific MCP Manager**: `mcp_manager.py` handles server management for individual platforms with auto-detection and platform targeting
- **LangGraph Orchestration**: Production-ready multi-agent coordination with TypeScript integration (replaces Claude-Flow)
- **Podman Container Management**: Rootless, daemonless container architecture (replaces Docker)
- **Modular Guide System**: Hierarchical documentation with context optimization:
  - `10_mcp/` - MCP setup and configuration guides
  - `20_credentials/` - Security and credential management guides
  - `30_implementation/` - Development strategy and workflow patterns
- **OpenTelemetry Observability**: Prometheus/Grafana/Jaeger monitoring stack
- **Enterprise Migration Framework**: 9-week implementation timeline with validation checkpoints
- **Schema Harmonization**: Handles differences between Claude Code CLI (`mcpServers`), VS Code (`servers`), and Claude Desktop (`mcpServers`) schemas
- **Archive System**: UTC-timestamped format `YYYYMMDDTHHMMSSZ_filename.ext`

## Common Commands

### MCP Management
```bash
# Always use system Python to avoid virtual environment issues

# Platform Status and Detection
/usr/bin/python3 mcp_manager.py --status         # Show all platform statuses
/usr/bin/python3 mcp_manager.py                  # Auto-detect first available platform
/usr/bin/python3 mcp_manager.py --list           # List servers from auto-detected platform

# Platform-Specific Operations
/usr/bin/python3 mcp_manager.py --platform claude-code --list      # List Claude Code CLI servers
/usr/bin/python3 mcp_manager.py --platform vscode --add           # Add server to VS Code MCP
/usr/bin/python3 mcp_manager.py --platform claude-desktop --remove # Remove from Claude Desktop

# Server Management (works with auto-detected or specified platform)
/usr/bin/python3 mcp_manager.py --add            # Interactive server addition
/usr/bin/python3 mcp_manager.py --remove         # Interactive server removal
/usr/bin/python3 mcp_manager.py --disable        # Temporarily disable servers
/usr/bin/python3 mcp_manager.py --enable         # Re-enable disabled servers
/usr/bin/python3 mcp_manager.py --deduplicate     # Remove duplicate servers (keeps DISABLED_ versions)

# Cross-Platform Features
/usr/bin/python3 mcp_manager.py --check-credentials  # Validate credential setup
/usr/bin/python3 mcp_manager.py --backup-only    # Create configuration backups
/usr/bin/python3 mcp_manager.py --file ~/.claude.json  # Work with specific config file

# Deduplication Examples
/usr/bin/python3 mcp_manager.py --deduplicate    # Auto-detect platform and remove duplicates
/usr/bin/python3 mcp_manager.py --platform claude-code --deduplicate  # Target specific platform

# Alternative Claude Code CLI commands
claude mcp list                                   # List configured servers
claude mcp add <name> <command> [args...]        # Add server
claude mcp remove <name>                         # Remove server
```

### Git Operations
```bash
# Repository connected to GitHub (contrib/stharrold is default branch)
git status && git add --all                  # Stage all changes
git log --oneline -10                         # Recent commit history

# Unified Git Conventions (branches, worktrees, commits)
feat/     # New features and enhancements
fix/      # Bug fixes
docs/     # Documentation changes
chore/    # Maintenance, dependencies, tooling
refactor/ # Code restructuring
test/     # Testing additions/updates

# Branch and worktree management
git worktree add ../stharrold-templates.worktrees/feat/12-task -b feat/12-task
git commit -m "feat: descriptive message"
git checkout main && git checkout contrib/stharrold

# Archive files with UTC timestamp
mv file.ext ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_file.ext
```

### Document Management
```bash
# Working with modular guide system
# Navigate to guides in execution order:
10_draft-merged/10_mcp/CLAUDE.md           # MCP setup and configuration
10_draft-merged/20_credentials/CLAUDE.md   # Security and credential management
10_draft-merged/30_implementation/CLAUDE.md # Development strategy and patterns

# Archive files with UTC timestamp
mv file.ext ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_file.ext

# Research documents awaiting integration
ls 00_draft-initial/
```

### Development and Testing
```bash
# Dependency management with UV (system default)
uv sync && uv add package_name            # Sync dependencies and add new packages

# Core Python testing
/usr/bin/python3 test_mcp_deduplication.py         # Test deduplication functionality
/usr/bin/python3 mcp_manager.py --validate-all     # Validate all configurations
python3 -c "import mcp_manager; mcp_manager.validate_credentials()"  # Test credentials

# Module verification
python3 -c "import mcp_manager; print('MCPConfig available:', hasattr(mcp_manager, 'MCPConfig'))"
```

### Code Quality and Security Analysis
```bash
# CRITICAL: Run after ANY file edit
./.codacy/cli.sh analyze --tool pylint edited_file.py    # Python files
./.codacy/cli.sh analyze edited_file                     # Any file

# CRITICAL: Run after dependency changes
./.codacy/cli.sh analyze --tool trivy .                  # Security scan

# Additional tools
./.codacy/cli.sh version                                 # Check CLI status
./.codacy/cli.sh analyze --tool semgrep                  # Security analysis
```

### Security Tools and Emergency Response
```bash
# Deploy security tools (see 25_mcp-security-tools.md)
pip install mcp-secrets-plugin && npx create-mcpauth-app

# Emergency credential management
mcp-secrets set github token && mcp-secrets list
```

## Critical Workflow Rules

### Code Quality Integration
**CRITICAL**: After ANY file edit, IMMEDIATELY run:
```bash
./.codacy/cli.sh analyze --tool pylint edited_file.py  # Python files
./.codacy/cli.sh analyze edited_file                   # Other files
```
If issues found, propose and apply fixes before continuing.

### File Size Constraints
- All files in `10_draft-merged/` must be ≤30KB for optimal AI context processing
- Use UTC timestamp format: `YYYYMMDDTHHMMSSZ_filename.ext` for `ARCHIVED/`

## MCP Server Configuration Architecture

### Platform Differences
- **Claude Code CLI & Desktop**: Use `"mcpServers": {}` as root key
- **VS Code MCP Extension**: Uses `"servers": {}` as root key
- **Config Paths**: `~/.claude.json` (CLI), platform-specific for VS Code/Desktop
- **Credentials**: Keychain (macOS), Credential Manager (Windows), environment variables (Linux)

## Platform Targeting
The `mcp_manager.py` tool operates on **one platform at a time**:
- **Auto-detection**: `--status` shows all platforms, tool auto-selects first available
- **Explicit targeting**: `--platform <name>` (claude-code, vscode, claude-desktop)
- **Common tokens**: GITHUB_TOKEN, OPENAI_API_KEY, ANTHROPIC_API_KEY

## CRITICAL: Code Quality Requirements

**⚠️ NON-NEGOTIABLE**: After ANY file edit or dependency change, IMMEDIATELY run:
1. **File edits**: `./.codacy/cli.sh analyze --tool pylint [edited_file]`
2. **Dependencies**: `./.codacy/cli.sh analyze --tool trivy .`

Complete details in `.github/instructions/codacy.instructions.md`

## Quick Reference for Development

### Most Common Commands
```bash
# System status and testing
/usr/bin/python3 mcp_manager.py --status
/usr/bin/python3 test_mcp_deduplication.py
/usr/bin/python3 mcp_manager.py --check-credentials

# Interactive MCP management
/usr/bin/python3 mcp_manager.py --add
/usr/bin/python3 mcp_manager.py --backup-only

# Code quality (CRITICAL after edits)
./.codacy/cli.sh analyze --tool pylint edited_file.py

# Git workflow with unified conventions
git worktree add ../worktrees/feat/12-task -b feat/12-task
git commit -m "feat: descriptive message"
```

## Important Guidelines
- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** unless explicitly requested
- Work on `contrib/stharrold` branch, create PRs to `develop` or `main`

## Documentation Structure

This repository implements a **structured document lifecycle** that moves content from research through integration to archival:

- **Modular Guides** (`10_draft-merged/`): Hierarchical documentation system with YAML frontmatter
  - Version-controlled with changelog tracking and 30KB file constraints
  - Organized into `10_mcp/`, `20_credentials/`, and `30_implementation/` directories
- **Draft Documents** (`00_draft-initial/`): Research reports and analysis awaiting integration
  - Contains specialized reports covering AI agents, embeddings, and architecture patterns
  - Research content gets integrated into modular guides then moved to archive
- **Archived Documents** (`ARCHIVED/`): Historical documents with UTC timestamps
  - Preserves evolution of ideas and implementation strategies
  - Critical for understanding context behind current implementations

### mcp_manager.py Architecture
The tool implements a **platform-specific management architecture** with:
- Auto-detection of available MCP platforms (Claude Code CLI, VS Code MCP, Claude Desktop)
- Platform-specific operations without cross-platform synchronization
- Server disable/enable via `DISABLED_` prefix renaming
- Deduplication and credential validation capabilities
- Schema harmonization between different platform configurations

**Core Classes and Functions:**
- `MCPConfig`: Main configuration management class with platform-specific logic
  - `__init__(platform: str, config_path: Optional[Path] = None)`: Initialize for specific platform
  - `load_config()`: Load platform-specific configuration file
  - `save_config()`: Save configuration with backup creation
  - `add_server()`, `remove_server()`: Interactive server management
  - `disable_server()`, `enable_server()`: DISABLED_ prefix management
- `select_target_platform()`: Auto-detection algorithm returning first available platform
- `validate_credentials()`: Cross-platform credential validation for common tokens
- `deduplicate_servers()`: Intelligent duplicate removal preserving DISABLED_ versions
- `get_platform_config_paths()`: Cross-platform path resolution for config files

**Platform Detection Logic:**
1. Checks for existing configuration files in platform-specific paths
2. Returns first available platform or prompts for selection
3. Handles macOS, Windows, and Linux path differences automatically

**Standard Python Import**: With the new filename (`mcp_manager.py`), use standard Python import:
```python
import mcp_manager
# Initialize: config = mcp_manager.MCPConfig('claude-code')
# Auto-detect: platform = mcp_manager.select_target_platform()
# Validate: results = mcp_manager.validate_credentials()
```

**Testing Pattern**: Standard Python imports work directly. The `test_mcp_deduplication.py` uses `import mcp_manager` for clean, Pythonic module access and tests core deduplication functionality.

### MCP Server Tiers
- **Tier 1**: Essential Core Development (GitHub, Git, Filesystem, Sequential Thinking)
- **Tier 2**: High-Impact Productivity (Codacy, Sentry, Azure DevOps, Terraform, DeepEval, Hypothesis)
- **Tier 3**: Advanced Collaboration (Slack, Notion, PostHog, Zapier)
- **Tier 4**: Specialized Domain (MongoDB, Figma, Apidog)

### Key Technologies (v4.0+)
- **LangGraph**: Multi-agent orchestration with TypeScript integration
- **Podman**: Rootless container management (replaces Docker)
- **OpenTelemetry**: Observability stack (Prometheus/Grafana/Jaeger)
- **Redis Cluster + Celery**: Distributed state management and task queues
- **DeepEval + Hypothesis**: LLM-specific testing and property-based testing

## Local Permissions
Claude Code permissions configured in `.claude/settings.local.json`:
- GitHub repository search and file access
- File system operations (`chmod`, `sed`, `grep`)
- Sequential thinking for complex problem solving
- Codacy analysis integration
- WebFetch for specific domains (github.com, mcpcat.io, apidog.com)

## Common Issues & Solutions

### MCP Manager Issues
- **Permission errors**: Run `chmod +x mcp_manager.py`
- **Platform not found**: Use `--status` to see available platforms or specify `--platform <name>`
- **Auto-detection issues**: Explicitly specify target platform with `--platform <name>`

### Local Codacy CLI Issues
- **CLI not executable**: Run `chmod +x ./.codacy/cli.sh`
- **CLI not found**: Verify binary cache exists: `ls -la ~/Library/Caches/Codacy/` (macOS)
- **Analysis fails**: Check file exists and tool supports the file type
- **No tools support file**: Expected for markdown/text files - tools focus on code analysis

### Python Development Issues
- **Import errors**: Use `/usr/bin/python3` for system Python or ensure proper virtual environment activation
- **Missing dependencies**: Run `uv sync` or `pip install -e .` in development mode
- **Configuration not found**: Check platform-specific paths with `--status` flag
- **Permission denied**: Run `chmod +x mcp_manager.py` or use `python3 mcp_manager.py` instead of direct execution
- **Platform detection fails**: Manually specify platform with `--platform <name>` flag

### Git Workflow Issues
- **Branch confusion**: Default branch is `contrib/stharrold`, not `main`
- **Push failures**: Ensure you're on the correct branch before pushing
- **PR creation**: Use GitHub web interface or `gh pr create` for pull requests

## Current State (as of 2025-09-14)
- **All MCP servers removed** from all platforms (clean slate)
- **Default branch**: `contrib/stharrold` for active development
- **GitHub integration**: Repository connected with minimal branch protection
- **v4.0 Breaking Changes Complete (100%)**:
  - **LangGraph orchestration** replaces Claude-Flow completely
  - **Podman container management** replaces Docker for rootless security
  - **Multi-agent modular guides**: 39a (LangGraph), 39b (state management), 39c (workflow implementation)
  - **Enterprise migration timeline**: 38a with 9-week implementation plan
  - **OpenTelemetry observability** stack with Prometheus/Grafana/Jaeger
  - **Essential testing tools**: DeepEval and Hypothesis integration
- **Document structure** optimized with 30KB constraints for AI context processing
- **Git workflow**: Simplified single-directory structure (no worktrees)
- **Security Enhancements Complete (v4.1)**:
  - **OAuth 2.1 implementation** with PKCE, resource indicators, and vulnerability mitigations
  - **Production security tools** integration (mcp-secrets-plugin, mcpauth, Auth0 MCP Server)
  - **Layered storage architecture** for credential management with graceful degradation
  - **Comprehensive monitoring** with anomaly detection and emergency response capabilities
  - **Trail of Bits vulnerability mitigations** addressing confused deputy, token passthrough, and session hijacking

## Development Philosophy

### Security-First Development Approach

This repository implements **comprehensive security patterns** for MCP deployments, addressing critical vulnerabilities identified in early MCP implementations:

- **Zero-trust credential management** with OS-native secure storage (Keychain/Credential Manager)
- **OAuth 2.1 compliance** with mandatory PKCE, resource indicators, and dynamic client registration
- **Vulnerability prevention** for confused deputy attacks, token passthrough vulnerabilities, and session hijacking
- **Production-ready security tools** providing immediate protection against plaintext credential exposure
- **Comprehensive audit trails** with anomaly detection and automated incident response

### Platform-Specific Management Approach

The repository maintains a **platform-specific management approach** rather than cross-platform synchronization, allowing for:
- Independent platform configuration without conflicts
- Selective server management based on platform capabilities
- Risk-minimized rollout through the modular guide system
- Documentation-driven development with 30KB context constraints for AI optimization