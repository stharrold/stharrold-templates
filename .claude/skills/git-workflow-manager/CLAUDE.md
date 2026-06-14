# git-workflow-manager (tactical notes)

Automated git operations for the git-flow + GitHub-flow hybrid workflow
with worktrees. See [`SKILL.md`](SKILL.md) for the canonical skill
definition, full script reference, and invocation examples.

This file holds only gotchas that cost someone >30 minutes to rediscover.

## Gotchas

### Worktree creation (`create_worktree.py`)

- **Feature worktrees require planning docs to exist and be committed
  BEFORE worktree creation.** If `planning/<slug>/` doesn't exist or
  has uncommitted changes, the script refuses with a clear error
  message. Fix: commit and push the planning docs first.
- **Branch naming uses compact ISO8601 timestamps** with no colons
  or hyphens: `feature/YYYYMMDDTHHMMSSZ_<slug>`. Colons would require
  shell escaping every time the branch name appears in a command.
- **Worktree directories use the `_` separator** between type and
  slug: `../{repo}_feature_{slug}/`. The project-name prefix is
  optional via `--project-name <name>`.

### Cleanup (`cleanup_feature.py`)

- **Atomic ordering is enforced**: archive TODO first, THEN delete
  worktree, THEN delete branches. If the TODO archive fails, no
  deletions happen (safe to retry).
- **Branch deletion is NOT automatic.** The script prints the
  commands and you run them. This is deliberate: automated branch
  deletion is how people lose work.

### Semantic versioning (`semantic_version.py`)

- **This is a backward-compat shim** that re-exports from
  `release_lib.semver` (issue #240). Canonical home is `release_lib`.
- **File-based change analysis only.** The script categorizes changes
  as MAJOR / MINOR / PATCH by file patterns (new files in `src/` =
  MINOR, changes to `docs/` or `tests/` = PATCH). It does NOT
  read commit messages or analyze actual code changes.
- **Output is the new version, no prefix.** `1.6.0`, not `v1.6.0`.

### Authentication

- **Scripts fail on `gh` commands with 401 auth** if `gh` picks up
  stale cached credentials. Re-authenticate with `gh auth login`.

## See also

- [`SKILL.md`](SKILL.md) -- canonical skill definition and script
  invocation examples
- `workflow-utilities` -- provides the VCS wrapper (`gh`/`az` auto-detect)
- `release_lib` -- canonical home for semver and VCS helpers (issue #240)
