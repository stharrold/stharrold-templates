# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Latest Update (2025-09-14)**: Enhanced with comprehensive MCP security patterns including OAuth 2.1 implementation, production security tools (mcp-secrets-plugin, mcpauth, Auth0), layered storage architecture, and Trail of Bits vulnerability mitigations. See feature/08_merge branch for detailed security enhancements.

## CRITICAL: Code Quality Requirements

**⚠️ NON-NEGOTIABLE**: After ANY file edit or dependency change, IMMEDIATELY run:

### After File Edits
```bash
./.codacy/cli.sh analyze --tool pylint edited_file.py  # Python files
./.codacy/cli.sh analyze edited_file                   # Other files
```

### After Dependency Changes
```bash
./.codacy/cli.sh analyze --tool trivy .                # Security scan
```

**If issues found, propose and apply fixes before continuing.** This requirement comes from `.github/instructions/codacy.instructions.md` and is critical for code quality.

## Repository Architecture

Templates and utilities repository for MCP (Model Context Protocol) server configuration and agentic development workflows. Provides cross-platform tools and modular guides for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

**Current State**: Clean slate (all MCP servers removed as of 2025-09-12). Default branch: `contrib/stharrold`.

## Development Prerequisites

```bash
# Python environment (using system Python)
/usr/bin/python3 --version  # Requires Python 3.8+

# No dependencies to install - scripts are standalone
# No package.json, pyproject.toml, or requirements.txt present

# Key executable files
chmod +x mcp_manager.py  # Ensure executable permissions
```

### Core Architecture

**Document Lifecycle:** `00_draft-initial/` → `10_draft-merged/` → `ARCHIVED/` (with UTC timestamps)

**Key Multi-File Relationships:**

1. **TODO Integration Pipeline:**
   - `TODO.md` tracks GitHub issues (#3-#24)
   - `TODO_FOR_*.md` files contain execution plans mapping sources to targets
   - 30KB file size limit enforced for AI context optimization

2. **Platform-Specific MCP Management:**
   - `mcp_manager.py` handles 3 platforms with different schemas (`mcpServers` vs `servers`)
   - `select_target_platform()` auto-detection algorithm
   - OS-native credential validation (Keychain/Credential Manager)

3. **Modular Guide Hierarchy:**
   - `10_draft-merged/10_mcp/` - MCP server configuration
   - `10_draft-merged/20_credentials/` - Security and credential management
   - `10_draft-merged/30_implementation/` - Development patterns

#### Management Tool Architecture
**`mcp_manager.py`** - 39KB Python file with platform-specific logic:
- `MCPConfig` class: Platform-specific configuration management
- `select_target_platform()`: Auto-detection algorithm for available platforms
- `validate_credentials()`: Cross-platform credential validation
- `deduplicate_servers()`: Intelligent duplicate removal preserving DISABLED_ versions
- Server disable/enable via `DISABLED_` prefix renaming

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

## Workflow-Based Commands

### Document Integration Workflow
```bash
# 1. Navigate to priority document for integration
ls 00_draft-initial/                      # Check draft documents awaiting integration
cat TODO.md                               # Review integration priorities

# 2. Read source and target files
head -20 00_draft-initial/source.md       # Preview source content
ls -la 10_draft-merged/target/             # Check target directory structure

# 3. Integrate content (following TODO_FOR_*.md plan)
# Edit target file to enhance with source content
# Keep file under 30KB limit

# 4. Archive source document
mv 00_draft-initial/source.md ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_source.md

# 5. Update tracking
# Edit TODO.md to mark task complete
# Close corresponding GitHub issue
```

### MCP Server Management Workflow
```bash
# 1. Check current platform status
/usr/bin/python3 mcp_manager.py --status         # Show all platform statuses

# 2. Platform-specific operations (Claude Code CLI, VS Code MCP, Claude Desktop)
/usr/bin/python3 mcp_manager.py --platform claude-code --list      # List servers
/usr/bin/python3 mcp_manager.py --platform vscode --add           # Add server
/usr/bin/python3 mcp_manager.py --platform claude-desktop --remove # Remove server

# 3. Interactive server management (auto-detects platform)
/usr/bin/python3 mcp_manager.py --add            # Add server
/usr/bin/python3 mcp_manager.py --remove         # Remove server
/usr/bin/python3 mcp_manager.py --disable        # Disable servers (DISABLED_ prefix)
/usr/bin/python3 mcp_manager.py --enable         # Re-enable servers

# 4. Maintenance operations
/usr/bin/python3 mcp_manager.py --deduplicate     # Remove duplicates
/usr/bin/python3 mcp_manager.py --backup-only    # Create backups
/usr/bin/python3 mcp_manager.py --check-credentials  # Validate credentials
```

### Testing Workflow
```bash
# 1. Core functionality tests
/usr/bin/python3 test_mcp_deduplication.py         # Test deduplication functionality

# 2. MCP manager validation
/usr/bin/python3 mcp_manager.py --validate-all     # Validate all configurations
python3 -c "import mcp_manager; mcp_manager.validate_credentials()"  # Test credentials

# 3. Module verification
python3 -c "import mcp_manager; print('MCPConfig available:', hasattr(mcp_manager, 'MCPConfig'))"

# 4. Test specific functions
python3 -c "import mcp_manager; mcp_manager.select_target_platform()"  # Test platform detection
python3 -c "import mcp_manager; config = mcp_manager.MCPConfig('claude-code'); config.load_config()"  # Test config loading

# 5. MCP server connectivity (after server setup)
claude mcp list                                   # List configured servers
# Use `/mcp` command in Claude Code CLI to test server connectivity
```

### Code Quality Workflow
```bash
# 1. CRITICAL: Run after EVERY file edit
./.codacy/cli.sh analyze --tool pylint edited_file.py    # Python files
./.codacy/cli.sh analyze edited_file                     # Other files

# 2. CRITICAL: Run after dependency changes
./.codacy/cli.sh analyze --tool trivy .                  # Security vulnerability scan

# 3. Additional analysis tools
./.codacy/cli.sh analyze --tool semgrep                  # Security-focused analysis
./.codacy/cli.sh version                                 # Check CLI status

# 4. Fix any issues found before continuing
# If issues found: propose fixes, apply them, re-run analysis
```

### Git Operations Workflow
```bash
# 1. Check status and prepare
git status && git add --all                  # Stage changes
git log --oneline -10                         # Review recent commits

# 2. Branch naming conventions
feat/     # New features and enhancements
fix/      # Bug fixes
docs/     # Documentation changes
chore/    # Maintenance, dependencies, tooling
refactor/ # Code restructuring
test/     # Testing additions/updates

# 3. Commit with descriptive message
git commit -m "feat: descriptive message including issue reference

Closes #123

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 4. Archive workflow (when moving files to ARCHIVED/)
mv file.ext ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_file.ext
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


## Quick Reference

### Essential Commands by Task
```bash
# System Status & Testing
/usr/bin/python3 mcp_manager.py --status                    # Check all platforms
/usr/bin/python3 test_mcp_deduplication.py                  # Run core tests
/usr/bin/python3 mcp_manager.py --check-credentials         # Validate credentials

# MCP Management
/usr/bin/python3 mcp_manager.py --add                       # Add server interactively
/usr/bin/python3 mcp_manager.py --platform claude-code --list  # Platform-specific ops
/usr/bin/python3 mcp_manager.py --backup-only               # Create backups

# Code Quality (Required after edits)
./.codacy/cli.sh analyze --tool pylint edited_file.py       # Python analysis
./.codacy/cli.sh analyze edited_file                        # General analysis
```


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