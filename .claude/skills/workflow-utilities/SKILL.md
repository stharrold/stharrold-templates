---
name: workflow-utilities
version: 5.3.0
description: |
  Shared utilities for file deprecation, directory structure creation,
  archive management, skill scaffolding, pre-commit hooks, version
  validation, and VCS abstraction (GitHub/Azure DevOps via release_lib.vcs).
  Used by all other skills.

  Use when: Need shared utilities, deprecating files, archiving files,
  creating skill scaffolds, running VCS operations.

  Triggers: deprecate, archive, create directory, create skill, VCS operations
---

## Quick Reference

```bash
# Archive deprecated files
uv run python .claude/skills/workflow-utilities/scripts/deprecate_files.py <desc> <files...>

# List/extract archives
uv run python .claude/skills/workflow-utilities/scripts/archive_manager.py list
uv run python .claude/skills/workflow-utilities/scripts/archive_manager.py extract <archive>

# Validate versions
uv run python .claude/skills/workflow-utilities/scripts/validate_versions.py
```

# Workflow Utilities

## Purpose

Provides reusable Python utilities for common workflow tasks that are used
across multiple skills.

## Scripts

### deprecate_files.py

Archive deprecated files with timestamp into ARCHIVED/ directory.

```bash
python .claude/skills/workflow-utilities/scripts/deprecate_files.py \
  <todo_file> <description> <file1> [file2 ...]
```

**Arguments:**
- `todo_file`: Path to TODO file (for timestamp extraction)
- `description`: Short description (e.g., 'old-auth-flow')
- `files`: One or more file paths to deprecate

**Creates:**
- `ARCHIVED/YYYYMMDDTHHMMSSZ_<description>.zip`

### directory_structure.py

Create standard directory structure with required files.

```bash
python .claude/skills/workflow-utilities/scripts/directory_structure.py \
  <directory>
```

**Arguments:**
- `directory`: Path to directory to create/populate

**Creates:**
- `CLAUDE.md` - Context-specific guidance
- `README.md` - Human-readable documentation
- `ARCHIVED/` subdirectory (with its own CLAUDE.md and README.md)

### archive_manager.py

List and extract archived files.

```bash
# List archives
python .claude/skills/workflow-utilities/scripts/archive_manager.py list [directory]

# Extract archive
python .claude/skills/workflow-utilities/scripts/archive_manager.py extract <archive> [output_dir]
```

### VCS Abstraction Layer (vcs/)

Backward-compat shim over `release_lib.vcs` (extracted in issue #240).

**Location:** `.claude/skills/workflow-utilities/scripts/vcs/__init__.py`

**Canonical home:** `release_lib/vcs/` — new code should import from there directly.

**Exported functions** (re-exported from `release_lib.vcs`):
`get_username`, `get_contrib_branch`, `create_pr`, `create_release`,
`create_issue`, `query_pr_review_threads`, `check_auth`, `detect_provider`

**Usage (legacy callers):**
```python
from vcs import create_pr, get_contrib_branch, get_username

branch = get_contrib_branch()  # auto-detects provider
username = get_username()

# Create PR
pr_url = create_pr(
    base=branch,
    head="feature/20251103T143000Z_auth",
    title="feat: auth system (v1.6.0)",
    body="PR body content",
)
```

**Key features:**
- Auto-detects provider from `git remote.origin.url` (github.com / dev.azure.com)
- Errors surfaced as `RuntimeError(stderr)` — callers inspect string contents
- PR creation, issue creation, release management, auth checking

## Usage Examples

### Deprecating Old Files

```python
import subprocess

# Deprecate old implementation files
subprocess.run([
    'python',
    '.claude/skills/workflow-utilities/scripts/deprecate_files.py',
    'TODO_feature_20251022T143022Z_json-validator.md',
    'old-validator',
    'src/old_validator.py',
    'tests/test_old_validator.py'
], check=True)
```

### Creating Standard Directories

```python
import subprocess

# Create planning directory with standard structure
subprocess.run([
    'python',
    '.claude/skills/workflow-utilities/scripts/directory_structure.py',
    'planning/json-validator'
], check=True)
```

## Directory Standards

All directories created by these utilities follow the standard structure:

```
directory/
├── CLAUDE.md      # Context for Claude Code
├── README.md      # Human-readable documentation
└── ARCHIVED/      # Deprecated files (except if directory IS archived)
    ├── CLAUDE.md
    └── README.md
```

## Integration with Other Skills

All skills can use these helper functions:

```python
# Example from bmad-planner
from pathlib import Path
import subprocess

def create_planning_with_structure(feature_name):
    """Create planning directory with standard structure."""

    planning_dir = Path('planning') / feature_name

    # Create directory structure
    subprocess.run([
        'python',
        '.claude/skills/workflow-utilities/scripts/directory_structure.py',
        str(planning_dir)
    ], check=True)

    # Now create planning documents
    # ...
```

## Best Practices

- Always use these utilities for consistency
- Don't manually create directory structures
- Use deprecation for old files, not deletion
- Update TODO file after each meaningful step
- Check archives before deleting files permanently
