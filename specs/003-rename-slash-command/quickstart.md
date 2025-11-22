# Quickstart: Verify Slash Command Namespace

**Feature**: 003-rename-slash-command
**Date**: 2025-11-22

## Verification Steps

### 1. Verify Directory Structure

```bash
# Check workflow directory exists
ls -la .claude/commands/workflow/

# Expected output:
# 0_specify.md
# 1_plan.md
# 2_tasks.md
# 3_implement.md
# 4_deploy.md
```

### 2. Verify Old Commands Removed

```bash
# Should NOT exist
ls .claude/commands/specify.md    # Should fail
ls .claude/commands/plan.md       # Should fail
ls .claude/commands/tasks.md      # Should fail
ls .claude/commands/workflow.md   # Should fail
```

### 3. Verify Frontmatter Navigation

```bash
# Check each file has correct description with navigation
head -5 .claude/commands/workflow/1_specify.md
# Expected: description includes "(start) → workflow/1_specify → workflow/2_plan"

head -5 .claude/commands/workflow/2_plan.md
# Expected: description includes "workflow/1_specify → workflow/2_plan → workflow/3_tasks"

head -5 .claude/commands/workflow/3_tasks.md
# Expected: description includes "workflow/2_plan → workflow/3_tasks → workflow/4_implement"

head -5 .claude/commands/workflow/4_implement.md
# Expected: description includes "workflow/3_tasks → workflow/4_implement → workflow/5_integrate"

head -5 .claude/commands/workflow/5_integrate.md
# Expected: description includes "workflow/4_implement → workflow/5_integrate → (end)"
```

### 4. Verify Commands Work in Claude Code

```
# In Claude Code CLI, type:
/1_specify test feature

# Should execute the specify workflow
# Help should show "(project:workflow)" tag
```

### 5. Verify CLAUDE.md Updated

```bash
# Check workflow order documentation
grep -A 10 "Slash Commands" CLAUDE.md

# Expected: Shows /1_specify, /2_plan, /3_tasks, /4_implement, /5_integrate
```

## Success Criteria

- [ ] All 5 command files exist in `workflow/` subdirectory
- [ ] Old command files removed from root commands directory
- [ ] Each command has navigation in description
- [ ] CLAUDE.md reflects new command names
- [ ] Commands execute correctly in Claude Code
