---
name: branch-release
description: Cut a release branch from develop, merge to main, tag, backmerge to develop, and rebase contrib/<user>. Run this when develop is ready to ship.
---

# Branch Release Skill

Takes develop from "ready" to "tagged on main" and keeps all branches in sync.
Four-stage flow: cut release → merge to main → backmerge to develop → rebase contrib.

## Input

The user may specify a version bump type: `patch`, `minor`, or `major`.
If not specified, infer from the commits on develop since the last tag:
- Any commit with `feat:` or `feat(...):`  → minor
- Any commit with `BREAKING CHANGE` or `!:` → major
- Otherwise → patch

The user may also supply an explicit version (e.g. `v1.2.0`). If so, use it directly
and skip the inference step.

---

## Checklist

### Phase 1 -- Determine version

```bash
# Find the current highest semver tag
git fetch --tags
CURRENT=$(git tag --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
echo "Current tag: ${CURRENT}"
```

If no tags exist, start at `v0.1.0` (first release is always minor).

Parse the version, apply the bump, and print the proposed next version:
```
Current : v1.2.3
Bump    : minor
Next    : v1.3.0
```

Ask the user to confirm the version before continuing if it was inferred
(skip confirmation if the user supplied it explicitly).

### Phase 2 -- Cut the release branch

```bash
git checkout develop
git pull origin develop

git checkout -b "release/v${NEXT}"
git push -u origin "release/v${NEXT}"
```

### Phase 3 -- Merge release to main

Create the PR:
```bash
gh pr create \
  --repo <owner/repo> \
  --base main \
  --head "release/v${NEXT}" \
  --title "release: v${NEXT}" \
  --body "$(cat <<'EOF'
## Release v${NEXT}

Merging release/v${NEXT} into main.

- Bump type: ${BUMP}
- Base: develop @ $(git rev-parse --short HEAD)
EOF
)"
```

Then invoke `/pr-ship` behaviour for this PR:
- Wait for CI (Phase 2 of pr-ship)
- Fix any failures (Phase 3 of pr-ship)
- Address reviewer comments (Phase 4 of pr-ship)
- **Do NOT auto-merge** -- pause and tell the user the PR is ready,
  then wait for explicit confirmation before merging.

Reason: release merges to main are high-stakes; the user should click merge
or give explicit approval ("go ahead") before this skill proceeds.

After confirmed merge:

```bash
git checkout main
git pull origin main
```

### Phase 4 -- Tag main

```bash
git tag "v${NEXT}" -m "release: v${NEXT}"
git push origin "v${NEXT}"
```

Confirm the tag is visible:
```bash
git tag --sort=-v:refname | head -3
```

### Phase 5 -- Backmerge release to develop

Create the backmerge PR:
```bash
gh pr create \
  --repo <owner/repo> \
  --base develop \
  --head "release/v${NEXT}" \
  --title "chore: backmerge v${NEXT} to develop" \
  --body "Backmerge release/v${NEXT} into develop after main merge."
```

Wait for CI to pass, then merge:
```bash
gh pr merge <number> --repo <owner/repo> --merge --delete-branch
```

Use `--merge` (not `--squash`) for backmerges -- preserves the release commit
on develop so git history is symmetric.

If GitHub reports "No commits between develop and release/v${NEXT}" (nothing
to backmerge), skip this step and note it in the summary.

### Phase 6 -- Rebase contrib/<user> onto develop

```bash
git fetch origin develop
git checkout contrib/<user>
git pull origin contrib/<user>
git rebase origin/develop
git push --force-with-lease origin contrib/<user>
```

`--force-with-lease` is safe here: it aborts if the remote has commits you
have not seen, protecting against accidentally overwriting someone else's push.

If the rebase has conflicts:
1. List the conflicting files.
2. Resolve them (prefer develop's version for files that are part of the release;
   prefer contrib's version for in-progress feature work).
3. `git rebase --continue` after each conflict set.
4. If the conflict is non-trivial, pause and surface it to the user.

### Phase 7 -- Final report

Print a summary:

```
Release complete
---------------
Version  : v${NEXT}
Tag      : v${NEXT} on main ($(git rev-parse --short v${NEXT}))
Backmerge: release/v${NEXT} -> develop  [merged | skipped]
Contrib  : contrib/<user> rebased onto develop

Branches now:
  main            <- v${NEXT} (tagged)
  develop         <- includes v${NEXT} backmerge
  contrib/<user> <- rebased onto develop
```

---

## Hard stops

- Do not proceed past Phase 3 without explicit user confirmation of the merge.
- Do not tag until `git pull origin main` confirms the release PR merged.
- Do not use `--force` (without `-with-lease`) on any push.
- If `develop` has uncommitted or unmerged feature work that should NOT be in
  this release, stop and tell the user before cutting the release branch.
- If the computed next version would be lower than the current highest tag
  (e.g. user requests patch but CURRENT is already v2.0.0), pause and confirm.
