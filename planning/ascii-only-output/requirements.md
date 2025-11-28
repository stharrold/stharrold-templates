# Requirements: ASCII-Only Output

**Issue**: #102
**Slug**: ascii-only-output
**Status**: Draft

## Problem Statement

Unicode characters (checkmarks, symbols, emojis) in script output cause errors on:
- Legacy systems without Unicode support
- Windows terminals with encoding issues (cp1252, etc.)
- CI/CD environments with limited character sets
- SSH sessions with misconfigured locales

## Functional Requirements

### FR-1: Replace Unicode Symbols with ASCII

All workflow scripts must use ASCII-only characters for output:

| Current Unicode | ASCII Replacement |
|-----------------|-------------------|
| `✓` (U+2713)    | `[OK]` or `[PASS]` |
| `✗` (U+2717)    | `[FAIL]` or `[ERROR]` |
| `⚠` (U+26A0)    | `[WARN]` |
| `→` (U+2192)    | `->` or `-->` |
| Emojis          | Remove or use text labels |

### FR-2: Maintain Readability

Output must remain clear and scannable:
- Status indicators clearly visible
- Progress steps distinguishable
- Error messages prominent

### FR-3: Consistent Style

All scripts must use the same ASCII conventions for consistency.

## Non-Functional Requirements

### NFR-1: Backward Compatibility

- No changes to script functionality
- No changes to exit codes
- No changes to file output formats

### NFR-2: Minimal Changes

- Only modify print/output statements
- Preserve existing logic

## User Stories

### US-1: Windows User

As a Windows user with default terminal settings, I want workflow scripts to display correctly so that I can see status messages without encoding errors.

### US-2: CI/CD Pipeline

As a CI/CD system, I want ASCII-only output so that logs are readable regardless of encoding configuration.

### US-3: Legacy System User

As a user on a legacy system, I want scripts to work without requiring UTF-8 support.

## Acceptance Criteria

1. All workflow scripts produce ASCII-only output
2. No `UnicodeEncodeError` on Windows with default settings
3. Output remains readable and clear
4. All existing tests pass
