# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Latest Update (2025-09-15)**: Enhanced with comprehensive MCP security patterns including OAuth 2.1 implementation, production security tools (mcp-secrets-plugin, mcpauth, Auth0), layered storage architecture, and multi-implementation worktree architecture supporting parallel development approaches. Integrated practical workflow secrets with step-by-step credential management examples, platform-specific verification commands, and error handling patterns via Speckit implementation.

## Repository Architecture

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and agentic development workflows. The repository provides cross-platform tools, comprehensive modular guides, automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

**Repository Configuration**: Default working branch is `contrib/stharrold` for active development. GitHub repository configured with minimal branch protection (deletion prevention only).

## Multi-Implementation Architecture

This repository supports parallel development using multiple implementation approaches through git worktrees:

### Implementation Methods Available
- **Speckit** - Traditional systematic approach
- **Claude** - AI-assisted development patterns
- **BMAD** - Framework-driven methodology
- **Claude2** - Multi-guide content distribution
- **Flow** - Workflow automation approach

### Worktree Structure
- **Main repo**: `/Users/stharrold/Documents/GitHub/stharrold-templates/`
- **Worktrees**: `../stharrold-templates.worktrees/{feature-branch}/`
- **Pattern**: Each implementation method uses dedicated worktrees to avoid conflicts

## Core Architecture

This repository implements a sophisticated **multi-platform management system** with a **structured document lifecycle**:

### Document Lifecycle Architecture
```
Research → Integration → Archive
   ↓           ↓          ↓
00_draft-   10_draft-   ARCHIVED/
initial/    merged/     (UTC timestamps)
```

### Key architectural relationships:

