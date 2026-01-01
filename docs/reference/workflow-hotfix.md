# Workflow Guide: Hotfix Phase (6)

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Previous:** [Integration Phases (4-5)](workflow-integration.md)
**Version:** 5.3.0

This document covers the hotfix workflow for production fixes.

---

### Phase 6: Hotfix Workflow (Production Fixes)

**Location:** Hotfix worktree
**Branch Flow:** `main` → `hotfix/vX.Y.Z-hotfix.N` → `main` (with tag) → back to `develop`
**Skills:** git-workflow-manager, speckit-author (optional), quality-enforcer, workflow-utilities

#### Overview

The hotfix workflow creates urgent fixes for production issues. Hotfixes branch from `main`, are fixed in isolation, and merge back to both `main` and `develop`.

**When to use hotfixes:**
- Critical production bugs
- Security vulnerabilities
- Data corruption issues
- Performance emergencies

**Key difference from features:**
- Branch from `main` (not contrib)
- Merge directly to `main` (not via contrib/develop)
- Back-merge to `develop` to keep it in sync
- SpecKit is **optional** (use for complex fixes only)

#### Step 6.1: Create Hotfix Worktree

**Prerequisites:**
- Production issue identified
- Issue severity warrants hotfix (not regular feature fix)
- Version number determined (vX.Y.Z-hotfix.N)

**Command:**
```bash
python .gemini/skills/git-workflow-manager/scripts/create_worktree.py \
  hotfix v1.3.0-hotfix.1 main
```

**Example:**
```bash
python .gemini/skills/git-workflow-manager/scripts/create_worktree.py \
  hotfix critical-auth-bypass main
```

**Output:**
```
✓ Worktree created: /Users/user/Documents/GitHub/standard_hotfix_critical-auth-bypass
✓ Branch: hotfix/20251024T093000Z_critical-auth-bypass
✓ TODO file: TODO_hotfix_20251024T093000Z_critical-auth-bypass.md
```

**Side effects:**
- Creates hotfix worktree directory
- Branches from `main` (not contrib)
- Creates TODO_hotfix_*.md in main repo
- Updates TODO.md manifest

#### Step 6.2: Switch to Hotfix Worktree

```bash
cd /Users/user/Documents/GitHub/standard_hotfix_critical-auth-bypass
```

#### Step 6.3: Create SpecKit Specifications (Optional)

**When to use SpecKit for hotfixes:**

✓ **Use SpecKit if:**
- Complex fix requiring multiple files
- Fix benefits from planning/task breakdown
- Need to document approach for team review
- Fix involves architectural changes

✗ **Skip SpecKit if:**
- Simple one-line fix
- Obvious solution (typo, config error)
- Time-critical emergency (fix immediately)
- Fix already well-understood

**Command (if using SpecKit):**
```bash
python .gemini/skills/speckit-author/scripts/create_specifications.py \
  hotfix critical-auth-bypass stharrold \
  --todo-file ../TODO_hotfix_20251024T093000Z_critical-auth-bypass.md
```

**Interactive session:**
```
======================================================================
SpecKit Interactive Specification Tool
======================================================================

⚠ No BMAD planning found for 'critical-auth-bypass'
I'll gather requirements through comprehensive Q&A.

What is the main purpose of this hotfix?
> Fix authentication bypass vulnerability in OAuth flow

Who are the primary users affected?
> All users with OAuth authentication

How will success be measured?
> Vulnerability patched, no auth bypass possible, all tests passing

[... continues with tech stack and testing questions ...]
```

**Output:**
- specs/critical-auth-bypass/spec.md (detailed fix approach)
- specs/critical-auth-bypass/plan.md (task breakdown)
- TODO_hotfix_*.md updated with tasks

**Note:** Most hotfixes skip SpecKit and proceed directly to implementation.

#### Step 6.4: Implement Fix

