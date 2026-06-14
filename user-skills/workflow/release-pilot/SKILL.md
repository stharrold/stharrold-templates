---
name: release-pilot
description: >-
  Autonomously drive a Python repo's release end to end through the
  contrib -> develop -> release -> main branch topology, with review/CI
  gates and an explicit human confirm before promoting to production.
  Use when the user says "cut a release", "ship this", "run the release
  pilot", "release vN.N.N", or asks to drive a PR through to main. Derives
  all phase/progress from git state -- no TODO files, no state database.
---

# release-pilot

Declarative playbook for driving a release. This skill is **policy and
topology**; the engine is built-in tooling (native worktrees, `/loop`,
`/code-review`, and the `superpowers` skills). Do not re-implement
orchestration in code -- read the git state, decide the next step, act.

## When this applies

Use when piloting a change from a working branch all the way to a tagged
`main` release. Skip for a single quick commit, or work that never leaves a
feature branch.

## Branch topology (authoritative)

```
release/<YYYYMMDDTHHMMSSZ>_<slug>   <- work branch (worktree); implementation
   |  PR + gate-merge (autonomous)
   v
contrib/<user>
   |  rebase onto develop, then PR + gate-merge (autonomous)
   v
develop
   |  ===== EXPLICIT HUMAN CONFIRM REQUIRED =====
   v
release/vN.N.N                     <- version branch
   |  PR + merge to main (confirm-gated), then tag vN.N.N on main
   v
main  (tag vN.N.N)
   |  backmerge release/vN.N.N -> develop (autonomous)
   v
develop  ->  rebase contrib/<user> onto develop
```

Two distinct `release/*` namespaces -- keep them straight:

- **Work branch** `release/<YYYYMMDDTHHMMSSZ>_<slug>`: timestamped, one per
  change. Where code is written. Replaces the old `feature/*`.
- **Version branch** `release/vN.N.N`: the production-promotion branch cut
  from `develop`. Created only after the confirm gate.

`<slug>` is hyphenated lowercase. Timestamp is UTC `date -u +%Y%m%dT%H%M%SZ`.

## The gates (decided contract)

| Gate | Type | Behavior |
|---|---|---|
| **Human reviews** | soft, 10-min ceiling | Poll `gh pr view <pr> --json reviews,reviewDecision` and unresolved threads. Address any review that arrives. **If none arrive within 10 minutes, proceed with the merge (merge-on-timeout). Do not block.** |
| **CI checks** | hard | `gh pr checks <pr>` must be green (all required checks) before any merge, including the merge-on-timeout case. **On failure: auto-fix, repush, re-poll.** |
| **`develop -> release -> main` promotion** | confirm | Stop and require explicit human confirmation before creating `release/vN.N.N`, merging to `main`, or tagging. This gate is confirm-driven -- it never auto-proceeds on a timeout. |

Autonomy boundary: everything up to and including the merge into `develop`
is autonomous (including merge-on-timeout). The production promotion is
human-gated.

### Polling, not sleeping

Drive the 10-minute review window with `/loop` (self-paced) or repeated
`gh pr checks <pr>` calls at ~60-270s cadence -- never a single fixed
`sleep`. The 10 minutes is a **ceiling that ends early** the moment reviews
land or CI goes green; it is not a mandatory wait.

### Verify the gate; never trust a masked exit code (learned in #241)

`gh pr checks <pr> --watch` returns non-zero on check failure -- but only
if you read *its* exit code. **Never pipe it into `tail`/`head`**: the
pipeline's status is the last command's (`tail`), so `$?` is always 0 and a
network drop (`TLS handshake timeout`) silently reads as "all green". This
masked a false pass during the first real run.

Rules:
- Capture gh's own exit: `gh pr checks <pr> --watch >log 2>&1; echo $?` (no
  pipe), or check `${PIPESTATUS[0]}`.
- A `--watch` that exits is a *hint*, not proof. Before any merge,
  **re-verify each check's conclusion explicitly** with `gh pr checks <pr>`
  and confirm `mergeStateStatus == CLEAN`. A watch that died on a network
  error is "unknown", not "pass".

### CI auto-fix loop

