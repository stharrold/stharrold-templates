# CLAUDE.md

Operating guide for Claude Code in the `stharrold-templates` repository.
This file is loaded into every session, so every line costs tokens.

## What goes here

Add an entry **only** when:

- A gotcha cost you (or would have cost a peer) more than ~30 minutes, AND
- It cannot be inferred by reading the relevant code.

Remove an entry the moment the underlying code stops being true. Prefer
deleting stale entries over adding caveats.

**What does NOT belong here:**

- Per-directory `Contents:` listings, auto-generated "Claude Code Context"
  stubs, or any file whose body is only a directory tree that `ls` would
  produce. The `claude-md-frontmatter` hook that used to enforce the stub
  pattern was removed in v8.9 -- along with `generate_claude_md.py` and
  `check_claude_md_frontmatter.py` -- because downstream experience
  (synavistra) proved the stubs were actively harmful.
- Architecture descriptions, stack diagrams, bundle maps.
  → [`BUNDLES.md`](BUNDLES.md) for bundle contents and file ownership.
  → [`WORKFLOW.md`](WORKFLOW.md) for the v7x1/sN workflow guide.
- Transient state, release notes, commit logs → git history,
  [`CHANGELOG.md`](CHANGELOG.md), GitHub issues.
- Per-skill reference docs → each skill's `SKILL.md` is the canonical
  skill definition.

**Anti-duplication rule:** when a fact applies in multiple sections,
state it once in the most specific location and cross-reference from
the rest.

## Contents

