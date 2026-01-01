# Application Guide: Applying stharrold-templates

Step-by-step instructions for applying the workflow system to target repositories.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Method 1: initialize_repository.py (New Repositories)](#method-1-initialize_repositorypy-new-repositories)
3. [Method 2: Manual Copy + Merge (Single Existing Repo)](#method-2-manual-copy--merge-single-existing-repo)
4. [Method 3: apply-workflow-batch.sh (Multiple Repos)](#method-3-apply-workflow-batchsh-multiple-repos)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before applying the workflow, ensure:

### For All Methods
- [ ] Git installed and configured
- [ ] Python 3.11+ installed
- [ ] UV package manager installed (`pip install uv`)
- [ ] Comfortable with command line operations
- [ ] Understand git basics (commit, branch, diff)

### For Target Repository
- [ ] Is a git repository (`git status` works)
- [ ] All changes committed (clean working directory)
- [ ] On correct branch (usually `contrib/<user>` or `develop`)
- [ ] No merge conflicts pending

### For Batch Operations
- [ ] Bash shell available (Git Bash on Windows, or WSL)
- [ ] Access to D:\Projects\ directory
- [ ] Write permissions on target repositories

---

## Method 1: initialize_repository.py (New Repositories)

**Best for:** Creating new repositories with complete workflow system

### Step 1: Prepare

```bash
# Ensure stharrold-templates is up to date
cd D:\Projects\stharrold-templates
git status  # Should be clean
git pull    # Get latest changes
```

### Step 2: Run Script

```bash
# For new repository in Gemini_Sessions
python D:\Projects\stharrold-templates\.gemini\skills\initialize-repository\scripts\initialize_repository.py \
  D:\Projects\stharrold-templates \
  D:\Projects\Gemini_Sessions\my-new-project
```

### Step 3: Answer Interactive Questions

**Phase 1: Configuration (9 questions)**

1. **Repository purpose** (select one):
   - Web application (FastAPI, Flask, Django)
   - CLI tool
   - Library/package
   - Data analysis
   - Machine learning
   - Other

2. **Brief description** (one line):
   - Example: "HIPAA-compliant SQL query execution tool"

3. **GitHub username** (auto-detected from `gh whoami`):
   - Example: "stharrold"

4. **Python version** (select one):
   - 3.11 (recommended for Synapse compatibility)
   - 3.12
   - 3.13

5. **Copy workflow system?**
   - Answer: YES (required for complete setup)

6. **Copy domain content (src/, resources/)?**
   - YES if you want sample code structure
   - NO for clean start

7. **Copy tests?**
   - YES if you want test structure
   - NO to write from scratch

8. **Copy containers (Containerfile, podman-compose.yml)?**
   - YES if using containerized development
   - NO if not using containers

9. **Copy CI/CD pipelines (.github/workflows)?**
   - YES if using GitHub Actions
   - NO if using other CI/CD or none

**Phase 2: Git Setup (4-5 questions)**

10. **Initialize git repository?**
    - YES for new repo
    - NO if repo already exists

11. **Create branch structure?** (if git=yes)
    - YES to create main, develop, contrib/<user>
    - NO for manual branch management

12. **Set up remote?** (if branches=yes)
    - YES to add remote origin
    - NO for local-only

13. **Remote URL?** (if remote=yes)
    - Example: `https://github.com/username/repo.git`

14. **Push to remote?** (if remote URL provided)
    - YES to push branches immediately
    - NO to push manually later

### Step 4: Review Output

Script will report:
```
✅ Created repository structure
✅ Copied 9 workflow skills
✅ Generated README.md, GEMINI.md, pyproject.toml
✅ Initialized git with 3-branch structure
✅ Pushed to remote

🎉 Repository initialized successfully!
```

### Step 5: Setup

```bash
cd D:\Projects\Gemini_Sessions\my-new-project

# Install dependencies
uv sync

# Run tests
uv run pytest

# Verify quality gates
python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
```

---

## Method 2: Manual Copy + Merge (Single Existing Repo)

**Best for:** Existing repositories with established code

### Step 1: Create Test Copy

```bash
# Create backup and test copy
cd D:\Projects
cp -r existing-repo existing-repo-backup-$(date +%Y%m%d)
cp -r existing-repo existing-repo-test
```

### Step 2: Copy Workflow Components to Test Copy

```bash
cd D:\Projects\existing-repo-test

# Copy .gemini directory
cp -r D:\Projects\stharrold-templates\.gemini .

# Copy workflow documentation
cp D:\Projects\stharrold-templates\WORKFLOW.md .
cp D:\Projects\stharrold-templates\docs\reference\WORKFLOW-INIT-PROMPT.md .

# Optional: Copy additional components
cp D:\Projects\stharrold-templates\Containerfile .
cp D:\Projects\stharrold-templates\podman-compose.yml .
```

### Step 3: Merge GEMINI.md

```bash
# Option A: Append workflow section to existing GEMINI.md
cat >> GEMINI.md << 'EOF'

## Standard Workflow System

This repository uses **Standard Workflow v1.15.1** with 9 specialized skills.

### Workflow Skills (Located in `.gemini/skills/`)

1. **workflow-orchestrator** - Main coordinator for workflow phases
2. **tech-stack-adapter** - Detects Python/uv project configuration
3. **git-workflow-manager** - Git operations, worktrees, semantic versioning
4. **bmad-planner** - Business Model + Architecture + Design planning
5. **speckit-author** - Specification generation with BMAD context reuse
6. **quality-enforcer** - Quality gates (≥80% coverage, linting, typing)
7. **workflow-utilities** - Shared utilities (file deprecation, TODO management)
8. **initialize-repository** - Bootstrap new repositories from template
9. **agentdb-state-manager** - DuckDB state tracking with MIT Agent Synchronization Pattern

### Quality Standards

**Enforced by quality-enforcer skill:**
- Test coverage ≥ 80%
- All tests passing
- Linting clean (ruff)
- Type checking strict (mypy --strict)

**Run quality gates:**
```bash
python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
```

### Workflow Documentation

- **Complete workflow guide:** `WORKFLOW.md`
- **Quick reference card:** `WORKFLOW-INIT-PROMPT.md`

EOF

# Option B: Manual edit with preferred editor
vim GEMINI.md  # Or: code GEMINI.md, nano GEMINI.md, etc.
```

### Step 4: Review Changes

```bash
cd D:\Projects\existing-repo-test

# Check what was added
git status

# Review detailed changes
git diff

# Verify skills were copied
ls .gemini/skills/

# Should show 9 directories:
#   agentdb-state-manager/
#   bmad-planner/
#   git-workflow-manager/
#   initialize-repository/
#   quality-enforcer/
#   speckit-author/
#   tech-stack-adapter/
#   workflow-orchestrator/
#   workflow-utilities/
```

### Step 5: Test Quality Gates

```bash
cd D:\Projects\existing-repo-test

# Install dependencies (if not already done)
uv sync

# Run quality gates
python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py

# Expected output:
# [1/5] Test Coverage...
# [2/5] Tests...
# [3/5] Build...
# [4/5] Linting...
# [5/5] AI Config Sync...
```

### Step 6: Apply to Production Repository

If satisfied with test copy:

```bash
# Copy to production
cp -r D:\Projects\existing-repo-test\.gemini D:\Projects\existing-repo\
cp D:\Projects\existing-repo-test\WORKFLOW.md D:\Projects\existing-repo\
cp D:\Projects\existing-repo-test\WORKFLOW-INIT-PROMPT.md D:\Projects\existing-repo\

# Merge GEMINI.md changes (manual)
# (Open both files and copy workflow section)
```

### Step 7: Commit

```bash
cd D:\Projects\existing-repo

# Stage all changes
git add .

# Commit
git commit -m "feat: integrate Standard Workflow v1.15.1 system

Applied stharrold-templates workflow to existing repository:

✅ Added workflow system:
- .gemini/ directory with 9 specialized skills
- WORKFLOW.md and WORKFLOW-INIT-PROMPT.md
- Updated GEMINI.md with workflow section

✅ Quality gates configured:
- Test coverage ≥ 80%
- Linting (ruff)
- Type checking (mypy --strict)

Source: D:\Projects\stharrold-templates (v1.15.1)

🤖 Generated with [Gemini Code](https://gemini.com/gemini-code)

Co-Authored-By: Gemini <noreply@anthropic.com>"
```

---

## Method 3: apply-workflow-batch.sh (Multiple Repos)

**Best for:** Applying workflow to multiple repositories at once

### Step 1: Update Batch Script

Before running, verify/update the script:

```bash
# Open script for editing
code D:\Projects\apply-workflow-batch.sh
# Or: vim D:\Projects\apply-workflow-batch.sh
```

#### 1.1: Update Source Paths (Lines 21-23)

**Current:**
```bash
SOURCE_GEMINI="D:/Projects/sql/.gemini"
SOURCE_WORKFLOW="D:/Projects/sql/WORKFLOW.md"
SOURCE_WORKFLOW_INIT="D:/Projects/sql/WORKFLOW-INIT-PROMPT.md"
```

**Updated to use stharrold-templates:**
```bash
SOURCE_GEMINI="D:/Projects/stharrold-templates/.gemini"
SOURCE_WORKFLOW="D:/Projects/stharrold-templates/WORKFLOW.md"
SOURCE_WORKFLOW_INIT="D:/Projects/stharrold-templates/docs/reference/WORKFLOW-INIT-PROMPT.md"
```

#### 1.2: Update PROJECTS Array (Lines 8-19)

**Current (10 projects):**
```bash
PROJECTS=(
    "app_geocode"
    "CBIA"
    "Demand"
    "emails"
    "GeocodedAddresses"
    "Huddles"
    "NRC"
    "PerformanceGoals"
    "Rooms"
    "SysIntg"
)
```

**Add missing projects (15 total):**
```bash
PROJECTS=(
    "app_geocode"
    "azure-devops"
    "azure-pr-reviewer"
    "catalog"
    "CBIA"
    "CPSC"
    "Demand"
    "emails"
    "GeocodedAddresses"
    "Huddles"
    "NRC"
    "OracleERP"
    "PerformanceGoals"
    "Rooms"
    "SysIntg"
)
```

### Step 2: Dry Run (Recommended)

Test on a single project first:

```bash
cd D:\Projects

# Edit script to use only one project
# Temporarily change PROJECTS=("app_geocode")

# Run script
bash apply-workflow-batch.sh

# Review the results
cd app_geocode
git log -1 --stat
git diff HEAD~1
```

### Step 3: Run Batch Script

```bash
cd D:\Projects
bash apply-workflow-batch.sh
```

**Expected output:**
```
================================================
Applying Standard Workflow v1.15.1 to 15 projects
Source: D:/Projects/stharrold-templates/.gemini
================================================

========================================
Processing: app_geocode
========================================
  [1/5] Creating checkpoint commit...
  [2/5] Copying .gemini/ directory...
  [3/5] Copying WORKFLOW documentation...
  [4/5] Adding Standard Workflow section to GEMINI.md...
  [5/5] Committing workflow integration...
  ✅ app_geocode complete!

... (repeat for each project)

================================================
Batch workflow application complete!
================================================

Projects updated:
  ✅ app_geocode
  ✅ azure-devops
  ✅ azure-pr-reviewer
  ...
```

### Step 4: Review Automated Commits

For each project:

```bash
cd D:\Projects\<project>

# View recent commits
git log --oneline -5

# Review workflow integration commit
git show HEAD

# Check what was added
git diff HEAD~1 --stat
```

---

## Verification

After applying any method, verify the installation:

### 1. Run verify-workflow.sh

```bash
cd D:\Projects
bash verify-workflow.sh
```

**Expected output:**
```
✅ app_geocode: 9 skills
    - agentdb-state-manager
    - bmad-planner
    - git-workflow-manager
    - initialize-repository
    - quality-enforcer
    - speckit-author
    - tech-stack-adapter
    - workflow-orchestrator
    - workflow-utilities

✅ catalog: 9 skills
    ...
```

### 2. Verify Skills Manually

```bash
cd D:\Projects\<project>

# Count skills
ls .gemini/skills/ | wc -l
# Should output: 9

# List skills
ls .gemini/skills/
```

### 3. Test Quality Gates

```bash
cd D:\Projects\<project>

# Install dependencies (if not done)
uv sync

# Run quality gates
python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
```

### 4. Verify Documentation

Check that these files exist:
- [ ] `.gemini/skills/` (9 subdirectories)
- [ ] `WORKFLOW.md`
- [ ] `WORKFLOW-INIT-PROMPT.md` (optional)
- [ ] `GEMINI.md` (with Standard Workflow section)

---

## Troubleshooting

### Issue 1: "Permission denied" when copying files

**Cause:** Insufficient permissions
**Solution:**
```bash
# On Windows, run as administrator
# Or check file permissions:
icacls D:\Projects\stharrold-templates\.gemini
```

### Issue 2: Script skips all projects with "Already has .gemini directory"

**Cause:** Projects already have `.gemini/` (batch script skips by default)
**Solution:**
```bash
# Option A: Remove existing .gemini/ first (backup first!)
mv .gemini .gemini-backup-$(date +%Y%m%d)
bash apply-workflow-batch.sh

# Option B: Manual copy to update
cp -r D:\Projects\stharrold-templates\.gemini\skills\* D:\Projects\<project>\.gemini\skills\
```

### Issue 3: Git commit fails with "nothing to commit"

**Cause:** Files already exist and are unchanged
**Solution:** This is expected if workflow was already applied

### Issue 4: Quality gates fail after application

**Cause:** Dependencies not installed or project doesn't meet standards yet
**Solution:**
```bash
# Install dependencies
uv sync

# Fix linting issues
uv run ruff check --fix .

# Add tests to meet 80% coverage
```

### Issue 5: GEMINI.md workflow section duplicated

**Cause:** Script appended section multiple times
**Solution:** Manually edit GEMINI.md to remove duplicate

### Issue 6: Wrong branch after application

**Cause:** Script doesn't change branches
**Solution:**
```bash
# Check current branch
git branch --show-current

# Switch to desired branch
git checkout contrib/<user>
```

### Issue 7: "Command not found: bash"

**Cause:** Bash shell not available (Windows)
**Solution:**
```powershell
# Install Git for Windows (includes Git Bash)
# Or use WSL (Windows Subsystem for Linux)
wsl bash apply-workflow-batch.sh
```

---

## Post-Application Checklist

After applying workflow to any repository:

- [ ] Ran `verify-workflow.sh` - confirmed 9 skills
- [ ] Tested quality gates - all passed or noted failures
- [ ] Reviewed `git diff` - no unexpected changes
- [ ] Updated `.vcs_config.yaml` if using Azure DevOps
- [ ] Tested slash commands (`/workflow/all --help`)
- [ ] Verified GEMINI.md has workflow section
- [ ] Committed all changes with descriptive message
- [ ] Pushed to remote (if applicable)
- [ ] Updated [Project Inventory](project-inventory.md) status

---

## Next Steps

1. **Learn the workflow:** Read `WORKFLOW.md` in your repository
2. **Try a feature:** Run `/workflow/all new "test feature"`
3. **Understand quality gates:** Review `.gemini/skills/quality-enforcer/SKILL.md`
4. **Customize:** Edit GEMINI.md for project-specific instructions
5. **Get help:** See workflow documentation in `docs/reference/`

---

## Additional Resources

- [Decision Matrix](decision-matrix.md) - Choosing the right method
- [Version Mapping](version-mapping.md) - Understanding version numbers
- [Project Inventory](project-inventory.md) - Current deployment status
- `stharrold-templates/WORKFLOW.md` - Complete workflow guide
- `.gemini/skills/initialize-repository/SKILL.md` - Detailed script documentation
