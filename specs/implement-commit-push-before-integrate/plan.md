# Implementation Plan: Implement Commit Push Before Integrate

**Type:** feature
**Slug:** implement-commit-push-before-integrate
**Date:** 2025-11-30
**GitHub Issue:** #117

## Task Breakdown

### Phase 1: Read Current Template

#### Task impl_001: Read and understand current 4_implement.md template

**Priority:** High

**Files:**
- `.claude/commands/workflow/4_implement.md`

**Description:**
Read the current `/4_implement` slash command template to understand its structure and identify where to add the new section.

**Steps:**
1. Read `.claude/commands/workflow/4_implement.md`
2. Identify the end of the template
3. Note any existing patterns for git operations or user prompts

**Acceptance Criteria:**
- [ ] Current template structure understood
- [ ] Location for new section identified

**Verification:**
```bash
cat .claude/commands/workflow/4_implement.md
```

**Dependencies:**
- None

---

### Phase 2: Implementation

#### Task impl_002: Add git commit/push section to 4_implement.md

**Priority:** High

**Files:**
- `.claude/commands/workflow/4_implement.md`

**Description:**
Add a new section at the end of the `/4_implement` template that instructs Claude to stage, commit, and push all changes after completing implementation tasks.

**Steps:**
1. Add "Final Steps: Commit and Push" section header
2. Add git add/commit/push instructions
3. Use appropriate placeholders for slug and issue number

**Acceptance Criteria:**
- [ ] Section added with `git add .` instruction
- [ ] Section includes `git commit` with appropriate message format
- [ ] Section includes `git push` instruction
- [ ] Placeholders match template conventions

**Verification:**
```bash
grep -A 20 "Final Steps" .claude/commands/workflow/4_implement.md
```

**Dependencies:**
- impl_001

---

#### Task impl_003: Add user prompt for next steps

**Priority:** High

**Files:**
- `.claude/commands/workflow/4_implement.md`

**Description:**
Add a prominent user prompt section that instructs the user to switch to the contrib branch in the main repository before running `/5_integrate`.

**Steps:**
1. Add "Next Steps" section with clear visual prominence
2. Include exact `cd` command to return to main repo
3. Include reminder about contrib branch
4. Include `/5_integrate` as next command

**Acceptance Criteria:**
- [ ] Prompt clearly visible at end of template
- [ ] Shows path to main repository
- [ ] Mentions contrib branch requirement
- [ ] Shows next command `/5_integrate`

**Verification:**
```bash
grep -A 15 "Next Steps" .claude/commands/workflow/4_implement.md
```

**Dependencies:**
- impl_002

---

### Phase 3: Testing

#### Task test_001: Manual workflow test

**Priority:** High

**Files:**
- None (manual testing)

**Description:**
Manually test the complete workflow from step 4 through step 5 to verify the changes work correctly.

**Steps:**
1. Run `/4_implement` and complete a small task
2. Verify final section prompts for git add/commit/push
3. Follow the user prompt to switch to main repo
4. Run `/5_integrate` and verify context validation passes

**Acceptance Criteria:**
- [ ] Git add/commit/push executes successfully
- [ ] User prompt displays correct path
- [ ] User can follow prompt to switch branches
- [ ] `/5_integrate` context validation passes

**Verification:**
Manual testing through workflow

**Dependencies:**
- impl_003

---

### Phase 4: Quality Gates

#### Task qa_001: Run quality gates

**Priority:** High

**Files:**
- None (runs existing quality gates)

**Description:**
Run the quality gates to ensure all checks pass before integration.

**Steps:**
1. Run `uv run python .claude/skills/quality-enforcer/scripts/run_quality_gates.py`
2. Fix any issues that arise

**Acceptance Criteria:**
- [ ] All 5 quality gates pass

**Verification:**
```bash
uv run python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
```

**Dependencies:**
- test_001

---

## Task Dependencies Graph

```
impl_001 ─> impl_002 ─> impl_003 ─> test_001 ─> qa_001
```

## Critical Path

1. impl_001: Read current template
2. impl_002: Add git commit/push section
3. impl_003: Add user prompt
4. test_001: Manual workflow test
5. qa_001: Run quality gates

## Quality Checklist

Before considering this feature complete:

- [ ] All tasks marked as complete
- [ ] Template syntax is valid markdown
- [ ] Git commands use correct syntax
- [ ] Path placeholders match existing conventions
- [ ] Manual testing performed
- [ ] Quality gates pass

## Notes

### Implementation Tips

- The template uses placeholders like `{slug}` and `{issue-number}` - follow existing patterns
- Keep the prompt visually distinct so users notice it
- Consider using markdown formatting like bold or blockquotes for emphasis

### Common Pitfalls

- Don't forget to push after committing
- Make sure the path to main repo accounts for worktree naming convention
- Ensure the commit message format follows project conventions
