# git-workflow-manager (tactical notes)

Automated git operations for the git-flow + GitHub-flow hybrid workflow
with worktrees. See [`SKILL.md`](SKILL.md) for the canonical skill
definition, full script reference, and invocation examples.

This file holds only gotchas that cost someone >30 minutes to rediscover.

## State tracking (v8.9)

**Git branches and PR state are the source of truth.** The AgentDB
state tracker is opt-in (see the `agentdb` bundle); do not require
it to exist. The internal phase keys recorded in AgentDB
(`phase_v7x1_1_worktree` .. `phase_v7x1_4_backmerge`) are deliberately
NOT renamed to match the `sN` slash commands -- they are stable dict
keys for backward compatibility with existing AgentDB databases.

Some older scripts (`create_worktree.py`, `cleanup_feature.py`) still
reference `TODO_*.md` files; these are deprecated but kept for
backward compatibility. New code should rely on branch + PR state.

## Gotchas

### Worktree creation (`create_worktree.py`)

- **Feature worktrees require planning docs to exist and be committed
  BEFORE worktree creation.** If `planning/<slug>/` doesn't exist or
  has uncommitted changes, the script refuses with a clear error
  message. Fix: commit and push the planning docs first, or run
  `/1_specify` to create them.
- **Branch naming uses compact ISO8601 timestamps** with no colons
  or hyphens: `feature/YYYYMMDDTHHMMSSZ_<slug>`. Colons would require
  shell escaping every time the branch name appears in a command.
- **Worktree directories use the `_` separator** between type and
  slug: `../{repo}_feature_{slug}/`. The project-name prefix is
  optional via `--project-name <name>`.
- **TODO files live in the main repo, not the worktree.** They
  persist after the worktree is deleted and are archived by
  `cleanup_feature.py`. Never move or copy them into the worktree.

### Cleanup (`cleanup_feature.py`)

- **Atomic ordering is enforced**: archive TODO first, THEN delete
  worktree, THEN delete branches. If the TODO archive fails, no
  deletions happen (safe to retry). This prevents orphaned TODO
  files if a manual cleanup was interrupted halfway.
- **Branch deletion is NOT automatic.** The script prints the
  commands and you run them. This is deliberate: automated branch
  deletion is how people lose work.
- **Idempotent on retry**: re-running after a partial failure picks
  up where it left off (the archived TODO is detected and not
  re-archived).

### Rebase (`daily_rebase.py`)

- **Hard requirement: clean working tree.** The script fails fast on
  uncommitted changes. Stash or commit before running.
- **Force-push uses `--force-with-lease`**, not `--force`. This
  prevents accidentally overwriting commits from another machine
  pushed after your last fetch.
- **Target branch is `origin/develop`** (hardcoded). If your repo
  uses a different integration branch, fork this script.

### Semantic versioning (`semantic_version.py`)

- **File-based change analysis only.** The script categorizes changes
  as MAJOR / MINOR / PATCH by file patterns (new files in `src/` =
  MINOR, changes to `docs/` or `tests/` = PATCH, etc). It does NOT
  read commit messages or analyze actual code changes.
- **Output is the new version, no prefix.** `1.6.0`, not `v1.6.0`.
  Callers that need the `v` prefix must add it themselves.

### Release workflow (`create_release.py`, `tag_release.py`, `backmerge_workflow.py`)

- **`release_workflow.py create-release` auto-calculates version**
  from the last git tag. Override manually for major bumps (the
  auto-calculator only ever bumps PATCH/MINOR).
- **Tags are annotated**, not lightweight. Annotated tags include
  author, date, and a message; lightweight tags don't. Always use
  annotated tags for releases.
- **Backmerge has a fallback for "No commits between"**: if the
  release branch has no unique commits (everything is already in
  develop via other paths), `pr-develop` falls back to a `main ->
  develop` PR instead of failing. This was a recurring failure
  mode fixed in v8.7.0 (#221).
- **Release-branch cleanup is manual.** The script prints the `git
  branch -d release/vX.Y.Z && git push origin --delete
  release/vX.Y.Z` commands for you to run. Deliberately not
  automated for the same "don't lose work" reason as feature
  cleanup.

### Authentication

- **v7x1 (now sN) scripts fail on `gh` commands with 401 auth** in
  some environments because `gh` picks up stale cached credentials
  from a login session that has expired. Re-authenticate with
  `gh auth login` and re-run. Some downstream repos (synavistra)
  work around this by sourcing a keychain token into `GITHUB_TOKEN`
  before invocation.

## See also

- [`SKILL.md`](SKILL.md) -- canonical skill definition and script
  invocation examples
- `workflow-orchestrator` -- calls this skill's scripts during the
  `sN` workflow steps
- `workflow-utilities` -- provides the VCS wrapper (`gh`/`az` auto-
  detect) and the TODO archiver
- `agentdb` bundle -- opt-in analytics layer for teams that want
  persistent workflow-state queries
