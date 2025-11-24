# Epics: AI Config Architecture Documentation

## Epic 1: Document Root Architecture

**Goal**: Add comprehensive AI configuration architecture section to CLAUDE.md

**Stories**:
- Add "AI Configuration Architecture" section
- Include Claude-first development statement
- Add directory roles table (.claude/ vs .agents/)
- Document what syncs vs what stays Claude-specific

## Epic 2: Update Directory Context Files

**Goal**: Ensure .claude/CLAUDE.md and .agents/CLAUDE.md clearly explain their roles

**Stories**:
- .claude/CLAUDE.md: Add PRIMARY source statement
- .claude/CLAUDE.md: List what gets mirrored vs what stays
- .agents/CLAUDE.md: Add OpenAI agents.md spec reference
- .agents/CLAUDE.md: List compatible AI tools

## Epic 3: Update Contributor Documentation

**Goal**: Ensure contributors know where to make changes

**Stories**:
- CONTRIBUTING.md: Add "AI Configuration Guidelines" section
- CONTRIBUTING.md: Clear "edit .claude/, not .agents/" rule
- README.md: Add cross-tool compatibility mention

## Task Breakdown

| Task | Epic | File | Description |
|------|------|------|-------------|
| T001 | 1 | CLAUDE.md | Add AI Configuration Architecture section |
| T002 | 2 | .claude/CLAUDE.md | Add PRIMARY source statement |
| T003 | 2 | .agents/CLAUDE.md | Add spec reference and tools list |
| T004 | 3 | CONTRIBUTING.md | Add AI configuration guidelines |
| T005 | 3 | README.md | Add cross-tool compatibility bullet |
| T006 | - | - | Sync and verify |
