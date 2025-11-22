# Quickstart: Workflow Command Rename and Release Workflow

**Branch**: `004-rename-4-deploy` | **Date**: 2025-11-22

## Overview

This feature renames `/4_deploy` to `/4_integrate` and adds `/5_release` and `/6_backmerge` commands for daily release workflows.

## New Workflow Structure

### Feature Workflow (Steps 1-5)

```
/0_specify → /1_plan → /2_tasks → /3_implement → /4_integrate
```

### Release Workflow (Steps 6-7)

```
/5_release → /6_backmerge
```

## Quick Reference

| Command | Purpose | Key Action |
|---------|---------|------------|
| `/4_integrate` | Integrate feature to develop | PR feature → contrib → develop |
| `/5_release` | Release to production | PR develop → release → main |
| `/6_backmerge` | Sync release back | PR release → develop, rebase contrib |

## Usage Examples

### After Feature Implementation

```bash
# Old way (no longer works)
/4_deploy

# New way
/4_integrate
```

### Daily Release Cycle

```bash
# 1. After features integrated to develop
/5_release

# 2. After release PR merged to main
/6_backmerge
```

### Complete Daily Workflow

```bash
# Morning: Start new feature
/0_specify "Add user authentication"
/1_plan
/2_tasks
/3_implement

# Afternoon: Integrate feature
/4_integrate

# End of day: Release to production
/5_release

# After release PR merged
/6_backmerge
```

## Validation Checklist

### After Implementation

- [ ] `/4_deploy` no longer exists (renamed to `/4_integrate`)
- [ ] `/4_integrate` has same behavior as old `/4_deploy`
- [ ] `/5_release` creates release branch and PR to main
- [ ] `/6_backmerge` creates PR to develop and rebases contrib
- [ ] All navigation strings updated in commands 0-6
- [ ] CLAUDE.md reflects 7-step workflow
- [ ] AGENTS.md synced from CLAUDE.md

### Manual Test Sequence

1. **Test `/4_integrate`**:
   - Create feature branch
   - Make small change
   - Run `/4_integrate`
   - Verify: PR created to contrib, then to develop

2. **Test `/5_release`**:
   - Ensure features in develop
   - Run `/5_release`
   - Verify: release branch created, PR to main

3. **Test `/6_backmerge`**:
   - Merge release PR to main
   - Run `/6_backmerge`
   - Verify: PR to develop, contrib rebased

## Migration Notes

### For Existing Users

The only breaking change is the command name:
- Old: `/4_deploy`
- New: `/4_integrate`

All functionality is preserved. Update any scripts or documentation that reference `/4_deploy`.

### For Documentation

Search and replace in all documentation:
- `/4_deploy` → `/4_integrate`
- "deploy" → "integrate" (in workflow context)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `/4_deploy` not found | Use `/4_integrate` instead |
| `/5_release` fails with "no changes" | Ensure develop has commits since last release |
| `/6_backmerge` rebase conflicts | Resolve conflicts manually, run `git rebase --continue` |
| Wrong branch after workflow | Run `git checkout contrib/<username>` |