- [Branch structure](#branch-structure)
- [Commands](#commands)
- [Gotchas](#gotchas)
  - [CI & GitHub Actions](#ci--github-actions)
  - [Git & VCS](#git--vcs)
  - [Pre-commit](#pre-commit)
  - [Bundles & apply_bundle.py](#bundles--apply_bundlepy)
  - [Skills & slash commands](#skills--slash-commands)
- [Bundles](#bundles)
- [Key context](#key-context)

---

## Branch structure

`main` <- `develop` <- `contrib/stharrold` <- `feature/*`

Always end sessions on `contrib/stharrold`.

## Commands

```bash
uv run pytest                              # All tests
uv run ruff check .                        # Lint
uv run pre-commit run --all-files          # Pre-commit hooks
uv run python .claude/skills/.../scripts/*.py  # Run skill scripts
```

---

## Gotchas

### CI & GitHub Actions

- **`claude-code-review.yml` requires `claude_args: "--allowedTools Bash,WebFetch,WebSearch,Skill,Task"`** (not `allowed_tools`), `id-token: write` (for OIDC auth), and `fetch-depth: 0` (so `git diff` can reach the base branch). Without these, tool calls are denied and diffs come up empty.
- **`claude-code-review.yml` changes must reach `main` before OIDC validates them.** PRs that edit this workflow fail with `"workflow file must have identical content to the version on the repository's default branch"`. Fix: land the change on `main` first (via a release branch), then edit the PR that uses it.
- **`tests.yml` checkout needs `lfs: true`.** Downstream repos that LFS-track PDFs or model weights see 131-byte pointer files on the runner without this -- validators hash the pointer and report spurious drift. Fixed in the shipped `ci` bundle; documented in `BUNDLES.md` under "Known CI gotchas". Traced to synavistra PR #706.
- **`tests.yml` has a `concurrency:` block** to dedupe rapid-fire pushes. Push and pull_request events intentionally stay in different groups because they test different commits (push tests raw HEAD, pull_request tests GitHub's synthetic merge commit).
- **`.claude/settings.local.json` is gitignored** -- do not commit. Restrictive Bash allowlists break the CI `claude-code-action` which needs unrestricted `gh` access.

### Git & VCS

- **`release_workflow.py create-release`** auto-calculates version from the last git tag. Override manually for major bumps.
- **`backmerge_workflow.py cleanup-release`** only prints instructions -- run `git branch -d release/vX.Y.Z && git push origin --delete release/vX.Y.Z` manually.
- **Backmerge order**: always try `backmerge_workflow.py pr-develop` (release → develop) first so review comments can be fixed on the release branch. Only fall back to a `main → develop` PR when `gh pr create` returns "No commits between develop and release".
- **`uv.lock` drifts when `pyproject.toml` version changes.** `uv run` will modify `uv.lock` silently. Commit the updated lockfile or the next `rebase-contrib` call will fail with "Uncommitted changes detected".
- **Git worktrees use a `.git` FILE, not a directory.** Use `.exists()`, not `.is_dir()`, when checking for a git repo.
- **VCS abstraction**: `from vcs import create_pr, get_contrib_branch, get_username` -- NOT `get_vcs_adapter()` (removed in v8.5). Auto-detects GitHub (`gh`) or Azure DevOps (`az`) from `git remote.origin.url`.

### Pre-commit

- **Ruff auto-fixes import ordering and formatting on commit.** First commit attempt fails; re-stage the modified files and commit again. This is the normal retry pattern, not an error.
- **SPDX headers are required on every Python file**: `# SPDX-FileCopyrightText: 2025 stharrold` + `# SPDX-License-Identifier: Apache-2.0`. The `check_spdx_headers.py` hook enforces this.
- **ASCII-only Python files**: the `check_ascii_only.py` hook rejects any non-ASCII character (em-dashes, smart quotes, etc.). Use `--` instead of `—` in docstrings and comments.
- **`check-added-large-files` caps at 1 MB (`--maxkb=1000`).** Training data JSONL and golden record JSONL commonly exceed this. Gitignore the data, upload to GCS with a timestamped prefix, and commit a small `manifest.json` with sha256 + line counts. See synavistra's `enterprise/golden-v4/` and `enterprise/training-data-v5-reclassified/` for the pattern.

### Bundles & apply_bundle.py

- **`apply_workflow.py` was removed** -- use `scripts/apply_bundle.py` instead. See `BUNDLES.md` for the bundle catalog and file-ownership rules (template-owned / user-owned-merge / user-owned-skip).
- **Bundle integration tests** live in `tests/integration/test_apply_bundle.py`; unit tests in `tests/unit/test_apply_bundle.py`.
- **`docs/archived/` and `docs/reference/` preserve historical Gemini references intentionally** -- do not update them during migrations.

### Skills & slash commands

- **Slash commands use Markdown format, not TOML** (migrated in v8.2+):
  - `description` → YAML frontmatter
  - `!{cmd}` → `` !`cmd` ``
  - `{{args}}` → `$ARGUMENTS`
- **Workflow slash-command prefixes were renamed in v8.9**: `v7x1_1-worktree` → `s1-worktree`, `v7x1_2-integrate` → `s2-integrate`, `v7x1_3-release` → `s3-release`, `v7x1_4-backmerge` → `s4-backmerge`. The `sN` prefix ("step N") is shorter and more descriptive.
- **`record_sync.py` (AgentDB state manager) auto-initializes the database on first use.** Failures print `[WARN]` to stderr and exit 0 (non-blocking by design).
- **AgentDB `init_database_if_needed` checks for the `agent_synchronizations` table**, not just file existence. Pass `--db-path` to `init_database.py` for custom paths.
- **After deleting or renaming Python modules under `.claude/skills/`**, grep all `*.md` files under the skills directory for stale references (CLAUDE.md, README.md, SKILL.md frontmatter all show up in the grep).

---

## Bundles

This repo provides installable workflow bundles. See [BUNDLES.md](BUNDLES.md)
for the authoritative catalog and file-ownership rules.

Current bundles: `git`, `secrets`, `ci`, `pipeline`, `sql-pipeline`,
`graphrag`, `data-catalog`, `full`.

CLI:

```bash
python scripts/apply_bundle.py <source-repo> <target-repo> \
  --bundle git [--bundle secrets] [--force] [--dry-run]
```

## Key context

- **`claude-code-review.yml`** ships with a hard-coded prompt overriding macOS-only patterns (keyring, GITHUB_TOKEN) for Ubuntu CI. Keep the prompt in sync if CLAUDE.md conventions change.
- **`../library/`** is the reference implementation for secrets management patterns.
- **`../synavistra/`** is the reference implementation for `claude-code-review.yml` and has proven several CLAUDE.md conventions used here.
- **`scripts/secrets_run.py`** runs commands with secrets from the OS keyring (#169).
- **AgentDB state manager** (`.claude/skills/agentdb-state-manager/`) has test coverage in `tests/skills/`. Kept as opt-in; no longer included in the `full` bundle as of v8.9.
