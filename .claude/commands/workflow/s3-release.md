---
description: Release to production (Step 3 of 4)
argument-hint: "[version e.g. v9.2.0]"
---

# /workflow:s3-release - Step 3 of 4

**Task**: Release version $ARGUMENTS (or compute from semver helper if empty)

## Step 1: Compute Next Version
If $ARGUMENTS is empty, compute: `uv run python -c "from release_lib.semver import next_version_from_tag; print(next_version_from_tag(ref='origin/main', base_branch='origin/main'))"`
Sanity-check: new top-level packages qualify as MINOR even if the heuristic says PATCH.

## Step 2: Create Release Branch and Bump Version
```bash
git checkout develop && git pull origin develop
git checkout -b release/{version}
# Bump version in pyproject.toml, then:
uv lock
git add pyproject.toml uv.lock
git commit -m "chore: bump version to {version}"
git push origin release/{version}
```

## Step 3: PR release -> main
```bash
gh pr create --base main --head release/{version} --title "Release {version}" --body "Release {version}"
```

## Step 4: Manual Merge (release -> main)
**Action**: Confirm CI is green, then merge the PR through GitHub.

## Step 5: Tag Release (After Merge)
```bash
git fetch origin main
git tag -a {version} -m "Release {version}" origin/main
git push origin {version}
```

## Error Recovery
- **Release branch exists**: Previous release in progress -- run `git branch -a | grep release` to check.
- **Version conflict**: Pass explicit version via $ARGUMENTS (e.g., `/workflow:s3-release v9.2.0`).
- **Tag already exists**: Delete with `git tag -d {version} && git push origin --delete {version}`, then re-run.
