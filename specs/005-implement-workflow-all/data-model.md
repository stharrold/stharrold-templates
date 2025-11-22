# Data Model: /workflow/all Command

## Entities

### WorkflowState
Represents the current state of the workflow, detected at runtime.

| Field | Type | Description |
|-------|------|-------------|
| current_branch | string | Git branch name |
| branch_type | enum | feature, contrib, develop, release, main |
| last_completed_step | int (0-6) | Last successfully completed step |
| is_paused | bool | Whether paused at manual gate |
| pause_reason | string? | Reason for pause (e.g., "PR merge required") |
| artifacts | ArtifactStatus | Which artifacts exist |

### ArtifactStatus
Tracks which workflow artifacts exist.

| Field | Type | Description |
|-------|------|-------------|
| spec_exists | bool | specs/{feature}/spec.md exists |
| research_exists | bool | specs/{feature}/research.md exists |
| tasks_exists | bool | specs/{feature}/tasks.md exists |
| implementation_complete | bool | All tasks marked done |

### StepResult
Result of executing a single workflow step.

| Field | Type | Description |
|-------|------|-------------|
| step_number | int (0-6) | Which step was executed |
| step_name | string | Command name (e.g., "1_plan") |
| success | bool | Whether step completed successfully |
| error | string? | Error message if failed |
| outputs | list[string] | Files/PRs created |
| manual_gate | bool | Whether this step ends at a manual gate |

### ManualGate
Defines points where workflow must pause for human action.

| Gate | After Step | Required Action |
|------|------------|-----------------|
| PR_FEATURE_CONTRIB | 4 | Merge feature→contrib PR |
| PR_CONTRIB_DEVELOP | 4 | Merge contrib→develop PR |
| PR_RELEASE_MAIN | 5 | Merge release→main PR |
| PR_RELEASE_DEVELOP | 6 | Merge release→develop PR |

## State Transitions

```
[start]
    │
    ▼
[detect_state] ──────────────────────┐
    │                                 │
    │ mode=new                        │ mode=default
    ▼                                 ▼
[step_0_specify] ◄─────────── [determine_start_step]
    │                                 │
    ▼                                 │
[step_1_plan]                         │
    │                                 │
    ▼                                 │
[step_2_tasks]                        │
    │                                 │
    ▼                                 │
[step_3_implement]                    │
    │                                 │
    ▼                                 │
[step_4_integrate] ◄──────────────────┘
    │
    ├──► [MANUAL_GATE: PR merges]
    │
    ▼
[step_5_release] ◄─── mode=release
    │
    ├──► [MANUAL_GATE: PR merge]
    │
    ▼
[step_6_backmerge]
    │
    ├──► [MANUAL_GATE: PR merge]
    │
    ▼
[complete]
```

## Branch Type Detection

```
branch_name → branch_type mapping:

/^\d{3}-/           → feature    (e.g., 005-implement-workflow-all)
/^feature\//        → feature    (e.g., feature/my-feature)
/^contrib\//        → contrib    (e.g., contrib/stharrold)
/^develop$/         → develop
/^release\//        → release    (e.g., release/v5.1.0)
/^main$/            → main
```

## Next Step Determination

| Branch Type | Artifacts | Next Step |
|-------------|-----------|-----------|
| feature | no spec | 0 (specify) |
| feature | spec only | 1 (plan) |
| feature | spec + research | 1 (plan, resume) |
| feature | spec + tasks | 3 (implement) |
| feature | all complete | 4 (integrate) |
| contrib | PRs pending | 4 (continue/wait) |
| contrib | PRs merged | 5 (release) |
| develop | has commits since last tag | 5 (release) |
| release | PR to main pending | 5 (continue/wait) |
| release | PR merged, no tag | 5 (tag-release) |
| release | tagged | 6 (backmerge) |
| main | - | 0 (new feature) |

## Validation Rules

1. **Mode Validation**:
   - `new` requires description argument
   - `release` requires current branch to be contrib or develop
   - `continue` requires previous pause state

2. **Step Prerequisites**:
   - Step N requires steps 0..(N-1) complete
   - Exception: `release` mode can skip to step 5

3. **Branch Safety**:
   - Never modify `main` or `develop` directly
   - Always end on editable branch (`contrib/*`)
