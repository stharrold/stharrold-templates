# Epics: implement-commit-push-before-integrate

## Epic 1: Add commit/push to step 4

### Description
Add a final section to `/4_implement` that stages, commits, and pushes all changes.

### Stories
1. Add `git add .` command to stage all changes
2. Add `git commit` with implementation summary message
3. Add `git push` to push changes to remote

### Acceptance Criteria
- All changes are staged before step completes
- Commit message summarizes implementation work
- Changes are pushed to remote branch

---

## Epic 2: Add user prompt for next steps

### Description
Display clear instructions telling the user to switch to contrib branch in main repo.

### Stories
1. Display the exact `cd` command to return to main repo
2. Display the next command (`/5_integrate`)
3. Remind user they need to be on contrib branch

### Acceptance Criteria
- Prompt shows exact path to main repo
- Prompt shows next slash command
- Prompt is clearly visible at end of step 4 output
