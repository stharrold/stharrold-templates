# Contract: /workflow/all Command

## Command Interface

### File Location
`.claude/commands/workflow/all.md`

### Frontmatter
```yaml
---
description: "Orchestrate full workflow | Run steps 0-6 with manual gate pauses"
order: 0
---
```

### Invocation Modes

| Mode | Syntax | Description |
|------|--------|-------------|
| Default | `/workflow/all` | Detect state, continue from current step |
| New | `/workflow/all new "description"` | Start fresh from step 0 |
| Release | `/workflow/all release` | Run steps 5-6 only |
| Continue | `/workflow/all continue` | Resume after manual gate |

## Input/Output Contract

### Inputs
| Input | Type | Required | Description |
|-------|------|----------|-------------|
| mode | string | No | "new", "release", "continue", or empty |
| description | string | If mode=new | Feature description for /0_specify |

### Outputs
| Output | Condition | Description |
|--------|-----------|-------------|
| Progress report | Always | Steps completed with status |
| Pause notification | At manual gate | URLs and resume instructions |
| Error report | On failure | Failed step, error, retry command |
| Completion summary | All steps done | Final status, branch, next actions |

## Behavior Contract

### State Detection
```
Given: User runs /workflow/all (no mode)
When: Command starts
Then:
  1. Get current branch via `git branch --show-current`
  2. Determine branch type (feature/contrib/develop/release/main)
  3. Check artifact existence in specs/{feature}/
  4. Check PR status via `gh pr list`
  5. Calculate next step based on state matrix
  6. Report detected state to user
  7. Begin execution from detected step
```

### New Feature Mode
```
Given: User runs /workflow/all new "add user authentication"
When: Command starts
Then:
  1. Validate description is not empty
  2. Invoke /workflow:0_specify with description
  3. Continue to /workflow:1_plan
  4. Continue to /workflow:2_tasks
  5. Continue to /workflow:3_implement
  6. Invoke /workflow:4_integrate
  7. PAUSE at manual gate (PR merges)
  8. Report PR URLs and resume command
```

### Release Mode
```
Given: User runs /workflow/all release
Given: Current branch is contrib/* or develop
When: Command starts
Then:
  1. Validate branch is appropriate for release
  2. Invoke /workflow:5_release
  3. PAUSE at manual gate (PR merge to main)
  4. Report PR URL and resume command
```

### Continue Mode
```
Given: User runs /workflow/all continue
Given: Previous execution paused at manual gate
When: Command starts
Then:
  1. Detect which gate was paused at
  2. Check if required PR is merged
  3. If not merged: Report status, remain paused
  4. If merged: Continue to next step
  5. Repeat until complete or next gate
```

### Error Handling
```
Given: Any step fails
When: Error detected
Then:
  1. Stop execution immediately
  2. Report: which step failed, error message
  3. Suggest: retry command, skip command
  4. Do not continue to subsequent steps
```

## Progress Output Format

### During Execution
```
/workflow/all - Orchestrating workflow

Detected state:
  Branch: 005-implement-workflow-all (feature)
  Artifacts: spec.md, research.md, tasks.md
  Starting from: Step 3 (/3_implement)

[▶] Step 3: /3_implement
    ... (step output) ...
[✓] Step 3: Complete

[▶] Step 4: /4_integrate
    ... (step output) ...
[✓] Step 4: Complete

⏸ PAUSED: Manual gate reached

PRs created:
  • feature→contrib: https://github.com/repo/pull/65
  • contrib→develop: https://github.com/repo/pull/66

Next: Merge PRs in GitHub, then run:
  /workflow/all continue
```

### On Completion
```
/workflow/all - Complete

✓ All steps completed successfully

Summary:
  • Feature: 005-implement-workflow-all
  • Branch: contrib/stharrold
  • PRs merged: 2
  • Duration: 12m 34s

Next: Run /workflow/all release when ready to deploy
```

### On Error
```
/workflow/all - Error

✗ Step 3 failed: /3_implement

Error: Test failure
  File: tests/test_workflow.py
  Line: 42
  Message: AssertionError: expected True, got False

To retry: /workflow/all
To skip:  /workflow/all --skip 3
```

## Integration Points

| Step | Command Invoked | Expected Artifacts |
|------|-----------------|-------------------|
| 0 | `/workflow:0_specify` | specs/{feature}/spec.md |
| 1 | `/workflow:1_plan` | research.md, data-model.md, contracts/, quickstart.md |
| 2 | `/workflow:2_tasks` | tasks.md |
| 3 | `/workflow:3_implement` | Source code, tests |
| 4 | `/workflow:4_integrate` | PRs created |
| 5 | `/workflow:5_release` | Release branch, PR to main |
| 6 | `/workflow:6_backmerge` | PR to develop, rebased contrib |
