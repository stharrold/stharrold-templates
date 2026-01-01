# Requirements: Copilot Review Batch Fix

**Issue**: #104
**Slug**: copilot-review-batch-fix
**Status**: Draft

## Problem Statement

Multiple Copilot code review comments from PRs #30, #33, #37, #40 remain open as GitHub issues. These are mostly nitpicks and minor fixes that should be addressed in a batch to maintain code quality.

## Issues to Address

| Issue | Source PR | Category | Description |
|-------|-----------|----------|-------------|
| #31 | #30 | Bug | Code block end markers counting logic incorrect |
| #32 | #30 | Bug | Extra space in regex pattern |
| #34 | #33 | Doc | Worktree cleanup commands placement |
| #35 | #33 | Security | Sensitive error information logging |
| #38 | #37 | Doc | Priority list status indicators |
| #39 | #37 | Doc | Archive location documentation |
| #41 | #40 | Doc | Blank line spacing in docs |
| #42 | #40 | Doc | Blank lines before Python code block |
| #43 | #40 | Security | Emergency log path permissions |
| #44 | #40 | Bug | Missing datetime/os imports |

## Functional Requirements

### FR-1: Fix Code Block Counting (#31)

The regex for counting code block end markers is incorrect. It only counts bare closing markers but not language-specific closings.

### FR-2: Fix Regex Pattern (#32)

Extra space between closing parenthesis and double quote in regex pattern.

### FR-3: Reorder Worktree Cleanup (#34)

Move worktree cleanup commands to after archive commands for proper workflow sequence.

### FR-4: Sanitize Error Logging (#35)

Sanitize error messages before logging to avoid exposing sensitive credential details.

### FR-5: Add Status Indicators (#38)

Add status indicators to priority list for clarity.

### FR-6: Document Archive Location (#39)

Explain where archives are located and how to extract them.

### FR-7: Fix Doc Formatting (#41, #42)

Restore consistent blank line spacing in documentation.

### FR-8: Fix Emergency Log Path (#43)

Use user-accessible log location instead of /var/log/.

### FR-9: Add Missing Imports (#44)

Add datetime and os module imports.

## Non-Functional Requirements

### NFR-1: Backward Compatibility

- No changes to script functionality beyond fixes
- No changes to exit codes
- All existing tests must pass

### NFR-2: Minimal Changes

- Only modify what's necessary to fix each issue
- Preserve existing logic where possible

## Acceptance Criteria

1. All 10 issues addressed with proper "Fixes #N" commit keywords
2. All tests pass
3. Quality gates pass
4. Changes merged to main via PR workflow
