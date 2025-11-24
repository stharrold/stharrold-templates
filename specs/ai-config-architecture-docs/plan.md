# Implementation Plan: AI Config Architecture Documentation

**Type:** feature
**Slug:** ai-config-architecture-docs
**Date:** 2024-11-24
**Issue:** #89

## Task Breakdown

### Phase 1: Root Documentation

#### Task doc_001: Add AI Configuration Architecture section to CLAUDE.md

**Priority:** High

**Files:**
- `CLAUDE.md`

**Description:**
Add comprehensive "AI Configuration Architecture" section to root CLAUDE.md explaining the relationship between `.claude/` and `.agents/`.

**Steps:**
1. Locate the appropriate section in CLAUDE.md (after "Core Architecture" or "Reference Documentation")
2. Add "AI Configuration Architecture" section with:
   - Directory roles table
   - Sync diagram
   - What syncs vs stays Claude-specific table
   - Cross-tool compatibility list
3. Verify markdown renders correctly

**Acceptance Criteria:**
- [ ] Section titled "AI Configuration Architecture" exists
- [ ] Directory roles table present (.claude/ vs .agents/)
- [ ] Sync diagram shows flow from .claude/ to .agents/
- [ ] Compatible tools listed (Cursor, Windsurf, Copilot)
- [ ] OpenAI agents.md spec referenced

**Verification:**
```bash
grep -q "AI Configuration Architecture" CLAUDE.md && echo "OK: Section exists"
grep -q "agents.md" CLAUDE.md && echo "OK: Spec referenced"
```

**Dependencies:**
- None

---

### Phase 2: Directory Context Files

#### Task doc_002: Add PRIMARY source statement to .claude/CLAUDE.md

**Priority:** High

**Files:**
- `.claude/CLAUDE.md`

**Description:**
Update .claude/CLAUDE.md to explicitly state it is the PRIMARY source for AI configuration.

**Steps:**
1. Read current .claude/CLAUDE.md content
2. Add "Source Status" section after "Purpose"
3. State PRIMARY source status
4. List what syncs and what stays Claude-specific

**Acceptance Criteria:**
- [ ] "PRIMARY source" statement present
- [ ] Lists synced targets (.agents/, AGENTS.md, copilot-instructions.md)
- [ ] Lists Claude-specific content (commands/, settings.local.json)

**Verification:**
```bash
grep -q "PRIMARY" .claude/CLAUDE.md && echo "OK: PRIMARY statement exists"
```

**Dependencies:**
- None

---

#### Task doc_003: Add OpenAI spec reference to .agents/CLAUDE.md

**Priority:** High

**Files:**
- `.agents/CLAUDE.md`

**Description:**
Update .agents/CLAUDE.md to reference OpenAI agents.md spec and list compatible tools.

**Steps:**
1. Read current .agents/CLAUDE.md content
2. Add "Directory Status" section
3. Add "READ-ONLY mirror" warning
4. Add OpenAI spec reference link
5. List compatible AI tools

**Acceptance Criteria:**
- [ ] "READ-ONLY mirror" statement present
- [ ] OpenAI agents.md spec link included
- [ ] Directory support proposal issue #9 referenced
- [ ] Compatible tools listed (Cursor, Windsurf, etc.)

**Verification:**
```bash
grep -q "READ-ONLY" .agents/CLAUDE.md && echo "OK: Read-only statement exists"
grep -q "openai/agents.md" .agents/CLAUDE.md && echo "OK: Spec link exists"
```

**Dependencies:**
- None

---

### Phase 3: Contributor Documentation

#### Task doc_004: Add AI configuration guidelines to CONTRIBUTING.md

**Priority:** Medium

**Files:**
- `CONTRIBUTING.md`

**Description:**
Add "AI Configuration Guidelines" section to CONTRIBUTING.md with clear editing rules.

**Steps:**
1. Read current CONTRIBUTING.md content
2. Find appropriate location (after main contributing guidelines)
3. Add "AI Configuration Guidelines" section
4. Add "Where to Make Changes" table
5. Explain why (sync mechanism)

**Acceptance Criteria:**
- [ ] Section titled "AI Configuration Guidelines" exists
- [ ] "Where to Make Changes" table present
- [ ] Clear "edit .claude/, not .agents/" guidance
- [ ] Sync mechanism explained

**Verification:**
```bash
grep -q "AI Configuration Guidelines" CONTRIBUTING.md && echo "OK: Section exists"
grep -q "edit .claude/" CONTRIBUTING.md && echo "OK: Edit guidance exists"
```

**Dependencies:**
- None

---

#### Task doc_005: Add cross-tool compatibility to README.md

**Priority:** Medium

**Files:**
- `README.md`

**Description:**
Add bullet point mentioning cross-tool AI compatibility in README.md.

**Steps:**
1. Read current README.md content
2. Locate features or capabilities section
3. Add bullet point about cross-tool compatibility
4. Mention OpenAI spec and compatible tools

**Acceptance Criteria:**
- [ ] Cross-tool compatibility mentioned
- [ ] .agents/ and AGENTS.md referenced
- [ ] Compatible tools listed

**Verification:**
```bash
grep -q "Cross-tool" README.md && echo "OK: Cross-tool mention exists"
```

**Dependencies:**
- None

---

### Phase 4: Verification and Sync

#### Task doc_006: Run sync and verify

**Priority:** High

**Files:**
- All modified files

**Description:**
Run AI config sync and verify all files are in sync.

**Steps:**
1. Run sync: `uv run python .claude/skills/workflow-utilities/scripts/sync_ai_config.py sync`
2. Verify: `uv run python .claude/skills/workflow-utilities/scripts/sync_ai_config.py verify`
3. Run linting: `uv run ruff check .`
4. Commit changes

**Acceptance Criteria:**
- [ ] Sync completes without errors
- [ ] Verify passes
- [ ] Linting clean
- [ ] All changes committed

**Verification:**
```bash
uv run python .claude/skills/workflow-utilities/scripts/sync_ai_config.py verify
uv run ruff check .
```

**Dependencies:**
- doc_001, doc_002, doc_003, doc_004, doc_005

---

## Task Dependencies Graph

```
doc_001 (CLAUDE.md) ─────────────────────────────┐
doc_002 (.claude/CLAUDE.md) ─────────────────────┼─> doc_006 (sync/verify)
doc_003 (.agents/CLAUDE.md) ─────────────────────┤
doc_004 (CONTRIBUTING.md) ───────────────────────┤
doc_005 (README.md) ─────────────────────────────┘
```

## Parallel Work Opportunities

All documentation tasks (doc_001 through doc_005) can be done in parallel since they affect different files.

## Quality Checklist

Before considering this feature complete:

- [ ] All tasks marked as complete
- [ ] All acceptance criteria from requirements.md met
- [ ] Linting clean (`uv run ruff check .`)
- [ ] AI Config sync passes
- [ ] No broken markdown links
- [ ] Code reviewed

## Risk Assessment

### Low Risk

All tasks are documentation-only with no code changes:
- No risk of breaking existing functionality
- Easy to review and verify
- Rollback is simple (revert documentation changes)

## Notes

### Implementation Tips

- Use the sync utility to verify changes propagate correctly
- Check markdown rendering in GitHub preview
- Ensure links are valid (use relative paths)

### Common Pitfalls

- Editing `.agents/` instead of `.claude/` - changes will be overwritten
- Forgetting to run sync after editing CLAUDE.md
- Using absolute paths instead of relative paths in links
