# Workflow Guide: Operations & Maintenance

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Previous:** [Hotfix Phase (6)](workflow-hotfix.md)
**Version:** 5.3.0

This document covers workflow operations, context management, and maintenance tasks.

---

## TODO.md Manifest System

### Structure (v5.2.0)

**File:** `TODO.md` (root of main repository)

**Format:**
```markdown
---
manifest_version: 5.2.0
last_updated: 2025-10-23T14:30:22Z
repository: standard
active_workflows:
  count: 2
  updated: 2025-10-23T14:30:22Z
archived_workflows:
  count: 45
  last_archived: 2025-10-22T09:15:00Z
---

# Workflow Manifest

## Active Workflows

### TODO_feature_20251023T104248Z_certificate-a1.md
Implements A1 level Standard vocabulary with grammatical gender and plural forms.

### TODO_feature_20251023T104355Z_certificate-a2.md
Extends A1 vocabulary with A2 level words and advanced grammar patterns.

## Recently Archived Workflows (Last 10)

### ARCHIVED_TODO_feature_20251022T103000Z_initial-foundation.md
Created foundational Standard vocabulary library structure and CI/CD pipeline.

[... 9 more archived workflows ...]

## Workflow Commands

- **Create feature**: `next step?` (from contrib branch)
- **Continue workflow**: `next step?` (from any context)
- **Check quality gates**: Tests, coverage, linting, type checking
- **Create PR**: Automatic after all gates pass
- **View status**: Check current phase in active TODO_*.md files

## Archive Management

Workflows are archived when:
- Feature/hotfix PR merged to contrib branch
- Release PR merged to develop branch
- Contributor manually archives with `archive workflow` command

Archive process:
1. Move TODO_*.md → ARCHIVED_TODO_*.md
2. Update timestamp in filename
3. Create zip of all related files (spec.md, plan.md, logs)
4. Update TODO.md manifest references
5. Commit archive changes to main repo
```

### Update Manifest

**Command:**
```bash
python .gemini/skills/workflow-utilities/scripts/todo_updater.py .
```

**Auto-updates when:**
- New worktree created
- Workflow archived
- Manual invocation

---

## Individual TODO_*.md Structure

**File:** `TODO_feature_<timestamp>_<slug>.md` (main repository)

**Format:**
```markdown
---
type: workflow-manifest
workflow_type: feature
slug: certificate-a1
timestamp: 20251023T104248Z
github_user: stharrold

workflow_progress:
  phase: 2
  current_step: "2.4"
  last_task: impl_003

quality_gates:
  test_coverage: 87
  tests_passing: true
  build_passing: true
  linting_clean: true
  types_clean: true
  semantic_version: "1.1.0"

metadata:
  worktree_path: /Users/stharrold/Documents/GitHub/standard_feature_certificate-a1
  branch_name: feature/20251023T104248Z_certificate-a1
  created: 2025-10-23T10:42:48Z
  last_updated: 2025-10-23T14:30:22Z

tasks:
  implementation:
    - id: impl_001
      description: "Create A1 vocabulary data structure"
      status: complete
      completed_at: "2025-10-23T11:00:00Z"
    - id: impl_002
      description: "Add grammatical gender metadata"
      status: complete
      completed_at: "2025-10-23T12:00:00Z"
    - id: impl_003
      description: "Implement vocabulary lookup functions"
      status: in_progress
      started_at: "2025-10-23T13:00:00Z"
  testing:
    - id: test_001
      description: "Unit tests for vocabulary module"
      status: pending
---

# TODO: Certificate A1 Vocabulary

Implements A1 level Standard vocabulary with grammatical gender and plural forms.

## Active Tasks

### impl_003: Vocabulary Lookup Functions
**Status:** in_progress
**Files:** src/vocabulary/a1.py
**Dependencies:** impl_001, impl_002

[... rest of TODO body ...]
```

---

## Common Commands Reference

### Project Setup
```bash
# Authenticate with GitHub
gh auth login

# Install dependencies
uv sync

# Detect technology stack
python .gemini/skills/tech-stack-adapter/scripts/detect_stack.py
```

