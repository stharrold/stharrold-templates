# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Latest Update (2025-09-14)**: Enhanced with comprehensive MCP security patterns including OAuth 2.1 implementation, production security tools (mcp-secrets-plugin, mcpauth, Auth0), layered storage architecture, and Trail of Bits vulnerability mitigations. BMAD framework integrated for agentic development workflows with full agent persona support and advanced task orchestration.

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

This is a **templates and utilities repository** for MCP (Model Context Protocol) server configuration and agentic development workflows. The repository provides cross-platform tools, comprehensive modular guides, automation scripts for managing MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop, plus BMAD framework integration for advanced agentic development.

**Current MCP State**: All MCP servers have been removed from all platforms (as of 2025-09-12). This provides a clean slate for selective server management using the platform-specific approach.

**Repository Configuration**: Default working branch is `contrib/stharrold` for active development. GitHub repository configured with minimal branch protection (deletion prevention only).

## BMAD Framework Integration

This repository includes the **BMAD-METHOD™ (Breakthrough Method of Agile AI-Driven Development)** framework for advanced agentic development workflows. BMAD provides specialized AI agent personas, task orchestration, and comprehensive development templates.

### BMAD Agent Personas Available
- **Architect** (`/BMad:agents:architect`) - System design, architecture documents, technology selection
- **Analyst** (`/BMad:agents:analyst`) - Requirements analysis, research, stakeholder interviews
- **PM** (`/BMad:agents:pm`) - Project management, roadmaps, resource planning
- **Dev** (`/BMad:agents:dev`) - Code implementation, technical execution
- **QA** (`/BMad:agents:qa`) - Quality assurance, testing strategies, validation
- **SM** (`/BMad:agents:sm`) - Scrum Master, story creation, sprint management

### BMAD Configuration
- **Core Config**: `.bmad-core/core-config.yaml`
- **Agent Directory**: `.bmad-core/agents/`
- **Task Templates**: `.bmad-core/tasks/`
- **Claude Commands**: `.claude/commands/BMad/`

### Core Architecture

This repository implements a sophisticated **multi-platform management system** with a **structured document lifecycle** that spans multiple interconnected files:

#### Document Lifecycle Architecture (Multi-File System)
```
Research → Integration → Archive
   ↓           ↓          ↓
00_draft-   10_draft-   ARCHIVED/
initial/    merged/     (UTC timestamps)
```

**Key architectural relationships that require reading multiple files:**

