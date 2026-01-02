---
name: workflow-v7x0-initialization-guide
version: 7.0.0
type: navigation-guide
description: Quick reference guide to v7x0 workflow system
last_updated: 2026-01-01
follows: DRY principle (references files, doesn't duplicate)
---

# Workflow System v7x0.0.0 - Quick Start Guide

This repository implements a streamlined 4-step development workflow using built-in Gemini CLI tools for autonomous implementation and automated **Gemini Code Review** for quality.

## Bootstrap a New Repository

**To replicate this workflow system to another repository:**

### From This Repo
```bash
python .gemini/skills/initialize-repository/scripts/initialize_repository.py . ../new-repo
```

### From Downloaded Release (for existing repositories)

User downloads stharrold-templates release to untracked directory in their repo, then tells Gemini Code:

**Prompt for Gemini Code:**
> "Read `/path/to/stharrold-templates`. Apply the workflow from `/path/to/stharrold-templates` to the current repository."

This copies all 6 skills, v7x0 command aliases, documentation, CI/CD configs, and directory structure.

---

## v7x0 Workflow Steps

The v7x0 workflow focuses on autonomous implementation using built-in tools.

### Step 1: Create Worktree
→ **Command:** `/workflow:v7x0_1-worktree "feature description"`
→ **Action:** Creates isolated git worktree and branch.
→ **Next:** Navigate to the worktree directory.

### Step 2: Implement Feature
→ **Action:** Chat with Gemini in the worktree to implement the feature.
→ **Example:** "Implement user authentication with JWT tokens"
→ **Next:** Return to main repo after completion.

### Step 3: Integrate
→ **Command:** `/workflow:v7x0_2-integrate ["feature/branch-name"]`
→ **Action:** Creates PR from feature to `contrib`, then `contrib` to `develop`.
→ **Next:** Merge PRs in GitHub UI.

### Step 4: Release & Backmerge
→ **Command:** `/workflow:v7x0_3-release`
→ **Action:** Creates release from `develop`, PR to `main`, tags release.
→ **Command:** `/workflow:v7x0_4-backmerge`
→ **Action:** Syncs release back to `develop`, rebases `contrib`, cleans up.

---

## Essential Reading

### 1. `GEMINI.md` (~300 tokens)
**Purpose:** Repository-specific guidance and v7x0 workflow overview.
**When:** First time working with this repository.

### 2. `WORKFLOW.md` (~1,500 tokens)
**Purpose:** Complete guide to the 4-step workflow with detailed procedures.
**When:** Need step-by-step guidance for specific steps.

---

## All 6 Skills Reference

For detailed documentation on each skill, read their respective SKILL.md files:

### Core Skills
1. **workflow-orchestrator** - `.gemini/skills/workflow-orchestrator/SKILL.md`
   - Purpose: Coordinate workflow phases and command aliases.

2. **git-workflow-manager** - `.gemini/skills/git-workflow-manager/SKILL.md`
   - Purpose: Git operations (worktrees, branches, versioning, PRs).

3. **tech-stack-adapter** - `.gemini/skills/tech-stack-adapter/SKILL.md`
   - Purpose: Detect project configuration (Python/uv/Podman).

4. **workflow-utilities** - `.gemini/skills/workflow-utilities/SKILL.md`
   - Purpose: Shared utilities (directories, file deprecation, VCS abstraction).

5. **agentdb-state-manager** - `.gemini/skills/agentdb-state-manager/SKILL.md`
   - Purpose: Persistent state tracking with AgentDB (DuckDB).

6. **initialize-repository** - `.gemini/skills/initialize-repository/SKILL.md`
   - Purpose: Bootstrap new repositories with this workflow system.

---

## Branch Protection (CRITICAL)

**Protected branches:**
- **`main`** - Production (tagged releases only)
- **`develop`** - Integration (PR merges only)

**Rules:**
- ❌ NEVER commit directly to main or develop.
- ✅ ONLY merge via pull requests (reviewed and approved).

---

## Summary

**This workflow system provides:**
- ✅ **Streamlined 4-step flow** (reduced from legacy 7-phase system).
- ✅ **Autonomous implementation** using built-in Gemini CLI tools.
- ✅ **Gemini Code Review** automated via GitHub Actions.
- ✅ **Token efficiency** through modular skills.
- ✅ **Cross-platform CI/CD** (GitHub Actions + Azure Pipelines).
