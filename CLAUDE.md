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
git status                                    # Check current status
git add --all                                # Stage all changes
git commit -m "type: message"                # Commit with message
git push                                      # Push to current branch
git log --oneline                             # View commit history

# Branch management
git checkout main                             # Switch to main branch
git checkout develop                          # Switch to develop branch
git checkout contrib/stharrold               # Switch back to contrib branch

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
# Dependency management with UV (preferred)
uv sync                                   # Sync dependencies from uv.lock
uv lock                                   # Update lock file
uv add package_name                       # Add new dependency

# Core Python Architecture Testing
/usr/bin/python3 test_mcp_deduplication.py    # Test core deduplication functionality
/usr/bin/python3 mcp_manager.py --validate-all # Validate all platform configurations

# Run specific tests
python3 -m pytest test_mcp_deduplication.py::test_function_name  # Single test
python3 -c "import mcp_manager; mcp_manager.validate_credentials()"  # Credential validation test

# Module import verification (now works with mcp_manager.py)
python3 -c "
import mcp_manager
print('Import successful: MCPConfig available')
print('Available classes:', [name for name in dir(mcp_manager) if name[0].isupper()])
config = mcp_manager.MCPConfig('claude-code')
print('MCPConfig initialized successfully')
"

# Python virtual environment (fallback if not using uv)
python3 -m venv .venv
source .venv/bin/activate                 # Linux/macOS
.venv\Scripts\activate                    # Windows
pip install -e .                         # Install in development mode
```

### Code Quality and Security Analysis
```bash
# Verify local Codacy CLI status
./.codacy/cli.sh version                  # Check CLI version and availability
./.codacy/cli.sh --help                  # Show available commands

# Code analysis (required after any file edit)
./.codacy/cli.sh analyze --tool pylint file.py    # Python files
./.codacy/cli.sh analyze file.ext                 # General analysis

# Security scanning (required after dependency changes)
./.codacy/cli.sh analyze --tool trivy .           # Vulnerability scanning
./.codacy/cli.sh analyze --tool semgrep          # Security-focused analysis

# Additional analysis tools
./.codacy/cli.sh analyze --tool lizard file.py   # Complexity analysis
./.codacy/cli.sh analyze --tool eslint file.js   # JavaScript analysis

# Generate reports
./.codacy/cli.sh analyze --format sarif -o results.sarif  # SARIF format
./.codacy/cli.sh analyze --format json -o results.json   # JSON format
```

### Security Tools and Emergency Response
```bash
# Deploy production security tools (see 10_draft-merged/20_credentials/25_mcp-security-tools.md)
pip install mcp-secrets-plugin           # Cross-platform credential storage
npx create-mcpauth-app                   # OAuth 2.1 server deployment
npm install @auth0/mcp-server           # Enterprise Auth0 integration

# Emergency credential management
mcp-secrets set github token             # Store credentials securely
mcp-secrets get github token             # Retrieve credentials
mcp-secrets list                         # List stored services

# Emergency response (kill switch capabilities)
python3 -c "from emergency_cred_manager import EmergencyCredentialManager; EmergencyCredentialManager().emergencyRevocation('Security breach detected', 'ALL')"

