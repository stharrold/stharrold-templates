# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Latest Update (2025-09-15)**: Completed Issue #12 security workflow integration, cleaned ARCHIVED directory structure to contain only 10 compressed date-based archives, and updated documentation to reflect current repository state. Enhanced Quick Start section and streamlined duplicate content sections.

## Repository Architecture

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and agentic development workflows. The repository provides cross-platform tools, comprehensive modular guides, automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.

**Repository Configuration**: Default working branch is `contrib/stharrold` for active development. GitHub repository configured with minimal branch protection (deletion prevention only).

## Multi-Implementation Architecture

This repository supports parallel development using multiple implementation approaches through git worktrees when needed for complex tasks with multiple viable solutions.

## Core Architecture

This repository implements a sophisticated **multi-platform management system** with a **structured document lifecycle** and **modular CLAUDE.md orchestration**:

### Document Lifecycle Architecture
```
Research → Integration → Archive
   ↓           ↓          ↓
00_draft-   10_draft-   ARCHIVED/
initial/    merged/     (UTC timestamps)
```

**Lifecycle Stages:**
- **00_draft-initial/**: New content awaiting review and integration
- **10_draft-merged/**: Production-ready content (≤30KB per file for AI context)
- **ARCHIVED/**: Compressed date-based archives (YYYYMMDD.tar.gz) preserving completed work

### Key architectural relationships:

1. **TODO-Driven Integration Pipeline:**
   - `TODO.md` tracks 22 GitHub issues (#3-#24) with integration priorities
   - Completed tasks are archived to ARCHIVED/ as compressed archives
   - Active integration status visible in TODO.md with clear priority ordering

2. **Platform-Specific MCP Management:**
   - `mcp_manager.py` handles 3 platforms: Claude Code CLI, VS Code MCP, Claude Desktop
   - Each platform uses different schema: `mcpServers` vs `servers` root keys
   - Platform auto-detection algorithm in `select_target_platform()` function

3. **Modular Guide Hierarchy:**
   - Each directory in `10_draft-merged/` has its own `CLAUDE.md` orchestrator
   - 30KB file size limit enforced across all modular guides for AI context optimization
   - Hierarchical navigation: main CLAUDE.md → subdirectory CLAUDE.md → specific guides
   - Cross-references between related concepts without loading full content

## Dependencies

### Core Requirements
- **Python 3.x**: Uses system Python at `/usr/bin/python3`
- **No external packages**: Uses Python standard library only
- **Codacy CLI**: For code quality analysis (pre-configured in `./.codacy/cli.sh`)
- **Git worktrees**: For parallel development workflows

### Optional Tools
- **GitHub CLI (`gh`)**: For PR and issue management
- **Various MCP servers**: Installed via npm/pip as needed

## Quick Start

Most common workflows:

```bash
# Check MCP server status across all platforms
/usr/bin/python3 mcp_manager.py --status

# Add a new MCP server (interactive)
/usr/bin/python3 mcp_manager.py --add

# Validate documentation before committing changes
./validate_documentation.sh

# Create new feature worktree
git worktree add ../stharrold-templates.worktrees/{feature-name} -b feat/{feature-name}
```

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

### Testing & Validation
```bash
# Documentation validation tests (run before committing documentation changes)
./test_file_size.sh              # Verify 30KB constraints
./test_cross_references.sh       # Check internal links
./test_content_duplication.sh    # Detect duplicate content
./test_command_syntax.sh         # Validate bash commands
./test_yaml_structure.sh         # Check YAML frontmatter
./validate_documentation.sh      # Comprehensive validation (orchestrates all 5 tests)

# Core functionality tests
/usr/bin/python3 test_mcp_deduplication.py         # Test deduplication functionality

# Module verification
python3 -c "import mcp_manager; print('MCPConfig available:', hasattr(mcp_manager, 'MCPConfig'))"

# Run single test file with directory target
./test_file_size.sh 10_draft-merged/30_implementation/  # Test specific directory
./test_cross_references.sh --verbose                    # Detailed link validation
./test_content_duplication.sh --threshold 85            # Custom similarity threshold

# Run individual Python tests
/usr/bin/python3 test_mcp_deduplication.py              # Test deduplication logic

# Test specific files or patterns
./test_command_syntax.sh 10_draft-merged/**/*.md        # Validate bash commands in markdown

# Shell script permissions (if tests fail with permission errors)
chmod +x test_*.sh validate_documentation.sh
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
/usr/bin/python3 mcp_manager.py --deduplicate     # Remove duplicates (run after seeing duplicate servers)
/usr/bin/python3 mcp_manager.py --backup-only    # Create backups without changes
/usr/bin/python3 mcp_manager.py --check-credentials  # Validate credentials (run before adding auth-required servers)
```

### Git Worktree Management
```bash
# List all worktrees
git worktree list