### Workflow Management
```bash
# Update TODO.md manifest
python .gemini/skills/workflow-utilities/scripts/todo_updater.py .

# Create feature worktree
python .gemini/skills/git-workflow-manager/scripts/create_worktree.py \
  feature <slug> contrib/<gh-user>

# Daily rebase contrib branch
python .gemini/skills/git-workflow-manager/scripts/daily_rebase.py \
  contrib/<gh-user>

# Run quality gates
python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py

# Calculate semantic version
python .gemini/skills/git-workflow-manager/scripts/semantic_version.py \
  develop v1.0.0

# Archive workflow (Phase 4.4)
python .gemini/skills/workflow-utilities/scripts/workflow_archiver.py \
  TODO_feature_*.md --summary "What was completed" --version "X.Y.Z"

# Create directory with standards (GEMINI.md, README.md, ARCHIVED/)
python .gemini/skills/workflow-utilities/scripts/directory_structure.py \
  create <directory-path> "<purpose-description>"

# Deprecate files (archive with timestamp)
python .gemini/skills/workflow-utilities/scripts/deprecate_files.py \
  <todo-file> "<description>" <file1> <file2> ...
```

### Testing & Quality
```bash
# Run tests with coverage
uv run pytest --cov=src --cov-report=term --cov-fail-under=80

# Run tests only
uv run pytest

# Lint code
uv run ruff check src/ tests/

# Format code
uv run ruff format src/

# Type check
uv run mypy src/

# Build package
uv build
```

### Container Operations
```bash
# Build container
podman build -t standard:latest .

# Run tests in container
podman run --rm standard:latest pytest

# Run with compose
podman-compose up -d
podman-compose logs
podman-compose down
```

### Git Operations
```bash
# List worktrees
git worktree list

# Remove worktree
git worktree remove <path>

# Delete branch
git branch -D <branch-name>

# Create PR (feature → contrib)
gh pr create --base "contrib/<gh-user>" --head "<feature-branch>"

# Create PR (contrib → develop)
gh pr create --base "develop" --head "contrib/<gh-user>"
```

---

## Context Management

### Critical Token Threshold: 100K Tokens

**Effective context:** ~136K tokens (200K total - 64K system overhead)

**At 100K tokens used (~73% of effective capacity):**

Gemini will **automatically**:
1. Save all task state to TODO_*.md (update YAML frontmatter)
2. Document current context in TODO body:
   - Current phase and step
   - Completed tasks
   - In-progress tasks
   - Next pending tasks
   - Any blockers or notes
3. Commit TODO_*.md updates

Then **you must**:
1. Run `/init` to update GEMINI.md memory files with current state
2. Run `/compact` to compress memory and reduce token usage
3. Continue working - context is preserved in TODO_*.md

**Monitor context usage:**
```bash
/context
```

Token usage is shown in system warnings after each tool use:
```
Token usage: 100543/200000; 99457 remaining
```

**When you see usage approaching 100K:**
- Gemini will proactively save state to TODO_*.md
- Wait for "✓ State saved to TODO file" confirmation
- Run /init (updates memory files) and /compact (compresses memory)
- Continue working with reduced token usage

**Best practices:**
- Check /context after each major phase (every 10-15K tokens)
- Archive completed workflows to reduce TODO.md size
- Use progressive skill loading (only load needed skills per phase)
- Expect 1-2 context resets per complex feature workflow

### State Preservation in TODO_*.md

When context reset is triggered, the following is saved to YAML frontmatter:

```yaml
workflow_progress:
  phase: 2                    # Current workflow phase (0-5)
  current_step: "2.4"        # Specific step within phase
  last_task: "impl_003"      # Last completed/active task ID
  last_update: "2025-10-23T15:30:00Z"
  status: "implementation"   # Current status

context_checkpoints:
  - timestamp: "2025-10-23T15:30:00Z"
    token_usage: 100234
    phase: 2
    step: "2.4"
    last_task: "impl_003"
    notes: "Completed script implementation, starting tests"
```

Plus task-level status updates for all tasks (pending → in_progress → completed)

---

## File Deprecation

When implementation replaces or removes existing files, use proper deprecation to maintain traceability.

### Deprecation Process

**When to deprecate files:**
- Replacing old implementation with new approach
- Removing obsolete features
- Consolidating multiple files into one
- Refactoring changes file structure

**Naming format:** `YYYYMMDDTHHMMSSZ_<description>.zip`
- **YYYYMMDDTHHMMSSZ:** Timestamp from the TODO file that deprecated the files
- **description:** Brief hyphen-separated description (e.g., "old-auth-flow", "legacy-api-v1")

