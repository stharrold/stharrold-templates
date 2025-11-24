# Workflow Guide: Integration & Release Phases (4-5)

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Previous:** [Planning Phases (0-3)](workflow-planning.md)
**Version:** 5.3.0

This document covers integration and release workflow phases.

---

### Phase 4: Integration & Pull Request

**Location:** Feature worktree → Main repository
**Skills:** git-workflow-manager, workflow-utilities

#### Step 4.1: Calculate Semantic Version

**Command:**
```bash
python .claude/skills/git-workflow-manager/scripts/semantic_version.py \
  develop v1.0.0
```

**Version bump logic:**
- **MAJOR (v2.0.0):** Breaking changes (API changes, removed features)
- **MINOR (v1.1.0):** New features (new files, new functions, new endpoints)
- **PATCH (v1.0.1):** Bug fixes, refactoring, docs, tests

**Output:**
```
Base version: v1.0.0
Changes detected:
  - New files: src/vocabulary/a1.py
  - New functions: 3

Recommended version: v1.1.0 (MINOR)
```

#### Step 4.1.5: Sync AI Assistant Configuration

**Purpose:** Ensure CLAUDE.md changes are synced to cross-tool compatible formats before creating PR

**When to run:** After quality gates pass, before creating pull request

**Manual sync (Windows/all platforms):**
```bash
# Sync CLAUDE.md to cross-tool formats
cp CLAUDE.md AGENTS.md
mkdir -p .github && cp CLAUDE.md .github/copilot-instructions.md
mkdir -p .agents && cp -r .claude/* .agents/

# Verify sync
ls -la AGENTS.md .github/copilot-instructions.md .agents/
```

**PowerShell alternative:**
```powershell
# Sync CLAUDE.md to cross-tool formats
cp CLAUDE.md AGENTS.md
mkdir -Force .github; cp CLAUDE.md .github/copilot-instructions.md
mkdir -Force .agents; cp -Recurse .claude/* .agents/
```

**Automatic sync (Linux/macOS with jq + rsync installed):**
```bash
# The PostToolUse hook runs automatically when CLAUDE.md is edited
# If hook didn't run, manually execute:
./.claude/hooks/sync-agents.sh
```

**What gets synced:**
- `CLAUDE.md` → `AGENTS.md` (industry standard instruction file)
- `CLAUDE.md` → `.github/copilot-instructions.md` (GitHub Copilot)
- `.claude/` → `.agents/` (tool-agnostic configuration directory)

**Why this matters:**
- Ensures GitHub Copilot users see updated instructions
- Enables Cursor, Aider, and other tools to use same configuration
- Maintains cross-tool compatibility for team members

**Skip if:** You haven't modified CLAUDE.md or .claude/ configuration in this feature

#### Step 4.2: Create Pull Request (feature → contrib)

**Command:**
```bash
gh pr create \
  --base "contrib/stharrold" \
  --head "feature/20251023T104248Z_certificate-a1" \
  --title "feat(vocab): add A1 certificate vocabulary" \
  --body "$(cat <<'EOF'
## Summary
- Implements A1 level Standard vocabulary module
- 150+ words with gender, plural, and examples
- Full test coverage (87%)

## Changes
- New module: src/vocabulary/a1.py
- Tests: tests/test_a1_vocabulary.py
- Spec: spec.md in worktree

## Quality Gates
- Coverage: 87% (✓ ≥80%)
- Tests: 45/45 passing (✓)
- Linting: Clean (✓)
- Types: Clean (✓)
- Build: Success (✓)

## Semantic Version
Recommended: v1.1.0 (MINOR - new feature)

## References
- TODO: TODO_feature_20251023T104248Z_certificate-a1.md
- Spec: See worktree spec.md
- Plan: See worktree plan.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**Output:**
```
✓ Pull request created: https://github.com/user/standard/pull/42
```

#### Step 4.3: Reviewers Add Comments

**Action:** Reviewers add comments and conversations in GitHub/Azure DevOps web portal

**What happens:**
- Reviewers add inline comments on specific files/lines
- Reviewers create conversation threads
- Some conversations require substantive changes (new features, refactoring)
- Some conversations are simple fixes (typos, formatting)

#### Step 4.4: Handle PR Feedback via Work-Items (Optional)

**When to use:**
- PR has unresolved conversations requiring substantive changes
- Changes are too large to fix on same feature branch
- Want to approve PR while tracking feedback separately

**Decision tree:**
```
PR reviewed with comments
├─ Simple fixes (typos, formatting, minor adjustments)
│  └─ Fix directly on feature branch, push update, skip to Step 4.5
└─ Substantive changes (new features, refactoring, architecture changes)
   └─ Generate work-items, continue below
