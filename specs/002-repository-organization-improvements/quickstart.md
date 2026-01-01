# Quickstart: Repository Organization Improvements

**Feature**: 002-repository-organization-improvements
**Date**: 2025-11-21

## Overview

This guide validates the repository reorganization was successful.

## Prerequisites

- Podman running (`podman info`)
- On feature branch or merged to contrib

## Validation Steps

### Step 1: Verify Test Structure

```bash
# Check tests directory exists
ls -la tests/

# Expected output:
# tests/
# ├── __init__.py
# ├── conftest.py
# └── test_mcp_deduplication.py
```

### Step 2: Run Tests

```bash
# Tests should discover and pass
podman-compose run --rm dev pytest -v

# Expected: All tests pass
```

### Step 3: Verify Gitignore

```bash
# Check .DS_Store is ignored
cat .gitignore | grep ".DS_Store"

# Check no .DS_Store files tracked
git ls-files | grep ".DS_Store"
# Expected: No output (empty)
```

### Step 4: Verify Documentation Structure

```bash
# Check new structure exists
ls -la docs/

# Expected:
# docs/
# ├── research/
# ├── guides/
# └── archived/

# Check old structure removed
ls 00_draft-initial/ 2>/dev/null
# Expected: "No such file or directory"
```

### Step 5: Verify README.md

```bash
# Check README exists
head -20 README.md

# Expected: Project title, description, quick start section
```

### Step 6: Verify TODO Consolidation

```bash
# Count TODO files at root
ls -1 TODO*.md

# Expected: Only TODO.md (single file)
```

### Step 7: Run Quality Gates

```bash
# All 6 gates must pass
podman-compose run --rm dev python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py

# Expected:
# Gate 1: Coverage ≥80% - PASS
# Gate 2: Tests pass - PASS
# Gate 3: Build succeeds - PASS
# Gate 4: Linting clean - PASS
# Gate 5: TODO frontmatter valid - PASS
# Gate 6: AI config synced - PASS
```

## Success Criteria

| Check | Expected |
|-------|----------|
| `tests/` exists | ✓ |
| pytest discovers tests | ✓ |
| No .DS_Store in git | ✓ |
| `docs/` structure correct | ✓ |
| README.md exists | ✓ |
| Single TODO.md | ✓ |
| Quality gates pass | ✓ |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| pytest can't find tests | Check `tests/__init__.py` exists |
| .DS_Store still showing | Run `git rm --cached .DS_Store` |
| Quality gate fails | Check specific gate output |
| Import errors | Run inside container: `podman-compose run --rm dev python` |

## Rollback

If reorganization causes issues:

```bash
# Revert to previous state
git checkout contrib/stharrold -- .

# Or reset branch
git reset --hard origin/contrib/stharrold
```