### Using the Deprecation Script

**Command:**
```bash
python .gemini/skills/workflow-utilities/scripts/deprecate_files.py \
  <todo-file> "<description>" <file1> <file2> ...
```

**Example:**
```bash
python .gemini/skills/workflow-utilities/scripts/deprecate_files.py \
  TODO_feature_20251023T104248Z_auth-refactor.md \
  "old-oauth-implementation" \
  src/auth/old_oauth.py \
  src/auth/legacy_tokens.py \
  tests/test_old_auth.py
```

**What happens:**
1. Extracts timestamp from TODO filename: `20251023T104248Z`
2. Creates archive: `ARCHIVED/20251023T104248Z_old-oauth-implementation.zip`
3. Adds files to zip archive
4. Removes original files from repository
5. Updates TODO file with deprecation entry
6. Commits changes

### Deprecation Examples

**Example 1: Replace authentication system**
```bash
# Deprecate old OAuth implementation
python .gemini/skills/workflow-utilities/scripts/deprecate_files.py \
  TODO_feature_20251023T140000Z_auth-v2.md \
  "oauth-v1-system" \
  src/auth/oauth_v1.py \
  src/auth/token_manager_v1.py \
  tests/test_oauth_v1.py
```

Result: `ARCHIVED/20251023T140000Z_oauth-v1-system.zip`

**Example 2: Consolidate vocabulary modules**
```bash
# Deprecate separate A1/A2 files (now combined)
python .gemini/skills/workflow-utilities/scripts/deprecate_files.py \
  TODO_feature_20251024T090000Z_vocab-consolidation.md \
  "separate-level-modules" \
  src/vocabulary/a1_nouns.py \
  src/vocabulary/a1_verbs.py \
  src/vocabulary/a2_nouns.py \
  src/vocabulary/a2_verbs.py
```

Result: `ARCHIVED/20251024T090000Z_separate-level-modules.zip`

**Example 3: Remove unused components**
```bash
# Deprecate experimental features that didn't work out
python .gemini/skills/workflow-utilities/scripts/deprecate_files.py \
  TODO_feature_20251025T110000Z_cleanup.md \
  "experimental-quiz-engine" \
  src/quiz/experimental_engine.py \
  src/quiz/adaptive_algorithm.py \
  tests/test_experimental_quiz.py \
  docs/quiz_algorithm.md
```

Result: `ARCHIVED/20251025T110000Z_experimental-quiz-engine.zip`

### Locating Deprecated Files

**List all archived files by date:**
```bash
ls -lt ARCHIVED/*.zip
```

**Search for specific deprecation:**
```bash
ls ARCHIVED/*oauth*.zip
ls ARCHIVED/*20251023*.zip
```

**View archive contents without extracting:**
```bash
unzip -l ARCHIVED/20251023T140000Z_oauth-v1-system.zip
```

**Extract archived files for review:**
```bash
# Extract to temporary directory
mkdir -p /tmp/review
unzip ARCHIVED/20251023T140000Z_oauth-v1-system.zip -d /tmp/review

# Review files
ls -la /tmp/review

# Clean up when done
rm -rf /tmp/review
```

### Archive Retention

**Policy:**
- Archives stored indefinitely in ARCHIVED/ directory
- Tracked in git history
- Listed in TODO.md manifest (last 10)
- Review quarterly for cleanup (remove after 1 year if not needed)

**Finding related TODO:**
Each archive timestamp matches a TODO file:
```bash
# Archive: ARCHIVED/20251023T140000Z_oauth-v1-system.zip
# TODO: TODO_feature_20251023T140000Z_*.md

# Find corresponding TODO
ls TODO_feature_20251023T140000Z_*.md
# or if archived:
ls ARCHIVED_TODO_feature_20251023T140000Z_*.md
```

---

## Documentation Update Process

When modifying skill implementations (scripts, templates, Q&A flow), **all related documentation must be updated** to prevent documentation drift.

### Quick Reference

**Full update checklist:**
```bash
cat .gemini/skills/UPDATE_CHECKLIST.md
```

**Validate versions:**
```bash
python .gemini/skills/workflow-utilities/scripts/validate_versions.py --verbose
```

**Semi-automated sync:**
```bash
python .gemini/skills/workflow-utilities/scripts/sync_skill_docs.py \
  <skill-name> <new-version>
```

