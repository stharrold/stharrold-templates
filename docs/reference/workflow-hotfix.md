# Workflow Guide: Hotfix (Production Fixes)

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Version:** 6.0.0

This document covers the hotfix workflow for urgent production issues.

---

## Overview

A hotfix is an urgent fix for a production issue. It follows a similar flow to features but branches from **`main`** instead of `develop`.

**When to use hotfixes:**
- Critical production bugs.
- Security vulnerabilities.
- Data corruption emergencies.

---

### Step 1: Create Hotfix Worktree

**Location:** Main repository
**Branch:** `main`
**Command:** `/workflow:v7x1_1-worktree "hotfix: brief description"`

The `/workflow:v7x1_1-worktree` command handles hotfix creation when run from the `main` branch (or by specifying `main` as base).

**Side effects:**
- Creates a `hotfix/YYYYMMDDTHHMMSSZ_slug` branch from `main`.
- Creates an isolated worktree directory.
- Records the transition in **AgentDB**.

---

### Step 2: Implement Fix

**Location:** Hotfix worktree
**Action:** Implement the fix using built-in Gemini CLI tools.

Inside the worktree, chat with Gemini to implement the fix.

**Best Practices:**
- **Minimal Changes**: Fix only the immediate issue.
- **Regression Tests**: Always include tests that prove the fix works and prevent recurrence.
- **Speed with Quality**: Even for urgent fixes, Gemini ensures code quality and correctness.

---

### Step 3: Integrate & Deploy

**Location:** Main repository
**Command:** `/workflow:v7x1_2-integrate "hotfix/branch-name"`

Integrating a hotfix involves merging into both production and development lines.

1. **Merge to Main**: Create a PR from **hotfix** → **main**.
2. **Tag Release**: After merging, use `/workflow:v7x1_3-release` to tag the new production version (e.g., `v7.0.1`).
3. **Backmerge to Develop**: Use `/workflow:v7x1_4-backmerge` to sync the fix into the `develop` branch.

---

## Production Safety & Rollback

### Instant Rollback
If a hotfix or release breaks production, the fastest solution is to redeploy the **previous tag**.

```bash
# Checkout last known good tag
git checkout v7.0.0
# Deploy this state to production
```

### Reverting a Bad Merge
If you need to remove a bad release from the `main` branch history:

1. Identify the merge commit.
2. Run `git revert -m 1 <merge-commit-hash>`.
3. Tag the revert as a new patch version (e.g., `v7.0.2`).
4. Deploy the new tag.

---

## Hotfix vs Feature Comparison

| Aspect | Feature Workflow | Hotfix Workflow |
|--------|-----------------|-----------------|
| **Base Branch** | `develop` (via `contrib`) | `main` |
| **Tool** | Gemini CLI | Gemini CLI |
| **Target Branch** | `develop` | `main` (then backmerge to `develop`) |
| **Urgency** | Standard | High |

---

**Next:** [Operations & Maintenance](workflow-operations.md)
