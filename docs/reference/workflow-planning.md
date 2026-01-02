# Workflow Guide: Planning & Implementation (Step 1-2)

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Version:** 6.0.0

This document covers the initial steps of the streamlined v6 workflow.

---

## v6 Workflow Overview

The v6 workflow simplifies development by leveraging Gemini's **feature-dev** plugin for autonomous planning, architecture, and implementation.

1.  **[/worktree](command:worktree)**: Create isolated development environment.
2.  **[/feature-dev](command:feature-dev)**: Autonomous implementation.
3.  **[/integrate](command:integrate)**: Sync with main repo and develop branch.
4.  **[/release](command:release)** & **[/backmerge](command:backmerge)**: Production deployment.

---

### Step 1: Create Worktree

**Location:** Main repository
**Branch:** `contrib/<gh-user>`
**Command:** `/worktree "feature description"`

This command automates the creation of an isolated git worktree for your feature.

**What it does:**
1.  Generates a kebab-case slug from your description.
2.  Creates a new branch: `feature/YYYYMMDDTHHMMSSZ_slug`.
3.  Creates a worktree directory at `../{project}_feature_...`.
4.  Initializes `.gemini-state/` for worktree state isolation.
5.  Records the transition in **AgentDB**.

**Output:**
-   Path to the new worktree.
-   Branch name.
-   Instructions for the next step.

---


### Step 2: Implement Feature (`feature-dev`)

**Location:** Feature worktree
**Branch:** `feature/*`
**Command:** `/feature-dev "feature description"`

Inside the worktree, you use the Gemini `feature-dev` plugin. This is the core of the v6 workflow.

**feature-dev replaces legacy phases:**
-   ❌ No more manual BMAD planning (Requirements/Architecture/Epics).
-   ❌ No more manual SpecKit specifications (Spec/Plan).
-   ❌ No more manual Quality Gates (feature-dev code review ensures quality).

**Process:**
1.  Gemini analyzes the codebase in the isolated worktree.
2.  Gemini creates an internal plan.
3.  Gemini writes the code and tests.
4.  Gemini reviews its own work for quality and security.

**Best Practices:**
-   Always run `feature-dev` in a worktree to keep the main repository clean.
-   Provide a clear, detailed description of the feature.
-   Review the implemented code before returning to the main repository.

---


## State Tracking (AgentDB)

Workflow state is tracked in **AgentDB** (DuckDB) located in `.gemini-state/agentdb.duckdb`.

**Query State:**
```bash
uv run python .gemini/skills/agentdb-state-manager/scripts/query_workflow_state.py
```

**Record Transition:**
```bash
uv run python .gemini/skills/agentdb-state-manager/scripts/record_sync.py \
  --sync-type workflow_transition \
  --pattern phase_v6_1_worktree
```

---

**Next:** [Integration & Release (Step 3-4)](workflow-integration.md)
