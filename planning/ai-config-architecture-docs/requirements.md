# Requirements: AI Config Architecture Documentation

## GitHub Issue

- **Issue**: #89
- **Title**: docs: Document AI configuration architecture (GEMINI.md/AGENTS.md relationship)

## Problem Statement

The relationship between Gemini-first development and cross-tool compatibility is not clearly documented:
- `.gemini/` is PRIMARY source, `.agents/` is read-only mirror
- `GEMINI.md` syncs to `AGENTS.md` and `.github/copilot-instructions.md`
- What gets synced vs what stays Gemini-specific is unclear

## User Stories

1. As a **contributor**, I need to know to edit `.gemini/` not `.agents/` so my changes persist
2. As an **AI tool** (Cursor, Windsurf, Copilot), I need to find instructions in `.agents/` and `AGENTS.md`
3. As a **new user**, I need to understand the Gemini-first development model
4. As a **repository maintainer**, I need clear documentation of the sync architecture

## Acceptance Criteria

- [ ] GEMINI.md has "AI Configuration Architecture" section explaining the relationship
- [ ] .gemini/GEMINI.md states it's the PRIMARY source
- [ ] .agents/GEMINI.md references OpenAI agents.md spec and lists compatible tools
- [ ] CONTRIBUTING.md has "edit .gemini/, not .agents/" guidance
- [ ] README.md mentions cross-tool compatibility

## Files to Update

| File | Change |
|------|--------|
| `GEMINI.md` | Add "AI Configuration Architecture" section |
| `.gemini/GEMINI.md` | Add PRIMARY source statement, what gets mirrored |
| `.agents/GEMINI.md` | Add OpenAI spec reference, compatible tools list |
| `CONTRIBUTING.md` | Add AI configuration guidelines section |
| `README.md` | Add cross-tool compatibility bullet |

## References

- OpenAI agents.md spec: https://github.com/openai/agents.md
- Directory support proposal: https://github.com/openai/agents.md/issues/9
