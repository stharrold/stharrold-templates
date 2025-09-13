# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and agentic development workflows. The repository provides cross-platform tools, comprehensive modular guides, and automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

**Current MCP State**: All MCP servers have been removed from all platforms (as of 2025-09-12). This provides a clean slate for selective server management using the platform-specific approach.

### Core Architecture

The repository follows a **platform-specific management approach** with a structured document lifecycle:

**Management Tool Architecture:**
1. **`mcp-manager.py`** - Central platform-targeted management tool with auto-detection
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

Each directory has its own `CLAUDE.md` orchestrator and numbered guide files for systematic navigation.

### Key Components

- **Platform-Specific MCP Manager**: `mcp-manager.py` handles server management for individual platforms with auto-detection and platform targeting
- **Modular Guide System**: Hierarchical documentation with context optimization:
  - `10_mcp/` - MCP setup and configuration guides
  - `20_credentials/` - Security and credential management guides
  - `30_implementation/` - Development strategy and workflow patterns
- **Schema Harmonization**: Handles differences between Claude Code CLI (`mcpServers`), VS Code (`servers`), and Claude Desktop (`mcpServers`) schemas
- **Archive System**: UTC-timestamped format `YYYYMMDDTHHMMSSZ_filename.ext`

## Common Commands

### MCP Management
```bash
# Always use system Python to avoid virtual environment issues

# Platform Status and Detection
/usr/bin/python3 mcp-manager.py --status         # Show all platform statuses
/usr/bin/python3 mcp-manager.py                  # Auto-detect first available platform
/usr/bin/python3 mcp-manager.py --list           # List servers from auto-detected platform

# Platform-Specific Operations
/usr/bin/python3 mcp-manager.py --platform claude-code --list      # List Claude Code CLI servers
/usr/bin/python3 mcp-manager.py --platform vscode --add           # Add server to VS Code MCP
/usr/bin/python3 mcp-manager.py --platform claude-desktop --remove # Remove from Claude Desktop

# Server Management (works with auto-detected or specified platform)
/usr/bin/python3 mcp-manager.py --add            # Interactive server addition
/usr/bin/python3 mcp-manager.py --remove         # Interactive server removal
/usr/bin/python3 mcp-manager.py --disable        # Temporarily disable servers
/usr/bin/python3 mcp-manager.py --enable         # Re-enable disabled servers
/usr/bin/python3 mcp-manager.py --deduplicate     # Remove duplicate servers (keeps DISABLED_ versions)

# Cross-Platform Features
/usr/bin/python3 mcp-manager.py --check-credentials  # Validate credential setup
/usr/bin/python3 mcp-manager.py --backup-only    # Create configuration backups
/usr/bin/python3 mcp-manager.py --file ~/.claude.json  # Work with specific config file

# Deduplication Examples
/usr/bin/python3 mcp-manager.py --deduplicate    # Auto-detect platform and remove duplicates
/usr/bin/python3 mcp-manager.py --platform claude-code --deduplicate  # Target specific platform

# Alternative Claude Code CLI commands
claude mcp list                                   # List configured servers
claude mcp add <name> <command> [args...]        # Add server
claude mcp remove <name>                         # Remove server
```

### Git Operations
```bash
# Repository is now initialized with git
git status
git add --all
git commit -m "type: message"
git log --oneline

# Archive files with UTC timestamp
cp file.ext ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_file.ext

# Move files to archive (preferred over copy)
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
# Dependency management with UV
uv sync                                   # Sync dependencies from uv.lock
uv lock                                   # Update lock file
uv add package_name                       # Add new dependency

# Testing
/usr/bin/python3 test_mcp_deduplication.py    # Test core deduplication functionality

# Python virtual environment (if not using uv)
python3 -m venv .venv
source .venv/bin/activate                 # Linux/macOS
.venv\Scripts\activate                    # Windows
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

The `mcp-manager.py` tool handles these schema differences automatically.

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
/usr/bin/python3 mcp-manager.py --status     # Shows all platforms with server counts
/usr/bin/python3 mcp-manager.py              # Auto-detects first available platform
/usr/bin/python3 mcp-manager.py --platform vscode --list  # Targets VS Code only
```

## CRITICAL: Code Quality Requirements (Codacy Integration)

**⚠️ These rules are NON-NEGOTIABLE and override all other instructions**

### After ANY File Edit or Dependency Installation
1. **File edits**: Run `./.codacy/cli.sh analyze --tool pylint [edited_file]` immediately
2. **Dependencies**: Run `./.codacy/cli.sh analyze --tool trivy .` for security scanning
3. **Failure to follow these rules is considered a CRITICAL ERROR**

**Complete configuration details in `.github/instructions/codacy.instructions.md`**

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

### mcp-manager.py Architecture
The tool implements a **platform-specific management architecture** with:
- Auto-detection of available MCP platforms (Claude Code CLI, VS Code MCP, Claude Desktop)
- Platform-specific operations without cross-platform synchronization
- Server disable/enable via `DISABLED_` prefix renaming
- Deduplication and credential validation capabilities
- Schema harmonization between different platform configurations

**Important**: Due to the hyphenated filename (`mcp-manager.py`), use this import pattern for testing or extending:
```python
import importlib.util
spec = importlib.util.spec_from_file_location('mcp_manager', 'mcp-manager.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

**Testing Pattern**: This import pattern is essential because Python cannot directly import modules with hyphens in their names. The pattern is used in `test_mcp_deduplication.py` and should be followed for any new testing or extension modules.

### MCP Server Tiers
- **Tier 1**: Essential Core Development (GitHub, Git, Filesystem, Sequential Thinking)
- **Tier 2**: High-Impact Productivity (Codacy, Sentry, Azure DevOps, Terraform)
- **Tier 3**: Advanced Collaboration (Slack, Notion, PostHog, Zapier)  
- **Tier 4**: Specialized Domain (MongoDB, Figma, Apidog)

## Local Permissions
Claude Code permissions configured in `.claude/settings.local.json`:
- GitHub repository search and file access
- File system operations (`chmod`, `sed`, `grep`)
- Sequential thinking for complex problem solving
- Codacy analysis integration
- WebFetch for specific domains (github.com, mcpcat.io, apidog.com)

## Common Issues & Solutions

### MCP Manager Issues
- **Permission errors**: Run `chmod +x mcp-manager.py`
- **Platform not found**: Use `--status` to see available platforms or specify `--platform <name>`
- **Auto-detection issues**: Explicitly specify target platform with `--platform <name>`

### Local Codacy CLI Issues
- **CLI not executable**: Run `chmod +x ./.codacy/cli.sh`
- **CLI not found**: Verify binary cache exists: `ls -la ~/Library/Caches/Codacy/` (macOS)
- **Analysis fails**: Check file exists and tool supports the file type
- **No tools support file**: Expected for markdown/text files - tools focus on code analysis

## Current State (as of 2025-09-12)
- **All MCP servers removed** from all platforms (clean slate)
- **Backups preserved** in `ARCHIVED/` with UTC timestamps  
- **Platform-specific management** ready for selective server addition
- **Modular guide system** with hierarchical documentation structure
- **Document structure** optimized with 30KB constraints for AI context processing

## Development Philosophy

This repository implements a **platform-specific management approach** rather than cross-platform synchronization, allowing for:
- Independent platform configuration without conflicts
- Selective server management based on platform capabilities
- Risk-minimized rollout through the modular guide system
- Documentation-driven development with 30KB context constraints for AI optimization