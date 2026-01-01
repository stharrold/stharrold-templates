# Contract: Slash Commands

**Feature**: 008-workflow-skill-integration
**Date**: 2025-11-23

## Overview

Each slash command MUST invoke the specified skills and record state in AgentDB.

---

## /1_specify Contract

**Input**: Feature description (string)
**Output**: Planning docs, worktree, state record

**Invocations**:
```bash
# 1. Detect stack (once per session)
podman-compose run --rm dev python .gemini/skills/tech-stack-adapter/scripts/detect_stack.py

# 2. Create GitHub Issue (optional, can be manual)
gh issue create --title "Feature: {description}" --label "feature"

# 3. Create planning documents (interactive)
podman-compose run --rm dev python .gemini/skills/bmad-planner/scripts/create_planning.py \
  --slug {slug} \
  --issue {issue-number}

# 4. Create worktree (no TODO file)
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/create_worktree.py \
  feature {slug} contrib/stharrold \
  --no-todo

# 5. Record state
podman-compose run --rm dev python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_1_specify \
  --source "planning/{slug}" \
  --target "worktree"
```

**Postconditions**:
- `planning/{slug}/` exists with requirements.md, architecture.md, epics.md
- Worktree exists at `../{project}_feature_{slug}/`
- AgentDB has sync record with pattern `phase_1_specify`

---

## /2_plan Contract

**Input**: None (reads from planning/)
**Output**: Specifications, state record

**Preconditions**:
- Must be in worktree
- `../planning/{slug}/` exists (from /1_specify)

**Invocations**:
```bash
# 1. Create specifications (interactive)
podman-compose run --rm dev python .gemini/skills/speckit-author/scripts/create_specifications.py \
  feature {slug} stharrold \
  --planning-dir ../planning/{slug} \
  --issue {issue-number}

# 2. Record state
podman-compose run --rm dev python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_2_plan \
  --source "../planning/{slug}" \
  --target "specs/{slug}"
```

**Postconditions**:
- `specs/{slug}/spec.md` exists
- `specs/{slug}/plan.md` exists with tasks
- AgentDB has sync record with pattern `phase_2_plan`

---

## /3_tasks Contract

**Input**: None (reads from specs/)
**Output**: Validated task list, state record

**Preconditions**:
- Must be in worktree
- `specs/{slug}/plan.md` exists with ## Tasks section

**Invocations**:
```bash
# 1. Validate tasks exist (Gemini reads plan.md directly)
# No script call - validation is inline

# 2. Record state
podman-compose run --rm dev python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_3_tasks \
  --source "specs/{slug}/plan.md"
```

**Postconditions**:
- Tasks parsed and ready for execution
- AgentDB has sync record with pattern `phase_3_tasks`

---

## /4_implement Contract

**Input**: Tasks from plan.md
**Output**: Implementation, quality gates passed, state record

**Preconditions**:
- Must be in worktree
- Tasks validated (/3_tasks completed)

**Invocations**:
```bash
# 1. Execute tasks (Gemini uses TodoWrite internally)

# 2. Run quality gates
podman-compose run --rm dev python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py

# 3. Calculate semantic version
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/semantic_version.py \
  develop v{current-version}

# 4. Record state
podman-compose run --rm dev python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type quality_gate \
  --pattern phase_4_implement
```

**Postconditions**:
- All tasks completed
- Quality gates pass (5/5)
- Semantic version calculated
- AgentDB has sync record with pattern `phase_4_implement`

---

## /5_integrate Contract

**Input**: Quality gates passed
**Output**: PRs created, worktree cleaned, state record

**Invocations**:
```bash
# 1. PR feature → contrib
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/pr_workflow.py finish-feature

# [MANUAL GATE: merge PR]

# 2. Cleanup worktree (no TODO archival)
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/cleanup_feature.py \
  {slug} --no-archive

# 3. Close GitHub Issue
gh issue close {issue-number} --comment "Implemented in PR #{pr-number}"

# 4. Sync GEMINI.md → AGENTS.md
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents

# 5. PR contrib → develop
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/pr_workflow.py start-develop

# 6. Record state
podman-compose run --rm dev python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_5_integrate
```

**Postconditions**:
- Feature PR merged
- Worktree deleted
- GitHub Issue closed
- Contrib → develop PR created
- AgentDB has sync record with pattern `phase_5_integrate`

---

## /6_release Contract

**Input**: Features integrated to develop
**Output**: Release branch, PR to main, tag, state record

**Invocations**:
```bash
# 1-4. Release workflow steps
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/release_workflow.py create-release
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/release_workflow.py run-gates
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/release_workflow.py pr-main
# [MANUAL GATE: merge PR]
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/release_workflow.py tag-release

# 5. Record state
podman-compose run --rm dev python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_6_release
```

**Postconditions**:
- Release branch created
- Release PR merged to main
- Tag created
- AgentDB has sync record with pattern `phase_6_release`

---

## /7_backmerge Contract

**Input**: Release tagged on main
**Output**: Branches synced, release cleaned, state record

**Invocations**:
```bash
# 1-3. Backmerge workflow steps
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/backmerge_workflow.py pr-develop
# [MANUAL GATE: merge PR]
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/backmerge_workflow.py rebase-contrib
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/backmerge_workflow.py cleanup-release

# 4. Record state
podman-compose run --rm dev python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_7_backmerge
```

**Postconditions**:
- Backmerge PR merged to develop
- Contrib rebased on develop
- Release branch deleted
- Backmerge branch deleted
- AgentDB has sync record with pattern `phase_7_backmerge`
- Workflow on `contrib/*` branch (editable)
