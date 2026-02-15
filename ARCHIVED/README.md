# Archived Files

This directory contains archived (deprecated) files that are no longer in active use.

Files are stored in timestamped zip archives for potential recovery.

## Archive Manifest

### 2025-12-29: Workflow v7x1 Migration

| Archive | Contents |
|---------|----------|
| `20251229T003405Z_v1-v7-workflow-commands.zip` | Old slash commands (v1-v7), replaced by v7x1 workflow |
| `20251229T003500Z_bmad-planner.zip` | BMAD planning skill, replaced by autonomous implementation |
| `20251229T003500Z_quality-enforcer.zip` | Quality gate skill, replaced by Claude Code Review |
| `20251229T003500Z_speckit-author.zip` | SpecKit specification skill, replaced by autonomous implementation |
| `20251229T004300Z_quality-enforcer-tests.zip` | Tests for deprecated quality-enforcer skill |
| `20251229T032905Z_planning.zip` | Planning docs for 7 features |
| `20251229T151018Z_specify.zip` | .specify framework, deprecated since v5.12.0 |
| `20251229T151643Z_legacy_bash_scripts.zip` | 6 bash test scripts, obsolete |

### 2026-01-01: Repository Cleanup

| Archive | Contents |
|---------|----------|
| `20260101T233947Z_planning.zip` | Second round of planning docs cleanup |
| `20260101T233947Z_specs.zip` | Specification documents cleanup |

### 2026-01-02: Major Cleanup

| Archive | Contents |
|---------|----------|
| `20260102T000712Z_ARCHITECTURE_v5.3.md.zip` | ARCHITECTURE.md v5.3, replaced by modular docs |
| `20260102T001518Z_AGENTS.md.zip` | AGENTS.md placeholder (114 bytes) |
| `20260102T001638Z_AGENTS.md.zip` | AGENTS.md full content |
| `20260102T001700Z_remove-agents-md.zip` | Removal commit for AGENTS.md |
| `20260102T001950Z_deprecated-specify.zip` | Deprecated specify framework |
| `20260102T002049Z_migrate-to-feature-dev.zip` | Feature development migration artifacts |
| `20260102T002118Z_archive-quality-enforcer.zip` | Quality enforcer archive |
| `20260102T002250Z_deprecated-dist.zip` | Deprecated dist/ build artifacts |
| `20260102T002302Z_deprecated-egg-info.zip` | Deprecated .egg-info metadata |
| `20260102T002304Z_deprecated-claude.zip` | Deprecated .claude config (22 bytes) |
| `20260102T002312Z_deprecated-sh-scripts.zip` | Deprecated shell scripts |
| `20260102T002315Z_deprecated-codacy.zip` | Codacy CLI and configs, replaced by ruff + pre-commit |
| `20260102T002356Z_deprecated-mcp-manager.zip` | MCP manager utility |
| `20260102T004424Z_cleanup-commit-msg.zip` | Cleanup commit message |

### 2026-01-18: Gemini Config Cleanup

| Archive | Contents |
|---------|----------|
| `20260118T165035Z_remove-redundant-gemini-configs.zip` | Redundant Gemini configuration files |
| `20260118T165117Z_remove-remaining-gemini-workflows.zip` | Remaining Gemini workflow files |

## Restoration

Use `archive_manager.py` to list and extract archived files:

```bash
# List archives
uv run python .claude/skills/workflow-utilities/scripts/archive_manager.py list

# Extract specific archive
uv run python .claude/skills/workflow-utilities/scripts/archive_manager.py extract ARCHIVED/<archive>.zip
```
