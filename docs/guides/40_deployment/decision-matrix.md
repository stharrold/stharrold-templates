# Decision Matrix: Choosing an Application Method

This guide helps you select the appropriate method for applying stharrold-templates to your repository.

## Method Overview

| Method | Best For | Tool | Interactive | Safe for Existing |
|--------|----------|------|-------------|-------------------|
| **initialize_repository.py** | New repositories | Script | Yes (13-14 questions) | Conditional |
| **Manual Copy + Merge** | Single existing repo | Manual | No | Yes (full control) |
| **apply-workflow-batch.sh** | Multiple existing repos | Script | No | Conditional |
| **verify-workflow.sh** | Verification only | Script | No | Yes (read-only) |

## Decision Tree

```
┌─────────────────────────────────────────────┐
│ Do you have an existing git repository?    │
└───────────┬─────────────────────────────────┘
            │
     ┌──────┴───────┐
     │              │
    No             Yes
     │              │
     ▼              ▼
┌────────────┐  ┌──────────────────────────────────┐
│ Use:       │  │ Is the repo empty/new structure? │
│ initialize │  └───────────┬──────────────────────┘
│ _repository│              │
│ .py        │       ┌──────┴──────┐
└────────────┘       │             │
                    Yes           No
                     │             │
                     ▼             ▼
           ┌──────────────┐  ┌─────────────────────────┐
           │ Use:         │  │ How many repositories?  │
           │ initialize   │  └──────────┬──────────────┘
           │ _repository  │             │
           │ .py (safe)   │      ┌──────┴───────┐
           └──────────────┘      │              │
                              1 repo        Multiple
                                 │              │
                                 ▼              ▼
                      ┌──────────────────┐  ┌──────────────┐
                      │ Use:             │  │ Use:         │
                      │ Manual Copy +    │  │ apply-       │
                      │ Merge            │  │ workflow-    │
                      │ (safest)         │  │ batch.sh     │
                      └──────────────────┘  └──────────────┘
```

## Method Details

### Method 1: initialize_repository.py

**When to use:**
- Creating a brand new repository
- Empty repository with minimal existing files
- Want interactive guidance
- Need complete workflow setup

**Pros:**
- Interactive Q&A (13-14 questions)
- Auto-generates all files (README, CLAUDE.md, pyproject.toml)
- Sets up git branches (main, develop, contrib/<user>)
- Validates setup after completion
- Token efficient (96% savings vs manual)

**Cons:**
- May overwrite existing files
- Less control over individual components
- Not ideal for established projects

**Command:**
```bash
python stharrold-templates/.claude/skills/initialize-repository/scripts/initialize_repository.py \
  D:\Projects\stharrold-templates D:\Projects\target-repo
```

**Interactive questions:**
1. Repository purpose
2. Brief description
3. GitHub username
4. Python version
5-9. Component selection (workflow, domain content, tests, containers, CI/CD)
10-14. Git setup (initialize, branches, remote, push)

---

### Method 2: Manual Copy + Merge

**When to use:**
- Single existing repository with established code
- Need maximum control
- Want to review changes before applying
- Have custom configurations to preserve

**Pros:**
- Complete control over what gets copied
- Can review each change
- Preserves existing configurations
- Safest for production repositories

**Cons:**
- Manual process (time-consuming)
- Requires git knowledge
- Need to merge documentation sections manually
- Risk of missing components

**Process:**
```bash
# 1. Create test copy
cp -r D:\Projects\existing-repo D:\Projects\existing-repo-test

# 2. Copy workflow components
cp -r D:\Projects\stharrold-templates\.gemini D:\Projects\existing-repo-test\
cp D:\Projects\stharrold-templates\WORKFLOW.md D:\Projects\existing-repo-test\

# 3. Review changes
cd D:\Projects\existing-repo-test
git status
git diff

# 4. Manually merge CLAUDE.md sections
# Open both files and copy workflow section from stharrold-templates/CLAUDE.md

# 5. Apply to production if satisfied
cp -r D:\Projects\existing-repo-test\.gemini D:\Projects\existing-repo\
# ... (repeat for other files)

# 6. Commit
cd D:\Projects\existing-repo
git add .
git commit -m "feat: integrate Standard Workflow v1.15.1"
```

---

### Method 3: apply-workflow-batch.sh

**When to use:**
- Multiple repositories need workflow
- All repos have similar structure
- Want automated batch processing
- Comfortable with automated commits

**Pros:**
- Processes multiple repos at once
- Automatic checkpoint commits
- Updates CLAUDE.md automatically
- Consistent application across projects

**Cons:**
- Less control per repository
- Skips repos that already have `.claude/`
- Automated commits (review afterward)
- May not suit all project structures

**Current limitation:** Only targets 10 specific projects (see `PROJECTS` array in script)