### Update Process (12 Steps)

When updating a skill (e.g., bmad-planner, speckit-author):

#### Step 1: Determine Version Bump

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR (X.0.0):** Breaking changes, removed features
- **MINOR (x.Y.0):** New features (backward compatible)
- **PATCH (x.y.Z):** Bug fixes, documentation improvements

#### Step 2-12: Follow UPDATE_CHECKLIST.md

The complete 12-step checklist ensures all files are updated:

```
.gemini/skills/<skill-name>/SKILL.md       ← Version, commands, integration
.gemini/skills/<skill-name>/GEMINI.md      ← Usage examples
.gemini/skills/<skill-name>/CHANGELOG.md   ← Version history
WORKFLOW.md                                 ← Phase sections, commands
GEMINI.md                                   ← Command reference
[Integration files]                         ← Other skills affected
```

### Validation Tools

**Automatic validation:**
```bash
python .gemini/skills/workflow-utilities/scripts/validate_versions.py
```

Validates:
- ✓ All SKILL.md files have valid semantic versions
- ✓ WORKFLOW.md has valid version
- ✓ TODO.md manifest version is valid
- ✓ Version references are consistent

**View current versions:**
```bash
python .gemini/skills/workflow-utilities/scripts/validate_versions.py --verbose
```

Output:
```
Skill Versions:
  bmad-planner              v5.1.0
  speckit-author            v5.0.0
  workflow-orchestrator     v5.0.0
  git-workflow-manager      v5.0.0
  quality-enforcer          v5.0.0
  tech-stack-adapter        v5.0.0
  workflow-utilities        v5.0.0
```

### Semi-Automated Sync Tool

**Update skill documentation in one command:**

```bash
python .gemini/skills/workflow-utilities/scripts/sync_skill_docs.py \
  bmad-planner 5.2.0
```

**What it does:**
1. Updates version in SKILL.md frontmatter
2. Prompts for CHANGELOG entry
3. Updates CHANGELOG.md
4. Identifies affected WORKFLOW.md sections
5. Creates git commit with proper format

**Options:**
```bash
--archive     # Archive previous SKILL.md version
--dry-run     # Preview changes without making them
--auto-commit # Skip commit confirmation
```

**Example:**
```bash
# Dry run to preview changes
python .gemini/skills/workflow-utilities/scripts/sync_skill_docs.py \
  bmad-planner 5.2.0 --dry-run

# Update with archive
python .gemini/skills/workflow-utilities/scripts/sync_skill_docs.py \
  bmad-planner 5.2.0 --archive
```

### Common Mistakes to Avoid

❌ **Updating script without updating SKILL.md version**
- All script changes require version bump

❌ **Inconsistent command examples**
- Commands must match exactly in SKILL.md, GEMINI.md, WORKFLOW.md

❌ **Forgetting to update WORKFLOW.md**
- Phase sections must reflect current skill behavior

❌ **Not updating token efficiency metrics**
- If script changes affect token usage, update all files

❌ **Missing CHANGELOG entry**
- Every version bump requires a CHANGELOG entry

### Example: Updating bmad-planner

**Change made:** Added database migration Q&A

**Version bump:** 5.0.0 → 5.1.0 (MINOR - new feature)

**Files updated:**
1. `.gemini/skills/bmad-planner/SKILL.md` (version, Q&A flow)
2. `.gemini/skills/bmad-planner/GEMINI.md` (examples)
3. `.gemini/skills/bmad-planner/CHANGELOG.md` (new entry)
4. `WORKFLOW.md` (Phase 1 interactive session)
5. `GEMINI.md` (Phase 1 description)
6. `.gemini/skills/speckit-author/SKILL.md` (integration note)

**Commit message:**
```
feat(bmad): add database migration strategy Q&A

Updated bmad-planner from v5.0.0 to v5.1.0:
- Added interactive Q&A for database migration strategy

Updated documentation:
- SKILL.md, GEMINI.md, WORKFLOW.md, CHANGELOG.md

Refs: .gemini/skills/bmad-planner/CHANGELOG.md
```

### Related Documentation

- **[UPDATE_CHECKLIST.md](.gemini/skills/UPDATE_CHECKLIST.md)** - Complete 12-step checklist
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contributor guidelines
- **[CHANGELOG.md](CHANGELOG.md)** - Repository changelog
- **[GEMINI.md](GEMINI.md)** - Quick command reference

