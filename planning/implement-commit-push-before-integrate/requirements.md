# Requirements: implement-commit-push-before-integrate

## Problem Statement

The `/4_implement` workflow step may complete without ensuring all work is properly committed and pushed. Users may also forget to switch back to the contrib branch in the main repo before running `/5_integrate`, causing context validation failures.

## Primary Users

Developers using the Claude Code workflow system

## Key Requirements

1. Step 4 must end with git add/commit/push sequence
2. User must receive clear prompt about switching to contrib branch
3. Step 5 context validation should catch if user is still in worktree

## User Stories

- As a developer, I want step 4 to automatically commit and push my changes so I don't forget
- As a developer, I want a clear prompt telling me to switch branches so I know the next action

## Acceptance Criteria

- [ ] All changes staged with `git add .` before step 4 completes
- [ ] All changes committed with appropriate message
- [ ] All changes pushed to remote branch
- [ ] Clear instruction displayed to switch to contrib branch in main repo
- [ ] Step 5 validates user is in main repo on contrib branch

## Out of Scope

- Automatic branch switching (user must do this manually)
- Changes to steps 1-3 or 5-7

## Constraints

Must work within existing slash command template system

## Success Metrics

- Users no longer forget to commit/push after step 4
- Users receive clear guidance on next steps
