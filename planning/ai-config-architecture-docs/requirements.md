# Requirements: AI Config Architecture Documentation

## GitHub Issue

- **Issue**: #89
- **Title**: docs: Document AI configuration architecture (CLAUDE.md/AGENTS.md relationship)

## Problem Statement

The relationship between Claude-first development and cross-tool compatibility is not clearly documented:
- `.claude/` is PRIMARY source, `.agents/` is read-only mirror
- `CLAUDE.md` syncs to `AGENTS.md` and `.github/copilot-instructions.md`
- What gets synced vs what stays Claude-specific is unclear

## User Stories

1. As a **contributor**, I need to know to edit `.claude/` not `.agents/` so my changes persist
2. As an **AI tool** (Cursor, Windsurf, Copilot), I need to find instructions in `.agents/` and `AGENTS.md`
3. As a **new user**, I need to understand the Claude-first development model
4. As a **repository maintainer**, I need clear documentation of the sync architecture

## Acceptance Criteria

- [ ] CLAUDE.md has "AI Configuration Architecture" section explaining the relationship
- [ ] .claude/CLAUDE.md states it's the PRIMARY source
- [ ] .agents/CLAUDE.md references OpenAI agents.md spec and lists compatible tools
- [ ] CONTRIBUTING.md has "edit .claude/, not .agents/" guidance
- [ ] README.md mentions cross-tool compatibility

## Files to Update

| File | Change |
|------|--------|
| `CLAUDE.md` | Add "AI Configuration Architecture" section |
| `.claude/CLAUDE.md` | Add PRIMARY source statement, what gets mirrored |
| `.agents/CLAUDE.md` | Add OpenAI spec reference, compatible tools list |
| `CONTRIBUTING.md` | Add AI configuration guidelines section |
| `README.md` | Add cross-tool compatibility bullet |

## References

- OpenAI agents.md spec: https://github.com/openai/agents.md
- Directory support proposal: https://github.com/openai/agents.md/issues/9
