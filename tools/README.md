# Workflow Tools

Selective integration of german workflow system tools (v5.3.0) for stharrold-templates repository.

## Overview

This directory contains cherry-picked workflow automation tools from german workflow system v5.3.0. All tools run within the Podman container environment with uv-managed Python 3.11.

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
podman-compose run --rm dev python tools/workflow-utilities/archive_manager.py list

# Extract archive
podman-compose run --rm dev python tools/workflow-utilities/archive_manager.py extract ARCHIVED/20251118.tar.gz output/

# Create new archive
podman-compose run --rm dev python tools/workflow-utilities/archive_manager.py create ARCHIVED/20251118.tar.gz file1.md file2.md
```

### directory_structure.py
Ensure CLAUDE.md and README.md exist in all directories with proper YAML frontmatter.

**Usage:**
```bash
# Validate directory structure
podman-compose run --rm dev python tools/workflow-utilities/directory_structure.py 10_draft-merged/

# Create missing files
podman-compose run --rm dev python tools/workflow-utilities/directory_structure.py --create 10_draft-merged/new_directory/
```

### validate_versions.py
Check version consistency across configuration files.

**Usage:**
```bash
# Check all versions
podman-compose run --rm dev python tools/workflow-utilities/validate_versions.py

# Verbose output with file locations
podman-compose run --rm dev python tools/workflow-utilities/validate_versions.py --verbose
```

## git-helpers/

Git workflow automation for semantic versioning and worktree management.

### semantic_version.py
Calculate semantic version from git diff analysis.

**Usage:**
```bash
# Calculate version bump from develop to HEAD
podman-compose run --rm dev python tools/git-helpers/semantic_version.py develop v5.0.0

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
podman-compose run --rm dev python tools/git-helpers/create_worktree.py feature my-feature contrib/stharrold

# Creates: ../stharrold-templates.worktrees/feature_<timestamp>_my-feature/
# Branch: feature/<timestamp>_my-feature
```

## Design Philosophy

These tools follow stharrold-templates design principles:

- **Containerized**: Run via podman-compose for consistency
- **Cross-platform**: Works on macOS, Linux, Windows
- **Standalone**: Each tool can be used independently
- **Well-documented**: Clear usage examples and error messages

## Running Tools

All tools are run via podman-compose:

```bash
podman-compose run --rm dev python tools/workflow-utilities/archive_manager.py list
podman-compose run --rm dev python tools/git-helpers/semantic_version.py develop v5.0.0
```

## Integration with Templates Repository

These tools complement existing templates infrastructure:

- **archive_manager.py** works with ARCHIVED/ compressed archives (YYYYMMDD.tar.gz format)
- **directory_structure.py** validates modular CLAUDE.md orchestration pattern
- **validate_versions.py** checks version consistency across pyproject.toml and documentation
- **semantic_version.py** automates version bumps for releases
- **create_worktree.py** standardizes worktree creation for parallel development

## Integrated Skills

The following german workflow skills are fully integrated in `.claude/skills/`:

- **BMAD planner** - BMAD planning (requirements + architecture)
- **SpecKit author** - SpecKit specifications (spec + plan)
- **Quality enforcer** - Quality gates (tests, coverage, linting)
- **AgentDB state manager** - DuckDB state synchronization
- **Workflow orchestrator** - Main workflow coordinator
- **Tech stack adapter** - Python/uv/Podman detection
- **Git workflow manager** - Git operations and release management
- **Initialize repository** - Repository initialization
- **Workflow utilities** - Archive, directory structure, version validation

## Reference

For complete german workflow documentation, see:
- `docs/reference/german-workflow-v5.3.0.md`
- `docs/reference/WORKFLOW-INIT-PROMPT.md`

## Version

Tools extracted from: german workflow v5.3.0 (2025-11-18)