**Command:**
```bash
cd D:\Projects
bash apply-workflow-batch.sh
```

**What it does per project:**
1. Creates checkpoint commit (before changes)
2. Copies `.claude/` directory
3. Copies `WORKFLOW.md` and `WORKFLOW-INIT-PROMPT.md`
4. Adds Standard Workflow section to CLAUDE.md (or creates it)
5. Commits workflow integration

---

### Method 4: verify-workflow.sh

**When to use:**
- After applying workflow (verification)
- Auditing current state
- Checking which projects have workflow
- Listing skills per project

**Pros:**
- Read-only (safe)
- Quick verification
- Lists all git repos
- Shows skill count per project

**Cons:**
- Verification only (doesn't apply)
- Current bug: counts top-level `.claude/` dirs, not skills in `.claude/skills/`

**Command:**
```bash
cd D:\Projects
bash verify-workflow.sh
```

**Output:**
```
✅ sql: 9 skills
    - agentdb-state-manager
    - bmad-planner
    - git-workflow-manager
    - initialize-repository
    - quality-enforcer
    - speckit-author
    - tech-stack-adapter
    - workflow-orchestrator
    - workflow-utilities

❌ OracleERP: NO WORKFLOW
```

---

## Comparison Matrix

| Aspect | initialize_repository.py | Manual Copy + Merge | apply-workflow-batch.sh |
|--------|-------------------------|---------------------|-------------------------|
| **Repositories** | 1 (new) | 1 (existing) | Many (existing) |
| **Control** | Medium | Maximum | Low |
| **Safety** | Medium | Maximum | Medium |
| **Speed** | Fast | Slow | Very Fast |
| **Review** | After completion | During process | After completion |
| **Git commits** | Auto-generated | Manual | Auto-generated |
| **CLAUDE.md** | Generated | Manual merge | Auto-updated |
| **Reversibility** | Via git reset | Full control | Via git reset |
| **Skill** | Beginner | Intermediate | Intermediate |

---

## Recommendations by Project Type

### New Repository (No Existing Code)
**Use:** `initialize_repository.py`

**Why:** Complete setup with Q&A guidance

---

### Production Repository (Established Codebase)
**Use:** Manual Copy + Merge (test-copy approach)

**Why:** Maximum control, can review all changes before applying

**Process:**
1. Copy repo to test location
2. Apply workflow to test copy
3. Review with `git diff`
4. Manually copy desired components to production
5. Commit

---

### Multiple Development Repositories
**Use:** `apply-workflow-batch.sh`

**Why:** Efficient batch processing

**Considerations:**
- Review automated commits afterward
- May need manual fixes for special cases
- Run `verify-workflow.sh` after completion

---

### Existing Repository (Minimal Changes Needed)
**Use:** Manual Copy (selective)

**Why:** Can copy only `.claude/` and `WORKFLOW.md`, skip other files

**Process:**
```bash
cp -r D:\Projects\stharrold-templates\.gemini D:\Projects\existing-repo\
cp D:\Projects\stharrold-templates\WORKFLOW.md D:\Projects\existing-repo\
# Manually add workflow section to CLAUDE.md
git commit -m "feat: add workflow system"
```

---

## Safety Checklist

Before applying any method:

- [ ] All changes committed (`git status` clean)
- [ ] On correct branch (usually `contrib/<user>`)
- [ ] Backup created (or confident in git reset)
- [ ] Understand what will be overwritten
- [ ] Read method documentation
- [ ] Have 15-30 minutes for review

After application:

- [ ] Run `git status` to see what changed
- [ ] Review `git diff` for unexpected changes
- [ ] Verify `.claude/skills/` has 9 skills
- [ ] Run `verify-workflow.sh` for confirmation
- [ ] Test quality gates: `python .claude/skills/quality-enforcer/scripts/run_quality_gates.py`

---

## Common Scenarios

### Scenario 1: "I want to try the workflow on a test project first"
**Solution:** Use `initialize_repository.py` to create a throwaway test repo

### Scenario 2: "I have 15 projects that need workflow"
**Solution:** Use `apply-workflow-batch.sh` (after updating `PROJECTS` array)

### Scenario 3: "I have an existing repo with custom setup"
**Solution:** Manual Copy + Merge (test-copy approach)

### Scenario 4: "I just want to check which projects have workflow"
**Solution:** Run `verify-workflow.sh`

### Scenario 5: "I want to update workflow in repos that already have it"
**Solution:** Manual copy of updated `.claude/skills/` dirs (preserves custom configs)

---

## Next Steps

Once you've selected a method:
1. Read the detailed [Application Guide](application-guide.md)
2. Check [Project Inventory](project-inventory.md) for current status
3. Understand [Version Mapping](version-mapping.md)
4. Apply the workflow
5. Verify with `verify-workflow.sh`