On a red required check:
1. Read the failing check's logs (`gh run view <run-id> --log-failed`).
2. Fix in the worktree (lint/format via the repo's tooling; real test/build
   breaks via `systematic-debugging`).
3. Commit, push, re-poll. Repeat until green or clearly stuck (then stop and
   report).

## The sequence

Determine the current step from git state (see Recovery), then execute from
there. Do not restart from step 1 if a later branch/PR/tag already exists.

1. **Worktree.** Create a worktree on `release/<ts>_<slug>` branched from
   `contrib/<user>` (native worktree tooling or `using-git-worktrees`).
2. **Implement.** Do the work in the worktree. For code changes use
   `test-driven-development`; commit in logical units.
3. **Self-review.** Run `/code-review` on the diff; address findings.
4. **PR to contrib.** Open `release/<ts>_<slug> -> contrib/<user>`. Apply
   the review soft-gate + CI hard-gate, then merge (autonomous).
5. **Integrate to develop.** Rebase `contrib/<user>` onto `develop` if
   behind; open `contrib/<user> -> develop`; gate-merge (autonomous).
6. **=== CONFIRM GATE ===** Compute the next `vN.N.N` with the deterministic
   `release-lib` helper `next_version_from_tag(base_branch="origin/main",
   ref="origin/main")` -- diffing develop against `origin/main` captures
   everything unreleased; using `base_branch="develop"` when HEAD is already
   on develop produces an empty diff and freezes the version. Never guess the version. **Sanity-check the bump:**
   the file-pattern heuristic only treats `src/**.py` as a feature, so a new
   top-level package (e.g. `release_lib/`) is under-classified as PATCH when
   it is really a MINOR -- flag the mismatch and offer the override. Present
   the proposed version + the `origin/main...origin/develop` diff summary and
   **wait for explicit human confirmation.**
7. **Version branch + main.** Create `release/vN.N.N` from `develop`; bump
   `pyproject.toml` to the chosen version and run `uv lock` so `uv.lock`
   doesn't drift (commit both); open `release/vN.N.N -> main`; merge only
   after confirm; then create an **annotated** tag `vN.N.N` on the merge
   commit and push it.
8. **Backmerge.** Open/merge `release/vN.N.N -> develop` (autonomous gate).
9. **Re-sync contrib.** Rebase `contrib/<user>` onto `develop`.
10. **Clean up.** Remove the worktree; delete the merged `release/*` branches
    locally and on the remote.

## Recovery (resume from git state, never from a file)

Phase is a pure function of git observables. To resume, check in order:

- Tag `vN.N.N` on `main` exists + open `release/vN.N.N -> develop` PR ->
  step 8 (backmerge) or step 9 (re-sync contrib).
- `release/vN.N.N` exists + open PR to `main` -> step 7 (awaiting confirm
  has passed; finish merge/tag).
- Open `contrib/<user> -> develop` PR -> step 5.
- Open `release/<ts>_<slug> -> contrib` PR -> step 4.
- Work branch exists, no PR -> step 3.
- Detached HEAD or nothing in flight -> report state, ask the user; do not
  guess.

Do **not** create or read `TODO_*.md` or any AgentDB/DuckDB state. Those are
deprecated; git + the GitHub PR/checks API are the only source of truth.

## Built-ins this skill drives (don't reinvent)

| Need | Use |
|---|---|
| Isolated worktree | native worktree tooling / `superpowers:using-git-worktrees` |
| Review-window / CI polling | `/loop` (self-paced) |
| Self-review a diff | `/code-review` |
| Acting on review feedback | `superpowers:receiving-code-review` |
| Finishing/merging a branch | `superpowers:finishing-a-development-branch` |
| Verifying before "done" | `superpowers:verification-before-completion` |
| Next version (deterministic) | `release-lib` semver helper (Tier 2, issue #240) |

## Anti-patterns

- A fixed `sleep` for the review window (use a polling ceiling).
- Merging to `main`, creating `release/vN.N.N`, or tagging without explicit
  confirm.
- Merging on red required CI (CI is a hard gate even on review timeout).
- Computing the next version by judgment instead of the semver helper.
- Writing `TODO_*.md` / touching AgentDB to track progress.
- Re-deriving phase from anything other than git + PR/checks state.