**Process:**
1. Identify root cause
2. Implement minimal fix (avoid scope creep)
3. Add/update tests to prevent regression
4. Document fix in commit message

**Best practices:**
- **Keep it minimal** - Fix only the immediate issue
- **Add regression tests** - Prevent issue from recurring
- **Document thoroughly** - Explain what broke and how fixed
- **Avoid refactoring** - Save non-critical improvements for features

**Commit format:**
```
fix(hotfix): <brief description of fix>

<detailed explanation of issue and fix>

Root cause: <what caused the bug>
Fix: <what was changed>
Impact: <who is affected>
Regression test: <test file added/updated>

Refs: TODO_hotfix_20251024T093000Z_critical-auth-bypass.md

🤖 Generated with [Gemini Code](https://gemini.com/gemini-code)

Co-Authored-By: Gemini <noreply@anthropic.com>
```

#### Step 6.5: Quality Assurance

**Run all quality gates:**
```bash
python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
```

**Quality gates (all must pass):**
1. **Test Coverage ≥ 80%**
   ```bash
   uv run pytest --cov=src --cov-report=term --cov-fail-under=80
   ```

2. **All Tests Passing** (including new regression tests)
   ```bash
   uv run pytest
   ```

3. **Linting Clean**
   ```bash
   uv run ruff check src/ tests/
   ```

4. **Type Checking Clean**
   ```bash
   uv run mypy src/
   ```

5. **Build Successful**
   ```bash
   uv build
   ```

**Output:**
```
Running Quality Gates...

COVERAGE: ✓ 82% (≥80% required)
TESTS: ✓ 47/47 passing (includes new regression test)
LINTING: ✓ 0 issues
TYPES: ✓ 0 errors
BUILD: ✓ Success

✓ ALL GATES PASSED

Next: Calculate hotfix version
```

#### Step 6.6: Calculate Hotfix Version

**Command:**
```bash
python .gemini/skills/git-workflow-manager/scripts/semantic_version.py \
  main v1.3.0
```

**Version format:** `vX.Y.Z-hotfix.N`
- Use current main version as base
- Increment hotfix number (N)
- Example: v1.3.0 → v1.3.0-hotfix.1

**Output:**
```
Base version: v1.3.0 (from main)
Hotfix number: 1

Recommended version: v1.3.0-hotfix.1 (HOTFIX)
```

#### Step 6.7: Create Pull Request (hotfix → main)

**Command:**
```bash
gh pr create \
  --base "main" \
  --head "hotfix/20251024T093000Z_critical-auth-bypass" \
  --title "hotfix(auth): fix critical authentication bypass vulnerability" \
  --body "$(cat <<'EOF'
## Hotfix: Critical Authentication Bypass

### Summary
- Fixes critical vulnerability in OAuth authentication flow
- Vulnerability allowed bypassing authentication via token manipulation
- Impact: All users with OAuth authentication

### Root Cause
Token validation was not checking signature properly, allowing
forged tokens to pass authentication.

### Fix
- Added proper JWT signature verification
- Enhanced token validation with expiry checks
- Added rate limiting to token endpoint

### Testing
- New regression test: tests/test_auth_bypass.py
- All existing tests passing
- Manual security testing completed

### Quality Gates
- Coverage: 82% (✓ ≥80%)
- Tests: 47/47 passing (✓ includes regression test)
- Linting: Clean (✓)
- Types: Clean (✓)
- Build: Success (✓)

### Hotfix Version
Recommended: v1.3.0-hotfix.1

### Security Advisory
This hotfix addresses CVE-XXXX-XXXXX (if applicable)

### Merge Instructions
1. Review security fix
2. Verify regression test coverage
3. Merge to main
4. Tag as v1.3.0-hotfix.1
5. Back-merge to develop

## References
- TODO: TODO_hotfix_20251024T093000Z_critical-auth-bypass.md
- Spec: specs/critical-auth-bypass/spec.md (if applicable)

🤖 Generated with [Gemini Code](https://gemini.com/gemini-code)
EOF
)"
```

