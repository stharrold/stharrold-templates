# Implementation Plan: ASCII-Only Output

**Type:** feature
**Slug:** ascii-only-output
**Date:** 2025-11-26
**Issue:** #102

## Task Breakdown

### Epic 1: Update safe_output.py

#### Task impl_001: Simplify safe_output.py to ASCII-only

**Priority:** High

**Files:**
- `.claude/skills/workflow-utilities/scripts/safe_output.py`
- `.agents/workflow-utilities/scripts/safe_output.py` (synced copy)

**Description:**
Modify the central output utilities module to use ASCII-only symbols, removing UTF-8 detection and fallback logic.

**Steps:**
1. Remove `_init_utf8()` function
2. Remove `_UTF8_SUPPORTED` variable
3. Update `SYMBOLS` dict to use ASCII values directly:
   - `checkmark`: `[OK]`
   - `cross`: `[FAIL]`
   - `arrow`: `->`
   - `bullet`: `*`
   - `warning`: `[WARN]`
4. Simplify `safe_print()` to just call `print()` (no fallback needed)
5. Remove Unicode replacement logic from `safe_print()`

**Acceptance Criteria:**
- [ ] All symbols are ASCII-only strings
- [ ] No Unicode characters in safe_output.py
- [ ] `safe_print()` is a simple wrapper around `print()`
- [ ] All format functions produce ASCII output

**Verification:**
```bash
uv run python -c "from .claude.skills.workflow_utilities.scripts.safe_output import SYMBOLS; print(all(v.isascii() for v in SYMBOLS.values()))"
```

**Dependencies:**
- None

---

#### Task impl_002: Update safe_output.py tests

**Priority:** High

**Files:**
- `tests/unit/test_safe_output.py`

**Description:**
Update existing tests to verify ASCII-only output and add new tests for the simplified implementation.

**Steps:**
1. Update test expectations for new ASCII symbols
2. Add `test_symbols_are_ascii()` to verify all symbols are ASCII
3. Add tests for each format function to verify ASCII output
4. Remove tests for Unicode fallback (no longer applicable)

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Tests verify ASCII-only output
- [ ] Test coverage maintained at >= 80%

**Verification:**
```bash
uv run pytest tests/unit/test_safe_output.py -v
```

**Dependencies:**
- impl_001

---

### Epic 2: Audit and Fix Direct Unicode Usage

#### Task impl_003: Fix initialize_repository.py

**Priority:** High

**Files:**
- `.claude/skills/initialize-repository/scripts/initialize_repository.py`

**Description:**
Replace Unicode characters in print statements with ASCII equivalents.

**Steps:**
1. Replace `print_error()` Unicode: `✗` -> `[FAIL]`
2. Replace `print_success()` Unicode: `✓` -> `[OK]`
3. Replace `print_warning()` Unicode: `⚠` -> `[WARN]`
4. Update template strings with checkmarks in output messages

**Acceptance Criteria:**
- [ ] No Unicode in print statements
- [ ] Output messages remain clear and readable
- [ ] Script functionality unchanged

**Verification:**
```bash
grep -E '[✓✗→⚠]' .claude/skills/initialize-repository/scripts/initialize_repository.py || echo "No Unicode found"
```

**Dependencies:**
- impl_001

---

#### Task impl_004: Fix create_planning.py

**Priority:** High

**Files:**
- `.claude/skills/bmad-planner/scripts/create_planning.py`

**Description:**
Replace Unicode characters in BMAD planner script.

**Steps:**
1. Replace `✓` with `[OK]` in all print statements
2. Replace `⚠` with `[WARN]` in warning messages
3. Verify no other Unicode characters remain

**Acceptance Criteria:**
- [ ] No Unicode in print statements
- [ ] Script functionality unchanged

**Verification:**
```bash
grep -E '[✓✗→⚠]' .claude/skills/bmad-planner/scripts/create_planning.py || echo "No Unicode found"
```