# Create new worktree for feature implementation
git worktree add ../stharrold-templates.worktrees/{feature-name} -b {branch-name}

# Switch to worktree
cd ../stharrold-templates.worktrees/{feature-name}

# Remove completed worktree
git worktree remove ../stharrold-templates.worktrees/{feature-name}

# Prune deleted worktrees
git worktree prune

# GitHub Issue synchronization
gh issue comment <number> --body "completion summary"
gh issue close <number> --comment "resolution notes"

# Archive completed task files
mv file.ext ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_file.ext
```

### Specify Workflow Commands
```bash
# Create feature specification (creates branch and spec file)
.specify/scripts/bash/create-new-feature.sh --json "feature description"

# Check task prerequisites
.specify/scripts/bash/check-task-prerequisites.sh

# Get feature paths for current branch
.specify/scripts/bash/get-feature-paths.sh

# Setup implementation plan
.specify/scripts/bash/setup-plan.sh
```

### Feature Specification Workflow
```bash
# Modular CLAUDE.md navigation patterns
# Always start with the main orchestrator, then follow hierarchical structure:
# 1. Read main CLAUDE.md for repository overview
# 2. Navigate to subdirectory CLAUDE.md for specific domain context
# 3. Access individual guide files through orchestrator navigation

# Example navigation workflow:
cat 10_draft-merged/CLAUDE.md                     # Main orchestrator
cat 10_draft-merged/30_implementation/CLAUDE.md   # Implementation context
cat 10_draft-merged/30_implementation/33_testing-standards.md  # Specific guide
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

# Core functionality tests
/usr/bin/python3 test_mcp_deduplication.py         # Test deduplication functionality

# Module verification
python3 -c "import mcp_manager; print('MCPConfig available:', hasattr(mcp_manager, 'MCPConfig'))"

# MCP server connectivity (after setup)
claude mcp list                                   # List configured servers
```

### Quality Assurance
```bash
# Codacy analysis (8 analysis tools: pylint, bandit, ruff, mypy, prospector, flake8, pydocstyle, pycodestyle)
./.codacy/cli.sh analyze {file_path}                   # Analyze specific file
./.codacy/cli.sh analyze 10_draft-merged/              # Analyze directory
./.codacy/cli.sh analyze --tool pylint mcp_manager.py  # Specific tool analysis
./.codacy/cli.sh analyze --tool bandit --format json   # Security scan with JSON output

# Multi-language analysis support
./.codacy/cli.sh analyze --help                        # View all available tools and languages

# Python validation
python3 test_mcp_deduplication.py                      # Run deduplication tests
python3 -c "import mcp_manager; print('Import successful')"  # Module validation

# File size validation (30KB limit for modular guides)
wc -c 10_draft-merged/**/*.md                          # Check file sizes
find 10_draft-merged/ -name "*.md" -size +30k          # Find oversized files

# Virtual environment activation (if .venv detected)
source .venv/bin/activate                              # Activate local venv
deactivate                                             # Deactivate when done
```

### Document Integration Workflow
```bash
# 1. Navigate to priority document for integration
ls 00_draft-initial/                      # Check draft documents awaiting integration
cat TODO.md                               # Review integration priorities

# 2. Read source and target files
head -20 00_draft-initial/source.md       # Preview source content
ls -la 10_draft-merged/target/             # Check target directory structure

# 3. Archive completed task files (individual files get compressed into date-based archives)
mv completed_file.ext ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_completed_file.ext
```

## Platform-Specific MCP Configuration
### File Size Constraints
- All files in `10_draft-merged/` must be ≤30KB for optimal AI context processing
- ARCHIVED/ contains only compressed date-based archives (YYYYMMDD.tar.gz)
- Individual files archived with UTC timestamp format: `YYYYMMDDTHHMMSSZ_filename.ext`

### Platform Differences
- **Claude Code CLI & Desktop**: Use `"mcpServers": {}` as root key
- **VS Code MCP Extension**: Uses `"servers": {}` as root key
- **Config Paths**: `~/.claude.json` (CLI), platform-specific for VS Code/Desktop
- **Credentials**: Keychain (macOS), Credential Manager (Windows), environment variables (Linux)
- **Auto-detection**: `--status` shows all platforms, tool auto-selects first available
- **Explicit targeting**: `--platform <name>` (claude-code, vscode, claude-desktop)
- **Common tokens**: GITHUB_TOKEN, OPENAI_API_KEY, ANTHROPIC_API_KEY


## MCP Manager Internal Architecture

The `mcp_manager.py` tool implements platform-specific server management:

### Key Functions & Classes:
- `MCPConfig(platform, config_path)` - Platform-specific configuration handler
- `select_target_platform()` - Returns first available platform (claude-code, vscode, claude-desktop)
- `deduplicate_servers()` - Preserves DISABLED_ prefixed versions during cleanup
- `validate_credentials()` - Checks keychain/credential manager for tokens

### Server Management Pattern:
- Active servers: Normal names (e.g., "github")
- Disabled servers: DISABLED_ prefix (e.g., "DISABLED_github")
- Platform schemas: "mcpServers" (Claude) vs "servers" (VS Code)

### Platform Configuration Paths:
- **macOS**: `~/.claude.json`, `~/Library/Application Support/Code/User/mcp.json`
- **Windows**: `~/.claude.json`, `~/AppData/Roaming/Code/User/mcp.json`
- **Linux**: `~/.claude.json`, `~/.config/Code/User/mcp.json`

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


## Git Workflow Conventions

### Branch Naming
- `feat/` - New features and enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `chore/` - Maintenance, dependencies, tooling

### Git Flow Hierarchy

**Branch Structure:**
```
main (production)
  ↓
