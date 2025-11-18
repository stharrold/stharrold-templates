# Workflow Tools

Selective integration of german workflow system tools (v5.3.0) for stharrold-templates repository.

## Overview

This directory contains cherry-picked workflow automation tools that add value without requiring external dependencies. All tools use Python standard library only.

## Directory Structure

- **workflow-utilities/** - File and workflow management utilities
- **git-helpers/** - Git workflow automation tools

## workflow-utilities/

Archive management, directory structure validation, and version consistency checking.

### archive_manager.py
Manage compressed archives in ARCHIVED/ directory.

**Usage:**
```bash
# List all archives
python3 tools/workflow-utilities/archive_manager.py list

# Extract archive
python3 tools/workflow-utilities/archive_manager.py extract ARCHIVED/20251118.tar.gz output/

# Create new archive
python3 tools/workflow-utilities/archive_manager.py create ARCHIVED/20251118.tar.gz file1.md file2.md
```

### directory_structure.py
Ensure CLAUDE.md and README.md exist in all directories with proper YAML frontmatter.

**Usage:**
```bash
# Validate directory structure
python3 tools/workflow-utilities/directory_structure.py 10_draft-merged/

# Create missing files
python3 tools/workflow-utilities/directory_structure.py --create 10_draft-merged/new_directory/
```

### validate_versions.py
Check version consistency across configuration files.

**Usage:**
```bash
# Check all versions
python3 tools/workflow-utilities/validate_versions.py

# Verbose output with file locations
python3 tools/workflow-utilities/validate_versions.py --verbose
```

## git-helpers/

Git workflow automation for semantic versioning and worktree management.

### semantic_version.py
Calculate semantic version from git diff analysis.

**Usage:**
```bash
# Calculate version bump from develop to HEAD
python3 tools/git-helpers/semantic_version.py develop v5.0.0

# Output: v5.1.0 (if new features added)
```

**Version Rules:**
- **MAJOR**: Breaking changes, removed features, API changes
- **MINOR**: New features, new files, backward-compatible additions
- **PATCH**: Bug fixes, refactoring, documentation, tests

### create_worktree.py
Create standardized git worktrees for parallel development.

**Usage:**
```bash
# Create feature worktree
python3 tools/git-helpers/create_worktree.py feature my-feature contrib/stharrold

# Creates: ../stharrold-templates.worktrees/feature_<timestamp>_my-feature/
# Branch: feature/<timestamp>_my-feature
```

## Design Philosophy

These tools follow stharrold-templates design principles:

- **Zero external dependencies**: Python stdlib only
- **Cross-platform**: Works on macOS, Linux, Windows
- **Standalone**: Each tool can be used independently
- **Well-documented**: Clear usage examples and error messages

## Integration with Templates Repository

These tools complement existing templates infrastructure:

- **archive_manager.py** works with ARCHIVED/ compressed archives (YYYYMMDD.tar.gz format)
- **directory_structure.py** validates modular CLAUDE.md orchestration pattern
- **validate_versions.py** checks version consistency across pyproject.toml and documentation
- **semantic_version.py** automates version bumps for releases
- **create_worktree.py** standardizes worktree creation for parallel development

## Not Included

The following german workflow components are NOT integrated:

- **BMAD planner** - Interactive planning Q&A (Python project focus)
- **SpecKit author** - Specification generation (Python project focus)
- **Quality enforcer** - pytest + coverage gates (overkill for documentation)
- **AgentDB state manager** - DuckDB tracking (external dependency)
- **Full workflow orchestrator** - 6-phase coordinator (not applicable)

## Reference

For complete german workflow documentation, see:
- `docs/reference/german-workflow-v5.3.0.md`
- `docs/reference/WORKFLOW-INIT-PROMPT.md`

## Version

Tools extracted from: german workflow v5.3.0 (2025-11-18)
