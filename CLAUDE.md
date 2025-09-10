# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and management. The repository provides cross-platform tools, comprehensive guides, and automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

### Core Architecture

The repository follows a **unified management approach** where:
1. **`mcp-manager.py`** serves as the central cross-platform management tool
2. **Documentation guides** in `10_draft-merged/` provide comprehensive setup instructions with cross-references
3. **Draft documents** in `00_draft-initial/` contain research and reports awaiting finalization
4. **Archive system** in `ARCHIVED/` stores historical documents with UTC timestamps

### Key Components

- **Cross-Platform MCP Manager**: `mcp-manager.py` handles server addition, removal, listing, and credential validation across all platforms
- **Three-Guide System**: 
  - `11_GUIDE-MCP.md` - MCP setup with tiered server categorization (Tier 1-4)
  - `12_GUIDE-CREDENTIALS.md` - Secure credential management with requirements table
  - `13_GUIDE-IMPLEMENTATION.md` - Phased rollout strategy and KPIs
- **Schema Harmonization**: Handles differences between Claude Code CLI (`mcpServers`), VS Code (`servers`), and Claude Desktop (`mcpServers`) schemas
- **Archive System**: UTC-timestamped format `YYYYMMDDTHHMMSSZ_filename.ext`

## Common Commands

### MCP Management
```bash
# Always use system Python to avoid virtual environment issues
/usr/bin/python3 mcp-manager.py --list           # List all servers (active and disabled)
/usr/bin/python3 mcp-manager.py --add            # Interactive server addition
/usr/bin/python3 mcp-manager.py --remove         # Interactive server removal
/usr/bin/python3 mcp-manager.py --disable        # Temporarily disable servers
/usr/bin/python3 mcp-manager.py --enable         # Re-enable disabled servers
/usr/bin/python3 mcp-manager.py --check-credentials  # Validate credential setup
/usr/bin/python3 mcp-manager.py --backup-only    # Create configuration backups
/usr/bin/python3 mcp-manager.py --file ~/.claude.json  # Work with specific config file
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

## Important Guidelines

### Code Quality (Codacy Integration)
After making ANY file edits, you MUST:
1. Run `codacy_cli_analyze` tool from Codacy's MCP Server
2. Set `rootPath` to the workspace path
3. Set `file` to the path of the edited file
4. Apply fixes for any issues found

### Security Dependencies
After installing ANY dependencies (npm, pip, etc.), you MUST:
1. Run `codacy_cli_analyze` with `tool: "trivy"`
2. Fix any vulnerabilities before continuing
3. Only proceed with original task after security issues are resolved

### Archive Management
When archiving files:
- Use UTC timestamp format: `YYYYMMDDTHHMMSSZ_`
- Place in `ARCHIVED/` directory
- Use `mv` not `cp` to move files

## Documentation Structure

### Active Guides (10_draft-merged/)
- **11_GUIDE-MCP.md**: Tiered server categorization, security considerations, monitoring
- **12_GUIDE-CREDENTIALS.md**: Credential requirements table, CVE warnings, rotation schedules
- **13_GUIDE-IMPLEMENTATION.md**: 4-phase rollout, KPIs, ROI calculations

### Draft Documents (00_draft-initial/)
Reports and research awaiting review or integration into guides

### Archived Documents (ARCHIVED/)
Historical documents with UTC timestamps for reference

## Critical Implementation Details

### mcp-manager.py Architecture
The tool implements a **MCPConfig class** for each platform with:
- Cross-platform path detection via `get_platform_config_paths()`
- Credential validation for environment variables and OS-native stores
- Schema-aware configuration management
- Interactive server addition/removal with automatic backups
- **Disable/Enable functionality**: Servers can be temporarily disabled by renaming with `DISABLED_` prefix
  - `disable_server()`: Renames server key to deactivate without deletion
  - `enable_server()`: Restores original server name to reactivate
  - `get_disabled_servers()`: Tracks all disabled servers across platforms
  - Preserves complete configuration while making servers inactive

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

## Troubleshooting

### Python Packaging Issues
- **Use system Python directly**: `/usr/bin/python3 mcp-manager.py`
- **Skip virtual environment**: Tool uses only standard library modules
- **Known issue**: pyproject.toml has hatchling build backend configuration issues

### Common Issues
- **Missing sync-mcp.sh**: Referenced in .vscode/tasks.json but not present (use mcp-manager.py instead)
- **Permission errors**: Run `chmod +x mcp-manager.py`
- **Credential failures**: Check GUIDE-CREDENTIALS.md for platform-specific setup