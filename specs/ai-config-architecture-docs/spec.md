# Specification: AI Config Architecture Documentation

**Type:** feature
**Slug:** ai-config-architecture-docs
**Date:** 2024-11-24
**Author:** stharrold
**Issue:** #89

## Overview

Document the AI configuration architecture to clarify the relationship between Claude-first development and cross-tool compatibility. This is a documentation-only feature - no code changes required.

## Requirements Reference

See: `planning/ai-config-architecture-docs/requirements.md` in main repository

## Problem Statement

The relationship between `.claude/` (PRIMARY) and `.agents/` (mirror) is not documented:
- Contributors don't know to edit `.claude/` instead of `.agents/`
- Other AI tools need to find instructions in `.agents/` and `AGENTS.md`
- The sync mechanism is unclear

## Detailed Specification

### Component 1: Root CLAUDE.md Update

**File:** `CLAUDE.md`

**Purpose:** Add comprehensive AI configuration architecture documentation at the repository root.

**Changes:**
- Add new "AI Configuration Architecture" section
- Document directory roles (`.claude/` vs `.agents/`)
- Explain sync mechanism
- List compatible AI tools

**Content to add:**

```markdown
## AI Configuration Architecture

### Directory Structure

| Directory | Role | Editable |
|-----------|------|----------|
| `.claude/` | PRIMARY source for AI configuration | Yes |
| `.agents/` | Read-only mirror (OpenAI agents.md spec) | No |

### Sync Mechanism

```
.claude/                          .agents/
├── commands/    (Claude-specific) │
├── skills/      ─────sync─────>  ├── (mirrored skills)
├── settings.local.json           │
└── CLAUDE.md                     └── CLAUDE.md

CLAUDE.md ─────sync─────> AGENTS.md
          └────sync─────> .github/copilot-instructions.md
```

### What Gets Synced vs What Stays Claude-Specific

| Source | Target | Synced |
|--------|--------|--------|
| `.claude/skills/` | `.agents/` | Yes |
| `CLAUDE.md` | `AGENTS.md` | Yes |
| `CLAUDE.md` | `.github/copilot-instructions.md` | Yes |
| `.claude/commands/` | - | No (Claude-specific) |
| `.claude/settings.local.json` | - | No (Claude-specific) |
| `.claude-state/` | - | No (runtime state) |

### Cross-Tool Compatibility

The `.agents/` directory follows the emerging [OpenAI agents.md spec](https://github.com/openai/agents.md).

Compatible tools:
- **Claude Code** - Primary (reads `.claude/` directly)
- **GitHub Copilot** - Via `.github/copilot-instructions.md`
- **Cursor** - Reads `.agents/` or `AGENTS.md`
- **Windsurf** - Reads `AGENTS.md`
- **Other AI assistants** - Via standard `AGENTS.md`
```

### Component 2: .claude/CLAUDE.md Update

**File:** `.claude/CLAUDE.md`

**Purpose:** Explicitly state that `.claude/` is the PRIMARY source.

**Changes:**
- Add PRIMARY source statement
- List what gets mirrored vs what stays

**Content to add:**

```markdown
## Source Status

**This directory (`.claude/`) is the PRIMARY source for AI configuration.**

Changes made here sync to:
- `.agents/` (skills only)
- `AGENTS.md` (from root CLAUDE.md)
- `.github/copilot-instructions.md` (from root CLAUDE.md)

Claude-specific content (NOT synced):
- `commands/` - Claude Code slash commands
- `settings.local.json` - Local settings
```

### Component 3: .agents/CLAUDE.md Update

**File:** `.agents/CLAUDE.md`

**Purpose:** Reference OpenAI spec and list compatible tools.

**Changes:**
- Add OpenAI agents.md spec reference
- List tools that read this directory
- Clear "read-only mirror" statement

**Content to add:**

```markdown
## Directory Status

**This directory (`.agents/`) is a READ-ONLY mirror of `.claude/skills/`.**

Do NOT edit files here. Edit `.claude/` instead.

### Specification

This directory follows the [OpenAI agents.md specification](https://github.com/openai/agents.md).

See also: [Directory support proposal](https://github.com/openai/agents.md/issues/9)

### Compatible Tools

Tools that read this directory:
- Cursor
- Windsurf
- Other AI coding assistants following the agents.md spec

Claude Code reads `.claude/` directly (does not use this mirror).
```

### Component 4: CONTRIBUTING.md Update

**File:** `CONTRIBUTING.md`

**Purpose:** Guide contributors on AI configuration editing.

**Changes:**
- Add "AI Configuration Guidelines" section
- Clear "edit .claude/, not .agents/" rule

**Content to add:**

```markdown
## AI Configuration Guidelines

### Where to Make Changes

| To change... | Edit this | NOT this |
|--------------|-----------|----------|
| Skills | `.claude/skills/` | `.agents/` |
| Commands | `.claude/commands/` | N/A |
| Root instructions | `CLAUDE.md` | `AGENTS.md` |

### Why?

- `.claude/` is the **PRIMARY** source
- `.agents/` is automatically synced (read-only mirror)
- `AGENTS.md` is automatically generated from `CLAUDE.md`

Changes to `.agents/` or `AGENTS.md` will be overwritten on next sync.

### Sync Mechanism

The sync happens:
1. **Pre-commit hook** - `sync-ai-config` runs automatically
2. **Manual** - `uv run python .claude/skills/workflow-utilities/scripts/sync_ai_config.py sync`
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

1. **CLAUDE.md** - Verify "AI Configuration Architecture" section exists
2. **.claude/CLAUDE.md** - Verify PRIMARY source statement
3. **.agents/CLAUDE.md** - Verify OpenAI spec reference and tools list
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
