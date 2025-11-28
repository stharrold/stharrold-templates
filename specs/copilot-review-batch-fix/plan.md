# Implementation Plan: Copilot Review Batch Fix

**Type:** feature
**Slug:** copilot-review-batch-fix
**Date:** 2025-11-28

## Task Breakdown

### Phase 1: Code Bug Fixes

#### Task impl_001: Fix code block end markers counting logic (#31)

**Priority:** High

**Description:**
The regex for counting code block end markers is incorrect. It only counts bare closing markers but not language-specific closings.

**Steps:**
1. Search for regex pattern that counts code block markers
2. Update regex to count all closing markers (```)
3. Verify fix doesn't break existing functionality

**Acceptance Criteria:**
- [ ] Regex counts all code block end markers correctly
- [ ] Existing tests pass

**Verification:**
```bash
uv run pytest -v
```

**Dependencies:**
- None

---

#### Task impl_002: Fix extra space in regex pattern (#32)

**Priority:** High

**Description:**
Extra space between closing parenthesis and double quote in regex pattern.

**Steps:**
1. Locate the regex with extra space
2. Remove the extraneous space
3. Verify fix

**Acceptance Criteria:**
- [ ] Extra space removed from regex
- [ ] Existing tests pass

**Verification:**
```bash
uv run pytest -v
```

**Dependencies:**
- None

---

#### Task impl_003: Add missing datetime/os imports (#44)

**Priority:** High

**Description:**
Code uses datetime and os modules without importing them.

**Steps:**
1. Find code using datetime and os without imports
2. Add proper imports at top of file
3. Verify imports work correctly

**Acceptance Criteria:**
- [ ] Missing imports added
- [ ] No import errors at runtime
- [ ] Existing tests pass

**Verification:**
```bash
uv run pytest -v
```

**Dependencies:**
- None

---

### Phase 2: Documentation Fixes

#### Task doc_001: Reorder worktree cleanup commands (#34)

**Priority:** Medium

**Description:**
Move worktree cleanup commands to after archive commands for proper workflow sequence.

**Steps:**
1. Locate documentation with worktree cleanup commands
2. Move cleanup commands after archive commands
3. Verify documentation flow makes sense

**Acceptance Criteria:**
- [ ] Cleanup commands appear after archive commands
- [ ] Documentation flow is logical

**Dependencies:**
- None

---

#### Task doc_002: Add status indicators to priority list (#38)

**Priority:** Medium

**Description:**
Add status indicators to priority list for clarity.

**Steps:**
1. Find priority list in documentation
2. Add [OK], [IN_PROGRESS], [ ] indicators
3. Verify formatting is consistent

**Acceptance Criteria:**
- [ ] Status indicators added to priority list
- [ ] Formatting is consistent

**Dependencies:**
- None

---

#### Task doc_003: Document archive location (#39)

**Priority:** Medium

**Description:**
Explain where archives are located and how to extract them.

**Steps:**
1. Find relevant documentation section
2. Add explanation of ARCHIVED/ directory
3. Include extraction instructions

**Acceptance Criteria:**
- [ ] Archive location documented
- [ ] Extraction instructions included

**Dependencies:**
- None

---

#### Task doc_004: Fix blank line spacing (#41)

**Priority:** Low

**Description:**
Restore consistent blank line spacing in documentation.

**Steps:**
1. Find section with missing blank line
2. Restore blank line between sections
3. Verify formatting

**Acceptance Criteria:**
- [ ] Blank line restored
- [ ] Consistent spacing throughout

**Dependencies:**
- None

---

#### Task doc_005: Fix blank lines before Python code block (#42)

**Priority:** Low

**Description:**
Restore explanatory text and spacing before Python code block.

**Steps:**
1. Find Python code block with missing spacing
2. Restore explanatory text if needed
3. Fix blank line spacing

**Acceptance Criteria:**
- [ ] Proper spacing before code block
- [ ] Explanatory text present if needed

**Dependencies:**
- None

---

### Phase 3: Security Fixes

#### Task sec_001: Sanitize error logging (#35)

**Priority:** High

**Description:**
Sanitize error messages before logging to avoid exposing sensitive credential details.

**Steps:**
1. Find functions logging error details
2. Implement sanitization for sensitive information
3. Test that errors are still useful for debugging
4. Verify no sensitive data in logs

**Acceptance Criteria:**
- [ ] Error messages sanitized before logging
- [ ] No sensitive credentials in log output
- [ ] Errors still provide useful debugging info

**Verification:**
```bash
uv run pytest -v
```

**Dependencies:**
- None

---

#### Task sec_002: Fix emergency log path permissions (#43)

**Priority:** High

**Description:**
Change /var/log/mcp-emergency.log to user-accessible location.

**Steps:**
1. Find emergency log path configuration
2. Change to ~/.local/share/mcp/emergency.log
3. Add proper error handling for permission failures
4. Test logging works without root permissions

**Acceptance Criteria:**
- [ ] Emergency log uses user-accessible path
- [ ] Proper error handling for permission failures
- [ ] Logging works without root permissions

**Verification:**
```bash
uv run pytest -v
```

**Dependencies:**
- None

---

### Phase 4: Verification

#### Task verify_001: Run quality gates

**Priority:** High

**Description:**
Run all quality gates to ensure fixes don't break anything.

**Steps:**
1. Run full test suite
2. Run quality gates
3. Verify all gates pass

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Coverage ≥ 80%
- [ ] Linting clean
- [ ] AI Config Sync verified

**Verification:**
```bash
uv run pytest --cov=. --cov-report=term
uv run python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
```

**Dependencies:**
- All impl_*, doc_*, sec_* tasks

---

## Task Dependencies Graph

```
impl_001 ─┐
impl_002 ─┤
impl_003 ─┤
doc_001  ─┤
doc_002  ─┼─> verify_001
doc_003  ─┤
doc_004  ─┤
doc_005  ─┤
sec_001  ─┤
sec_002  ─┘
```

## Parallel Work Opportunities

All tasks in Phases 1, 2, and 3 can be done in parallel as they are independent fixes.

## Quality Checklist

Before considering this feature complete:

- [ ] All tasks marked as complete
- [ ] Test coverage ≥ 80%
- [ ] All tests passing
- [ ] Linting clean (`uv run ruff check .`)
- [ ] Quality gates pass
- [ ] All 10 issues addressed with proper "Fixes #N" commit keywords

## Notes

### Commit Strategy

Single commit with all fixes using multiple "Fixes #N" references:
```
fix: address Copilot review batch fixes

Fixes #31, Fixes #32, Fixes #34, Fixes #35, Fixes #38,
Fixes #39, Fixes #41, Fixes #42, Fixes #43, Fixes #44
```

### Implementation Tips

- Start with code bug fixes (Phase 1) as they're most likely to affect tests
- Security fixes may need careful testing to ensure errors are still useful
- Documentation fixes are low risk and can be done quickly

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes | Low | Medium | Run full test suite |
| Missing context | Medium | Low | Review original PR comments |
| Incomplete fix | Low | Low | Verify each fix manually |
