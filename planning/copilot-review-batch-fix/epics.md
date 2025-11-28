# Epics: Copilot Review Batch Fix

**Issue**: #104
**Slug**: copilot-review-batch-fix

## Epic 1: Code Bug Fixes (#31, #32, #44)

**Goal**: Fix code-level bugs identified by Copilot

### Tasks

1. [ ] Fix code block end markers counting logic (#31)
   - Find the regex that counts code block markers
   - Update to count all closing markers, not just bare ones
2. [ ] Fix extra space in regex pattern (#32)
   - Locate the regex with extra space
   - Remove the extraneous space
3. [ ] Add missing imports (#44)
   - Find code using datetime and os without imports
   - Add proper imports at top of file

## Epic 2: Documentation Fixes (#34, #38, #39, #41, #42)

**Goal**: Fix documentation formatting and content issues

### Tasks

1. [ ] Reorder worktree cleanup commands (#34)
   - Move cleanup commands after archive commands
   - Maintain proper workflow sequence
2. [ ] Add status indicators to priority list (#38)
   - Add [OK], [IN_PROGRESS], [ ] indicators
3. [ ] Document archive location (#39)
   - Add explanation of ARCHIVED/ directory
   - Include extraction instructions
4. [ ] Fix blank line spacing (#41)
   - Restore blank line between sections
5. [ ] Fix blank lines before code block (#42)
   - Restore explanatory text and spacing

## Epic 3: Security Fixes (#35, #43)

**Goal**: Address security concerns in logging and file paths

### Tasks

1. [ ] Sanitize error logging (#35)
   - Find functions logging error details
   - Sanitize sensitive information before logging
2. [ ] Fix emergency log path (#43)
   - Change /var/log/mcp-emergency.log to user-accessible location
   - Use ~/.local/share/mcp/emergency.log
   - Add proper error handling for permission failures

## Estimated Scope

- **Files to modify**: ~5-10 files
- **Complexity**: Low (targeted fixes)
- **Risk**: Low
- **Version bump**: PATCH
