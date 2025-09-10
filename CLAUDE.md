# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and management. The repository provides cross-platform tools, comprehensive guides, and automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

### Core Architecture

The repository follows a **unified management approach** where:
1. **`mcp-manager.py`** serves as the central cross-platform management tool
2. **Documentation guides** (`GUIDE-MCP.md`, `GUIDE-CREDENTIALS.md`) provide comprehensive setup instructions with cross-references
3. **Configuration templates** demonstrate platform-specific schemas and credential patterns
4. **Automation scripts** handle synchronization across different MCP client configurations

### Key Components

- **Cross-Platform MCP Manager**: `mcp-manager.py` handles server addition, removal, listing, and credential validation across all platforms
- **Comprehensive Documentation**: Interconnected guides covering MCP setup, credential security, and troubleshooting
- **Schema Harmonization**: Configuration examples and sync tools that handle differences between Claude Code CLI (`mcpServers`), VS Code (`servers`), and Claude Desktop (`mcpServers`) schemas
- **Archive System**: UTC-timestamped historical documents in `ARCHIVED/` with format `YYYYMMDDTHHMMSSZ_filename.ext`
- **Automation Infrastructure**: VS Code auto-sync tasks and shell scripts for configuration synchronization

## Common Commands

### Development Environment
```bash
# Install dependencies with uv (if using virtual environment)
uv sync

# Note: mcp-manager.py uses only standard library modules
# Run directly with system Python for best compatibility
/usr/bin/python3 mcp-manager.py --help

# Make scripts executable when needed
chmod +x mcp-manager.py
```

### MCP Management
```bash
# List MCP servers across all platforms
/usr/bin/python3 mcp-manager.py --list

# Add MCP servers interactively
/usr/bin/python3 mcp-manager.py --add

# Remove MCP servers with Python tool (interactive)
/usr/bin/python3 mcp-manager.py --remove

# Validate credential setup
/usr/bin/python3 mcp-manager.py --check-credentials

# Backup MCP configurations
/usr/bin/python3 mcp-manager.py --backup-only

# Work with specific config file only
/usr/bin/python3 mcp-manager.py --file ~/.claude.json

# Note: sync-mcp.sh referenced in .vscode/tasks.json but not present in repository
# Manual sync can be achieved using mcp-manager.py across platforms
```

### File Organization
```bash
# Archive files with timestamp prefix
cp file.ext ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_file.ext

# Make scripts executable
chmod +x script-name.sh
```

## MCP Server Configuration Architecture

The repository handles three distinct MCP client configurations with different schemas:

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
Cross-platform credential management using OS-native stores:
- **macOS**: Keychain Access via `security` command
- **Windows**: Credential Manager via PowerShell `CredentialManager` module
- **Linux**: Environment variables (fallback)

## Development Workflow

### Unified MCP Management Pattern
When working with MCP configurations, follow this pattern:
1. **Credential Setup**: Use `GUIDE-CREDENTIALS.md` for secure credential storage
2. **Server Management**: Use `mcp-manager.py --add` for interactive addition across all platforms
3. **Validation**: Use `mcp-manager.py --check-credentials` and `mcp-manager.py --list`
4. **Testing**: Verify with `/mcp` command in Claude Code

### Cross-Platform Considerations
- **Path Detection**: `mcp-manager.py` automatically detects platform-specific paths
- **Schema Handling**: Sync tools automatically convert between `mcpServers` and `servers` keys
- **Credential Validation**: Tool validates both environment variables and OS-native credential stores

## Important Guidelines

### Code Quality (Codacy Integration)
After making any file edits, you MUST:
1. Run `codacy_cli_analyze` tool from Codacy's MCP Server for each edited file
2. Set `rootPath` to the workspace path  
3. Set `file` to the path of the edited file
4. Apply fixes for any issues found

### Security Dependencies
After installing any dependencies (npm, pip, etc.), you MUST:
1. Run `codacy_cli_analyze` with `tool: "trivy"`
2. Fix any vulnerabilities before continuing
3. Only proceed with original task after security issues are resolved

### Archive Management
When archiving files:
- Use UTC timestamp format: `YYYYMMDDTHHMMSSZ_`
- Place in `ARCHIVED/` directory
- Preserve original file permissions

## Configuration Files

### AI Development Configuration
- `.claude/settings.local.json` - Claude Code permissions (GitHub search, file operations, sequential thinking, WebFetch domains)
- `.github/instructions/codacy.instructions.md` - Mandatory Codacy integration rules for code quality enforcement

### Automation Infrastructure  
- `.vscode/tasks.json` - VS Code startup task configuration (references missing ~/bin/sync-mcp.sh)
- `pyproject.toml` - Python project metadata with packaging configuration issues

### Documentation Architecture
- `GUIDE-MCP.md` - Cross-platform MCP setup with unified workflow examples and Quick Start patterns
- `GUIDE-CREDENTIALS.md` - OS-native credential management patterns for secure token storage
- `report-mcp-servers-agentic-development-2025.md` - Comprehensive analysis of MCP servers for development workflows
- Cross-references between guides ensure cohesive user experience

## Critical Implementation Details

### mcp-manager.py Architecture
The tool implements a **MCPConfig class** for each platform with:
- **Cross-platform path detection** via `get_platform_config_paths()`
- **Credential validation** for environment variables and OS-native stores
- **Schema-aware configuration management** handling differences between platforms
- **Interactive server addition/removal** with automatic backups

### Documentation Cross-Reference Pattern
- All guides reference each other for complete workflows
- Troubleshooting sections point to credential validation tools
- Configuration examples are standardized across platforms
- Quick Start workflows integrate all tools

## Local Permissions

This repository has specific Claude Code permissions configured:
- GitHub repository search and file access
- File system operations (`chmod`)
- Sequential thinking for complex problem solving

These permissions are defined in `.claude/settings.local.json`.

## Troubleshooting

### Python Packaging Issues
The `mcp-manager.py` tool has packaging configuration issues with hatchling. If you encounter build errors:

1. **Use system Python directly**: `/usr/bin/python3 mcp-manager.py --help`
2. **Skip virtual environment**: The tool works fine without package installation
3. **Fix packaging**: Add proper package configuration to `pyproject.toml` if needed

### Common Issues
- **Virtual environment conflicts**: Use system Python path `/usr/bin/python3`
- **Missing dependencies**: The tool uses only standard library modules
- **Permission errors**: Ensure script has execute permissions (`chmod +x mcp-manager.py`)
- **Missing sync-mcp.sh**: Referenced in .vscode/tasks.json but not present in repository
- **Packaging configuration**: pyproject.toml has issues with hatchling build backend