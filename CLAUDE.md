# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and management. The repository provides cross-platform tools, comprehensive guides, and automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

### Core Architecture

The repository follows a **platform-specific management approach** where:
1. **`mcp-manager.py`** serves as the central platform-targeted management tool with auto-detection
2. **Documentation guides** in `10_draft-merged/` provide comprehensive setup instructions with cross-references
3. **Draft documents** in `00_draft-initial/` contain research and reports awaiting finalization
4. **Archive system** in `ARCHIVED/` stores historical documents with UTC timestamps

### Key Components

- **Platform-Specific MCP Manager**: `mcp-manager.py` handles server management for individual platforms with auto-detection and platform targeting
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

### Testing
```bash
# Run deduplication test
/usr/bin/python3 test_mcp_deduplication.py

# Test specific functionality before fixes (TDD approach)
# 1. Write test to reproduce issue
# 2. Confirm test fails with expected error
# 3. Apply fix
# 4. Verify test passes
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

## Important Guidelines

### File Management
- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** (*.md) or README files unless explicitly requested
- Do what has been asked; nothing more, nothing less

### Code Quality (Codacy Integration)
After making ANY file edits, you MUST:
1. **IMMEDIATELY** run `codacy_cli_analyze` tool from Codacy's MCP Server
2. Set `rootPath` to the workspace path  
3. Set `file` to the path of the edited file
4. Apply fixes for any issues found
5. **This is non-negotiable** - failure to follow this rule is considered a critical error

### Security Dependencies
After installing ANY dependencies (npm, pip, yarn, pnpm, etc.), you MUST:
1. **IMMEDIATELY** run `codacy_cli_analyze` with `tool: "trivy"`
2. Stop all other operations if vulnerabilities are found
3. Fix any vulnerabilities before continuing
4. Only proceed with original task after security issues are resolved
5. Example: After `npm install react-markdown`, run Codacy with trivy BEFORE any other tasks

### Codacy Analysis Requirements
- Run analysis on EVERY file modification without exception
- For security scanning: use `tool: "trivy"` parameter
- For code quality: leave `tool` parameter empty/unset
- Always use standard filesystem paths (not URL-encoded)
- If Codacy MCP Server unavailable, suggest user check VS Code Copilot MCP settings

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
The tool implements a **platform-specific management architecture** with:
- **Platform Selection**: `select_target_platform()` method with auto-detection and explicit targeting
- **MCPConfig class** for individual platform operations with:
  - Platform-specific path detection via `get_platform_config_paths()`
  - Credential validation for environment variables and OS-native stores
  - Schema-aware configuration management
  - Interactive server management with automatic backups
- **Platform Mapping**: `platform_map` dictionary for CLI argument to platform name translation
- **Disable/Enable functionality**: Servers can be temporarily disabled by renaming with `DISABLED_` prefix
  - `disable_server()`: Renames server key to deactivate without deletion
  - `enable_server()`: Restores original server name to reactivate
  - `get_disabled_servers()`: Tracks disabled servers for the target platform
  - Preserves complete configuration while making servers inactive
- **Deduplication functionality**: Remove duplicate servers where both active and DISABLED_ versions exist
  - `remove_duplicate_servers()`: Identifies and removes active duplicates, keeping DISABLED_ versions
  - Automatically creates backups before deduplication
  - Reports which duplicates were found and removed
- **Single-Platform Operations**: All interactive methods work with one platform at a time

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

## Development Workflow

### Test-Driven Development (TDD)
When fixing bugs or adding features, follow the TDD pattern:

1. **Write failing test first**:
   ```python
   # test_feature.py
   import importlib.util
   spec = importlib.util.spec_from_file_location("mcp_manager", "mcp-manager.py")
   mcp_manager = importlib.util.module_from_spec(spec)
   spec.loader.exec_module(mcp_manager)
   
   # Test that reproduces the issue
   def test_feature():
       # Arrange
       config = mcp_manager.MCPConfig(test_config)
       # Act & Assert
       assert config.feature_works()
   ```

2. **Verify test fails** with expected error
3. **Implement minimal fix** to make test pass
4. **Run test again** to verify fix
5. **Test with actual command** to confirm real-world behavior
6. **Run Codacy analysis** on modified files

### Import Pattern for Hyphenated Files
```python
import importlib.util
spec = importlib.util.spec_from_file_location("module_name", "file-name.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

## Project Configuration

### Codacy Tools Available
The repository includes `.codacy/codacy.yaml` with the following analysis tools:
- **dartanalyzer@3.7.2**: Dart static analysis
- **eslint@8.57.0**: JavaScript/TypeScript linting
- **lizard@1.17.31**: Code complexity analysis
- **pmd@7.11.0**: Java source code analyzer
- **pylint@3.3.6**: Python code analysis
- **revive@1.7.0**: Go linting
- **semgrep@1.78.0**: Pattern-based static analysis
- **trivy@0.65.0**: Security vulnerability scanner

### Required Runtimes
- Dart 3.7.2
- Go 1.22.3
- Java 17.0.10
- Node 22.2.0
- Python 3.11.11

## Troubleshooting

### Python Packaging Issues
- **Use system Python directly**: `/usr/bin/python3 mcp-manager.py`
- **Skip virtual environment**: Tool uses only standard library modules
- **Known issue**: pyproject.toml has hatchling build backend configuration issues
- **Module import errors**: When importing mcp-manager.py in tests, use `importlib.util.spec_from_file_location()` due to hyphen in filename

### Common Issues
- **Missing sync-mcp.sh**: Referenced in .vscode/tasks.json but not present (use mcp-manager.py instead)
- **Permission errors**: Run `chmod +x mcp-manager.py`
- **Credential failures**: Check GUIDE-CREDENTIALS.md for platform-specific setup
- **Platform not found**: Use `--status` to see available platforms, or specify different platform with `--platform`
- **Auto-detection issues**: Explicitly specify target platform with `--platform <name>` if auto-detection fails
- **No servers shown**: Ensure you're targeting the correct platform where servers are configured

### Recently Fixed Issues
- **AttributeError in deduplication**: Fixed in remove_duplicate_servers method
  - Changed `self.config` → `self.data`
  - Changed `self.platform_name` → `self.name`
  - Changed `self.server_key` → `'mcpServers'`
  - Changed method calls from `backup_config()` → `backup()` and `save_config()` → `save()`