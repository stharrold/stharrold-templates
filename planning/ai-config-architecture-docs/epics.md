# Epics: AI Config Architecture Documentation

## Epic 1: Document Root Architecture

**Goal**: Add comprehensive AI configuration architecture section to GEMINI.md

**Stories**:
- Add "AI Configuration Architecture" section
- Include Gemini-first development statement
- Add directory roles table (.gemini/ vs .agents/)
- Document what syncs vs what stays Gemini-specific

## Epic 2: Update Directory Context Files

**Goal**: Ensure .gemini/GEMINI.md and .agents/GEMINI.md clearly explain their roles

**Stories**:
- .gemini/GEMINI.md: Add PRIMARY source statement
- .gemini/GEMINI.md: List what gets mirrored vs what stays
- .agents/GEMINI.md: Add OpenAI agents.md spec reference
- .agents/GEMINI.md: List compatible AI tools

## Epic 3: Update Contributor Documentation

**Goal**: Ensure contributors know where to make changes

**Stories**:
- CONTRIBUTING.md: Add "AI Configuration Guidelines" section
- CONTRIBUTING.md: Clear "edit .gemini/, not .agents/" rule
- README.md: Add cross-tool compatibility mention

## Task Breakdown

| Task | Epic | File | Description |
|------|------|------|-------------|
| T001 | 1 | GEMINI.md | Add AI Configuration Architecture section |
| T002 | 2 | .gemini/GEMINI.md | Add PRIMARY source statement |
| T003 | 2 | .agents/GEMINI.md | Add spec reference and tools list |
| T004 | 3 | CONTRIBUTING.md | Add AI configuration guidelines |
| T005 | 3 | README.md | Add cross-tool compatibility bullet |
| T006 | - | - | Sync and verify |
