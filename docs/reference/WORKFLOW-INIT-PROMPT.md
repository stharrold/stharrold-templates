---
name: workflow-v5.2-initialization-guide
version: 5.2.0
type: navigation-guide
description: Quick reference guide to workflow system - links to detailed documentation
last_updated: 2025-11-06
follows: DRY principle (references files, doesn't duplicate)
token_efficiency: 30-55% savings vs comprehensive prompt
---

# Workflow System v5.2.0 - Quick Start Guide

This repository implements a comprehensive skill-based development workflow system with 9 specialized skills, 6 workflow phases, automated quality gates, and cross-platform CI/CD support.

## Bootstrap a New Repository

**To replicate this workflow system to another repository:**

### From This Repo (if you're working in german)
```bash
python .claude/skills/initialize-repository/scripts/initialize_repository.py . ../new-repo
```

### From Downloaded Release (for existing repositories)

User downloads german release to untracked directory in their repo, then tells Claude Code:

**Prompt for Claude Code:**
> "Read `/path/to/german`. Apply the workflow from `/path/to/german` to the current repository."

This copies all 9 skills, documentation, CI/CD configs, and directory structure to the target repository.

---

## What Should I Read?

### Bootstrapping a New Repository?
→ **Read:** `.claude/skills/initialize-repository/SKILL.md` (~500 tokens)
→ **Purpose:** Understand what gets copied and how to configure the new repo
→ **Then:** Run the bootstrap command above

### Starting Phase 1 (Planning)?
→ **Read:** `.claude/skills/bmad-planner/SKILL.md` (~600 tokens)
→ **Purpose:** Interactive planning tool (Business Model, Architecture, Design)
→ **Alternative:** `.claude/skills/speckit-author/SKILL.md` if skipping BMAD planning

### Implementing a Feature (Phase 2-3)?
→ **Read:** `.claude/skills/git-workflow-manager/SKILL.md` (~700 tokens)
→ **Purpose:** Worktree creation, branch management, semantic versioning
→ **Then:** `.claude/skills/speckit-author/SKILL.md` (~800 tokens)
→ **Purpose:** Create specifications and implementation plans
→ **Then:** `.claude/skills/quality-enforcer/SKILL.md` (~400 tokens)
→ **Purpose:** Run quality gates before PR creation

### Need Full Understanding?
→ **Read:** `WORKFLOW.md` (~4,000 tokens, 2000+ lines)
→ **Purpose:** Complete guide to all 6 phases with detailed procedures

### Quick Command Reference?
→ **See:** Command table below

---

## Essential Reading (Start Here)

These files provide the foundation for understanding and using the workflow system:

### 1. `.claude/skills/initialize-repository/SKILL.md` (~500 tokens)
**Purpose:** How to bootstrap new repositories with this workflow
**When:** Phase 0 - Before starting work in a new repository
**Key Info:** Interactive Q&A flow, what gets copied, configuration options

### 2. `CLAUDE.md` - Sections: "Workflow v5.2 Architecture" + "Available Skills" (~300 tokens)
**Purpose:** Repository-specific guidance and skill overview
**When:** First time working with this repository
**Key Info:** 9 skills list, workflow version, tech stack, branch structure

### 3. `WORKFLOW.md` - Phase 0 section (~400 tokens) OR full file (~4,000 tokens)
**Purpose:** Detailed workflow procedures
**When:** Need step-by-step guidance for specific phase
**Key Info:** Complete 6-phase workflow, commands, integration patterns

---

## Phase-Specific Reading

### Phase 0: Repository Initialization (One-Time)

**Essential:**
- `.claude/skills/initialize-repository/SKILL.md` - Bootstrap new repos
- `.github/workflows/tests.yml` - GitHub Actions CI/CD reference
- `azure-pipelines.yml` - Azure Pipelines CI/CD reference

**Commands:**
```bash
python .claude/skills/initialize-repository/scripts/initialize_repository.py <source> <target>
```

---

### Phase 1: Planning (Main Repo, contrib branch)

**Essential:**
- `.claude/skills/bmad-planner/SKILL.md` - Interactive planning with 3 personas
- `WORKFLOW.md` - Phase 1 section (lines ~200-400)

**Commands:**
```bash
python .claude/skills/bmad-planner/scripts/create_planning.py <slug> <gh_user>
```

**Output:** `planning/<slug>/` with requirements.md, architecture.md, epics.md

---

### Phase 2-3: Implementation + Quality (Feature Worktree)

**Essential:**
- `.claude/skills/git-workflow-manager/SKILL.md` - Worktree and branch management
- `.claude/skills/speckit-author/SKILL.md` - Specification generation
- `.claude/skills/quality-enforcer/SKILL.md` - Quality gates
- `WORKFLOW.md` - Phase 2-3 sections (lines ~400-800)

**Commands:**
```bash
# Create worktree
python .claude/skills/git-workflow-manager/scripts/create_worktree.py feature <slug> contrib/<gh_user>

# Create specifications (in worktree)
cd ../german_feature_<slug>
python .claude/skills/speckit-author/scripts/create_specifications.py feature <slug> <gh_user> --todo-file ../TODO_feature_*.md

# Run quality gates
python .claude/skills/quality-enforcer/scripts/run_quality_gates.py

# Calculate semantic version
python .claude/skills/git-workflow-manager/scripts/semantic_version.py develop v1.5.0
```

**Output:** `specs/<slug>/` with spec.md, plan.md

---

### Phase 4: Integration (Main Repo, contrib branch)

**Essential:**
- `.claude/skills/workflow-utilities/SKILL.md` - TODO management and archival
- `.claude/skills/speckit-author/SKILL.md` - As-built documentation update
- `WORKFLOW.md` - Phase 4 section (lines ~800-1000)

**Commands:**
```bash
# After PR merge: Archive workflow
python .claude/skills/workflow-utilities/scripts/workflow_archiver.py TODO_feature_*.md --summary "Completed feature" --version "1.6.0"

# Update BMAD with as-built (optional)
python .claude/skills/speckit-author/scripts/update_asbuilt.py planning/<slug> specs/<slug>

# Daily rebase contrib
python .claude/skills/git-workflow-manager/scripts/daily_rebase.py contrib/<gh_user>
```

---

### Phase 5: Release (Main Repo)

**Essential:**
- `.claude/skills/git-workflow-manager/SKILL.md` - Release scripts
- `WORKFLOW.md` - Phase 5 section (lines ~1000-1400)

**Commands:**
```bash
# Create release branch
python .claude/skills/git-workflow-manager/scripts/create_release.py v1.6.0 develop

# After PR merge: Tag release
python .claude/skills/git-workflow-manager/scripts/tag_release.py v1.6.0 main

# Back-merge to develop
python .claude/skills/git-workflow-manager/scripts/backmerge_release.py v1.6.0 develop

# Cleanup release branch
python .claude/skills/git-workflow-manager/scripts/cleanup_release.py v1.6.0
```

---

### Phase 6: Hotfix (Hotfix Worktree from main)

**Essential:**
- `.claude/skills/git-workflow-manager/SKILL.md` - Hotfix worktree creation
- `WORKFLOW.md` - Phase 6 section (lines ~1400-1600)

**Commands:**
```bash
# Create hotfix worktree
python .claude/skills/git-workflow-manager/scripts/create_worktree.py hotfix <slug> main

# (Optional) Create specifications for complex fixes
python .claude/skills/speckit-author/scripts/create_specifications.py hotfix <slug> <gh_user>

# Run quality gates
python .claude/skills/quality-enforcer/scripts/run_quality_gates.py

# After PR merge: Tag hotfix
python .claude/skills/git-workflow-manager/scripts/tag_release.py v1.3.0-hotfix.1 main

# Back-merge to develop
python .claude/skills/git-workflow-manager/scripts/backmerge_release.py v1.3.0-hotfix.1 develop
```

---

## Quick Command Reference

| Phase | Command | Purpose |
|-------|---------|---------|
| 0 | `initialize_repository.py <source> <target>` | Bootstrap new repo |
| 0 | `detect_stack.py` | Detect project configuration |
| 1 | `create_planning.py <slug> <user>` | BMAD planning (interactive) |
| 2 | `create_worktree.py feature <slug> contrib/<user>` | Create feature worktree |
| 2 | `create_specifications.py feature <slug> <user> --todo-file <path>` | Create specs (interactive) |
| 3 | `run_quality_gates.py` | Run all quality checks |
| 3 | `semantic_version.py <base> <current>` | Calculate next version |
| 4 | `workflow_archiver.py <todo-file> --summary "..." --version "X.Y.Z"` | Archive completed workflow |
| 4 | `update_asbuilt.py planning/<slug> specs/<slug>` | Update BMAD with as-built |
| 4 | `daily_rebase.py contrib/<user>` | Rebase contrib on develop |
| 5 | `create_release.py <version> develop` | Create release branch |
| 5 | `tag_release.py <version> main` | Tag release on main |
| 5 | `backmerge_release.py <version> develop` | Back-merge to develop |
| 5 | `cleanup_release.py <version>` | Delete release branch |
| 6 | `create_worktree.py hotfix <slug> main` | Create hotfix worktree |
| * | `todo_updater.py <file> <task_id> <status>` | Update task status |
| * | `deprecate_files.py <todo-file> "<desc>" <file1>...` | Archive old files |

---

## All 9 Skills Reference

For detailed documentation on each skill, read their respective SKILL.md files:

### Phase 0: Bootstrapping
1. **initialize-repository** - `.claude/skills/initialize-repository/SKILL.md`
   - Purpose: Bootstrap new repositories with complete workflow system
   - Token savings: 96% reduction (~3,350 tokens saved)

2. **tech-stack-adapter** - `.claude/skills/tech-stack-adapter/SKILL.md`
   - Purpose: Detect project configuration (Python/uv/Podman)
   - Always loaded first in each session

### Phase 1: Planning
3. **bmad-planner** - `.claude/skills/bmad-planner/SKILL.md`
   - Purpose: Interactive planning with 3 personas (Analyst, Architect, PM)
   - Token savings: 92% reduction (~2,300 tokens saved)

### Phase 2-3: Implementation
4. **git-workflow-manager** - `.claude/skills/git-workflow-manager/SKILL.md`
   - Purpose: Git operations (worktrees, branches, versioning, PRs)
   - Key: Manages protected branches (main, develop)

5. **speckit-author** - `.claude/skills/speckit-author/SKILL.md`
   - Purpose: Create specifications and implementation plans
   - Token savings: 85-90% reduction (~1,700-2,700 tokens saved)
   - Integration: Auto-detects BMAD planning for context reuse

6. **quality-enforcer** - `.claude/skills/quality-enforcer/SKILL.md`
   - Purpose: Enforce quality gates (≥80% coverage, tests pass, linting, typing)

### Cross-Phase: Utilities
7. **workflow-utilities** - `.claude/skills/workflow-utilities/SKILL.md`
   - Purpose: Shared utilities (directories, TODO management, file deprecation, VCS abstraction)
   - Used by all other skills

8. **workflow-orchestrator** - `.claude/skills/workflow-orchestrator/SKILL.md`
   - Purpose: Coordinate workflow phases, progressive skill loading
   - Context management: Checkpoint at 100K tokens

### Optional Advanced
9. **agentdb-state-manager** - `.claude/skills/agentdb-state-manager/SKILL.md`
   - Purpose: Persistent state tracking with DuckDB (analytics cache)
   - Token savings: 89% reduction (~2,500 tokens saved for complex queries)
   - Note: TODO_*.md files remain source of truth

---

## Additional Documentation

### Workflow Standards
- `WORKFLOW.md` - Complete 6-phase workflow guide (2000+ lines)
- `CONTRIBUTING.md` - Contributor guidelines and standards
- `.claude/skills/UPDATE_CHECKLIST.md` - How to update skills properly

### Configuration Files
- `pyproject.toml` - Python project configuration (version, deps, quality thresholds)
- `.gitignore` - Git exclusions
- `.github/workflows/tests.yml` - GitHub Actions CI/CD
- `azure-pipelines.yml` - Azure Pipelines CI/CD

### Directory Standards
Every directory must contain:
- `CLAUDE.md` - Context for Claude Code
- `README.md` - Human-readable documentation
- `ARCHIVED/` subdirectory (except ARCHIVED itself)

See `.claude/skills/workflow-utilities/SKILL.md` for directory creation utilities.

---

## Branch Protection (CRITICAL)

**Protected branches:**
- **`main`** - Production (tagged releases only)
- **`develop`** - Integration (PR merges only)

**Rules:**
- ❌ NEVER commit directly to main or develop
- ❌ NEVER delete main or develop
- ✅ ONLY merge via pull requests (reviewed and approved)

**Exception:** `backmerge_release.py` commits to develop (Phase 5.5) - documented in WORKFLOW.md

**Enforcement:** See `.github/BRANCH_PROTECTION.md` for GitHub configuration

---

## Quality Standards

All features must pass these gates before PR creation:

- **Test coverage:** ≥80% (configurable in pyproject.toml)
- **All tests:** Must pass (zero failures)
- **Build:** Must succeed
- **Linting:** Clean (ruff check)
- **Type checking:** Clean (mypy)

Enforced by: `.claude/skills/quality-enforcer/scripts/run_quality_gates.py`

---

## Token Efficiency Metrics

The skill-based system provides significant token savings:

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Workflow loading | 2,718 tokens | 600-900 tokens | 66-77% |
| Repository bootstrap | 3,500 tokens | 150 tokens | 96% |
| BMAD planning | 2,500 tokens | 200 tokens | 92% |
| SpecKit specifications | 2,000-3,000 tokens | 200-300 tokens | 85-90% |
| AgentDB queries | 2,800 tokens | 300 tokens | 89% |

**Progressive loading:** Only load skills needed for current phase (not all 9 at once)

---

## Context Management

**Token threshold:** 100K tokens (~73% of 136K effective capacity)

**At 100K tokens:**
1. Claude automatically saves state to TODO_*.md
2. Commits checkpoint
3. User must run `/init` + `/compact`
4. Continue working - context preserved in TODO files

**Warning at 80K tokens:** Complete current task before checkpoint

See `.claude/skills/workflow-orchestrator/SKILL.md` for details.

---

## Official Claude Code Documentation

This workflow extends official Claude Code patterns:

- **Skills:** https://docs.claude.com/en/docs/agents-and-tools/agent-skills
- **Building Agents:** https://docs.claude.com/en/docs/agents-and-tools/building-agents
- **Getting Started:** https://docs.claude.com/en/docs/claude-code/getting-started
- **Docs Map:** https://docs.claude.com/en/docs/claude-code/claude_code_docs_map.md

**Skill creation:** Use `.claude/skills/workflow-utilities/scripts/create_skill.py <skill-name>` - automatically fetches official docs and compares patterns.

---

## Summary

**This workflow system provides:**
- ✅ Complete automation (Phases 0-6)
- ✅ Token efficiency (66-96% reduction across components)
- ✅ Quality enforcement (≥80% coverage, all tests pass)
- ✅ Semantic versioning (automated from code changes)
- ✅ Progressive skill loading (600-900 tokens vs 2,718 monolithic)
- ✅ Cross-platform CI/CD (GitHub Actions + Azure Pipelines)
- ✅ VCS abstraction (GitHub + Azure DevOps support)
- ✅ Context management (checkpoint at 100K tokens)
- ✅ Living documentation (BMAD → SpecKit → As-Built feedback loop)

**Apply to any Python repository using:**
```bash
python .claude/skills/initialize-repository/scripts/initialize_repository.py . ../new-repo
```

Then refer to this guide and the linked SKILL.md files for detailed usage.
