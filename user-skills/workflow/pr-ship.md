---
name: pr-ship
description: Push a feature branch, wait for CI, fix failures, address reviewer comments, merge, and clean up the merged worktree + local branch -- fully autonomous with pause points for judgment calls.
---

# PR Ship Skill

Autonomously take a feature branch from "ready to push" to "merged". Works across
any repo that uses GitHub Actions CI and gh CLI.

## Checklist

Work through each phase in order. Mark each task complete before moving to the next.
Pause and surface to the user whenever a step requires judgment (see Phase 4).

---

### Phase 1 -- Ensure PR exists

1. Run `git status` and `git branch --show-current` to confirm the working tree is
   clean and you are on a feature branch.
2. If there are uncommitted changes, commit them first (follow the repo's commit
   conventions; check git log for style).
3. Push the branch: `git push -u origin <branch>` (or just `git push` if tracking
   is already set).
4. Check whether a PR already exists:
   `gh pr list --repo <owner/repo> --head <branch> --json number,url`
   - If none exists: create one with `gh pr create --title "..." --body "..."`.
     Use a HEREDOC for the body. Set base branch to develop (or main if no develop).
   - If one exists: note its number and URL; proceed.
5. Print the PR URL so it is visible in the conversation.

---

### Phase 2 -- Wait for CI

Repeat until all checks complete (pass or fail) or 20 minutes have elapsed:

```
gh pr view <number> --repo <owner/repo> --json statusCheckRollup
```

- If status is QUEUED or IN_PROGRESS: wait 30 seconds, then check again.
  Use a polling loop -- do NOT sleep longer than 30 s per iteration so you stay
  responsive to early failures.
- If all checks show SUCCESS: proceed to Phase 4.
- If any check shows FAILURE: proceed to Phase 3.
- If 20 minutes elapse with checks still running: pause and tell the user.

---

### Phase 3 -- Fix CI failures (loop back to Phase 2 when done)

For each failing check:

1. Get the run ID from the statusCheckRollup detailsUrl or:
   `gh run list --repo <owner/repo> --branch <branch> --limit 5`
2. Read the failure log:
   `gh run view <run-id> --repo <owner/repo> --log-failed`
3. Diagnose the root cause from the log. Common categories:
   - **Compilation error**: fix the Swift/TS/Python source file directly.
   - **Test failure**: read the test output, fix the failing assertion or the code
     under test. Do NOT delete or skip tests to make CI pass.
   - **Missing file / lock file**: generate and commit the missing artifact
     (e.g. `npm install` for package-lock.json).
   - **Build config error** (xcodegen, tsconfig, wrangler): fix the config file.
   - **Flaky test / infrastructure timeout**: re-run once with
     `gh run rerun <run-id> --repo <owner/repo>` before diagnosing further.
4. Apply the fix, commit with a concise message, push.
5. Return to Phase 2.

If the same check fails 3 times with different error messages (indicating the fix
is not converging): pause and explain the situation to the user before continuing.

---

### Phase 4 -- Address reviewer comments

1. Fetch all open PR review comments:
   ```
   gh api repos/<owner/repo>/pulls/<number>/comments \
     --jq '.[] | {id, path, line, body}'
   ```
   Also fetch top-level review bodies:
   ```
   gh pr view <number> --repo <owner/repo> --json reviews \
     --jq '.reviews[] | {author: .author.login, state, body}'
   ```

2. For each comment, classify it:

   **Mechanical** (fix autonomously):
   - OOM / memory / performance fix with a clear correct approach
   - Stale / misleading comment in code
   - Deprecated API swap with obvious replacement
   - Missing null check, defer, error cleanup
   - Trailing slash, copy/paste bug, typo
   - Test coverage gap with an obvious test to add

   **Judgment required** (pause and surface to user):
   - Architecture or design disagreement
   - Request to change a tradeoff that was deliberately chosen
   - Ambiguous requirement ("make this more robust")
   - Comment that conflicts with a decision recorded in CLAUDE.md or a resolved OD
   - Any comment you are not confident you can fix correctly in one pass

3. Apply all mechanical fixes. Group logically related fixes into a single commit.
   Push. Return to Phase 2 to let CI verify the fixes.

4. For judgment-required comments: list them clearly (file, line, comment text,
   why you are pausing) and wait for the user before continuing.

---

### Phase 5 -- Merge

Only proceed when:
- All CI checks show SUCCESS (re-run Phase 2 to confirm after the last push).
- No open reviewer comments remain that you have not addressed or escalated.

Merge:
```
gh pr merge <number> --repo <owner/repo> --squash --delete-branch
```

Use `--squash` unless the repo's CLAUDE.md or branch conventions specify otherwise
(e.g. some repos prefer `--merge` to preserve individual commits).

After merging, confirm with:
```
gh pr view <number> --repo <owner/repo> --json state,mergedAt
```

Print the merge confirmation so it is visible in the conversation.

---

### Phase 6 -- Clean up the merged feature branch

`--delete-branch` removes the REMOTE branch, but feature work here lives in a git
worktree, so two things linger and accumulate: the worktree directory and the local
branch (a branch checked out in a worktree cannot be deleted by `--delete-branch`).
After the merge is confirmed MERGED, clean both up -- from the repo's MAIN checkout,
since you cannot remove the worktree you are standing in:

```
# cd to the main checkout first if cwd is inside the feature worktree
git worktree remove <path-to-feature-worktree>   # no --force: refuses if dirty
git branch -d <feature-branch>                    # safe -d: refuses if unmerged
```

Safety (do not weaken):
- Use `git branch -d`, never `-D`. If `-d` refuses, the branch has commits not in
  the merge target (e.g. work committed after the PR head merged) -- STOP and report
  it; do not force-delete (those commits may exist only on this branch).
- Use `git worktree remove` without `--force`. If it refuses (uncommitted or
  untracked files), report the path for manual review instead of forcing.
- Clean up ONLY the just-merged branch here -- never batch-delete other branches.

---

## Hard stops (always pause, never skip)

- The user has explicitly said a comment requires their input in CLAUDE.md or earlier
  in the conversation.
- Fixing a CI failure would require deleting or skipping a test.
- The fix touches a file the user marked as off-limits or out of scope.
- The PR branch has diverged from its base (merge conflict): resolve or rebase, then
  confirm with the user before pushing a force-push equivalent.
- The PR targets main directly and the repo has a protect rule -- check first.

## Tips

- Always use `--repo <owner/repo>` on every `gh` command to avoid acting on the
  wrong repo when worktrees or multiple remotes are involved.
- `gh run view --log-failed` only shows the failed steps. Use `--log` (full log)
  only when --log-failed is not enough to diagnose.
- If CI checks have not appeared yet after a push, wait 15 s and re-poll --
  GitHub takes a moment to enqueue checks.
- Do not amend published commits. Always create new commits when fixing CI failures
  on an open PR.
