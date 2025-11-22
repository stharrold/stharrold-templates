# Quickstart: /workflow/all Command

## Overview

The `/workflow/all` command orchestrates the complete 7-step workflow, automatically detecting your current state and continuing from where you left off.

## Usage

### Start a New Feature
```
/workflow/all new "add dark mode toggle to settings"
```
Runs: `/0_specify` → `/1_plan` → `/2_tasks` → `/3_implement` → `/4_integrate`

Pauses at: PR merges (feature→contrib, contrib→develop)

### Continue After PR Merge
```
/workflow/all continue
```
Detects merged PRs and continues to next step.

### Release to Production
```
/workflow/all release
```
Runs: `/5_release` → `/6_backmerge`

Pauses at: PR merges (release→main, release→develop)

### Auto-Detect and Continue
```
/workflow/all
```
Detects current state from branch and artifacts, continues from appropriate step.

## Example Session

```bash
# 1. Start new feature
> /workflow/all new "implement user preferences API"

Detected state: Starting fresh
[▶] Step 0: /0_specify ... [✓]
[▶] Step 1: /1_plan    ... [✓]
[▶] Step 2: /2_tasks   ... [✓]
[▶] Step 3: /3_implement ... [✓]
[▶] Step 4: /4_integrate ... [✓]

⏸ PAUSED: Manual gate - PR merges required
  • PR #67: feature→contrib
  • PR #68: contrib→develop

Run: /workflow/all continue (after merging PRs)

# 2. Merge PRs in GitHub UI...

# 3. Continue workflow
> /workflow/all continue

Detected state: PRs merged, ready for release
[▶] Step 5: /5_release ... [✓]

⏸ PAUSED: Manual gate - PR merge required
  • PR #69: release→main

Run: /workflow/all continue (after merging PR)

# 4. Merge PR in GitHub UI...

# 5. Complete backmerge
> /workflow/all continue

Detected state: Release merged, backmerge pending
[▶] Step 6: /6_backmerge ... [✓]

✓ Workflow complete!
  Branch: contrib/stharrold
  Ready for next feature: /workflow/all new "..."
```

## State Detection

The command automatically detects your state:

| You're On | Artifacts | What Happens |
|-----------|-----------|--------------|
| Feature branch, no spec | - | Starts at step 0 |
| Feature branch, has spec | spec.md | Continues at step 1 |
| Feature branch, has tasks | tasks.md | Continues at step 3 |
| Contrib, PRs pending | - | Waits or runs step 4 |
| Contrib, PRs merged | - | Suggests step 5 |
| Develop | - | Runs step 5 (release) |
| Release branch | - | Runs step 6 (backmerge) |

## Manual Gates

The workflow pauses at these points requiring human action:

1. **After `/4_integrate`**: Merge feature→contrib and contrib→develop PRs
2. **After `/5_release`**: Merge release→main PR
3. **After `/6_backmerge` (pr-develop)**: Merge release→develop PR

## Error Recovery

If a step fails:
```
✗ Step 3 failed: /3_implement
Error: Test failure in test_auth.py

To retry: /workflow/all
To skip:  /workflow/all --skip 3
```

## Tips

1. **Don't worry about state** - The command figures out where you are
2. **Safe to re-run** - Running `/workflow/all` multiple times won't duplicate work
3. **Check PR status** - If stuck, check if PRs need merge in GitHub
4. **Use release mode** - When ready to deploy, use `/workflow/all release`
