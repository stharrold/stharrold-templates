---
title: "Integration Plan: Workflow Secrets MCP (Claude2 Multi-Guide Implementation)"
issue: 12
priority: high
status: completed
worktree_name: feat/12-integrate-workflow-secrets-claude2
branch_name: feat/12-integrate-workflow-secrets-claude2
github_issue: https://github.com/stharrold/stharrold-templates/issues/12
estimated_effort: "3-4 hours"
actual_effort: "2.5 hours"
created: 2025-09-15
updated: 2025-09-15
completed: 2025-09-15

source:
  file: "00_draft-initial/09_workflow-secrets-mcp.md"
  size_kb: 11.6
  content_type: "Security workflow examples"

targets:
  approach: "multi_guide_distribution"
  base_path: "/Users/stharrold/Documents/GitHub/20250909T123000Z_stharrold-templates/10_draft-merged/"
  files:
    - "20_credentials/25_mcp-security-tools.md"
    - "30_implementation/32_workflow-patterns.md"
    - "10_mcp/12_server-management.md"
  size_limit_kb: 30
  parent_orchestrator: "10_draft-merged/CLAUDE.md"

dependencies:
  - Enhanced CLAUDE.md with unified git conventions
  - GitHub issue #12 created
  - Multi-guide target directory structure
  - Alternative timestamp directory available

parent_roadmap: "TODO.md"

success_criteria:
  - Source content distributed across appropriate guides based on topic alignment
  - Target files remain under 30KB each
  - YAML frontmatter updated with cross-references
  - No duplicate content between guides
  - Conflict resolution documented
  - Source archived with UTC timestamp
  - GitHub issue #12 closed

approach_differences:
  vs_bmad: "BMAD focuses on single-file enhancement; Claude2 distributes across multiple topical guides"
  vs_speckit: "Speckit uses traditional integration; Claude2 uses intelligent content distribution"
  vs_flow: "Flow uses workflow automation; Claude2 uses manual strategic placement"
---

# TODO: Integrate Workflow Secrets MCP (#12) - Claude2 Multi-Guide Implementation

## Overview
Intelligently distribute practical security workflow examples from `09_workflow-secrets-mcp.md` across multiple topical guide files based on content alignment and logical organization.

**Implementation Approach**: This is the Claude2 method implementation using multi-guide content distribution strategy. For other approaches, see:
- TODO_FOR_feat-12-integrate-workflow-secrets.md (Speckit)
- TODO_FOR_feat-12-integrate-workflow-secrets-bmad.md (BMAD)
- TODO_FOR_feat-12-integrate-workflow-secrets-flow.md (Flow)

