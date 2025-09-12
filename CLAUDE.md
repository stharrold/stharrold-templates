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
# Run deduplication test
/usr/bin/python3 test_mcp_deduplication.py

# Test specific functionality before fixes (TDD approach)
# 1. Write test to reproduce issue
# 2. Confirm test fails with expected error
# 3. Apply fix
# 4. Verify test passes

# Testing import pattern for hyphenated files
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('mcp_manager', 'mcp-manager.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print('Import successful')
"

# Code quality analysis (via Codacy MCP Server when available)
# Automatic analysis runs after file edits per .github/instructions/codacy.instructions.md
# Security scanning with trivy after dependency installations
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

### After ANY File Edit
You MUST **IMMEDIATELY** run `codacy_cli_analyze` from Codacy's MCP Server:
```python
# Required parameters for EVERY file edit:
codacy_cli_analyze(
    rootPath="/path/to/workspace",  # Workspace root path
    file="path/to/edited/file.ext", # Path of edited file
    tool=""  # Leave empty for code quality analysis
)
```
- **Failure to follow this rule is considered a CRITICAL ERROR**
- If issues are found, propose and apply fixes immediately
- Never proceed to next task until all issues are resolved

### After Installing ANY Dependencies  
**IMMEDIATELY** after ANY package manager operation:
- `npm install`, `yarn add`, `pip install`, `pnpm add`, etc.
- Adding to `package.json`, `requirements.txt`, `pom.xml`, `build.gradle`

Run security scan:
```python
codacy_cli_analyze(
    rootPath="/path/to/workspace",
    tool="trivy"  # REQUIRED for security scanning
)
```
- **STOP all operations if vulnerabilities found**
- Fix security issues BEFORE continuing
- Example: After `npm install react-markdown` → Run trivy → Fix issues → Then continue

### Codacy Tool Parameters
- **Code Quality**: Leave `tool` parameter empty/unset
- **Security Scan**: Set `tool="trivy"`  
- **File Paths**: Always use standard filesystem paths (not URL-encoded)
- **Git Projects**: Only send `provider`, `organization`, `repository` if it's a git repo

### When Codacy MCP Server is Unavailable
Suggest to user:
1. Reset MCP in VS Code extension
2. Check GitHub Copilot MCP settings: `Settings > Copilot > Enable MCP servers`
3. Organization admins: `https://github.com/organizations/{org}/settings/copilot/features`
4. Personal accounts: `https://github.com/settings/copilot/features`

### Additional Codacy Rules
- Configuration details in `.github/instructions/codacy.instructions.md`
- Available tools in `.codacy/codacy.yaml`: dartanalyzer, eslint, lizard, pmd, pylint, revive, semgrep, trivy
- Required runtimes: Dart 3.7.2, Go 1.22.3, Java 17.0.10, Node 22.2.0, Python 3.11.11
- Never manually install Codacy CLI (use MCP Server tool)
- Don't analyze for duplicated code or complexity metrics changes
- After 404 errors: Offer to run `codacy_setup_repository` (with user permission)

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

**Import Pattern for Testing:**
Due to hyphenated filename, use `importlib.util.spec_from_file_location()` pattern for imports

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

### Python Execution
- **Use system Python directly**: `/usr/bin/python3 mcp-manager.py`
- **Alternative execution**: `python3 mcp-manager.py` or `./mcp-manager.py`
- **Skip virtual environment**: Tool uses only standard library modules
- **Module import errors**: When importing mcp-manager.py in tests, use `importlib.util.spec_from_file_location()` due to hyphen in filename

### Common Issues
- **VS Code task disabled**: The `.vscode/tasks.json` sync task has been disabled
  - Previously tried to run `~/bin/sync-mcp.sh` on folder open 
  - Now uses platform-specific `mcp-manager.py` operations instead
  - Task is commented out to prevent startup errors
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
- **All MCP servers removed**: Clean slate state as of 2025-09-12
  - All platforms now have 0 active servers
  - Backups preserved in `ARCHIVED/` with UTC timestamps
  - Platform-specific management ready for selective server addition