**Output:**
```
✓ Pull request created: https://github.com/user/standard/pull/48
```

#### Step 6.8: User Merges Hotfix to Main

**Action:** User reviews and merges PR in GitHub UI (main branch)

**Result:** Hotfix code now on main branch

#### Step 6.9: Tag Hotfix Release

**Command:**
```bash
python .gemini/skills/git-workflow-manager/scripts/tag_release.py \
  v1.3.0-hotfix.1 main
```

**Steps:**
1. Checkout main branch
2. Pull latest (includes hotfix merge commit)
3. Create annotated tag v1.3.0-hotfix.1
4. Push tag to origin
5. Trigger GitHub release creation

**Output:**
```
✓ Checked out main branch
✓ Pulled latest changes (includes hotfix commit def789)
✓ Created annotated tag: v1.3.0-hotfix.1
   Message: "Hotfix v1.3.0-hotfix.1: Fix critical auth bypass vulnerability"
✓ Pushed tag to origin
✓ View release: https://github.com/user/standard/releases/tag/v1.3.0-hotfix.1
```

#### Step 6.10: Back-merge Hotfix to Develop

**Purpose:** Keep develop branch in sync with production hotfix

**Command:**
```bash
python .gemini/skills/git-workflow-manager/scripts/backmerge_release.py \
  v1.3.0-hotfix.1 develop
```

**Steps:**
1. Checkout develop branch
2. Pull latest from origin
3. Merge hotfix/vX.Y.Z-hotfix.N into develop
4. Resolve conflicts (if any)
5. Push to origin

**Output (no conflicts):**
```
✓ Checked out develop
✓ Pulled latest changes
✓ Merged hotfix/20251024T093000Z_critical-auth-bypass into develop
✓ Pushed to origin/develop
✓ Back-merge complete
```

**Output (with conflicts):**
```
⚠ Merge conflicts detected
✓ Created PR: https://github.com/user/standard/pull/49
  Title: "chore(hotfix): back-merge v1.3.0-hotfix.1 to develop"

Please resolve conflicts in GitHub UI and merge.
```

#### Step 6.11: Cleanup Hotfix Worktree

**Return to main repo:**
```bash
cd /Users/user/Documents/GitHub/standard
```

**Delete hotfix worktree:**
```bash
git worktree remove ../standard_hotfix_critical-auth-bypass
git branch -D hotfix/20251024T093000Z_critical-auth-bypass
```

**Archive TODO file:**
```bash
python .gemini/skills/workflow-utilities/scripts/archive_manager.py \
  archive TODO_hotfix_20251024T093000Z_critical-auth-bypass.md
```

**Output:**
```
✓ Removed worktree: ../standard_hotfix_critical-auth-bypass
✓ Deleted branch: hotfix/20251024T093000Z_critical-auth-bypass
✓ Archived TODO_hotfix_20251024T093000Z_critical-auth-bypass.md
✓ Updated TODO.md manifest
```

#### Step 6.12: Update Contrib Branch

**Rebase contrib to include hotfix:**
```bash
python .gemini/skills/git-workflow-manager/scripts/daily_rebase.py \
  contrib/stharrold
```

This ensures contrib branch is up-to-date with hotfix (via develop back-merge).

---

## Hotfix vs Feature Comparison

| Aspect | Feature Workflow | Hotfix Workflow |
|--------|-----------------|-----------------|
| **Branches from** | contrib/<user> | main |
| **Merges to** | contrib → develop | main (then back to develop) |
| **SpecKit** | Standard (Phase 2.3) | Optional (use for complex fixes) |
| **BMAD Planning** | Recommended (Phase 1) | Not applicable |
| **Scope** | New functionality | Minimal fix only |
| **Quality gates** | Required (≥80% coverage) | Required (≥80% coverage) |
| **Versioning** | MAJOR/MINOR/PATCH | vX.Y.Z-hotfix.N |
| **Timeline** | Days to weeks | Hours to days (urgent) |
| **Worktree** | Yes (isolation) | Yes (isolation) |

