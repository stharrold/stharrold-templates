---
description: "workflow/4_implement → workflow/5_integrate → workflow/6_release | Integrate feature to develop"
order: 5
prev: /4_implement
next: /6_release
---

# /5_integrate - Step 5 of 7

**Workflow**: `/1_specify` → `/2_plan` → `/3_tasks` → `/4_implement` → `/5_integrate` → `/6_release` → `/7_backmerge`

**Purpose**: Integrate completed feature work into shared branches (PR to contrib, cleanup, PR to develop).

**Prerequisites**: Implementation complete, quality gates passed (from `/4_implement`)

**Outputs**: PRs created, worktree cleaned, GitHub Issue closed, AgentDB state record

**Next**: Run `/6_release` to release to production

---

## Step 0: Verify Context (REQUIRED - STOP if fails)

**Run this first. If it fails, STOP and tell the user to fix the context.**

```bash
python .claude/skills/workflow-utilities/scripts/verify_workflow_context.py --step 5
```

Expected: Main repo, `contrib/*` branch

---

## Step 1: Create PR feature → contrib

Create a pull request from the feature branch to contrib:
```bash
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py finish-feature
```

**MANUAL GATE**: Wait for PR approval and merge in GitHub UI.

## Step 2: Cleanup Feature Worktree

After PR is merged, cleanup the worktree (no TODO archival):
```bash
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/cleanup_feature.py \
  {slug} --no-archive
```

This deletes:
- Feature worktree directory
- Local feature branch
- Remote feature branch

## Step 3: Close GitHub Issue

If a GitHub Issue was linked, close it:
```bash
gh issue close {issue-number} --comment "Implemented in PR #{pr-number}"
```

## Step 4: Sync AI Configs

Sync CLAUDE.md to cross-tool formats:
```bash
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents
```

## Step 5: Create PR contrib → develop

Create a pull request from contrib to develop:
```bash
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py start-develop
```

**MANUAL GATE**: Wait for PR approval and merge in GitHub UI.

## Step 6: Record State in AgentDB

Record the workflow transition:
```bash
podman-compose run --rm dev python .claude/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_5_integrate
```

## Step 7: Report Completion

Report to the user:
- Feature PR merged to contrib
- Worktree cleaned up
- GitHub Issue closed (if applicable)
- Contrib → develop PR created
- Next step: Run `/6_release` when ready for production
