---
title: "Integration Plan: Workflow Secrets MCP (Claude Implementation)"
issue: 12
priority: high
status: pending
worktree_name: feat/12-integrate-workflow-secrets-claude
branch_name: feat/12-integrate-workflow-secrets-claude
github_issue: https://github.com/stharrold/stharrold-templates/issues/12
estimated_effort: "2-3 hours"
created: 2025-09-14
updated: 2025-09-14

source:
  file: "00_draft-initial/09_workflow-secrets-mcp.md"
  size_kb: 11.6
  content_type: "Security workflow examples"

target:
  file: "10_draft-merged/20_credentials/25_mcp-security-tools.md"
  action: "enhance_existing"
  size_limit_kb: 30
  parent_orchestrator: "10_draft-merged/20_credentials/CLAUDE.md"

dependencies:
  - Enhanced CLAUDE.md with unified git conventions
  - GitHub issue #12 created
  - Worktree structure established

parent_roadmap: "TODO.md"

success_criteria:
  - Source content integrated without duplication
  - Target file remains under 30KB
  - Cross-references updated
  - Codacy analysis passes
  - Source archived with UTC timestamp
  - GitHub issue #12 closed
---

# TODO: Integrate Workflow Secrets MCP (#12) - Claude Implementation

## Overview
Integrate practical security workflow examples from `09_workflow-secrets-mcp.md` into the existing `25_mcp-security-tools.md` file to enhance security patterns documentation.

**Implementation Approach**: This is the Claude-specific implementation. For Speckit approach, see TODO_FOR_feat-12-integrate-workflow-secrets.md (PR #25)

**Part of main roadmap**: See [TODO.md](TODO.md) for complete project status and priority context.

**Worktree Implementation**: This task is being completed in Claude-specific worktree `feat/12-integrate-workflow-secrets-claude` to differentiate from GitHub Speckit approach. See [TODO.md line 28](TODO.md#L28) for tracking.

## Pre-Integration Analysis

### [ ] 1. Read and analyze source document
- [ ] Review `00_draft-initial/09_workflow-secrets-mcp.md` content
- [ ] Identify unique workflow examples not in target
- [ ] Note key sections: mcp-secrets-plugin, mcpauth, platform-specific storage
- [ ] Extract reusable patterns and code examples

### [ ] 2. Read current target file
- [ ] Review `10_draft-merged/20_credentials/25_mcp-security-tools.md` structure
- [ ] Check current file size (must stay under 30KB)
- [ ] Identify integration points for new content
- [ ] Assess overlap with existing content

### [ ] 3. Plan integration strategy
- [ ] Map source sections to target locations
- [ ] Identify unique content to add
- [ ] Plan workflow examples placement
- [ ] Ensure no content duplication

## Content Integration

### [ ] 4. Create worktree and branch
**Note**: Work is being completed in Claude-specific worktree to differentiate from GitHub Speckit approach.

```bash
git worktree add ../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude -b feat/12-integrate-workflow-secrets-claude
cd ../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude
```

**Current Status**: ✅ Worktree created at `../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude`

### [ ] 5. Enhance target file
- [ ] Add step-by-step installation workflows
- [ ] Include mcp-secrets-plugin CLI examples
- [ ] Add mcpauth OAuth 2.1 workflow
- [ ] Include platform-specific credential verification
- [ ] Add troubleshooting section
- [ ] Preserve existing structure and references

### [ ] 6. Validate integration
- [ ] Check file size remains under 30KB
- [ ] Ensure no duplicate content
- [ ] Verify all code examples are complete
- [ ] Test example commands are accurate

## Quality Assurance

### [ ] 7. Update cross-references
- [ ] Update `20_credentials/CLAUDE.md` if needed
- [ ] Verify navigation reflects enhanced content
- [ ] Check internal links work correctly

### [ ] 8. Run code quality checks
- [ ] Run Codacy analysis on modified file:
  ```bash
  ./.codacy/cli.sh analyze 10_draft-merged/20_credentials/25_mcp-security-tools.md
  ```
- [ ] Address any issues found
- [ ] Verify analysis passes

### [ ] 9. Test and validate
- [ ] Manually review enhanced file
- [ ] Verify workflow examples are clear
- [ ] Check YAML frontmatter is valid
- [ ] Ensure 30KB limit maintained

## Completion

### [ ] 10. Archive source document
- [ ] Move source to ARCHIVED/ with UTC timestamp:
  ```bash
  mv 00_draft-initial/09_workflow-secrets-mcp.md ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_09_workflow-secrets-mcp.md
  ```

### [ ] 11. Commit changes
- [ ] Stage all changes
- [ ] Commit with descriptive message:
  ```bash
  git add --all
  git commit -m "feat: integrate workflow secrets patterns into security tools (Claude implementation)

  - Enhanced 25_mcp-security-tools.md with practical workflow examples
  - Added mcp-secrets-plugin installation and usage patterns
  - Included mcpauth OAuth 2.1 server deployment workflow
  - Added platform-specific credential verification steps
  - Archived source document with UTC timestamp
  - Claude-specific implementation approach

  Closes #12

  🤖 Generated with [Claude Code](https://claude.ai/code)

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

### [ ] 12. Update tracking
- [ ] Mark issue #12 complete in TODO.md
- [ ] Close GitHub issue #12
- [ ] Update TODO.md sync status

### [ ] 13. Merge and cleanup
- [ ] Switch back to contrib/stharrold branch
- [ ] Merge or create PR as appropriate
- [ ] Remove worktree when complete

## Integration Mapping

### Key Content Sections to Integrate:
1. **Step 1-2**: mcp-secrets-plugin installation → "Installation" section
2. **Step 3-4**: Configuration examples → "Configuration" section
3. **Step 5**: Credential verification → "Verification" section
4. **OAuth Examples**: mcpauth workflow → "OAuth 2.1" section
5. **Platform Storage**: macOS/Windows/Linux verification → "Platform-Specific" section
6. **Emergency Response**: Kill switch patterns → "Emergency Response" section

### Files Modified:
- `10_draft-merged/20_credentials/25_mcp-security-tools.md` (enhanced)
- `00_draft-initial/09_workflow-secrets-mcp.md` (archived)
- `TODO.md` (updated)

## Success Metrics
- [ ] Enhanced security tools documentation with practical examples
- [ ] File size under 30KB maintained
- [ ] No duplicate content
- [ ] All workflow examples functional
- [ ] Cross-references updated
- [ ] Codacy analysis passes
- [ ] GitHub issue #12 closed