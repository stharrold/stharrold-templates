# Archived Files

This directory contains archived (deprecated) files that are no longer in active use.

Files are stored in timestamped zip archives for potential recovery.

## Archive Manifest

| Archive | Date | Reason | Contents |
|---------|------|--------|----------|
| `20251229T003405Z_v1-v7-workflow-commands.zip` | 2025-12-29 | Replaced by v6 workflow | Old slash commands (v1-v7) |
| `20251229T003500Z_bmad-planner.zip` | 2025-12-29 | Replaced by feature-dev plugin | BMAD planning skill |
| `20251229T003500Z_quality-enforcer.zip` | 2025-12-29 | Replaced by feature-dev plugin | Quality gate skill |
| `20251229T003500Z_speckit-author.zip` | 2025-12-29 | Replaced by feature-dev plugin | SpecKit specification skill |
| `20251229T004300Z_quality-enforcer-tests.zip` | 2025-12-29 | Tests for deprecated skill | Quality enforcer tests |
| `20251229T032904Z_specs.zip` | 2025-12-29 | Replaced by feature-dev plugin | 8 feature specs (001-008) |
| `20251229T032905Z_planning.zip` | 2025-12-29 | Replaced by feature-dev plugin | Planning docs for 7 features |
| `20251229T151018Z_specify.zip` | 2025-12-29 | Deprecated since v5.12.0 | .specify framework |
| `20251229T151643Z_legacy_bash_scripts.zip` | 2025-12-29 | Obsolete, non-functional | 6 bash test scripts |
| `20251229T151742Z_codacy.zip` | 2025-12-29 | Replaced by ruff + pre-commit | Codacy CLI and configs |

## Restoration

Use `archive_manager.py` to list and extract archived files:

```bash
# List archives
uv run python .gemini/skills/workflow-utilities/scripts/archive_manager.py list

# Extract specific archive
uv run python .gemini/skills/workflow-utilities/scripts/archive_manager.py extract ARCHIVED/<archive>.zip
```
