# Specification: AI Config Architecture Documentation

**Type:** feature
**Slug:** ai-config-architecture-docs
**Date:** 2024-11-24
**Author:** stharrold
**Issue:** #89

## Overview

Document the AI configuration architecture to clarify the relationship between Gemini-first development and cross-tool compatibility. This is a documentation-only feature - no code changes required.

## Requirements Reference

See: `planning/ai-config-architecture-docs/requirements.md` in main repository

## Problem Statement

The relationship between `.gemini/` (PRIMARY) and `.agents/` (mirror) is not documented:
- Contributors don't know to edit `.gemini/` instead of `.agents/`
- Other AI tools need to find instructions in `.agents/` and `AGENTS.md`
- The sync mechanism is unclear

## Detailed Specification

### Component 1: Root GEMINI.md Update

**File:** `GEMINI.md`

**Purpose:** Add comprehensive AI configuration architecture documentation at the repository root.

**Changes:**
- Add new "AI Configuration Architecture" section
- Document directory roles (`.gemini/` vs `.agents/`)
- Explain sync mechanism
- List compatible AI tools

**Content to add:**

```markdown
## AI Configuration Architecture

### Directory Structure

| Directory | Role | Editable |
|-----------|------|----------|
| `.gemini/` | PRIMARY source for AI configuration | Yes |
| `.agents/` | Read-only mirror (OpenAI agents.md spec) | No |

### Sync Mechanism

```
.gemini/                          .agents/
├── commands/    (Gemini-specific) │
├── skills/      ─────sync─────>  ├── (mirrored skills)
├── settings.local.json           │
└── GEMINI.md                     └── GEMINI.md

GEMINI.md ─────sync─────> AGENTS.md
          └────sync─────> .github/copilot-instructions.md
```

### What Gets Synced vs What Stays Gemini-Specific

| Source | Target | Synced |
|--------|--------|--------|
| `.gemini/skills/` | `.agents/` | Yes |
| `GEMINI.md` | `AGENTS.md` | Yes |
| `GEMINI.md` | `.github/copilot-instructions.md` | Yes |
| `.gemini/commands/` | - | No (Gemini-specific) |
| `.gemini/settings.local.json` | - | No (Gemini-specific) |
| `.gemini-state/` | - | No (runtime state) |

### Cross-Tool Compatibility

The `.agents/` directory follows the emerging [OpenAI agents.md spec](https://github.com/openai/agents.md).

Compatible tools:
- **Gemini Code** - Primary (reads `.gemini/` directly)
- **GitHub Copilot** - Via `.github/copilot-instructions.md`
- **Cursor** - Reads `.agents/` or `AGENTS.md`
- **Windsurf** - Reads `AGENTS.md`
- **Other AI assistants** - Via standard `AGENTS.md`
```

### Component 2: .gemini/GEMINI.md Update

**File:** `.gemini/GEMINI.md`

**Purpose:** Explicitly state that `.gemini/` is the PRIMARY source.

**Changes:**
- Add PRIMARY source statement
- List what gets mirrored vs what stays

**Content to add:**

```markdown
## Source Status

**This directory (`.gemini/`) is the PRIMARY source for AI configuration.**

Changes made here sync to:
- `.agents/` (skills only)
- `AGENTS.md` (from root GEMINI.md)
- `.github/copilot-instructions.md` (from root GEMINI.md)

Gemini-specific content (NOT synced):
- `commands/` - Gemini Code slash commands
- `settings.local.json` - Local settings
```

### Component 3: .agents/GEMINI.md Update

**File:** `.agents/GEMINI.md`

**Purpose:** Reference OpenAI spec and list compatible tools.

**Changes:**
- Add OpenAI agents.md spec reference
- List tools that read this directory
- Clear "read-only mirror" statement

**Content to add:**

```markdown
## Directory Status

**This directory (`.agents/`) is a READ-ONLY mirror of `.gemini/skills/`.**

Do NOT edit files here. Edit `.gemini/` instead.

### Specification

This directory follows the [OpenAI agents.md specification](https://github.com/openai/agents.md).

See also: [Directory support proposal](https://github.com/openai/agents.md/issues/9)

### Compatible Tools

Tools that read this directory:
- **Cursor** - Reads `.agents/` or `AGENTS.md`
- **Windsurf** - Reads `AGENTS.md`
- **Other AI coding assistants** - Following the agents.md spec

Gemini Code reads `.gemini/` directly (does not use this mirror).
```

### Component 4: CONTRIBUTING.md Update

**File:** `CONTRIBUTING.md`

**Purpose:** Guide contributors on AI configuration editing.

**Changes:**
- Add "AI Configuration Guidelines" section
- Clear "edit .gemini/, not .agents/" rule

**Content to add:**

```markdown
## AI Configuration Guidelines

### Where to Make Changes

| To change... | Edit this | NOT this |
|--------------|-----------|----------|
| Skills | `.gemini/skills/` | `.agents/` |
| Commands | `.gemini/commands/` | N/A |
| Root instructions | `GEMINI.md` | `AGENTS.md` |

### Why?

- `.gemini/` is the **PRIMARY** source
- `.agents/` is automatically synced (read-only mirror)
- `AGENTS.md` is automatically generated from `GEMINI.md`

Changes to `.agents/` or `AGENTS.md` will be overwritten on next sync.

### Sync Mechanism

The sync happens:
1. **Pre-commit hook** - `sync-ai-config` runs automatically
2. **Manual** - `uv run python .gemini/skills/workflow-utilities/scripts/sync_ai_config.py sync`
3. **PR workflow** - `pr_workflow.py sync-agents` during integration
```

### Component 5: README.md Update

**File:** `README.md`

**Purpose:** Mention cross-tool compatibility.

**Changes:**
- Add bullet point in features/capabilities section

**Content to add:**

```markdown
- **Cross-tool AI compatibility** - Configuration syncs to `.agents/` (OpenAI spec) and `.github/copilot-instructions.md` for Cursor, Windsurf, GitHub Copilot, and other AI assistants
```

## Testing Requirements

### Verification Steps

1. **GEMINI.md** - Verify "AI Configuration Architecture" section exists
2. **.gemini/GEMINI.md** - Verify PRIMARY source statement
3. **.agents/GEMINI.md** - Verify OpenAI spec reference and tools list
4. **CONTRIBUTING.md** - Verify AI configuration guidelines section
5. **README.md** - Verify cross-tool compatibility mention

### Quality Gates

- [ ] All acceptance criteria from requirements.md met
- [ ] Linting clean (`ruff check .`)
- [ ] AI Config sync passes (`sync_ai_config.py verify`)
- [ ] No broken markdown links

## Dependencies

None - documentation only feature.

## References

- [OpenAI agents.md spec](https://github.com/openai/agents.md)
- [Directory support proposal](https://github.com/openai/agents.md/issues/9)
- [GitHub Issue #89](https://github.com/stharrold/stharrold-templates/issues/89)
