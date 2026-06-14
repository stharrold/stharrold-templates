---
name: branch-start
description: Create a timestamped feature branch and its own git worktree. Run this at the start of every new feature -- before writing any code.
---

# Branch Start Skill

Creates a feature branch and an isolated git worktree for a single piece of work.
The worktree keeps the main repo checkout clean while the feature is in progress.

## Input

The user must supply a short slug describing the feature. If they did not provide
one, ask before proceeding:

> "What's a short slug for this feature? (e.g. `add-ocr-engine`, `fix-model-download`)"

Slugs use lowercase hyphens only. No underscores, no spaces, no uppercase.
Strip the slug of any leading/trailing hyphens.

---

## Checklist

### Step 1 -- Collect context

Run these commands from the main repo checkout (not from inside a worktree):

```bash
# Confirm you are in the main repo, not a worktree
git rev-parse --show-toplevel
pwd

# Repo name (used for the worktree directory)
basename "$(git rev-parse --show-toplevel)"

# Current branch (should be main, develop, or contrib/<user> -- not a feature branch)
git branch --show-current

# Confirm contrib/stharrold exists locally or on remote
git branch -a | grep contrib/stharrold
```

If you are already inside a worktree (`pwd` differs from `--show-toplevel`):
stop and tell the user. Branch creation must happen from the main checkout.

If `contrib/stharrold` does not exist locally, fetch it:
```bash
git fetch origin contrib/stharrold:contrib/stharrold
```

### Step 2 -- Generate names

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
echo "timestamp: ${TS}"
```

Compose the names:
- **Branch**: `feature/${TS}_${SLUG}`  (e.g. `feature/20260605T163000Z_add-ocr-engine`)
- **Worktree dir**: `../${REPO_NAME}_feature_${TS}_${SLUG}`
  (e.g. `../claristra_feature_20260605T163000Z_add-ocr-engine`)

Print both so the user can see them before any git commands run.

### Step 3 -- Create the worktree and branch

The feature branch starts from `contrib/stharrold` so the feature inherits
any in-progress work that is already integrated but not yet on develop.

```bash
git worktree add \
  "../${REPO_NAME}_feature_${TS}_${SLUG}" \
  -b "feature/${TS}_${SLUG}" \
  contrib/stharrold
```

Confirm success:
```bash
git worktree list
```

### Step 4 -- Push the branch to remote

```bash
cd "../${REPO_NAME}_feature_${TS}_${SLUG}"
git push -u origin "feature/${TS}_${SLUG}"
```

### Step 5 -- Report and hand off

Print a summary block the user can copy:

```
Worktree : ../${REPO_NAME}_feature_${TS}_${SLUG}
Branch   : feature/${TS}_${SLUG}
Base     : contrib/stharrold
Remote   : pushed

Next steps:
  cd ../${REPO_NAME}_feature_${TS}_${SLUG}   # work here
  /pr-ship                                    # when ready to merge
```

All subsequent work for this feature happens inside the worktree directory.
The main repo checkout stays on its original branch and is undisturbed.

---

## Hard stops

- Do not create a worktree if `git status` shows uncommitted changes in the main
  repo -- commit or stash first.
- Do not use `_` in slugs (worktree directory uses `_` as a separator between
  the repo name, "feature", timestamp, and slug -- mixing in slug underscores
  breaks that structure).
- Do not create a feature branch from `main` or `develop` directly -- always
  branch from `contrib/stharrold`.
- If a worktree for this slug already exists (leftover from a previous attempt),
  pause and ask the user whether to remove it or reuse it.