---

## Production Safety & Rollback

### Overview

Production deployments should always use **tagged releases** (e.g., `v1.5.1`), never branch heads. Tags provide immutable snapshots that enable instant rollback without code changes.

### Deployment Best Practices

**✓ DO:**
- Deploy from tags: `git checkout v1.5.1`
- Test releases thoroughly before tagging on main
- Keep multiple recent tags available for rollback
- Monitor production after deployment
- Have rollback procedure documented and rehearsed

**✗ DON'T:**
- Deploy from `main` branch head (moving target)
- Deploy from feature/hotfix branches directly
- Delete tags after deployment (keep for rollback)
- Skip quality gates before releasing

### Emergency Rollback Procedures

#### Scenario 1: Production Broken After Release

**Symptoms:**
- v1.5.1 deployed to production
- Critical issue discovered (crashes, data loss, security vulnerability)
- Need immediate rollback

**Solution: Deploy Previous Tag (Fastest - 2 minutes)**

```bash
# 1. Checkout last known good tag
git checkout v1.5.0

# 2. Deploy this tag to production
# (deployment mechanism varies: docker, kubernetes, etc.)

# Result: Production now running v1.5.0
# - No code changes needed
# - Instant rollback
# - v1.5.1 remains tagged on main (untouched)
```

**Timeline:**
- 0:00 - Issue detected in production (v1.5.1)
- 0:02 - Checkout v1.5.0 tag
- 0:05 - Deploy v1.5.0 to production
- 0:10 - Verify production stable on v1.5.0
- **Total: ~10 minutes to restore service**

---

#### Scenario 2: Need to Remove Bad Release from Main

**Symptoms:**
- v1.5.1 deployed and rolled back to v1.5.0
- v1.5.1 merge commit still on main branch
- Need to remove bad code from main branch

**Solution: Revert Merge Commit**

```bash
# 1. Find the merge commit that introduced v1.5.1
git log --oneline main | head -10
# Example output:
#   abc123f Merge pull request #42 from user/release/v1.5.1
#   def456g docs(release): update CHANGELOG.md for v1.5.1
#   ...

# 2. Revert the merge commit

# ⚠️ WARNING: Before proceeding, review the current state of main!
# If main has moved forward significantly since the problematic release,
# ensure you are reverting the correct commit and not affecting newer changes.
# Use the following to inspect recent history:
git log --oneline main | head -20
# Confirm the merge commit hash and its position in history.

git checkout main
git pull origin main
git revert abc123f -m 1

# Explanation:
# -m 1 = keep parent 1 (main branch history)
# This creates a NEW commit that undoes the merge

# 3. Push revert commit
git push origin main

# 4. Tag the revert as new patch version
git tag -a v1.5.2 -m "Revert broken v1.5.1 release"
git push origin v1.5.2

# 5. Deploy v1.5.2 to production
git checkout v1.5.2
# Deploy...

# Result:
# - main branch now has revert commit
# - v1.5.2 tag points to reverted state
# - v1.5.1 tag still exists (for reference)
# - Production running v1.5.2 (functionally = v1.5.0)
```

**Timeline:**
- Already rolled back to v1.5.0 (production stable)
- Create revert commit: ~10 minutes
- Tag and deploy v1.5.2: ~10 minutes
- **Total: ~20 minutes (non-urgent, production already stable)**

---

#### Scenario 3: Hotfix Taking Too Long

**Symptoms:**
- Production broken, rolled back to v1.5.0
- Working on hotfix in worktree (v1.5.0-hotfix.1)
- Hotfix more complex than expected (hours, not minutes)
- Production still running v1.5.0 (stable but missing features from v1.5.1)

**Solution: Keep Production on v1.5.0, Finish Hotfix Properly**

