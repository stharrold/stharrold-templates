# Workflow Guide: Implementation (Step 1-2)

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Version:** 6.0.0

This document covers the initial steps of the streamlined v7x0 workflow.

---

## v7x0 Workflow Overview

The v7x0 workflow simplifies development by leveraging built-in Gemini CLI tools for autonomous planning, architecture, and implementation.

1. **[/workflow:v7x0_1-worktree](command:workflow:v7x0_1-worktree)**: Create isolated development environment.
2. **Implementation**: Autonomous development using built-in tools.
3. **[/workflow:v7x0_2-integrate](command:workflow:v7x0_2-integrate)**: Sync with main repo and develop branch.
4. **[/workflow:v7x0_3-release](command:workflow:v7x0_3-release)** & **[/workflow:v7x0_4-backmerge](command:workflow:v7x0_4-backmerge)**: Production deployment.

---

### Step 1: Create Worktree

**Location:** Main repository
**Branch:** `contrib/<gh-user>`
**Command:** `/workflow:v7x0_1-worktree "feature description"`

This command automates the creation of an isolated git worktree for your feature.

**What it does:**
1. Generates a kebab-case slug from your description.
2. Creates a new branch: `feature/YYYYMMDDTHHMMSSZ_slug`.
3. Creates a worktree directory at `../{project}_feature_...`.
4. Initializes `.gemini-state/` for worktree state isolation.
5. Records the transition in **AgentDB**.

**Output:**
- Path to the new worktree.
- Branch name.
- Instructions for the next step.

---

### Step 2: Feature Implementation

**Location:** Feature worktree
**Branch:** `feature/*`

Inside the worktree, you use built-in Gemini CLI tools to implement the feature.

**Autonomous implementation replaces legacy phases:**
- ❌ No more manual BMAD planning (Requirements/Architecture/Epics).
- ❌ No more manual SpecKit specifications (Spec/Plan).
- ❌ No more manual Quality Gates (Gemini Code Review ensures quality).

**Process:**
1. Chat with Gemini in the isolated worktree to implement the feature.
2. Gemini analyzes the codebase and creates an internal plan.
3. Gemini writes the code and tests.
4. Gemini reviews its own work for quality and security.

**Best Practices:**
- Always perform implementation in a worktree to keep the main repository clean.
- Provide a clear, detailed description of the feature to Gemini.
- Review the implemented code before returning to the main repository.

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
  --pattern phase_v7x0_1_worktree
```

---

**Next:** [Integration & Release (Step 3-4)](workflow-integration.md)
