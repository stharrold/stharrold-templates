# Epics: ASCII-Only Output

**Issue**: #102
**Slug**: ascii-only-output

## Epic 1: Update safe_output.py

**Goal**: Change Unicode constants to ASCII equivalents

### Tasks

1. [ ] Update `CHECKMARK` constant: `"✓"` → `"[OK]"`
2. [ ] Update `CROSS` constant: `"✗"` → `"[FAIL]"`
3. [ ] Update `WARNING` constant: `"⚠"` → `"[WARN]"`
4. [ ] Update `ARROW` constant: `"→"` → `"->"`
5. [ ] Remove Unicode fallback logic (no longer needed)
6. [ ] Update tests for safe_output.py

## Epic 2: Audit and Fix Direct Unicode Usage

**Goal**: Find and replace any Unicode not going through safe_output

### Tasks

1. [ ] Grep for Unicode characters in `.claude/skills/` scripts
2. [ ] Replace Unicode in `daily_rebase.py` (uses print directly)
3. [ ] Replace Unicode in any other scripts found
4. [ ] Verify no Unicode in user-facing output

## Epic 3: Testing and Validation

**Goal**: Ensure changes work across platforms

### Tasks

1. [ ] Run full test suite
2. [ ] Test with `PYTHONIOENCODING=ascii`
3. [ ] Verify quality gates pass
4. [ ] Update CHANGELOG.md

## Estimated Scope

- **Files to modify**: ~5-10 Python scripts
- **Complexity**: Low (string replacements)
- **Risk**: Low (no logic changes)
- **Version bump**: PATCH (backward compatible fix)
