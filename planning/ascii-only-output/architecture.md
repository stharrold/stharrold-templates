# Architecture: ASCII-Only Output

**Issue**: #102
**Slug**: ascii-only-output

## Overview

This is a refactoring task with no new architecture. The change involves replacing Unicode characters with ASCII equivalents in existing scripts.

## Affected Components

### Scripts with Unicode Output

Based on existing `safe_output.py` usage and grep for Unicode characters:

1. **git-workflow-manager/scripts/**
   - `backmerge_workflow.py` - Uses `safe_print()` with Unicode
   - `daily_rebase.py` - Uses print with Unicode
   - `release_workflow.py` - Uses `safe_print()` with Unicode
   - `create_worktree.py` - May have Unicode
   - `cleanup_feature.py` - May have Unicode

2. **quality-enforcer/scripts/**
   - `run_quality_gates.py` - Uses `safe_print()` with Unicode

3. **workflow-utilities/scripts/**
   - `safe_output.py` - Contains the Unicode→ASCII fallback logic
   - Other utility scripts

4. **agentdb-state-manager/scripts/**
   - Various scripts with status output

## Current State

The codebase already has `safe_output.py` which provides:
- `safe_print()` - Attempts Unicode, falls back on encoding errors
- Unicode symbols defined as constants

## Target State

### Option A: Modify safe_output.py (Recommended)

Change the constants in `safe_output.py` to use ASCII by default:

```python
# Before
CHECKMARK = "✓"
CROSS = "✗"
WARNING = "⚠"
ARROW = "→"

# After
CHECKMARK = "[OK]"
CROSS = "[FAIL]"
WARNING = "[WARN]"
ARROW = "->"
```

**Pros**: Single point of change, consistent across all scripts
**Cons**: Loss of visual appeal on Unicode-capable terminals

### Option B: Environment Variable Toggle

Add environment variable to control output style:

```python
ASCII_ONLY = os.environ.get("ASCII_OUTPUT", "1") == "1"
CHECKMARK = "[OK]" if ASCII_ONLY else "✓"
```

**Pros**: User choice, backward compatible
**Cons**: More complex, environment dependency

## Recommendation

**Option A** - Direct ASCII replacement. Simplicity over configurability. The slight visual degradation is worth the guaranteed compatibility.

## Implementation Steps

1. Update `safe_output.py` constants to ASCII
2. Search for any direct Unicode usage in scripts (not via safe_output)
3. Replace any remaining Unicode with ASCII
4. Run tests to verify no regressions
5. Test on Windows/legacy systems

## Testing Strategy

1. Run all existing tests
2. Manual test on Windows terminal
3. Manual test with `PYTHONIOENCODING=ascii`
4. Verify CI/CD logs are clean
