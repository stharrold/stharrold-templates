# Architecture: AI Config Documentation

## Overview

This is a documentation-only feature. No code changes required.

## Current Architecture

```
.gemini/                          .agents/
├── commands/    (Gemini-specific) │
├── skills/      ─────sync─────>  ├── (mirrored skills)
├── settings.local.json           │
└── GEMINI.md                     └── GEMINI.md

GEMINI.md ─────sync─────> AGENTS.md
          └────sync─────> .github/copilot-instructions.md
```

## Sync Mechanism

1. **Pre-commit hook**: `sync-ai-config` runs on commit
2. **Manual sync**: `uv run python .gemini/skills/workflow-utilities/scripts/sync_ai_config.py sync`
3. **PR workflow**: `pr_workflow.py sync-agents` during `/5_integrate`

## What Gets Synced

| Source | Target | Synced |
|--------|--------|--------|
| `.gemini/skills/` | `.agents/` | ✅ Yes |
| `GEMINI.md` | `AGENTS.md` | ✅ Yes |
| `GEMINI.md` | `.github/copilot-instructions.md` | ✅ Yes |
| `.gemini/commands/` | - | ❌ No (Gemini-specific) |
| `.gemini/settings.local.json` | - | ❌ No (Gemini-specific) |
| `.gemini-state/` | - | ❌ No (runtime state) |

## Cross-Tool Compatibility

The `.agents/` directory follows the emerging OpenAI agents.md spec:
- https://github.com/openai/agents.md
- Issue #9 proposes directory support

Compatible tools:
- GitHub Copilot (via `.github/copilot-instructions.md`)
- Cursor (reads `.agents/` or `AGENTS.md`)
- Windsurf (reads `AGENTS.md`)
- Other AI coding assistants