**Dependencies:**
- impl_001

---

#### Task impl_005: Fix create_specifications.py

**Priority:** High

**Files:**
- `.claude/skills/speckit-author/scripts/create_specifications.py`

**Description:**
Replace Unicode characters in SpecKit author script.

**Steps:**
1. Replace `✓` with `[OK]` in success messages
2. Replace `⚠` with `[WARN]` in warning messages
3. Verify no other Unicode characters remain

**Acceptance Criteria:**
- [ ] No Unicode in print statements
- [ ] Script functionality unchanged

**Verification:**
```bash
grep -E '[✓✗→⚠]' .claude/skills/speckit-author/scripts/create_specifications.py || echo "No Unicode found"
```

**Dependencies:**
- impl_001

---

#### Task impl_006: Fix create_skill.py

**Priority:** High

**Files:**
- `.claude/skills/workflow-utilities/scripts/create_skill.py`

**Description:**
Replace Unicode characters in skill creation script.

**Steps:**
1. Replace `✗` with `[FAIL]` in error messages
2. Replace `✓` with `[OK]` in success messages
3. Replace `⚠` with `[WARN]` in warning messages
4. Update completion summary output

**Acceptance Criteria:**
- [ ] No Unicode in print statements
- [ ] Script functionality unchanged

**Verification:**
```bash
grep -E '[✓✗→⚠]' .claude/skills/workflow-utilities/scripts/create_skill.py || echo "No Unicode found"
```

**Dependencies:**
- impl_001

---

#### Task impl_007: Fix checkpoint_manager.py

**Priority:** Medium

**Files:**
- `.claude/skills/agentdb-state-manager/scripts/checkpoint_manager.py`

**Description:**
Replace Unicode characters in AgentDB checkpoint manager.

**Steps:**
1. Replace `✓` with `[OK]` in status messages

**Acceptance Criteria:**
- [ ] No Unicode in print statements

**Verification:**
```bash
grep -E '[✓✗→⚠]' .claude/skills/agentdb-state-manager/scripts/checkpoint_manager.py || echo "No Unicode found"
```

**Dependencies:**
- impl_001

---

#### Task impl_008: Fix check_coverage.py

**Priority:** Medium

**Files:**
- `.claude/skills/quality-enforcer/scripts/check_coverage.py`

**Description:**
Replace Unicode characters in coverage check script.

**Steps:**
1. Replace `✓` with `[OK]` and `✗` with `[FAIL]` in status output

**Acceptance Criteria:**
- [ ] No Unicode in print statements

**Verification:**
```bash
grep -E '[✓✗→⚠]' .claude/skills/quality-enforcer/scripts/check_coverage.py || echo "No Unicode found"
```

**Dependencies:**
- impl_001

---

#### Task impl_009: Fix run_quality_gates.py

**Priority:** High

**Files:**
- `.claude/skills/quality-enforcer/scripts/run_quality_gates.py`

**Description:**
Replace Unicode characters in quality gates runner.

**Steps:**
1. Replace `⚠️` with `[WARN]` in warning messages
2. Update sync status messages

**Acceptance Criteria:**
- [ ] No Unicode in print statements
- [ ] Quality gates functionality unchanged

**Verification:**
```bash
grep -E '[✓✗→⚠]' .claude/skills/quality-enforcer/scripts/run_quality_gates.py || echo "No Unicode found"
```

**Dependencies:**
- impl_001

---

### Epic 3: Testing and Validation

#### Task test_001: Run full test suite

**Priority:** High

**Files:**
- All test files

**Description:**
Run full test suite to ensure no regressions from ASCII changes.

**Steps:**
1. Run `uv run pytest` to execute all tests
2. Verify all tests pass
3. Check coverage is >= 80%

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Coverage >= 80%

**Verification:**
```bash
uv run pytest --cov=. --cov-fail-under=80
```

**Dependencies:**
- impl_001 through impl_009