1. **TODO-Driven Integration Pipeline:**
   - `TODO.md` tracks 22 GitHub issues (#3-#24) with integration priorities
   - `TODO_FOR_*.md` files contain detailed execution plans for high-priority integrations
   - Dual implementation approaches supported: Speckit vs Claude-specific worktrees
   - Separate TODO_FOR files for each approach (e.g., `TODO_FOR_*-speckit.md` vs `TODO_FOR_*-claude.md`)
   - Each plan maps source files to target locations with size constraints
   - GitHub issues sync automatically with TODO items

2. **Platform-Specific MCP Management:**
   - `mcp_manager.py` handles 3 platforms: Claude Code CLI, VS Code MCP, Claude Desktop
   - Each platform uses different schema: `mcpServers` vs `servers` root keys
   - Platform auto-detection algorithm in `select_target_platform()` function
   - Credential validation spans OS-native storage (Keychain/Credential Manager)

3. **Modular Guide Hierarchy:**
   - Each directory in `10_draft-merged/` has its own `CLAUDE.md` orchestrator
   - Cross-references between `10_mcp/`, `20_credentials/`, `30_implementation/`
   - 30KB file size limit enforced across all modular guides for AI context optimization
   - YAML frontmatter tracks version history and cross-references

4. **Security-First Integration:**
   - Security tools span multiple files: credential setup, OAuth 2.1 patterns, vulnerability scanning
   - Integration of security workflows from `.github/instructions/codacy.instructions.md`
   - Production-ready tools integration (mcp-secrets-plugin, mcpauth, Auth0)

## Essential Development Commands

### BMAD Agent Commands
```bash
# Activate BMAD agent personas (use in Claude Code CLI)
/BMad:agents:architect     # System architecture and design
/BMad:agents:analyst       # Requirements and research
/BMad:agents:pm           # Project management
/BMad:agents:dev          # Development and implementation
/BMad:agents:qa           # Quality assurance and testing
/BMad:agents:sm           # Scrum Master and story management

# BMAD task execution examples
/BMad:tasks:document-project           # Document existing project architecture
/BMad:tasks:create-doc                # Create documentation with templates
/BMad:tasks:create-next-story         # Generate development stories
/BMad:tasks:review-story              # Review and validate stories
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

### Testing and Validation
```bash
# Core functionality tests
/usr/bin/python3 test_mcp_deduplication.py       # Test deduplication functionality

# Module verification
python3 -c "import mcp_manager; print('MCPConfig available:', hasattr(mcp_manager, 'MCPConfig'))"

# MCP server connectivity (after setup)
claude mcp list                                   # List configured servers
```

### Code Quality Workflow (RECOMMENDED)
```bash
# Python code quality (when available)
python3 -m pylint mcp_manager.py                        # Lint main Python files
python3 -m flake8 mcp_manager.py                       # Style checking

# Manual validation
python3 test_mcp_deduplication.py                      # Run deduplication tests
python3 -c "import mcp_manager; print('Import successful')"  # Module validation

# BMAD quality assurance
/BMad:agents:qa                                         # Activate QA agent for review
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

## Platform-Specific MCP Configuration

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

### TODO_FOR Files Pattern
```
TODO_FOR_feat-{issue}-{task}-{method}.md
```

Example for issue #12:
- `TODO_FOR_feat-12-integrate-workflow-secrets.md` (Speckit method)
- `TODO_FOR_feat-12-integrate-workflow-secrets-claude.md` (Claude method)
- `TODO_FOR_feat-12-integrate-workflow-secrets-bmad.md` (BMAD method)

### Worktree Implementation Pattern
```bash
# Work completed in separate worktrees
../stharrold-templates.worktrees/{worktree-name}/
```

Each implementation method uses dedicated worktrees to avoid conflicts.

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
1. **Completed**: Issue #12 (security workflow integration) - BMAD implementation ✅
2. **High Priority**: Issue #19 (state management integration) - Next priority
3. **Security Enhancements**: Issues #3-5 (mcp-secrets-plugin, OAuth 2.1, Auth0)
4. **Medium Priority**: Document integrations (#13-18, #21)
5. **Infrastructure**: Testing and monitoring setup (#8-11)

### BMAD-Specific Workflows
- Use `/BMad:agents:pm` for roadmap planning and prioritization
- Use `/BMad:agents:analyst` for requirements analysis on new features
- Use `/BMad:tasks:create-next-story` for implementing TODO items

## Common Issues & Solutions

### MCP Manager Issues
- **Permission errors**: Run `chmod +x mcp_manager.py` or use `python3 mcp_manager.py`
- **Platform not found**: Use `--status` to see available platforms
- **Auto-detection issues**: Explicitly specify `--platform <name>`

### BMAD Framework Issues
- **Agent commands not found**: Ensure you're using Claude Code CLI with `/BMad:` prefix
- **Agent not responding correctly**: Check `.bmad-core/core-config.yaml` for configuration
- **Task execution fails**: Verify task dependencies in `.bmad-core/tasks/` directory
- **Missing BMAD files**: Run `ls .bmad-core/` to verify installation integrity

### Python Development Issues
- **Import errors**: Use `/usr/bin/python3` for system Python
- **Configuration not found**: Check platform-specific paths with `--status`

## Critical Guidelines

- **ALWAYS prefer editing existing files** over creating new ones
- **NEVER proactively create documentation files** unless explicitly requested
- Follow the document lifecycle: Research → Integration → Archive
- Maintain bidirectional references between TODO.md and TODO_FOR files
- Use platform-specific MCP management approach (no cross-platform sync)
- **Use BMAD agents for complex tasks**: Activate appropriate personas for specialized work
- **Leverage BMAD task templates**: Use existing tasks in `.bmad-core/tasks/` for consistency
- **Document BMAD workflows**: When using BMAD agents, document the persona and reasoning