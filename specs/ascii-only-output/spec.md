# Specification: ASCII-Only Output

**Type:** feature
**Slug:** ascii-only-output
**Date:** 2025-11-26
**Author:** stharrold
**Issue:** #102

## Overview

Replace Unicode symbols (checkmarks, crosses, arrows, warnings) with ASCII equivalents in all workflow scripts to ensure compatibility with legacy systems, Windows terminals with encoding issues, CI/CD environments, and SSH sessions with misconfigured locales.

## Requirements Reference

See: `planning/ascii-only-output/requirements.md` in main repository

Key requirements:
- FR-1: Replace Unicode symbols with ASCII (`[OK]`, `[FAIL]`, `[WARN]`, `->`)
- FR-2: Maintain output readability
- FR-3: Consistent style across all scripts
- NFR-1: No changes to functionality or exit codes
- NFR-2: Minimal changes (output statements only)

## Detailed Specification

### Component 1: safe_output.py Constants

**File:** `.claude/skills/workflow-utilities/scripts/safe_output.py`

**Purpose:** Central location for output symbols used by all workflow scripts

**Current Implementation:**
```python
SYMBOLS = {
    'checkmark': '[OK]' if _UTF8_SUPPORTED else '[OK]',
    'cross': '[X]' if _UTF8_SUPPORTED else '[X]',
    'arrow': '->' if _UTF8_SUPPORTED else '->',
    'bullet': '*' if _UTF8_SUPPORTED else '*',
    'warning': '!' if _UTF8_SUPPORTED else '!',
}
```

**Target Implementation (Option A - Direct ASCII):**
```python
# ASCII-only output for maximum compatibility
# Rationale: Simplicity over configurability - guaranteed compatibility
# on Windows cp1252, legacy systems, CI/CD, SSH sessions

SYMBOLS = {
    'checkmark': '[OK]',
    'cross': '[FAIL]',
    'arrow': '->',
    'bullet': '*',
    'warning': '[WARN]',
}
```

**Changes:**
1. Remove `_UTF8_SUPPORTED` conditional logic
2. Use ASCII values directly
3. Change `[X]` to `[FAIL]` (per requirements)
4. Change `!` to `[WARN]` (per requirements)
5. Remove `_init_utf8()` function (no longer needed)
6. Simplify `safe_print()` to just call `print()` (no fallback needed)

### Component 2: Scripts with Direct Unicode

**Files with direct Unicode print statements (not using safe_output):**

1. `.claude/skills/initialize-repository/scripts/initialize_repository.py`
   - Lines 84, 94, 112: `print_error()`, `print_success()`, `print_warning()` with Unicode
   - Lines 520-654, 1193-1229: Template strings with Unicode checkmarks

2. `.claude/skills/bmad-planner/scripts/create_planning.py`
   - Lines 346, 486, 601, 605, 827, 878, 902, 918, 952, 976, 1029-1035, 1041, 1072

3. `.claude/skills/speckit-author/scripts/create_specifications.py`
   - Lines 251, 345, 545, 553, 559, 596, 706, 732

4. `.claude/skills/workflow-utilities/scripts/create_skill.py`
   - Lines 98, 108, 126, 346, 936, 945-954

5. `.claude/skills/agentdb-state-manager/scripts/checkpoint_manager.py`
   - Lines 43, 74

6. `.claude/skills/quality-enforcer/scripts/check_coverage.py`
   - Line 46

7. `.claude/skills/quality-enforcer/scripts/run_quality_gates.py`
   - Lines 143, 152, 159, 162, 172, 178

**Strategy:** Each script should either:
- Import and use `safe_output.py` functions, OR
- Replace inline Unicode with ASCII directly

### Component 3: Documentation Files

**Files:** `.claude/skills/*/CLAUDE.md`, `*.md` in skills directories

Unicode in markdown documentation is acceptable since:
- Markdown is rendered, not printed to console
- Documentation is read in browsers/editors with Unicode support

**Decision:** Keep Unicode in markdown documentation files.

## Symbol Mapping

| Current | ASCII Replacement | Context |
|---------|-------------------|---------|
| `✓` | `[OK]` | Success status |
| `✗` | `[FAIL]` | Error/failure status |
| `⚠` | `[WARN]` | Warning status |
| `→` | `->` | Arrows in text |
| `•` | `*` | Bullet points |

## Testing Requirements

### Unit Tests

**File:** `tests/unit/test_safe_output.py`

Update existing tests to verify ASCII-only output:

```python
def test_symbols_are_ascii():
    """Verify all symbols are ASCII-only."""
    from workflow_utilities.scripts.safe_output import SYMBOLS
    for name, symbol in SYMBOLS.items():
        assert symbol.isascii(), f"{name} contains non-ASCII: {symbol!r}"

def test_format_check_ascii():
    """Test format_check produces ASCII output."""
    from workflow_utilities.scripts.safe_output import format_check
    result = format_check("test message")
    assert result.isascii()
    assert result == "[OK] test message"

def test_format_cross_ascii():
    """Test format_cross produces ASCII output."""
    from workflow_utilities.scripts.safe_output import format_cross
    result = format_cross("test message")
    assert result.isascii()
    assert result == "[FAIL] test message"
```

### Integration Tests

**File:** `tests/integration/test_ascii_output.py` (new)

```python
def test_no_unicode_in_script_output():
    """Run scripts and verify no UnicodeEncodeError."""
    import subprocess
    import os

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'ascii'

    result = subprocess.run(
        ['uv', 'run', 'python', '-c',
         'from .claude.skills.workflow_utilities.scripts.safe_output import *; '
         'print_success("test"); print_error("test"); print_warning("test")'],
        capture_output=True,
        text=True,
        env=env
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
```

## Quality Gates

- [x] All existing tests pass (after updates)
- [ ] New ASCII-specific tests pass
- [ ] No `UnicodeEncodeError` with `PYTHONIOENCODING=ascii`
- [ ] Test coverage >= 80%
- [ ] Linting clean (`ruff check .`)

## Dependencies

No new dependencies. This is a refactoring of existing code.

## Implementation Notes

### Key Considerations

1. **Backward Compatibility**: Scripts must continue to work identically - only visual output changes
2. **Exit Codes**: Must remain unchanged
3. **File Outputs**: Must remain unchanged (only console output affected)

### Error Handling

No changes to error handling. The simplified `safe_print()` can just call `print()` directly since all output will be ASCII.

### Testing Strategy

1. Run all existing tests to ensure no regressions
2. Test with `PYTHONIOENCODING=ascii` to simulate legacy environments
3. Visual inspection of output to ensure readability

## References

- GitHub Issue: #102
- Planning: `planning/ascii-only-output/`
- Existing implementation: `.claude/skills/workflow-utilities/scripts/safe_output.py`