---

#### Task test_002: Test with ASCII-only encoding

**Priority:** High

**Files:**
- None (manual testing)

**Description:**
Test scripts with restricted ASCII encoding to verify no UnicodeEncodeError.

**Steps:**
1. Set `PYTHONIOENCODING=ascii`
2. Run key workflow scripts
3. Verify no encoding errors

**Acceptance Criteria:**
- [ ] No UnicodeEncodeError with ASCII encoding
- [ ] Output is readable and clear

**Verification:**
```bash
PYTHONIOENCODING=ascii uv run python -c "
from .claude.skills.workflow_utilities.scripts.safe_output import *
print_success('test')
print_error('test')
print_warning('test')
"
```

**Dependencies:**
- impl_001 through impl_009

---

#### Task test_003: Run quality gates

**Priority:** High

**Files:**
- None

**Description:**
Run quality gates to ensure all checks pass.

**Steps:**
1. Run quality gates script
2. Verify all 5 gates pass

**Acceptance Criteria:**
- [ ] Coverage gate passes
- [ ] Tests gate passes
- [ ] Build gate passes
- [ ] Linting gate passes
- [ ] AI Config Sync gate passes

**Verification:**
```bash
uv run python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
```

**Dependencies:**
- test_001, test_002

---

#### Task doc_001: Update CHANGELOG.md

**Priority:** Medium

**Files:**
- `CHANGELOG.md`

**Description:**
Add changelog entry for ASCII-only output feature.

**Steps:**
1. Add new version entry (patch bump)
2. Document the changes under appropriate category

**Acceptance Criteria:**
- [ ] CHANGELOG updated with version bump
- [ ] Changes documented clearly

**Dependencies:**
- test_003

---

## Task Dependencies Graph

```
impl_001 ─┬─> impl_002 ─────────────────────────────────────────┐
          ├─> impl_003 ─────────────────────────────────────────┤
          ├─> impl_004 ─────────────────────────────────────────┤
          ├─> impl_005 ─────────────────────────────────────────┤
          ├─> impl_006 ─────────────────────────────────────────┼─> test_001 ─┬─> test_003 ─> doc_001
          ├─> impl_007 ─────────────────────────────────────────┤             │
          ├─> impl_008 ─────────────────────────────────────────┤             └─> test_002
          └─> impl_009 ─────────────────────────────────────────┘
```

## Critical Path

1. impl_001 (safe_output.py core changes)
2. impl_002 (update tests)
3. impl_003-impl_009 (can be parallelized)
4. test_001 (full test suite)
5. test_002 (ASCII encoding test)
6. test_003 (quality gates)
7. doc_001 (changelog)

## Parallel Work Opportunities

- Tasks impl_003 through impl_009 can be done in parallel after impl_001
- test_002 can run in parallel with test_001

## Quality Checklist

Before considering this feature complete:

- [ ] All tasks marked as complete
- [ ] Test coverage >= 80%
- [ ] All tests passing
- [ ] Linting clean (`uv run ruff check .`)
- [ ] No Unicode in Python script output statements
- [ ] No UnicodeEncodeError with ASCII encoding
- [ ] CHANGELOG updated
- [ ] Code reviewed

## Risk Assessment

### Low Risk

All tasks are low risk because:
- Simple string replacements only
- No logic changes
- Existing tests catch regressions
- Easy to verify with grep

### Potential Issues

- **Missed Unicode**: Grep might miss some Unicode characters
  - Mitigation: Test with `PYTHONIOENCODING=ascii`

- **Test failures**: Existing tests may expect Unicode output
  - Mitigation: Update test expectations (impl_002)

## Notes

### Implementation Tips

1. Use search/replace with regex: `[✓✗→⚠]`
2. Check both `.claude/skills/` and `.agents/` directories
3. Keep markdown documentation Unicode (only fix Python scripts)

### Version Bump

This is a PATCH version bump (backward compatible fix).
