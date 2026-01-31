---
description: Integrate feature to develop (Step 2 of 4)
argument-hint: "[feature-branch]"
---

# /workflow:v7x1_2-integrate - Step 2 of 4

**Task**: Integrate feature branch: $ARGUMENTS

**Mode Detection**:
- If $ARGUMENTS is empty: Contrib-only mode (direct PR contrib -> develop)
- If $ARGUMENTS has branch: Full mode (feature -> contrib PR, cleanup, contrib -> develop PR)

## Step 0: Detect Contrib Branch
Detect the contrib branch: run `git branch --list 'contrib/*'` and use the first result (trimmed). If none found, fall back to the current branch.

## Step 1: feature -> contrib [FULL MODE]
Push $ARGUMENTS and create PR to `{contrib_branch}` using `gh pr create`.

## Step 2: Manual Merge (feature -> contrib) [FULL MODE]
**Action**: Merge the PR manually through the GitHub web portal GUI.

## Step 3: Cleanup [FULL MODE]
Run: `uv run python .claude/skills/git-workflow-manager/scripts/cleanup_feature.py {slug}`

## Step 4: contrib -> develop
Push `{contrib_branch}` and create PR to `develop`.

## Step 5: Manual Merge (contrib -> develop)
**Action**: Merge the PR manually through the GitHub web portal GUI.

## Step 6: Record State
Run: `uv run python .claude/skills/agentdb-state-manager/scripts/record_sync.py --sync-type workflow_transition --pattern phase_v7x1_2_integrate`

## Error Recovery
- **PR creation fails**: Check `gh auth status`. Ensure branch is pushed (`git push origin <branch>`).
- **Merge conflicts**: Resolve in GitHub UI or locally with `git merge --no-ff`, then push.
- **Cleanup fails**: Run cleanup_feature.py manually. If worktree is stuck, use `git worktree remove --force <path>`.
- **Wrong mode detected**: Pass explicit branch name for full mode, or omit for contrib-only mode.