1. **TODO-Driven Integration Pipeline:**
   - `TODO.md` tracks 22 GitHub issues (#3-#24) with integration priorities
   - `TODO_FOR_*.md` files contain detailed execution plans for high-priority integrations
   - Five implementation approaches supported: Speckit, Claude, BMAD, Claude2, and Flow
   - Each plan maps source files to target locations with size constraints

2. **Platform-Specific MCP Management:**
   - `mcp_manager.py` handles 3 platforms: Claude Code CLI, VS Code MCP, Claude Desktop
   - Each platform uses different schema: `mcpServers` vs `servers` root keys
   - Platform auto-detection algorithm in `select_target_platform()` function

3. **Modular Guide Hierarchy:**
   - Each directory in `10_draft-merged/` has its own `CLAUDE.md` orchestrator
   - 30KB file size limit enforced across all modular guides for AI context optimization

## Essential Development Commands

### Most Frequently Used
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

### MCP Manager Operations
```bash
# System status and platform detection
/usr/bin/python3 mcp_manager.py --status

# Interactive MCP management (auto-detects platform)
/usr/bin/python3 mcp_manager.py --add            # Add server
/usr/bin/python3 mcp_manager.py --remove         # Remove server
/usr/bin/python3 mcp_manager.py --disable        # Disable servers (DISABLED_ prefix)
/usr/bin/python3 mcp_manager.py --enable         # Re-enable servers

# Platform-specific operations
/usr/bin/python3 mcp_manager.py --platform claude-code --list
/usr/bin/python3 mcp_manager.py --platform vscode --add
/usr/bin/python3 mcp_manager.py --platform claude-desktop --remove

# Maintenance operations
/usr/bin/python3 mcp_manager.py --deduplicate     # Remove duplicates
/usr/bin/python3 mcp_manager.py --backup-only    # Create backups
/usr/bin/python3 mcp_manager.py --check-credentials  # Validate credentials
```

### Git Worktree Management
```bash
# List all worktrees
git worktree list

# Create new worktree for feature implementation
git worktree add ../stharrold-templates.worktrees/{feature-name} -b {branch-name}

# Switch to worktree
cd ../stharrold-templates.worktrees/{feature-name}

<<<<<<< HEAD
# GitHub Issue synchronization
gh issue comment <number> --body "completion summary"
gh issue close <number> --comment "resolution notes"

# Archive files with UTC timestamp
mv file.ext ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_file.ext
=======
# Remove completed worktree
git worktree remove ../stharrold-templates.worktrees/{feature-name}

# Prune deleted worktrees
git worktree prune
>>>>>>> 9d876d4c4bdceaca2fad2814380117b8ee61b8a9
```

### MCP Manager Operations
```bash
# System status and platform detection
/usr/bin/python3 mcp_manager.py --status

# Interactive MCP management (auto-detects platform)
/usr/bin/python3 mcp_manager.py --add            # Add server
/usr/bin/python3 mcp_manager.py --remove         # Remove server
/usr/bin/python3 mcp_manager.py --disable        # Disable servers (DISABLED_ prefix)
/usr/bin/python3 mcp_manager.py --enable         # Re-enable servers

# Platform-specific operations
/usr/bin/python3 mcp_manager.py --platform claude-code --list
/usr/bin/python3 mcp_manager.py --platform vscode --add
/usr/bin/python3 mcp_manager.py --platform claude-desktop --remove

# Maintenance operations
/usr/bin/python3 mcp_manager.py --deduplicate     # Remove duplicates
/usr/bin/python3 mcp_manager.py --backup-only    # Create backups
/usr/bin/python3 mcp_manager.py --check-credentials  # Validate credentials
```

<<<<<<< HEAD
### Feature Specification Workflow
```bash
# .specify workflow commands
.specify/scripts/bash/create-new-feature.sh    # Create new feature spec
.specify/scripts/bash/setup-plan.sh            # Initialize implementation plan
.specify/scripts/bash/check-task-prerequisites.sh  # Validate prerequisites
```

### Testing & Validation
```bash
# Documentation validation tests
./test_file_size.sh              # Verify 30KB constraints
./test_cross_references.sh       # Check internal links
./test_content_duplication.sh    # Detect duplicate content
./test_command_syntax.sh         # Validate bash commands
./test_yaml_structure.sh         # Check YAML frontmatter
./validate_documentation.sh      # Comprehensive validation

# Python testing
/usr/bin/python3 test_mcp_deduplication.py         # Test deduplication functionality
/usr/bin/python3 mcp_manager.py --validate-all     # Validate all configurations
python3 -c "import mcp_manager; mcp_manager.validate_credentials()"  # Test credentials
=======
### Testing and Validation
```bash
# Core functionality tests
/usr/bin/python3 test_mcp_deduplication.py       # Test deduplication functionality
>>>>>>> 9d876d4c4bdceaca2fad2814380117b8ee61b8a9

# Module verification
python3 -c "import mcp_manager; print('MCPConfig available:', hasattr(mcp_manager, 'MCPConfig'))"

<<<<<<< HEAD
# Dependency management with UV (system default)
uv sync && uv add package_name            # Sync dependencies and add new packages
=======
# MCP server connectivity (after setup)
claude mcp list                                   # List configured servers
>>>>>>> 9d876d4c4bdceaca2fad2814380117b8ee61b8a9
```

### Quality Assurance
```bash
# Codacy analysis (configured in repository)
./.codacy/cli.sh analyze {file_path}                   # Analyze specific file
./.codacy/cli.sh analyze 10_draft-merged/              # Analyze directory

# Python validation
python3 test_mcp_deduplication.py                      # Run deduplication tests
python3 -c "import mcp_manager; print('Import successful')"  # Module validation

# File size validation (30KB limit for modular guides)
wc -c 10_draft-merged/**/*.md                          # Check file sizes
```

### Document Integration Workflow
```bash
# 1. Navigate to priority document for integration
ls 00_draft-initial/                      # Check draft documents awaiting integration
cat TODO.md                               # Review integration priorities

# 2. Read source and target files
head -20 00_draft-initial/source.md       # Preview source content
ls -la 10_draft-merged/target/             # Check target directory structure

# 3. Archive source document after integration
mv 00_draft-initial/source.md ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_source.md
```

<<<<<<< HEAD
## Critical Workflow Rules


### File Size Constraints
- All files in `10_draft-merged/` must be ≤30KB for optimal AI context processing
- Use UTC timestamp format: `YYYYMMDDTHHMMSSZ_filename.ext` for `ARCHIVED/`

## MCP Server Configuration Architecture
=======
## Platform-Specific MCP Configuration
>>>>>>> 9d876d4c4bdceaca2fad2814380117b8ee61b8a9

### Platform Differences
- **Claude Code CLI & Desktop**: Use `"mcpServers": {}` as root key
- **VS Code MCP Extension**: Uses `"servers": {}` as root key
- **Config Paths**: `~/.claude.json` (CLI), platform-specific for VS Code/Desktop
- **Credentials**: Keychain (macOS), Credential Manager (Windows), environment variables (Linux)

### Platform Auto-Detection
The `mcp_manager.py` tool operates on **one platform at a time**:
- **Auto-detection**: `--status` shows all platforms, tool auto-selects first available
- **Explicit targeting**: `--platform <name>` (claude-code, vscode, claude-desktop)
- **Common tokens**: GITHUB_TOKEN, OPENAI_API_KEY, ANTHROPIC_API_KEY

## Multi-Implementation Architecture

This repository supports multiple implementation approaches for the same task:

<<<<<<< HEAD
Complete details in `.github/instructions/codacy.instructions.md`

=======
### TODO_FOR Files Pattern
```
TODO_FOR_feat-{issue}-{task}-{method}.md
```
>>>>>>> 9d876d4c4bdceaca2fad2814380117b8ee61b8a9

Example for issue #12:
- `TODO_FOR_feat-12-integrate-workflow-secrets.md` (Speckit method)
- `TODO_FOR_feat-12-integrate-workflow-secrets-claude.md` (Claude method)
- `TODO_FOR_feat-12-integrate-workflow-secrets-bmad.md` (BMAD method)
- `TODO_FOR_feat-12-integrate-workflow-secrets-claude2.md` (Claude2 multi-guide method)
- `TODO_FOR_feat-12-integrate-workflow-secrets-flow.md` (Flow method)

### Active Worktrees (Current)
```bash
# Main repository
/Users/stharrold/Documents/GitHub/stharrold-templates   [contrib/stharrold]

# Implementation worktrees
../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets         [Speckit]
../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-bmad    [BMAD]
../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude  [Claude]
../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-flow    [Flow]
```

Each implementation method uses dedicated worktrees to avoid conflicts and enable parallel development.

## Core Classes and Functions

### mcp_manager.py Architecture
- `MCPConfig`: Main configuration management class with platform-specific logic
  - `__init__(platform: str, config_path: Optional[Path] = None)`: Initialize for specific platform
  - `add_server()`, `remove_server()`: Interactive server management
  - `disable_server()`, `enable_server()`: DISABLED_ prefix management
- `select_target_platform()`: Auto-detection algorithm returning first available platform
- `validate_credentials()`: Cross-platform credential validation for common tokens
- `deduplicate_servers()`: Intelligent duplicate removal preserving DISABLED_ versions

### Standard Python Import Pattern
```python
import mcp_manager
# Initialize: config = mcp_manager.MCPConfig('claude-code')
# Auto-detect: platform = mcp_manager.select_target_platform()
# Validate: results = mcp_manager.validate_credentials()
```

## File Size and Context Constraints

- All files in `10_draft-merged/` must be ≤30KB for optimal AI context processing
- Use UTC timestamp format: `YYYYMMDDTHHMMSSZ_filename.ext` for `ARCHIVED/`
- YAML frontmatter tracks version history and cross-references in modular guides

## Git Workflow Conventions

### Branch Naming
- `feat/` - New features and enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `chore/` - Maintenance, dependencies, tooling

### Default Branch
- Work on `contrib/stharrold` branch for active development
- Create PRs to `develop` or `main` as appropriate

### Commit Message Format
```bash
git commit -m "feat: descriptive message including issue reference

Closes #123

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Integration Priority System

Current priorities (from TODO.md):
1. **In Progress**: Issue #12 (security workflow integration) - Multiple implementations in worktrees
2. **High Priority**: Issue #19 (state management integration) - Next priority
3. **Security Enhancements**: Issues #3-5 (mcp-secrets-plugin, OAuth 2.1, Auth0)
4. **Medium Priority**: Document integrations (#13-18, #21)
5. **Infrastructure**: Testing and monitoring setup (#8-11)

## Common Issues & Solutions

### MCP Manager Issues
- **Permission errors**: Run `chmod +x mcp_manager.py` or use `python3 mcp_manager.py`
- **Platform not found**: Use `--status` to see available platforms
- **Auto-detection issues**: Explicitly specify `--platform <name>`

### Worktree Management Issues
- **Worktree conflicts**: Use `git worktree list` to check active worktrees
- **Branch conflicts**: Ensure each worktree uses unique branch names
- **Disk space**: Worktrees create full working copies; monitor disk usage
- **Sync issues**: Changes in one worktree don't automatically sync to others

### Python Development Issues
- **Import errors**: Use `/usr/bin/python3` for system Python
- **Configuration not found**: Check platform-specific paths with `--status`

## Critical Guidelines

- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** unless explicitly requested
- Follow the document lifecycle: Research → Integration → Archive
- Maintain bidirectional references between TODO.md and TODO_FOR files
- Use platform-specific MCP management approach (no cross-platform sync)
- **Use appropriate implementation method**: Choose Speckit, Claude, BMAD, Claude2, or Flow based on task requirements
- **Leverage worktrees for parallel work**: Create separate worktrees for different implementation approaches
- **Document implementation decisions**: Record rationale for chosen implementation method in TODO_FOR files