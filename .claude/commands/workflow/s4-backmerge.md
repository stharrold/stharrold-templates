---
description: Sync release to develop and contrib (Step 4 of 4)
---

# /workflow:s4-backmerge - Step 4 of 4

## Step 1: PR release -> develop
```bash
gh pr create --base develop --head release/{version} --title "Backmerge {version} -> develop" --body "Backmerge {version}"
```

## Step 2: Manual Merge (release -> develop)
**Action**: Merge the PR through GitHub.

## Step 3: Rebase Contrib (After Merge)
```bash
git fetch origin develop
git checkout contrib/stharrold
git rebase origin/develop
git push --force-with-lease origin contrib/stharrold
```

## Step 4: Cleanup
```bash
git branch -d release/{version}
git push origin --delete release/{version}
```

## Error Recovery
- **No release branch**: Backmerge requires an active `release/*` branch. Run `/workflow:s3-release` first.
- **Rebase conflicts**: Resolve manually with `git rebase --continue` or `git rebase --abort` to restart.
- **Branch divergence**: If contrib diverged from remote, run `git fetch origin && git rebase origin/develop`.