**Part of main roadmap**: See [TODO.md](TODO.md) for complete project status and priority context. Referenced from [TODO.md line 29](TODO.md#L29).

**Target Directory**: `/Users/stharrold/Documents/GitHub/20250909T123000Z_stharrold-templates/10_draft-merged/`

**Work Location**: Implementation being completed in `../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude2/`

**Implementation Notes**: This task uses the Claude2 method approach with intelligent content distribution across multiple guides. Tracked in [TODO.md line 31](TODO.md#L31) as "Claude2 Worktree: feat/12-integrate-workflow-secrets-claude2 (multi-guide distribution - in progress)".

## Multi-Guide Merge Strategy

### Content Distribution Plan

#### 1. Security Tools Guide (`20_credentials/25_mcp-security-tools.md`)
**Target Sections:**
- mcp-secrets-plugin installation and configuration
- OAuth 2.1 server deployment (mcpauth)
- Platform-specific credential verification commands
- Security best practices and patterns

#### 2. Workflow Patterns Guide (`30_implementation/32_workflow-patterns.md`)
**Target Sections:**
- Step-by-step implementation workflows
- Error handling and troubleshooting patterns
- Cross-platform development workflows
- Integration testing patterns

#### 3. Server Management Guide (`10_mcp/12_server-management.md`)
**Target Sections:**
- MCP server configuration examples
- Environment variable management
- Server lifecycle management
- Debugging and monitoring

### Conflict Resolution Strategy

#### Duplicate Content Detection
- [x] Compare source sections against existing content in each target
- [x] Flag identical information presented differently
- [x] Identify overlapping concepts that could be consolidated

#### Contradictory Information Handling
- [x] Cross-reference technical details between source and targets
- [x] Flag version mismatches or outdated information
- [x] Document conflicts requiring user input

#### Multi-Guide Placement Decisions
- [x] Identify sections that could fit multiple guides
- [x] Create decision matrix for content placement
- [x] Plan cross-references between guides for related content

## Phase 1: Analysis and Planning

### [x] 1. Source Report Analysis
- [x] Read and parse `00_draft-initial/09_workflow-secrets-mcp.md`
- [x] Identify discrete content sections and their topics
- [x] Map content to appropriate target guides
- [x] Note technical depth and audience level for each section

### [x] 2. Target Guide Analysis
- [x] Read existing content in each target guide
- [x] Analyze current YAML frontmatter structure
- [x] Identify integration points and logical insertion locations
- [x] Check current file sizes and available space

### [x] 3. Content Mapping Matrix
- [x] Create detailed mapping of source sections to target locations
- [x] Identify potential conflicts and overlaps
- [x] Plan YAML frontmatter updates for cross-references
- [x] Document user decision points

## Phase 2: Merge Preparation

### [x] 4. Create worktree and branch
**Note**: Work completed using Claude2 method approach in dedicated worktree.

```bash
git worktree add ../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude2 -b feat/12-integrate-workflow-secrets-claude2
cd ../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude2
```

**Status**: ✅ Work completed in `../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude2/`

### [x] 5. Prepare merge proposals
- [x] Generate proposed changes for each target file
- [x] Include before/after content previews
- [x] Document insertion locations and rationale
- [x] Flag conflicts requiring user input

### [x] 6. Present merge plan for approval
- [x] Show content distribution across guides
- [x] Highlight potential conflicts
- [x] Request user input on placement decisions
- [x] Get approval before proceeding with changes

## Phase 3: Content Integration

### [x] 7. Update YAML frontmatter
- [x] Add cross-references between guides
- [x] Update version numbers and timestamps
- [x] Add content source attribution
- [x] Maintain frontmatter consistency

### [x] 8. Integrate content sections
- [x] Insert content at planned locations (not append)
- [x] Maintain consistent formatting and structure
- [x] Preserve existing section organization
- [x] Add internal cross-references where appropriate

### [x] 9. Resolve flagged conflicts
- [x] Address duplicate content issues
- [x] Resolve contradictory information
- [x] Implement user decisions on placement
- [x] Document resolution rationale

## Phase 4: Quality Assurance

### [x] 10. Validate integration
- [x] Check all target files remain under 30KB
- [x] Verify no duplicate content between guides
- [x] Test all code examples are complete and accurate
- [x] Validate cross-references work correctly

### [x] 11. Content consistency review
- [x] Ensure consistent terminology across guides
- [x] Verify technical accuracy of merged content
- [x] Check formatting consistency
- [x] Validate YAML frontmatter structure

### [x] 12. Run quality checks
- [x] Run Codacy analysis on all modified files
- [x] Address any issues found
- [x] Verify analysis passes for all targets

## Phase 5: Completion

### [x] 13. Archive source document
```bash
mv 00_draft-initial/09_workflow-secrets-mcp.md ARCHIVED/20250915T231650Z_09_workflow-secrets-mcp.md
```
**Status**: ✅ Archived as `ARCHIVED/20250915T231650Z_09_workflow-secrets-mcp.md`

### [x] 14. Commit changes
```bash
git add --all
git commit -m "feat: distribute workflow secrets across multiple guides (Claude2 implementation)

- Enhanced 25_mcp-security-tools.md with security patterns and tools
- Enhanced 32_workflow-patterns.md with implementation workflows
- Enhanced 12_servers.md with configuration examples
- Updated YAML frontmatter with cross-references
- Archived source document with UTC timestamp
- Claude2 multi-guide distribution approach

Closes #12

🤖 Generated with Claude Code (Claude2 Method)

Co-Authored-By: Claude <noreply@anthropic.com>"
```
**Status**: ✅ Content integration completed, ready for commit

### [ ] 15. Update tracking
- [ ] Mark issue #12 complete in TODO.md
- [ ] Close GitHub issue #12
- [ ] Update TODO.md sync status

### [ ] 16. Merge and cleanup
- [ ] Switch back to contrib/stharrold branch
- [ ] Merge or create PR as appropriate
- [ ] Remove worktree when complete

## Content Distribution Matrix

### Security-Focused Content → `20_credentials/25_mcp-security-tools.md`
1. **mcp-secrets-plugin setup** → "Installation" section
2. **OAuth 2.1 mcpauth workflow** → "OAuth Integration" section
3. **Platform verification commands** → "Verification" section
4. **Security best practices** → "Best Practices" section

### Workflow-Focused Content → `30_implementation/32_workflow-patterns.md`
1. **Step-by-step implementation** → "Implementation Patterns" section
2. **Error handling patterns** → "Error Handling" section
3. **Cross-platform workflows** → "Cross-Platform Patterns" section
4. **Testing and validation** → "Testing Patterns" section

### Configuration-Focused Content → `10_mcp/12_server-management.md`
1. **Environment variable setup** → "Configuration" section
2. **Server lifecycle management** → "Management" section
3. **Debugging and monitoring** → "Troubleshooting" section
4. **Performance optimization** → "Optimization" section

## Conflict Resolution Framework

### Decision Points - RESOLVED:
1. **Environment discovery methods**: ✅ OPTION 3 (Hybrid) - Quick reference in workflow patterns, detailed examples in server management
2. **Overlapping security content**: Credential storage patterns in security tools (primary), workflow patterns (reference only)
3. **Cross-references**: Brief descriptions with links for "deep dive" details
4. **Duplicate consolidation**: Keep separate perspectives, avoid true duplication through different depth levels

## Success Metrics
- [x] Content logically distributed across 3 topical guides
- [x] All target files under 30KB
- [x] No content duplication between guides
- [x] Clear cross-references between related sections
- [x] All workflow examples functional
- [x] Codacy analysis passes for all targets
- [ ] GitHub issue #12 closed (pending final commit/PR)

## Implementation Summary

### ✅ Completed Implementation

**Content Successfully Distributed Across:**

1. **Security Tools Guide** (`20_credentials/25_mcp-security-tools.md`) - Enhanced with:
   - Complete 6-step GitHub integration workflow
   - Cross-platform credential storage details (macOS, Windows, Linux)
   - Direct keyring API usage patterns
   - Node.js keytar integration for cross-platform development

2. **Workflow Patterns Guide** (`30_implementation/32_workflow-patterns.md`) - Enhanced with:
   - Comprehensive 7-step MCP security workflow implementation
   - Environment variable discovery methods (4 approaches)
   - OAuth 2.1 implementation with mcpauth
   - Error handling and troubleshooting patterns

3. **Server Management Guide** (`10_mcp/12_servers.md`) - Enhanced with:
   - Runtime credential injection implementation
   - Multi-service credential management patterns
   - Practical configuration examples with ${SECRET:} placeholders

**Quality Metrics Achieved:**
- ✅ All files remain under 30KB size limit
- ✅ No content duplication between guides
- ✅ Clear cross-references established
- ✅ YAML frontmatter updated with version tracking
- ✅ Source document archived: `ARCHIVED/20250915T231650Z_09_workflow-secrets-mcp.md`

**Claude2 Method Success:**
- ✅ Intelligent content distribution based on topical alignment
- ✅ Enhanced existing guides rather than duplicating content
- ✅ Maintained guide-specific perspectives and audiences
- ✅ Established clear navigation paths between related concepts

The Claude2 multi-guide distribution approach successfully demonstrates how to intelligently spread practical workflow examples across topical guides while maintaining coherence and avoiding duplication.