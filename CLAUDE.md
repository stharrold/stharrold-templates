# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and management. The repository provides cross-platform tools, comprehensive guides, and automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

**Current MCP State**: All MCP servers have been removed from all platforms (as of 2025-09-12). This provides a clean slate for selective server management using the platform-specific approach.

### Core Architecture

The repository follows a **platform-specific management approach** with a structured document lifecycle:

**Management Tool Architecture:**
1. **`mcp-manager.py`** - Central platform-targeted management tool with auto-detection
   - Single-platform operations (not cross-platform synchronization)
   - MCPConfig class handles individual platform operations
   - Platform selection via `select_target_platform()` with auto-detection
   - Disable/enable servers via `DISABLED_` prefix renaming

**Document Lifecycle Management:**
2. **Research Phase** (`00_draft-initial/`) - Raw research, reports, and analysis awaiting integration
3. **Active Guides** (`10_draft-merged/`) - Finalized, cross-referenced documentation with YAML frontmatter
4. **Archive System** (`ARCHIVED/`) - Historical documents with UTC timestamps (`YYYYMMDDTHHMMSSZ_filename.ext`)

### Key Components

- **Platform-Specific MCP Manager**: `mcp-manager.py` handles server management for individual platforms with auto-detection and platform targeting
- **Three-Guide System** (recently enhanced with enterprise search capabilities): 
  - `11_GUIDE-MCP.md` - MCP setup with tiered server categorization plus enterprise search architecture
  - `12_GUIDE-CREDENTIALS.md` - Secure credential management plus enterprise search security considerations
  - `13_GUIDE-IMPLEMENTATION.md` - Phased rollout strategy plus comprehensive RAG implementation phases
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

### Document Workflow Management
```bash
# Working with the three-guide system
# Edit active guides in 10_draft-merged/:
code 10_draft-merged/11_GUIDE-MCP.md          # MCP setup and configuration
code 10_draft-merged/12_GUIDE-CREDENTIALS.md  # Secure credential management
code 10_draft-merged/13_GUIDE-IMPLEMENTATION.md # Implementation strategy

# Research and reports in 00_draft-initial/ (awaiting integration)
ls 00_draft-initial/                          # List draft documents
```

### Testing and Code Quality
```bash
# Run deduplication test (tests the critical deduplication fix)
/usr/bin/python3 test_mcp_deduplication.py

# Import pattern for hyphenated files (due to mcp-manager.py filename)
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('mcp_manager', 'mcp-manager.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print('Import successful')
"

# Project uses uv for dependency management
uv lock                                   # Update lock file
uv sync                                   # Sync dependencies
```

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

## Platform Selection

### Platform Targeting
The tool operates on **one platform at a time** with the following options:
- **Explicit targeting**: Use `--platform <name>` to specify target platform (`claude-code`, `vscode`, `claude-desktop`)
- **Auto-detection**: When no platform specified, automatically selects first available platform
- **Platform status**: Use `--status` to see all platform configurations and server counts

### Platform Selection Behavior
```bash
# Auto-detection workflow
/usr/bin/python3 mcp-manager.py              # Auto-detects first available platform
# Output: "Auto-detected platform: claude-code (Claude Code CLI)"

# Explicit platform targeting
/usr/bin/python3 mcp-manager.py --platform vscode --list  # Targets VS Code only

# Platform availability check
/usr/bin/python3 mcp-manager.py --status     # Shows all platforms with server counts
```

### Breaking Change from Previous Versions
**Operations now target one platform at a time** instead of synchronizing across all platforms. This change:
- Provides cleaner, more predictable operations
- Eliminates cross-platform synchronization complexity  
- Allows independent management of each platform's MCP servers
- Maintains backward compatibility with `--file` flag for direct file operations

## CRITICAL: Code Quality Requirements (Codacy Integration)

**⚠️ These rules are NON-NEGOTIABLE and override all other instructions**

### After ANY File Edit or Dependency Installation
- **File edits**: Run `codacy_cli_analyze` immediately with `rootPath` and `file` parameters
- **Dependencies**: Run `codacy_cli_analyze` with `tool="trivy"` for security scanning
- **Failure to follow these rules is considered a CRITICAL ERROR**