# OAuth 2.1 compliance validation
claude oauth validate --all-providers --health-check
claude oauth refresh --provider github --force-rotation
```

## Critical Workflow Rules

### Code Quality Integration
**Note**: This repository uses the **local Codacy CLI only** - no MCP server is required or configured for code quality analysis.

After ANY file edit:
1. **IMMEDIATELY** run the local Codacy CLI for each edited file:
   ```bash
   ./.codacy/cli.sh analyze --tool pylint path/to/edited/file.py
   ```
2. For non-Python files or general analysis:
   ```bash
   ./.codacy/cli.sh analyze path/to/edited/file
   ```
3. If issues are found, propose and apply fixes before continuing

### File Size Constraints
- All files in `10_draft-merged/` must be ≤30KB for optimal AI context processing
- Use `auto_compact_at: 95` when approaching limits
- Cross-reference between files rather than duplicating content

### Archive Management
- Use UTC timestamp format: `YYYYMMDDTHHMMSSZ_filename.ext`
- Move (don't copy) files to `ARCHIVED/` when superseded
- Maintain changelog entries in YAML frontmatter

## MCP Server Configuration Architecture

### Platform-Specific Paths
| Platform | Claude Code CLI | VS Code MCP | Claude Desktop |
|----------|----------------|-------------|----------------|
| **macOS** | `~/.claude.json` | `~/Library/Application Support/Code/User/mcp.json` | `~/Library/Application Support/Claude/config.json` |
| **Windows** | `~/.claude.json` | `~/AppData/Roaming/Code/User/mcp.json` | `~/AppData/Roaming/Claude/config.json` |
| **Linux** | `~/.claude.json` | `~/.config/Code/User/mcp.json` | `~/.config/claude/config.json` |

### Schema Differences
- **Claude Code CLI & Desktop**: Use `"mcpServers": {}` as root key
- **VS Code MCP Extension**: Uses `"servers": {}` as root key
- **Environment Variables**: All platforms support `${env:TOKEN_NAME}` syntax

### Credential Security Strategy
- **macOS**: Keychain Access via `security` command
- **Windows**: Credential Manager via PowerShell `CredentialManager` module
- **Linux**: Environment variables (fallback)

## Platform-Specific Notes

### Cross-Platform Schema Differences
- **Claude Code CLI**: Uses `mcpServers` key
- **VS Code MCP**: Uses `servers` key  
- **Claude Desktop**: Uses `mcpServers` key

The `mcp_manager.py` tool handles these schema differences automatically.

### Credential Management
Common environment variables validated:
- `GITHUB_TOKEN` - GitHub integration
- `OPENAI_API_KEY` - OpenAI services
- `ANTHROPIC_API_KEY` - Anthropic services
- Platform-specific credential storage (Keychain on macOS, Credential Manager on Windows)

### Platform Targeting
The tool operates on **one platform at a time** with the following options:
- **Explicit targeting**: Use `--platform <name>` to specify target platform (`claude-code`, `vscode`, `claude-desktop`)
- **Auto-detection**: When no platform specified, automatically selects first available platform
- **Platform status**: Use `--status` to see all platform configurations and server counts

```bash
# Platform detection examples
/usr/bin/python3 mcp_manager.py --status     # Shows all platforms with server counts
/usr/bin/python3 mcp_manager.py              # Auto-detects first available platform
/usr/bin/python3 mcp_manager.py --platform vscode --list  # Targets VS Code only
```

## CRITICAL: Code Quality Requirements (Codacy Integration)

**⚠️ These rules are NON-NEGOTIABLE and override all other instructions**

### After ANY File Edit or Dependency Installation
1. **File edits**: Run `./.codacy/cli.sh analyze --tool pylint [edited_file]` immediately
2. **Dependencies**: Run `./.codacy/cli.sh analyze --tool trivy .` for security scanning
3. **Failure to follow these rules is considered a CRITICAL ERROR**

**Complete configuration details in `.github/instructions/codacy.instructions.md`**

## Quick Reference for Development

### Most Common Commands (Copy-Paste Ready)
```bash
# Check system status
/usr/bin/python3 mcp_manager.py --status

# Test core functionality
/usr/bin/python3 test_mcp_deduplication.py

# Add a new MCP server interactively
/usr/bin/python3 mcp_manager.py --add

# Validate all credentials
/usr/bin/python3 mcp_manager.py --check-credentials

# Run code quality analysis after edits
./.codacy/cli.sh analyze --tool pylint mcp_manager.py
./.codacy/cli.sh analyze modified_file.py

# Quick backup before major changes
/usr/bin/python3 mcp_manager.py --backup-only
```

### Development Workflow
1. **Check current state**: `--status` to see all platform configurations
2. **Test before changes**: Run `test_mcp_deduplication.py` to verify base functionality
3. **Make changes**: Use interactive commands (`--add`, `--remove`, `--disable`)
4. **Validate changes**: Use `--check-credentials` and re-run tests
5. **Code quality**: Run Codacy analysis on any modified Python files
6. **Git workflow**: Work on `contrib/stharrold`, create PRs to `develop` or `main` as needed

## Important Guidelines

### File Management
- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** (*.md) or README files unless explicitly requested
- Do what has been asked; nothing more, nothing less

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