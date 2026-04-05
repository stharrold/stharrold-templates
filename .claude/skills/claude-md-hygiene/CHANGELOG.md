# Changelog

## [1.0.0] - 2026-04-05

### Added
- Initial `claude-md-hygiene` skill with `audit_claude_md.py` linter.
- Rubric: files must earn their existence (non-obvious content, <=500 lines,
  no dated headers, no stub pattern, no duplication with SKILL.md/code).
- `--strict` mode for CI failure on stub or oversized files.
- `--root <dir>` flag for scoped scans.