---

## Troubleshooting

### Worktree Creation Failed
```bash
# Check for stale worktrees
git worktree list
git worktree prune

# Verify branch doesn't exist
git branch -a | grep <branch-name>
```

### Quality Gates Failing
```bash
# Check coverage
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Check linting
uv run ruff check src/ tests/ --fix

# Check types
uv run mypy src/ --show-error-codes
```

### TODO.md Out of Sync
```bash
# Rebuild manifest
python .gemini/skills/workflow-utilities/scripts/todo_updater.py .

# Verify
cat TODO.md
```

### Merge Conflicts
```bash
# In worktree
git fetch origin
git rebase origin/contrib/<gh-user>
# Resolve conflicts
git add .
git rebase --continue
```

---

## Success Metrics

Track these metrics to validate workflow effectiveness:

- **Token usage per phase:** Target <1,000 tokens (orchestrator + 1-2 skills)
- **Context resets:** Target <3 per feature
- **Quality gate pass rate:** Target 100% on first run
- **PR cycle time:** Track for optimization
- **Test coverage:** Maintain ≥80%
- **Manifest accuracy:** TODO.md reflects actual state (100%)

---

## Key Design Principles

1. **Progressive disclosure:** Load only relevant skills per phase
2. **Independence:** Skills don't cross-reference, orchestrator coordinates
3. **Token efficiency:** YAML metadata compact, load SKILL.md only when needed
4. **Context awareness:** Detect repo vs worktree, load appropriately
5. **User confirmation:** Always wait for "Y" before executing
6. **Quality enforcement:** Gates must pass before PR
7. **Python ecosystem:** uv, pytest-cov, Podman, FastAPI
8. **Semantic versioning:** Automatic calculation
9. **Archive management:** Proper deprecation with timestamps

---

## Related Documentation

- **[GEMINI.md](GEMINI.md)** - Gemini Code interaction guide and quick command reference
- **[README.md](README.md)** - Project overview and getting started

### Skill Documentation

Referenced throughout this workflow:
- **Phase 0 (Initialization):** [initialize-repository](/.gemini/skills/initialize-repository/SKILL.md) (meta-skill for bootstrapping new repos)
- **Phase 0 (Setup):** [tech-stack-adapter](/.gemini/skills/tech-stack-adapter/SKILL.md), [git-workflow-manager](/.gemini/skills/git-workflow-manager/SKILL.md), [workflow-utilities](/.gemini/skills/workflow-utilities/SKILL.md)
- **Phase 1:** [bmad-planner](/.gemini/skills/bmad-planner/SKILL.md), [workflow-utilities](/.gemini/skills/workflow-utilities/SKILL.md)
- **Phase 2:** [git-workflow-manager](/.gemini/skills/git-workflow-manager/SKILL.md), [speckit-author](/.gemini/skills/speckit-author/SKILL.md), [quality-enforcer](/.gemini/skills/quality-enforcer/SKILL.md), [workflow-utilities](/.gemini/skills/workflow-utilities/SKILL.md)
- **Phase 3:** [quality-enforcer](/.gemini/skills/quality-enforcer/SKILL.md), [workflow-utilities](/.gemini/skills/workflow-utilities/SKILL.md)
- **Phase 4:** [git-workflow-manager](/.gemini/skills/git-workflow-manager/SKILL.md), [workflow-utilities](/.gemini/skills/workflow-utilities/SKILL.md)
- **Phase 5:** [git-workflow-manager](/.gemini/skills/git-workflow-manager/SKILL.md), [quality-enforcer](/.gemini/skills/quality-enforcer/SKILL.md), [workflow-utilities](/.gemini/skills/workflow-utilities/SKILL.md)
- **Phase 6:** [git-workflow-manager](/.gemini/skills/git-workflow-manager/SKILL.md), [speckit-author](/.gemini/skills/speckit-author/SKILL.md) (optional), [quality-enforcer](/.gemini/skills/quality-enforcer/SKILL.md), [workflow-utilities](/.gemini/skills/workflow-utilities/SKILL.md)
- **Always available:** [workflow-orchestrator](/.gemini/skills/workflow-orchestrator/SKILL.md)

---

**For more details on specific skills, see `.gemini/skills/<skill-name>/SKILL.md`**