develop (integration)
  ↓
contrib/stharrold (active development)
  ↓
feature worktrees (individual features)
```

**PR Merge Flow (reverse direction):**
```
Feature Worktree
  ↓ PR targets
contrib/stharrold (working branch)
  ↓ PR targets
develop (integration testing)
  ↓ PR targets
main (production release)
```

**Branch Purposes:**
- **main**: Production-ready code, stable releases
- **develop**: Integration branch for testing combined features
- **contrib/stharrold**: Active development branch for ongoing work
- **worktrees**: Feature-specific development branches

**IMPORTANT**: Always create PRs to the branch your feature was derived from:
- Feature worktrees → `contrib/stharrold`
- contrib/stharrold → `develop` (when ready for integration)
- develop → `main` (for production releases)

### Commit Message Format
```bash
git commit -m "feat: descriptive message including issue reference

Closes #123

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Issue Integration Architecture

The repository follows a structured issue-to-implementation pipeline:

1. **GitHub Issues** → Numbered sequentially (#3-24, #31-44)
2. **Planning Documents** → `TODO_FOR_issue-{number}-{approach}.md`
3. **Worktrees** → `../stharrold-templates.worktrees/issue/{number}-{approach}`
4. **Document Order** → Files numbered by source (09_, 11_, 12_) integrate in sequence
5. **Multi-Approach** → Single issue can have multiple worktrees (claude, bmad, speckit, flow)

Example flow for Issue #15:
- Source: `00_draft-initial/12_report-baml-documentation-extractor.md`
- Plan: `TODO_FOR_issue-15-merge-12-baml.md`
- Worktree: `issue/15-merge-12-baml`
- Target: `10_draft-merged/30_implementation/42_documentation-patterns.md`

## Integration Priority System

Current priorities (from TODO.md):
1. **Top Priority**: Issue #13 (Document #11 - embedding model integration)
2. **Priority 2-5**: Core technical documentation (#15-16, #22-23)
3. **Security Enhancements**: Issues #3-5 (mcp-secrets-plugin, OAuth 2.1, Auth0)
4. **Infrastructure**: Testing and monitoring setup (#8-11)

**Completed**: Issue #12 (security workflow integration) - archived in ARCHIVED/

## Common Issues & Solutions

### MCP Manager Issues
- **Permission errors**: Run `chmod +x mcp_manager.py` or use `python3 mcp_manager.py`
- **Platform not found**: Use `--status` to see available platforms
- **Auto-detection issues**: Explicitly specify `--platform <name>`

### Worktree Management Issues
- **Current state**: No active worktrees (use `git worktree list` to verify)
- **When needed**: Create worktrees for complex parallel implementations
- **Cleanup**: Remove worktrees after PR merge to keep repository clean

### Python Development Issues
- **Import errors**: Use `/usr/bin/python3` for system Python
- **Configuration not found**: Check platform-specific paths with `--status`

## Development Environment Setup

### Shell Script Execution
All test and validation scripts require proper permissions. If scripts fail with permission errors:
```bash
# Make all shell scripts executable
chmod +x *.sh test_*.sh validate_documentation.sh

# Or make specific scripts executable as needed
chmod +x test_file_size.sh test_cross_references.sh

# Verify script permissions
ls -la *.sh | grep rwx
```

### Virtual Environment Management
The repository supports virtual environments for Python dependencies:
```bash
# Create virtual environment (if .venv doesn't exist)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Verify activation
which python3              # Should show .venv path
pip list                   # Show installed packages

# Deactivate when done
deactivate
```

## Critical Guidelines

- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** unless explicitly requested
- Follow the document lifecycle: Research → Integration → Archive (compressed)
- Use platform-specific MCP management approach (no cross-platform sync)
- Archive completed tasks to maintain clean repository state
- Check TODO.md for current integration priorities
- **Use modular CLAUDE.md navigation**: Start with orchestrators, follow hierarchy
- **Test before committing**: Run `./validate_documentation.sh` for documentation changes