# Quickstart: Remove Redundant TODO*.md System

**Feature Branch**: `007-remove-redundant-todo`
**Date**: 2025-11-23
**Estimated Time**: 15-30 minutes

---

## Prerequisites

- [x] On branch `007-remove-redundant-todo`
- [x] Spec and design artifacts complete
- [ ] Podman available (`podman info`)

---

## Validation Scenarios

### Scenario 1: Archive TODO.md

**Given**: `TODO.md` exists in repository root
**When**: Archive operation completes
**Then**:
- `TODO.md` no longer in root
- `docs/archived/20251123T*_TODO.md` exists
- File content preserved

**Verification**:
```bash
# Before
ls TODO.md  # Should exist

# After
ls TODO.md  # Should fail (not found)
ls docs/archived/*TODO*.md  # Should show archived file
```

---

### Scenario 2: Quality Gates Pass Without TODO Files

**Given**: No `TODO*.md` files in repository root
**When**: Quality gates run
**Then**: All 5 gates pass

**Verification**:
```bash
podman-compose run --rm dev python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
# Expected: 5/5 gates pass
# Expected: No "[5/6]" or "[6/6]" output
```

---

### Scenario 3: GEMINI.md Updated

**Given**: GEMINI.md previously referenced TODO system
**When**: Documentation update completes
**Then**:
- No "TODO Frontmatter" in quality gates table
- No "TODO*.md YAML Frontmatter" section
- No "archive-todo" in PR workflow
- Gate 6 renumbered to Gate 5

**Verification**:
```bash
# Should return NO matches
grep -n "TODO Frontmatter" GEMINI.md
grep -n "archive-todo" GEMINI.md
grep -n "TODO\*.md YAML" GEMINI.md

# Should show Gate 5 is AI Config Sync
grep -n "5. AI Config Sync" GEMINI.md
```

---

### Scenario 4: AGENTS.md Synced

**Given**: GEMINI.md has been updated
**When**: Sync operation completes
**Then**: AGENTS.md matches GEMINI.md (no TODO references)

**Verification**:
```bash
# Run sync
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents

# Verify sync
grep -n "TODO Frontmatter" AGENTS.md  # Should return nothing
```

---

## Quick Implementation Checklist

### Phase 1: Archive Files
```bash
# 1. Archive TODO.md
mv TODO.md docs/archived/20251123T000000Z_TODO.md
```

### Phase 2: Update Quality Gates Script
```bash
# 2. Edit run_quality_gates.py
# - Remove check_todo_frontmatter() function
# - Remove Gate 5 call
# - Renumber Gate 6 → Gate 5
# - Update gate count from 6 to 5
```

### Phase 3: Update Documentation
```bash
# 3. Edit GEMINI.md
# - Remove Gate 5 row from table
# - Renumber Gate 6 → 5
# - Remove "TODO*.md YAML Frontmatter" section
# - Remove "archive-todo" from PR workflow
# - Remove "TODO files require YAML frontmatter" from guidelines
```

### Phase 4: Sync and Verify
```bash
# 4. Sync AGENTS.md
podman-compose run --rm dev python .gemini/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents

# 5. Run quality gates
podman-compose run --rm dev python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
```

---

## Success Criteria

| Criterion | Verification Command | Expected Result |
|-----------|---------------------|-----------------|
| TODO.md archived | `ls TODO.md` | File not found |
| Archive exists | `ls docs/archived/*TODO*` | Shows archived file |
| Gates pass | `run_quality_gates.py` | 5/5 pass |
| No TODO refs in docs | `grep "TODO Frontmatter" GEMINI.md` | No output |
| AGENTS.md synced | `diff GEMINI.md AGENTS.md` | Minimal diff (headers only) |

---

## Rollback Plan

If issues occur:
```bash
# Restore TODO.md
mv docs/archived/20251123T000000Z_TODO.md TODO.md

# Revert changes
git checkout HEAD -- GEMINI.md AGENTS.md
git checkout HEAD -- .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
```
