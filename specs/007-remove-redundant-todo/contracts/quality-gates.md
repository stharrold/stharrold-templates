# Contract: Quality Gates Update

**Feature Branch**: `007-remove-redundant-todo`
**Date**: 2025-11-23

---

## Contract Purpose

Define the expected behavior of the quality gates system after removing the TODO frontmatter gate.

---

## Interface Contract

### Function: `run_all_gates()`

**Location**: `.claude/skills/quality-enforcer/scripts/run_quality_gates.py`

**Before**:
```python
def run_all_gates():
    # Runs 6 gates
    # Gate 5: check_todo_frontmatter()
    # Returns dict with 'todo_frontmatter_passed' key
```

**After**:
```python
def run_all_gates():
    # Runs 5 gates (Gate 5 removed, Gate 6 renumbered)
    # No TODO-related keys in results
    # Returns dict WITHOUT 'todo_frontmatter_passed' key
```

---

## Removed Function Contract

### Function: `check_todo_frontmatter()` (REMOVED)

**Behavior (documented for removal verification)**:
- Scans for `TODO*.md` files in root
- Validates YAML frontmatter presence
- Checks required fields: `status`, `feature`, `branch`
- Returns `True` if all valid or no files exist

**Expected After Removal**:
- Function does not exist
- No import or call references
- No `todo_frontmatter` in gate results

---

## Output Contract

### Gate Results Dictionary

**Before**:
```python
{
    "coverage": {"passed": bool, "percentage": float},
    "tests": {"passed": bool},
    "build": {"passed": bool},
    "linting": {"passed": bool},
    "todo_frontmatter": {"passed": bool},  # REMOVE
    "ai_config_sync": {"passed": bool}
}
```

**After**:
```python
{
    "coverage": {"passed": bool, "percentage": float},
    "tests": {"passed": bool},
    "build": {"passed": bool},
    "linting": {"passed": bool},
    "ai_config_sync": {"passed": bool}  # Renumbered to Gate 5
}
```

---

## Console Output Contract

**Before**:
```
[1/6] Coverage...
[2/6] Tests...
[3/6] Build...
[4/6] Linting...
[5/6] TODO*.md Frontmatter...
[6/6] AI Config Sync...
```

**After**:
```
[1/5] Coverage...
[2/5] Tests...
[3/5] Build...
[4/5] Linting...
[5/5] AI Config Sync...
```

---

## Validation Tests

### Test: Gate count reduced
```python
def test_gate_count():
    """Quality gates should have 5 gates, not 6."""
    # Run gates
    # Assert console output shows "[X/5]" pattern
    # Assert no "[X/6]" pattern
```

### Test: TODO function removed
```python
def test_no_todo_function():
    """check_todo_frontmatter should not exist."""
    from run_quality_gates import *
    assert not hasattr(module, 'check_todo_frontmatter')
```

### Test: Results dict structure
```python
def test_results_no_todo_key():
    """Results should not contain todo_frontmatter key."""
    results = run_all_gates()
    assert 'todo_frontmatter' not in results
```

### Test: All gates pass with no TODO files
```python
def test_gates_pass_without_todo():
    """Quality gates should pass when no TODO*.md exists."""
    # Ensure no TODO*.md in root
    results = run_all_gates()
    assert all(v.get('passed', True) for v in results.values())
```
