---
type: claude-context
directory: specs/ascii-only-output
purpose: Specifications for ASCII-only output feature - replacing Unicode symbols with ASCII equivalents
parent: ../CLAUDE.md
sibling_readme: README.md
children: []
---

# Claude Code Context: ascii-only-output

## Purpose

This directory contains specifications for the ASCII-only output feature (#102).

## Contents

- `spec.md` - Technical specification
- `plan.md` - Implementation plan with task breakdown
- `README.md` - Human-readable overview
- `CLAUDE.md` - This file

## Feature Summary

Replace Unicode symbols with ASCII equivalents in all workflow scripts:
- `[OK]` instead of checkmark
- `[FAIL]` instead of cross
- `[WARN]` instead of warning symbol
- `->` instead of arrow

## Key Files to Modify

1. `.claude/skills/workflow-utilities/scripts/safe_output.py` - Central output utilities
2. Scripts with direct Unicode: `initialize_repository.py`, `create_planning.py`, `create_specifications.py`, etc.

## Related

- **Parent**: [specs](../CLAUDE.md)
- **Issue**: #102
- **Planning**: `planning/ascii-only-output/`
