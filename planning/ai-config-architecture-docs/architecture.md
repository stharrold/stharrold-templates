# Architecture: AI Config Documentation

## Overview

This is a documentation-only feature. No code changes required.

## Current Architecture

```
.claude/                          .agents/
├── commands/    (Claude-specific) │
├── skills/      ─────sync─────>  ├── (mirrored skills)
├── settings.local.json           │
└── CLAUDE.md                     └── CLAUDE.md

CLAUDE.md ─────sync─────> AGENTS.md
          └────sync─────> .github/copilot-instructions.md
```

## Sync Mechanism

1. **Pre-commit hook**: `sync-ai-config` runs on commit
2. **Manual sync**: `uv run python .claude/skills/workflow-utilities/scripts/sync_ai_config.py sync`
3. **PR workflow**: `pr_workflow.py sync-agents` during `/5_integrate`

## What Gets Synced

| Source | Target | Synced |
|--------|--------|--------|
| `.claude/skills/` | `.agents/` | ✅ Yes |
| `CLAUDE.md` | `AGENTS.md` | ✅ Yes |
| `CLAUDE.md` | `.github/copilot-instructions.md` | ✅ Yes |
| `.claude/commands/` | - | ❌ No (Claude-specific) |
| `.claude/settings.local.json` | - | ❌ No (Claude-specific) |
| `.claude-state/` | - | ❌ No (runtime state) |

## Cross-Tool Compatibility

The `.agents/` directory follows the emerging OpenAI agents.md spec:
- https://github.com/openai/agents.md
- Issue #9 proposes directory support

Compatible tools:
- GitHub Copilot (via `.github/copilot-instructions.md`)
- Cursor (reads `.agents/` or `AGENTS.md`)
- Windsurf (reads `AGENTS.md`)
- Other AI coding assistants
