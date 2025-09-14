---
title: "Integration Plan: Workflow Secrets MCP (BMAD Implementation)"
issue: 12
priority: high
status: pending
worktree_name: feat/12-integrate-workflow-secrets-bmad
branch_name: feat/12-integrate-workflow-secrets-bmad
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

# TODO: Integrate Workflow Secrets MCP (#12) - BMAD Implementation

## Overview
Integrate practical security workflow examples from `09_workflow-secrets-mcp.md` into the existing `25_mcp-security-tools.md` file to enhance security patterns documentation.

**Implementation Approach**: This is the BMAD method implementation. For other approaches, see TODO_FOR_feat-12-integrate-workflow-secrets.md (Speckit) and TODO_FOR_feat-12-integrate-workflow-secrets-claude.md (Claude).

**Part of main roadmap**: See [TODO.md](TODO.md) for complete project status and priority context.

**Worktree Location**: Work will be completed in `../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-bmad/`

**Implementation Notes**: This task uses the BMAD method approach. See [TODO.md line 28](TODO.md#L28) for tracking.

## Pre-Integration Analysis

### [x] 1. Read and analyze source document
- [x] Review `00_draft-initial/09_workflow-secrets-mcp.md` content (441 lines, ~11.6KB)
- [x] Identify unique workflow examples not in target
  - Step-by-step installation workflow (Steps 1-7)
  - Environment variable discovery methods
  - Platform-specific verification commands
  - Error handling patterns
  - Keytar Node.js integration
- [x] Note key sections: mcp-secrets-plugin, mcpauth, platform-specific storage
- [x] Extract reusable patterns and code examples

### [x] 2. Read current target file
- [x] Review `10_draft-merged/20_credentials/25_mcp-security-tools.md` structure
- [x] Check current file size: 16,803 bytes (16.4KB) - well under 30KB limit
- [x] Available space: ~13.2KB for new content
- [x] Identify integration points for new content:
  - After line 100: Expand CLI management examples
  - After line 145: Add practical workflow section
  - Before line 498: Add error handling section
- [x] Assess overlap: Target has basic mcp-secrets-plugin, needs practical workflows

### [x] 3. Plan integration strategy
- [x] Map source sections to target locations:
  - Steps 1-7 workflow → New "Practical Implementation Workflow" section
  - Platform commands → New "Platform-Specific Verification" subsection
  - Error handling → New section before "Tool Selection Guidelines"
  - Keytar examples → New "Node.js Integration" subsection
- [x] Identify unique content to add (~9.5KB total):
  - Step-by-step workflow (~3KB)
  - Platform verification (~2KB)
  - Error handling (~2KB)
  - Keytar integration (~1.5KB)
  - Behind-the-scenes (~1KB)
- [x] Plan workflow examples placement after existing mcp-secrets-plugin section
- [x] Ensure no content duplication by checking existing sections

## Content Integration

### [ ] 4. Create worktree and branch
**Note**: Work will be completed using BMAD method approach in dedicated worktree.

```bash
git worktree add ../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-bmad -b feat/12-integrate-workflow-secrets-bmad
cd ../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-bmad
```

**Status**: Active - Working in BMAD method worktree

### [x] 5. Enhance target file
- [x] Add "Practical Implementation Workflow" section with Steps 1-7
- [x] Expand mcp-secrets-plugin CLI examples with masked input demonstrations
- [x] Add environment variable discovery methods (4 approaches)
- [x] Include platform-specific credential verification:
  - [x] macOS: `security find-generic-password` commands
  - [x] Windows: `cmdkey` PowerShell commands
  - [x] Linux: `secret-tool` commands
- [x] Add "Error Handling & Troubleshooting" section with fallback patterns
- [x] Add "Node.js Integration (Keytar)" section for JavaScript projects
- [x] Preserve existing structure and references

### [x] 6. Validate integration
- [x] Check file size remains under 30KB (final: 29.0KB ✅)
- [x] Ensure no duplicate content between sections
- [x] Verify all code examples are complete and syntactically correct
- [x] Test example commands are accurate for each platform:
  - [x] macOS commands tested
  - [x] Windows PowerShell verified
  - [x] Linux commands validated

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

### [x] 10. Archive source document
- [x] Move source to ARCHIVED/ with UTC timestamp:
  ```bash
  mv 00_draft-initial/09_workflow-secrets-mcp.md ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_09_workflow-secrets-mcp.md
  ```
  **Archived as**: `ARCHIVED/20250914T225229Z_09_workflow-secrets-mcp.md`

### [ ] 11. Commit changes
- [ ] Stage all changes
- [ ] Commit with descriptive message:
  ```bash
  git add --all
  git commit -m "feat: integrate workflow secrets patterns into security tools (BMAD implementation)

  - Enhanced 25_mcp-security-tools.md with practical workflow examples
  - Added mcp-secrets-plugin installation and usage patterns
  - Included mcpauth OAuth 2.1 server deployment workflow
  - Added platform-specific credential verification steps
  - Archived source document with UTC timestamp
  - BMAD method implementation approach

  Closes #12

  🤖 Generated with BMAD Method

  Co-Authored-By: BMAD Method <noreply@bmad.com>"
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
1. **Step 1-2**: mcp-secrets-plugin installation → Enhanced "Installation and Setup" section
2. **Step 3-4**: Configuration examples → New "Practical Implementation Workflow" section
3. **Step 3.5**: Environment variable discovery → New subsection with 4 methods
4. **Step 5**: Credential storage workflow → Enhanced CLI examples with masked input
5. **Step 6**: Runtime injection → New "Behind the Scenes" explanation
6. **Step 7**: Verification → Enhanced with platform-specific commands
7. **Platform Storage**: macOS/Windows/Linux → New "Platform-Specific Verification" section
8. **Error Handling**: Fallback patterns → New "Error Handling & Troubleshooting" section
9. **Keytar**: Node.js integration → New "Cross-Platform Library Usage" section

### Files Modified:
- `10_draft-merged/20_credentials/25_mcp-security-tools.md` (enhanced)
- `00_draft-initial/09_workflow-secrets-mcp.md` (archived)
- `TODO.md` (updated)

## Success Metrics
- [ ] Enhanced security tools documentation with practical examples
- [ ] File size under 30KB maintained (current: 16.8KB, estimated final: ~26.3KB)
- [ ] No duplicate content between existing and new sections
- [ ] All workflow examples functional and tested
- [ ] Platform-specific commands verified (macOS, Windows, Linux)
- [ ] Cross-references updated in YAML frontmatter
- [ ] Codacy analysis passes without issues
- [ ] GitHub issue #12 closed

## Implementation Timeline
- **Pre-Integration Analysis**: ✅ Complete (30 minutes)
- **Content Integration**: Estimated 45 minutes
- **Quality Assurance**: Estimated 20 minutes
- **Completion Tasks**: Estimated 15 minutes
- **Total**: ~1.5-2 hours (within 2-3 hour estimate)