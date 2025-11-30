# Specification: Implement Commit Push Before Integrate

**Type:** feature
**Slug:** implement-commit-push-before-integrate
**Date:** 2025-11-30
**Author:** stharrold
**GitHub Issue:** #117

## Overview

This feature ensures that `/4_implement` properly finalizes all work before users transition to `/5_integrate`. Currently, users may forget to commit/push their changes or may not realize they need to switch to the contrib branch in the main repo. This modification adds a final section to `/4_implement` that:

1. Stages, commits, and pushes all changes
2. Displays a clear prompt instructing the user to switch to the contrib branch in the main repo

## Implementation Context

**BMAD Planning:** See `planning/implement-commit-push-before-integrate/` for complete requirements and architecture.

**Implementation Preferences:**

- **Task Granularity:** Small tasks (1-2 hours each)
- **Follow Epic Order:** True

## Requirements Reference

See: `planning/implement-commit-push-before-integrate/requirements.md`

## Detailed Specification

### Component: Slash Command Template Modification

**File:** `.claude/commands/workflow/4_implement.md`

**Purpose:** Add a final section to the `/4_implement` slash command that ensures all changes are committed and pushed, then displays guidance for the next step.

**Changes Required:**

1. **Add "Final Steps" section** at the end of the template
2. **Git operations:**
   - Run `git add .` to stage all changes
   - Run `git commit` with a summary message about implementation completion
   - Run `git push` to push changes to the remote feature branch
3. **User prompt:**
   - Display the path to the main repository
   - Show the exact `cd` command to return to the main repo
   - Remind user to be on `contrib/*` branch
   - Show the next command (`/5_integrate`)

### Template Section to Add

```markdown
## Final Steps: Commit and Push

**After completing all tasks:**

1. Stage all changes:
   ```bash
   git add .
   ```

2. Commit with implementation summary:
   ```bash
   git commit -m "feat({slug}): implement feature per plan.md

   - [Summary of changes made]
   - Refs: #{issue-number}"
   ```

3. Push to remote:
   ```bash
   git push
   ```

## Next Steps

**IMPORTANT:** Return to the main repository and switch to the contrib branch:

```bash
cd {main-repo-path}
git checkout contrib/stharrold
```

Then run `/5_integrate` to create PRs and cleanup the worktree.
```

## Integration Points

- **Integrates with:** Existing `/4_implement` slash command
- **Consumed by:** `/5_integrate` which validates context (must be in main repo on contrib branch)

## Quality Gates

This is a documentation/template change, not code. Quality gates are:

- [ ] Template syntax is valid markdown
- [ ] Git commands are correct
- [ ] Path placeholders use correct format
- [ ] Instructions are clear and complete

## Testing Requirements

### Manual Testing

1. Run `/4_implement` on a test feature
2. Verify the final section appears with correct instructions
3. Verify the git commands execute correctly
4. Verify the user prompt displays the correct path
5. Follow the prompt and verify `/5_integrate` runs successfully

## References

- Planning documents: `planning/implement-commit-push-before-integrate/`
- Current template: `.claude/commands/workflow/4_implement.md`
- Step 5 context validation: `.claude/skills/workflow-utilities/scripts/verify_workflow_context.py`
