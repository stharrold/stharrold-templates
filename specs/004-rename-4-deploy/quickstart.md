# Quickstart: Workflow Command Rename and Release Workflow

**Branch**: `004-rename-4-deploy` | **Date**: 2025-11-22

## Overview

This feature renames `/5_integrate` to `/5_integrate` and adds `/6_release` and `/7_backmerge` commands for daily release workflows.

## New Workflow Structure

### Feature Workflow (Steps 1-5)

```
/1_specify → /2_plan → /3_tasks → /4_implement → /5_integrate
```

### Release Workflow (Steps 6-7)

```
/6_release → /7_backmerge
```

## Quick Reference

| Command | Purpose | Key Action |
|---------|---------|------------|
| `/5_integrate` | Integrate feature to develop | PR feature → contrib → develop |
| `/6_release` | Release to production | PR develop → release → main |
| `/7_backmerge` | Sync release back | PR release → develop, rebase contrib |

## Usage Examples

### After Feature Implementation

```bash
# Old way (no longer works)
/5_integrate

# New way
/5_integrate
```

### Daily Release Cycle

```bash
# 1. After features integrated to develop
/6_release

# 2. After release PR merged to main
/7_backmerge
```

### Complete Daily Workflow

```bash
# Morning: Start new feature
/1_specify "Add user authentication"
/2_plan
/3_tasks
/4_implement

# Afternoon: Integrate feature
/5_integrate

# End of day: Release to production
/6_release

# After release PR merged
/7_backmerge
```

## Validation Checklist

### After Implementation

- [ ] `/5_integrate` no longer exists (renamed to `/5_integrate`)
- [ ] `/5_integrate` has same behavior as old `/5_integrate`
- [ ] `/6_release` creates release branch and PR to main
- [ ] `/7_backmerge` creates PR to develop and rebases contrib
- [ ] All navigation strings updated in commands 0-6
- [ ] CLAUDE.md reflects 7-step workflow
- [ ] AGENTS.md synced from CLAUDE.md

### Manual Test Sequence

1. **Test `/5_integrate`**:
   - Create feature branch
   - Make small change
   - Run `/5_integrate`
   - Verify: PR created to contrib, then to develop

2. **Test `/6_release`**:
   - Ensure features in develop
   - Run `/6_release`
   - Verify: release branch created, PR to main

3. **Test `/7_backmerge`**:
   - Merge release PR to main
   - Run `/7_backmerge`
   - Verify: PR to develop, contrib rebased

## Migration Notes

### For Existing Users

The only breaking change is the command name:
- Old: `/5_integrate`
- New: `/5_integrate`

All functionality is preserved. Update any scripts or documentation that reference `/5_integrate`.

### For Documentation

Search and replace in all documentation:
- `/5_integrate` → `/5_integrate`
- "deploy" → "integrate" (in workflow context)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `/5_integrate` not found | Use `/5_integrate` instead |
| `/6_release` fails with "no changes" | Ensure develop has commits since last release |
| `/7_backmerge` rebase conflicts | Resolve conflicts manually, run `git rebase --continue` |
| Wrong branch after workflow | Run `git checkout contrib/<username>` |