```bash
# Production remains on v1.5.0 (stable)
# Continue hotfix work:

# 1. In hotfix worktree
cd ../standard_hotfix_issue-name

# 2. Complete the fix
# - Add tests
# - Run quality gates
# - Ensure ≥80% coverage

# 3. Create PR: hotfix → main
gh pr create --base main --title "hotfix(issue): description"

# 4. After merge, tag hotfix
git checkout main
git pull origin main
git tag -a v1.5.0-hotfix.1 -m "Hotfix: description"
git push origin v1.5.0-hotfix.1

# 5. Deploy hotfix
git checkout v1.5.0-hotfix.1
# Deploy...

# 6. Back-merge to develop
python .gemini/skills/git-workflow-manager/scripts/backmerge_release.py \
  v1.5.0-hotfix.1 develop

# Result:
# - Production moved from v1.5.0 → v1.5.0-hotfix.1
# - Hotfix tested and properly merged
# - develop updated with fix
```

**Key principle:** Don't rush hotfixes. Production is stable on v1.5.0. Take time to do hotfix correctly.

---

### Why Tag-Based Deployment?

**Problem with branch-based deployment:**
```bash
# Deploy from main branch (BAD)
git checkout main
git pull origin main    # Gets latest commits
# Deploy...

# Issue: "latest" changes constantly
# - Can't reproduce exact deployment
# - Can't rollback without code changes
# - Unclear what version is running
```

**Solution with tag-based deployment:**
```bash
# Deploy from tag (GOOD)
git checkout v1.5.1    # Exact snapshot
# Deploy...

# Benefits:
# - v1.5.1 never changes (immutable)
# - Can reproduce deployment anytime
# - Rollback = checkout v1.5.0
# - Clear version in production
```

---

### Main Branch Protection

**How main stays safe during hotfix work:**

1. **Hotfix work isolated in worktree**
   ```bash
   # Main repo
   /Users/user/Documents/GitHub/standard (main branch untouched)

   # Hotfix worktree
   /Users/user/Documents/GitHub/standard_hotfix_issue (isolated work)
   ```

2. **Main only updated via merged PRs**
   - No direct commits to main
   - All changes reviewed
   - Quality gates enforced

3. **Tagged releases are immutable**
   - v1.5.0 tag never changes
   - Can always rollback to v1.5.0
   - Even if main branch has bad commits

---

### Rollback Decision Tree

```
Production broken after v1.5.1 deployment?
│
├─ YES → Checkout v1.5.0 and deploy (instant rollback)
│        │
│        ├─ Production now stable?
│        │  │
│        │  ├─ YES → Decide next action:
│        │  │        ├─ Remove v1.5.1 from main? → Revert merge commit, tag v1.5.2
│        │  │        ├─ Fix issue? → Create hotfix (v1.5.0-hotfix.1 or v1.5.1-hotfix.1)
│        │  │        └─ Wait for next release? → Keep v1.5.0, work on v1.6.0
│        │  │
│        │  └─ NO → Escalate (v1.5.0 also broken, checkout v1.4.0)
│        │
│        └─ Hotfix taking too long?
│           └─ Keep v1.5.0 in production (stable), complete hotfix properly
│
└─ NO → Continue with normal operations
```

---

### Summary

**Production Safety:**
- ✓ Deploy from tags (v1.5.1), never branches
- ✓ Keep multiple tags for instant rollback
- ✓ Hotfix work isolated (main untouched)
- ✓ Quality gates before tagging
- ✓ Can always rollback without code changes

**Emergency Rollback:**
- **Fastest:** `git checkout v1.5.0` → deploy (2 minutes)
- **Clean main:** Revert merge commit → tag v1.5.2 (20 minutes)
- **Proper fix:** Create hotfix from last good tag (hours)

**Key Principle:** Production stability > speed. Rollback first, fix properly second.

---


---

**Next:** [Operations & Maintenance](workflow-operations.md)