**Complete configuration details in `.github/instructions/codacy.instructions.md`**

**Available tools**: dartanalyzer, eslint, lizard, pmd, pylint, revive, semgrep, trivy
**Required runtimes**: Dart 3.7.2, Go 1.22.3, Java 17.0.10, Node 22.2.0, Python 3.11.11

## Important Guidelines

### File Management
- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** (*.md) or README files unless explicitly requested
- Do what has been asked; nothing more, nothing less

### Archive Management
When archiving files:
- Use UTC timestamp format: `YYYYMMDDTHHMMSSZ_`
- Place in `ARCHIVED/` directory
- Use `mv` not `cp` to move files

## Documentation Structure

This repository implements a **structured document lifecycle** that moves content from research through integration to archival:

- **Active Guides** (`10_draft-merged/`): Three-guide system with cross-references and YAML frontmatter
  - Version-controlled with changelog tracking
  - Recently merged with enterprise search and RAG implementation content
- **Draft Documents** (`00_draft-initial/`): Research reports and analysis awaiting integration
  - Contains 19 specialized reports covering AI agents, embeddings, BAML, AutoGen, DSPy architectures
  - Research content gets merged into active guides then moved to archive
- **Archived Documents** (`ARCHIVED/`): Historical documents with UTC timestamps
  - Preserves evolution of ideas and implementation strategies
  - Critical for understanding context behind current implementations

## Critical Implementation Details

### mcp-manager.py Architecture
The tool implements a **platform-specific management architecture** with:

**Platform Selection & Management:**
- `select_target_platform()` method with auto-detection and explicit targeting
- `platform_map` dictionary for CLI argument to platform name translation
- Breaking change: Operations target one platform at a time (no cross-platform sync)

**MCPConfig Class Features:**
- Platform-specific path detection via `get_platform_config_paths()`
- Credential validation for environment variables and OS-native stores
- Schema-aware configuration management (handles `mcpServers` vs `servers` differences)
- Interactive server management with automatic backups

**Server State Management:**
- **Disable/Enable**: Servers temporarily disabled by renaming with `DISABLED_` prefix
  - `disable_server()`: Renames server key to deactivate without deletion
  - `enable_server()`: Restores original server name to reactivate
  - Preserves complete configuration while making servers inactive
- **Deduplication**: Remove duplicate servers where both active and DISABLED_ versions exist
  - `remove_duplicate_servers()`: Keeps DISABLED_ versions, removes active duplicates
  - Automatically creates backups before deduplication

**Import Pattern:** Due to hyphenated filename, use `importlib.util.spec_from_file_location()` for importing in tests

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
- **Permission errors**: Run `chmod +x mcp-manager.py`
- **Module import errors**: Use `importlib.util.spec_from_file_location()` pattern due to hyphenated filename
- **Platform not found**: Use `--status` to see available platforms or specify `--platform <name>`
- **Auto-detection issues**: Explicitly specify target platform with `--platform <name>`
- **VS Code task disabled**: The `.vscode/tasks.json` sync task is commented out to prevent startup errors

## Current State (as of 2025-09-12)
- **All MCP servers removed** from all platforms (clean slate)
- **Backups preserved** in `ARCHIVED/` with UTC timestamps  
- **Platform-specific management** ready for selective server addition
- **Active guides enhanced** with enterprise search and RAG implementation patterns
- **Document merging completed** from Graph RAG Kuzu report into all three guides

## Document Merging Workflow

When integrating reports from `00_draft-initial/` into active guides:

1. **Read source content thoroughly** to understand key concepts and implementation patterns
2. **Map content to appropriate guides** based on topic alignment (MCP, Credentials, Implementation)  
3. **Update YAML frontmatter** with version increments and changelog entries
4. **Insert content at logical locations** maintaining existing structure and flow
5. **Add cross-references** between guides for comprehensive coverage
6. **Run quality checks** using Codacy analysis after all edits
7. **Archive source documents** with UTC timestamps after successful integration