```

**Command:**
```bash
python .claude/skills/git-workflow-manager/scripts/generate_work_items_from_pr.py 42
```

**Output:**
```
ℹ Analyzing PR #42 for unresolved conversations...
✓ Found 3 unresolved conversations
✓ Created work-item: pr-42-issue-1 (https://github.com/user/standard/issues/123)
  Title: "PR #42 feedback: Add error handling for missing vocabulary files"
  Labels: pr-feedback, pr-42
✓ Created work-item: pr-42-issue-2 (https://github.com/user/standard/issues/124)
  Title: "PR #42 feedback: Refactor gender validation to use enum"
  Labels: pr-feedback, pr-42
✓ Created work-item: pr-42-issue-3 (https://github.com/user/standard/issues/125)
  Title: "PR #42 feedback: Add examples to vocabulary word model"
  Labels: pr-feedback, pr-42

ℹ Work-items created. For each work-item:
  1. Create feature worktree: create_worktree.py feature pr-42-issue-1 contrib/stharrold
  2. Implement fix (SpecKit optional for simple fixes)
  3. Run quality gates
  4. Create PR: feature/YYYYMMDDTHHMMSSZ_pr-42-issue-1 → contrib/stharrold
  5. Merge in web portal
  6. Repeat for remaining work-items
```

**What it does:**
- Detects VCS provider (GitHub or Azure DevOps)
- Fetches unresolved PR conversations:
  - GitHub: `reviewThreads.isResolved == false`
  - Azure DevOps: `threads.status == active|pending`
- Creates work-items (GitHub issues or Azure DevOps tasks)
- Work-item slug pattern: `pr-{pr_number}-issue-{sequence}`
- Preserves conversation context (file, line, author, timestamps)

**Benefits:**
- Enables PR approval without blocking on follow-up work
- Creates traceable lineage: PR → work-items → feature branches → new PRs
- Compatible with all issue trackers (GitHub, Azure DevOps, others)
- Each work-item follows standard Phase 2-4 workflow

**For each work-item, repeat workflow:**
1. Create feature worktree: `create_worktree.py feature pr-42-issue-1 contrib/stharrold`
2. Implement fix (SpecKit optional for simple fixes)
3. Run quality gates (Phase 3)
4. Create PR: `feature/YYYYMMDDTHHMMSSZ_pr-42-issue-1 → contrib/stharrold`
5. Merge in web portal
6. Repeat until all work-items resolved

#### Step 4.5: User Approves and Merges PR

**Action:** User approves and merges PR in GitHub/Azure DevOps web portal

**Note:** Conversations may remain unresolved if work-items were generated (Step 4.4). This is expected - work-items track the follow-up work.

#### Step 4.6: Atomic Cleanup (Archive TODO + Delete Worktree + Delete Branches)

**⚠️ IMPORTANT:** Use the atomic cleanup script to ensure proper ordering. This script prevents orphaned TODO files by enforcing: Archive TODO → Delete worktree → Delete branches.

**Return to main repo:**
```bash
cd /Users/user/Documents/GitHub/standard
```

**Atomic cleanup (recommended):**
```bash
python .claude/skills/git-workflow-manager/scripts/cleanup_feature.py \
  certificate-a1 \
  --summary "Implemented A1 Standard certificate guide with complete exam structure" \
  --version "1.3.0"
```

**Output:**
```
🚀 Cleaning up feature: certificate-a1
======================================================================
✓ Found TODO: TODO_feature_20251023T104248Z_certificate-a1.md
✓ Found worktree: /Users/user/Documents/GitHub/standard_feature_certificate-a1
✓ Found branch: feature/20251023T104248Z_certificate-a1

======================================================================
Starting atomic cleanup operations...
======================================================================

📦 Archiving TODO: TODO_feature_20251023T104248Z_certificate-a1.md
✓ TODO archived to ARCHIVED/TODO_feature_20251023T104248Z_certificate-a1.md

🗑️  Removing worktree: /Users/user/Documents/GitHub/standard_feature_certificate-a1
✓ Worktree removed: /Users/user/Documents/GitHub/standard_feature_certificate-a1

🗑️  Deleting local branch: feature/20251023T104248Z_certificate-a1
✓ Local branch deleted: feature/20251023T104248Z_certificate-a1

🗑️  Deleting remote branch: origin/feature/20251023T104248Z_certificate-a1
✓ Remote branch deleted: origin/feature/20251023T104248Z_certificate-a1

======================================================================
✅ Feature cleanup complete: certificate-a1
======================================================================
```

**Why atomic cleanup?**
- **Prevents orphaned TODO files**: Cannot delete worktree without archiving TODO first
- **Single command**: One command instead of remembering 4 separate commands
- **Atomic operation**: Either everything succeeds or nothing changes (safe to retry)
- **Clear ordering**: Archives TODO → Deletes worktree → Deletes branches (guaranteed)
- **Error handling**: If TODO archive fails, worktree/branches NOT deleted (safe state)

**Manual cleanup (not recommended):**

If you need manual control, use these commands IN THIS ORDER:

1. Archive TODO (MUST be first):
```bash
python .claude/skills/workflow-utilities/scripts/workflow_archiver.py \
  TODO_feature_20251023T104248Z_certificate-a1.md \
  --summary "..." \
  --version "1.3.0"
```

2. Delete worktree (only after archive succeeds):
```bash
git worktree remove ../standard_feature_certificate-a1
```

3. Delete branches (only after worktree deletion):
```bash
git branch -D feature/20251023T104248Z_certificate-a1
git push origin --delete feature/20251023T104248Z_certificate-a1
```

**⚠️ WARNING:** Manual cleanup is error-prone. If you delete the worktree before archiving the TODO, you'll have an orphaned TODO file in the main repo. Use the atomic cleanup script to avoid this.

#### Step 4.7: Rebase contrib onto develop

**Command:**
```bash
python .claude/skills/git-workflow-manager/scripts/daily_rebase.py \
  contrib/stharrold
```

**Steps:**
1. Checkout contrib branch
2. Fetch origin
3. Rebase onto origin/develop
4. Force push with lease

#### Step 4.8: Create Pull Request (contrib → develop)

**Command:**
```bash
gh pr create \
  --base "develop" \
  --head "contrib/stharrold" \
  --title "feat(vocab): A1 certificate vocabulary module" \
  --body "Completed feature: A1 vocabulary with full test coverage"
```

**User merges in GitHub UI (develop branch)**

---

### Phase 5: Release Workflow

**Location:** Main repository
**Branch Flow:** `develop` → `release/vX.Y.Z` → `main` (with tag) → back to `develop`
**Skills:** git-workflow-manager, quality-enforcer, workflow-utilities

#### Overview

The release workflow creates a production release from the develop branch, tags it on main, and back-merges to develop. This follows git-flow release branch pattern.

#### Step 5.1: Create Release Branch

**Prerequisites:**
- All features merged to develop
- Quality gates passing on develop
- Version number determined

**Command:**
```bash
python .claude/skills/git-workflow-manager/scripts/create_release.py \
  v1.1.0 develop
```

**Steps:**
1. Verify develop branch is clean and up-to-date
2. Calculate/confirm semantic version from develop
3. Create `release/v1.1.0` branch from develop
4. Create release TODO file
5. Update version files (if applicable)

**Output:**
```
✓ Created release branch: release/v1.1.0
✓ Base: develop (commit abc123)
✓ TODO file: TODO_release_20251023T143000Z_v1-1-0.md
✓ Ready for final QA and documentation updates
```

#### Step 5.2: Release Quality Assurance

**In release branch:**

1. **Final quality gates:**
   ```bash
   python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
   ```

2. **Update release documentation:**
   - Update CHANGELOG.md
   - Update version in pyproject.toml (if not already done)
   - Update README.md if needed
   - Final review of documentation

3. **Commit release prep:**
   ```bash
   git add .
   git commit -m "chore(release): prepare v1.1.0 release

   - Update CHANGELOG.md with v1.1.0 changes
   - Update version in pyproject.toml
   - Final documentation review

   Refs: TODO_release_20251023T143000Z_v1-1-0.md
   "
   git push origin release/v1.1.0
   ```

#### Step 5.3: Create Pull Request (release → main)

**Command:**
```bash
gh pr create \
  --base "main" \
  --head "release/v1.1.0" \
  --title "release: v1.1.0" \
  --body "$(cat <<'EOF'
## Release v1.1.0

### Summary
Production release with new features and improvements from develop branch.

### Changes Since v1.0.0
- Feature: A1 certificate vocabulary module
- Feature: A2 certificate vocabulary module
- Enhancement: Improved vocabulary search
- Fix: Grammar validation edge cases

### Quality Gates
- Coverage: 87% (✓ ≥80%)
- Tests: 156/156 passing (✓)
- Linting: Clean (✓)
- Types: Clean (✓)
- Build: Success (✓)

### Merge Instructions
1. Review changes
2. Merge to main
3. Tag will be created automatically (v1.1.0)
4. Release notes will be generated
5. Back-merge to develop will follow

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**Output:**
```
✓ Pull request created: https://github.com/user/standard/pull/45
```

#### Step 5.4: User Merges Release to Main

**Action:** User reviews and merges PR in GitHub UI (main branch)

**Result:** Release code now on main branch

#### Step 5.5: Tag Release

**Command:**
```bash
python .claude/skills/git-workflow-manager/scripts/tag_release.py \
  v1.1.0 main
```

**Steps:**
1. Checkout main branch
2. Pull latest (includes merge commit)
3. Create annotated tag v1.1.0
4. Push tag to origin
5. Trigger GitHub release creation (if configured)

**Output:**
```
✓ Checked out main branch
✓ Pulled latest changes (commit def456)
✓ Created annotated tag: v1.1.0
   Message: "Release v1.1.0: Production release with vocabulary modules"
✓ Pushed tag to origin
✓ View release: https://github.com/user/standard/releases/tag/v1.1.0
```

#### Step 5.6: Back-merge Release to Develop

**Purpose:** Merge any release-specific changes back to develop through PR

**⚠️ CRITICAL: Backmerge Direction**

```
CORRECT:  release/vX.Y.Z → develop  (release branch to develop)
WRONG:    main → develop            (NEVER do this!)
```

The backmerge must ALWAYS be from the **release branch**, not from main.
This ensures only release-specific changes (version bumps, changelog updates)
are merged back to develop, not the entire main branch history.

**Command:**
```bash
python .claude/skills/git-workflow-manager/scripts/backmerge_release.py \
  v1.1.0 develop
```

**Important:** This script ALWAYS creates a PR (never pushes directly to develop), ensuring proper review workflow and branch protection compliance. The script validates that the source is a release/* branch and will reject attempts to use main/develop as the source.

**Steps:**
1. Checkout develop branch
2. Pull latest from origin
3. Attempt merge locally to check for conflicts
4. Abort local merge (will merge via PR)
5. Create PR: release/v1.1.0 → develop

**Output (no conflicts):**
```
✓ No merge conflicts detected
✓ Created PR: https://github.com/user/standard/pull/46
  Title: "chore(release): back-merge v1.1.0 to develop"

📋 Next steps:
  1. Review PR in GitHub/Azure DevOps portal
  2. Approve through portal
  3. Merge through portal
  4. Run cleanup: python .claude/skills/git-workflow-manager/scripts/cleanup_release.py v1.1.0
```

**Output (with conflicts):**
```
⚠️  Merge conflicts detected in 2 file(s)
✓ Created PR: https://github.com/user/standard/pull/46
  Title: "chore(release): back-merge v1.1.0 to develop"

Conflicting files:
  - pyproject.toml
  - uv.lock

📋 Next steps:
  1. Review PR in GitHub/Azure DevOps portal
  2. Resolve conflicts (see PR description for commands)
  3. Approve and merge through portal
  4. Run cleanup: python .claude/skills/git-workflow-manager/scripts/cleanup_release.py v1.1.0
```

**User Action Required:**
1. **Review PR in GitHub/Azure DevOps UI**
2. **Approve** (required by branch protection)
3. **Merge** through portal merge button
4. **Continue to Step 5.7** after merge completes

#### Step 5.7: Cleanup Release Branch

**After back-merge is complete:**

**Command:**
```bash
python .claude/skills/git-workflow-manager/scripts/cleanup_release.py \
  v1.1.0
```

**Steps:**
1. Verify tag v1.1.0 exists
2. Verify back-merge to develop is complete
3. Delete local release/v1.1.0 branch
4. Delete remote release/v1.1.0 branch
5. Archive release TODO file

**Output:**
```
✓ Verified tag v1.1.0 exists
✓ Verified back-merge to develop complete
✓ Deleted local branch: release/v1.1.0
✓ Deleted remote branch: origin/release/v1.1.0
✓ Archived: TODO_release_20251023T143000Z_v1-1-0.md
✓ Release workflow complete for v1.1.0
```

#### Step 5.8: Update Contrib Branch

**After release is complete, rebase contrib:**

**Command:**
```bash
python .claude/skills/git-workflow-manager/scripts/daily_rebase.py \
  contrib/stharrold
```

This ensures contrib branch is up-to-date with latest develop (which now includes the release back-merge).

---


---

**Next:** [Hotfix Phase (6)](workflow-hotfix.md)
