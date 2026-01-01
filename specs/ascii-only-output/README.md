# ASCII-Only Output

**Issue:** #102
**Status:** In Progress
**Type:** Feature (PATCH version bump)

## Overview

Replace Unicode symbols with ASCII equivalents in all workflow scripts to ensure compatibility with:
- Legacy systems without Unicode support
- Windows terminals with encoding issues (cp1252)
- CI/CD environments with limited character sets
- SSH sessions with misconfigured locales

## Symbol Mapping

| Unicode | ASCII | Context |
|---------|-------|---------|
| `[checkmark]` | `[OK]` | Success status |
| `[cross]` | `[FAIL]` | Error status |
| `[warning]` | `[WARN]` | Warning status |
| `[arrow]` | `->` | Arrows |

## Files

- `spec.md` - Technical specification
- `plan.md` - Implementation plan with tasks
- `GEMINI.md` - AI context

## Implementation

The primary change is in `.gemini/skills/workflow-utilities/scripts/safe_output.py`:
- Remove UTF-8 detection logic
- Use ASCII symbols directly
- Simplify `safe_print()` function

Secondary changes: Update all scripts that use direct Unicode print statements.

## Testing

1. Run existing tests: `uv run pytest`
2. Test with ASCII encoding: `PYTHONIOENCODING=ascii uv run python script.py`
3. Run quality gates

## References

- Planning: `planning/ascii-only-output/`
- GitHub Issue: #102
