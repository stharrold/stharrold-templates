# Contributing to stharrold-templates

Thank you for considering contributing to this project! This document provides guidelines for contributing to the MCP configuration templates and workflow automation tools.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [MCP Server Contributions](#mcp-server-contributions)
- [Documentation Requirements](#documentation-requirements)
- [Pull Request Process](#pull-request-process)
- [Quality Standards](#quality-standards)

## Code of Conduct

This project follows a professional and respectful code of conduct:

- Be respectful and inclusive
- Focus on constructive feedback
- Prioritize technical accuracy and truthfulness
- Welcome contributions from all skill levels

## Getting Started

### Prerequisites

Ensure you have the required tools installed:

```bash
# Required
python3 --version     # Python 3.11+ (system python or via uv)
git --version         # Version control
gh --version          # GitHub CLI (for PR management)

# Optional but recommended
uv --version          # Python package manager (for dev tools)
```

### Initial Setup

1. **Fork and clone the repository:**
   ```bash
   gh repo fork stharrold/stharrold-templates --clone
   cd stharrold-templates
   ```

2. **Install development dependencies (optional):**
   ```bash
   uv sync  # Installs pytest, ruff, mypy
   ```

3. **Test MCP manager:**
   ```bash
   /usr/bin/python3 mcp_manager.py --status
   ```

4. **Run validation scripts:**
   ```bash
   ./validate_documentation.sh
   ```

## Development Workflow

This repository uses a contrib branch workflow for personal contributions:

### Branch Structure

```
main (production)
  ↑
develop (integration)
  ↑
contrib/stharrold (active development)
  ↑
feature/* (individual features via worktrees)
```

### Creating a Feature Branch

```bash
# Option 1: Using workflow tool (recommended)
python3 tools/git-helpers/create_worktree.py feature my-feature contrib/stharrold

# Option 2: Manual worktree creation
git worktree add ../stharrold-templates.worktrees/my-feature -b feat/my-feature
```

### Daily Maintenance

```bash
# Rebase contrib branch onto develop
git checkout contrib/stharrold
git fetch origin
git rebase origin/develop
git push origin contrib/stharrold --force-with-lease
```

### Pull Request Flow

1. **Feature → contrib/stharrold**: After feature implementation
2. **contrib/stharrold → develop**: When ready for integration
3. **develop → main**: For production releases

## MCP Server Contributions

### Adding New MCP Server Templates

When adding templates for new MCP servers:

1. **Document in 10_draft-merged/**
   - Create guide following modular CLAUDE.md pattern
   - Keep file size ≤30KB for AI context optimization
   - Include server configuration, credentials, platform compatibility

2. **Test on all platforms:**
   - Claude Code CLI (`~/.claude.json`)
   - VS Code MCP Extension (platform-specific paths)
   - Claude Desktop (platform-specific paths)

3. **Update mcp_manager.py if needed:**
   - Add platform detection logic
   - Handle new credential types
   - Test deduplication logic

### MCP Configuration Standards

**JSON Structure:**
```json
{
  "mcpServers": {  // or "servers" for VS Code
    "server-name": {
      "command": "command",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

**Credential Management:**
- Use keychain/credential manager (not plaintext)
- Document required environment variables
- Test with `mcp_manager.py --check-credentials`

## Documentation Requirements

### Modular CLAUDE.md Pattern

All directories must have:

1. **CLAUDE.md** - AI context and navigation
   - YAML frontmatter with type, parent, children
   - Cross-references to related concepts
   - Command examples and workflows

2. **README.md** - Human-readable documentation
   - YAML frontmatter with directory metadata
   - Detailed explanations and tutorials
   - Usage examples

3. **ARCHIVED/** - Deprecated files subdirectory

### File Size Constraints

- All files in `10_draft-merged/` must be ≤30KB
- Use modular structure with cross-references
- ARCHIVED/ uses compressed date-based archives (YYYYMMDD.tar.gz)

### Validation

Before committing documentation changes:

```bash
./validate_documentation.sh  # Runs all 5 validation tests:
# - test_file_size.sh (30KB limit)
# - test_cross_references.sh (internal links)
# - test_content_duplication.sh (detect duplicates)
# - test_command_syntax.sh (validate bash commands)
# - test_yaml_structure.sh (check frontmatter)
```

## Pull Request Process

### 1. Create Pull Request

```bash
# Push feature branch
git push origin feat/my-feature

# Create PR to contrib/stharrold
gh pr create \
  --title "feat: descriptive title" \
  --body "Detailed description" \
  --base contrib/stharrold
```

### 2. PR Requirements

- [ ] All validation scripts pass
- [ ] MCP manager functional (if Python changes)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No external dependencies added (stdlib only)

### 3. Commit Message Format

```
<type>(<scope>): <subject>

<body>

Closes #issue-number

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** feat, fix, docs, style, refactor, test, chore

### 4. Review Process

- Self-merge enabled for personal contrib branches
- Request review for significant changes
- Address feedback before merge

### 5. After Merge

```bash
# Cleanup worktree and branches
git worktree remove ../stharrold-templates.worktrees/my-feature
git branch -D feat/my-feature
git push origin --delete feat/my-feature
```

## Quality Standards

### Python Code Standards

**Core Principles:**
- **Stdlib only**: No external dependencies for core tools
- **Cross-platform**: Works on macOS, Linux, Windows
- **System Python**: Use `/usr/bin/python3` in scripts
- **Error handling**: Comprehensive try/except with clear messages

**Development Tools (optional):**
```bash
# Linting
uv run ruff check .

# Type checking
uv run mypy mcp_manager.py

# Auto-fix linting issues
uv run ruff check --fix .
```

### Documentation Standards

**CLAUDE.md Files:**
- Purpose-focused (what this directory contains)
- Command-focused (quick reference)
- Navigation-focused (where to go next)
- Context-optimized (≤30KB)

**README.md Files:**
- Explanation-focused (why and how)
- Tutorial-focused (step-by-step guides)
- Reference-focused (complete documentation)
- Human-optimized (no size limit)

### Testing Standards

**Manual Testing:**
```bash
# MCP manager functionality
/usr/bin/python3 mcp_manager.py --status
/usr/bin/python3 test_mcp_deduplication.py

# Documentation validation
./validate_documentation.sh

# New workflow tools
python3 tools/workflow-utilities/archive_manager.py list
python3 tools/git-helpers/semantic_version.py develop v5.0.0
```

**Automated Testing (CI/CD):**
- GitHub Actions runs on push/PR
- Azure Pipelines available
- Must pass before merge

## Workflow Tools Integration

This repository includes selective tools from german workflow v5.3.0:

### Using Workflow Tools

```bash
# Archive management
python3 tools/workflow-utilities/archive_manager.py list

# Directory structure validation
python3 tools/workflow-utilities/directory_structure.py 10_draft-merged/

# Version consistency checking
python3 tools/workflow-utilities/validate_versions.py

# Semantic versioning
python3 tools/git-helpers/semantic_version.py develop v5.0.0

# Worktree creation
python3 tools/git-helpers/create_worktree.py feature my-feature contrib/stharrold
```

### NOT Included from German Workflow

The following are intentionally NOT integrated:
- BMAD planner (Python project focus)
- SpecKit author (Python project focus)
- Quality enforcer with pytest (overkill for documentation)
- AgentDB state manager (external dependency)
- Full 6-phase workflow orchestrator (not applicable)

See `docs/reference/german-workflow-v5.3.0.md` for complete workflow documentation.

## Questions or Issues?

- Open an issue on GitHub
- Check CLAUDE.md for detailed guidance
- Review existing PRs for examples

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
