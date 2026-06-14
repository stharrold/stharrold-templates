# Workflow Guide

**Version:** 9.1.1

## Three-tier model

| Tier | Role | Location |
|------|------|----------|
| **Tier 1 — policy** | `release-pilot` skill: declarative playbook (gates, topology, autonomy contract) | `~/.claude/skills/release-pilot/` (user-level) |
| **Tier 2 — library** | `release_lib`: deterministic Python helpers (`semver.py`, `vcs/`, `bundles.py`) | `release_lib/` in this repo |
| **Tier 3 — CI** | GitHub Actions: `tests.yml`, `claude-code-review.yml`, `secrets-example.yml` | `.github/workflows/` (shipped via `ci` bundle) |

**The product is the three tiers**, not the sN slash commands. The sN commands
(`/workflow:s1-worktree` .. `/workflow:s4-backmerge`) are low-level helpers shipped
by the `git` bundle; `release-pilot` drives them as needed. For a full release cycle,
invoke `release-pilot` via the `Skill` tool.

## Prerequisites

Required tools:
- **VCS CLI** - GitHub (`gh`) for PR operations
- **uv** - Python package manager
- **git** - Version control with worktree support
- **Python 3.11+** - Language runtime
- **Claude Code** - AI development assistant

Verify prerequisites:
```bash
gh auth status          # Must be authenticated
uv --version            # Must be installed
python3 --version       # Must be 3.11+
```

## Branch topology

```
release/<YYYYMMDDTHHMMSSZ>_<slug>   <- work branch (worktree)
   |  PR + gate-merge (autonomous; release-pilot drives this)
   v
contrib/<user>                       <- personal integration (e.g. contrib/stharrold)
   |  rebase onto develop, PR + gate-merge (autonomous)
   v
develop
   |  ===== EXPLICIT HUMAN CONFIRM REQUIRED =====
   v
release/vN.N.N                      <- version branch (cut from develop)
   |  PR to main; confirm-gated
   v
main  (tag vN.N.N)
   |  backmerge release/vN.N.N -> develop (autonomous)
   v
develop  ->  rebase contrib/<user> onto develop
```

Work branches (`release/<ts>_<slug>`) replace the old `feature/*` naming.
Two distinct `release/*` namespaces: timestamped work branches vs. versioned
promotion branches (`release/vN.N.N`).

### Branch protection

**Protected (PR-only):** `main`, `develop`

**Editable:** `contrib/*`, `release/<ts>_<slug>`

**Ephemeral:** `release/vN.N.N` — deleted after backmerge completes.

## Gates (decided contract)

| Gate | Type | Behavior |
|------|------|----------|
| Human reviews | soft, 10-min ceiling | Poll `gh pr view --json reviews`. Merge on timeout if CI is green. |
| CI checks | hard | `gh pr checks` must be green before any merge. Auto-fix on failure. |
| `develop -> release -> main` | confirm | Stop; require explicit human confirmation before creating `release/vN.N.N` or tagging. |

## Starting a release

Invoke via Skill tool:

```
Skill("release-pilot")
```

`release-pilot` reads git state, determines current phase, and drives forward.
For the specific steps it executes see `~/.claude/skills/release-pilot/SKILL.md`.

## sN slash commands (low-level)

The sN commands are building blocks used by `release-pilot`; you can also invoke them directly:

```
/workflow:s1-worktree "feature description"   # Create worktree on release/<ts>_<slug>
/workflow:s2-integrate "release/<ts>_<slug>"  # PR work->contrib->develop
/workflow:s3-release                          # Cut release/vN.N.N, PR->main, tag
/workflow:s4-backmerge                        # PR release/vN.N.N->develop, cleanup
```

### Step 1: Create Worktree (`/workflow:s1-worktree`)

Creates an isolated git worktree on a `release/<ts>_<slug>` branch from `contrib/<user>`.

```bash
/workflow:s1-worktree "add user authentication"
```

**Output:** Branch `release/<timestamp>_<slug>`, worktree at `../<project>_release_<timestamp>_<slug>/`

### Step 2: Integrate (`/workflow:s2-integrate`)

From the main repo after implementation is complete:

```bash
/workflow:s2-integrate "release/20251229T120000Z_add-user-auth"
```

**Two modes:**
- **Full mode** (with branch arg): PR work->contrib, worktree cleanup, PR contrib->develop
- **Contrib-only mode** (no arg): PR contrib->develop only

### Step 3: Release (`/workflow:s3-release`)

```bash
/workflow:s3-release           # auto-calculate version via release_lib.semver
/workflow:s3-release v1.2.0    # explicit version
```

Creates `release/vN.N.N` from develop, PRs to main, tags on merge.

### Step 4: Backmerge (`/workflow:s4-backmerge`)

```bash
/workflow:s4-backmerge
```

PRs `release/vN.N.N -> develop`, rebases `contrib/<user>` onto develop, deletes the release branch.

## Bootstrapping a new repository

Apply the `git` bundle (Tier 1 skills + sN commands + `WORKFLOW.md` + `CONTRIBUTING.md`):

```bash
cd /path/to/new-repo
git clone https://github.com/stharrold/stharrold-templates.git .tmp/stharrold-templates
uv run python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git
rm -rf .tmp/stharrold-templates
```

For the full workflow system (all tiers):

```bash
# Tier 1+3: apply git + ci bundles
cd /path/to/new-repo
git clone https://github.com/stharrold/stharrold-templates.git .tmp/stharrold-templates
uv run python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git --bundle ci
rm -rf .tmp/stharrold-templates

# Tier 1 policy skill: install release-pilot separately (user-level)
# Copy ~/.claude/skills/release-pilot/ from a working instance or craft from SKILL.md.
```

Or use `initialize-repository` to interactively scaffold a complete project:

```bash
uv run python .claude/skills/initialize-repository/scripts/initialize_repository.py . /path/to/new-repo
```

## Skills

| Skill | Bundle | Purpose |
|-------|--------|---------|
| `release-pilot` | user-level (not bundled) | Declarative release playbook; drives the full cycle |
| `git-workflow-manager` | `git` | Worktrees, PR operations, semantic versioning helpers |
| `workflow-utilities` | `git` | VCS wrapper (`gh`/`az`), pre-commit hooks, version validator |
| `tech-stack-adapter` | `full` | Python/uv stack detection, `TEST_CMD`/`BUILD_CMD` emission |
| `claude-md-hygiene` | not bundled (in-repo only) | Enforces the "earn it" CLAUDE.md discipline |
| `initialize-repository` | `full` | Meta-skill: bootstraps a new repo with the full workflow system |

## Related documentation

- **[CLAUDE.md](CLAUDE.md)** - Gotchas and key context for Claude Code sessions
- **[BUNDLES.md](BUNDLES.md)** - Bundle catalog and file ownership rules
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
