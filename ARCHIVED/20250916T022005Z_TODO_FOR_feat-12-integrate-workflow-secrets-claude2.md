---
title: "Integration Plan: Workflow Secrets MCP (Claude2 Multi-Guide Implementation)"
issue: 12
priority: high
status: pending
worktree_name: feat/12-integrate-workflow-secrets-claude2
branch_name: feat/12-integrate-workflow-secrets-claude2
github_issue: https://github.com/stharrold/stharrold-templates/issues/12
estimated_effort: "3-4 hours"
created: 2025-09-15
updated: 2025-09-15

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
- [ ] Compare source sections against existing content in each target
- [ ] Flag identical information presented differently
- [ ] Identify overlapping concepts that could be consolidated

#### Contradictory Information Handling
- [ ] Cross-reference technical details between source and targets
- [ ] Flag version mismatches or outdated information
- [ ] Document conflicts requiring user input

#### Multi-Guide Placement Decisions
- [ ] Identify sections that could fit multiple guides
- [ ] Create decision matrix for content placement
- [ ] Plan cross-references between guides for related content

## Phase 1: Analysis and Planning

### [ ] 1. Source Report Analysis
- [ ] Read and parse `00_draft-initial/09_workflow-secrets-mcp.md`
- [ ] Identify discrete content sections and their topics
- [ ] Map content to appropriate target guides
- [ ] Note technical depth and audience level for each section

### [ ] 2. Target Guide Analysis
- [ ] Read existing content in each target guide
- [ ] Analyze current YAML frontmatter structure
- [ ] Identify integration points and logical insertion locations
- [ ] Check current file sizes and available space

### [ ] 3. Content Mapping Matrix
- [ ] Create detailed mapping of source sections to target locations
- [ ] Identify potential conflicts and overlaps
- [ ] Plan YAML frontmatter updates for cross-references
- [ ] Document user decision points

## Phase 2: Merge Preparation

### [ ] 4. Create worktree and branch
**Note**: Work will be completed using Claude2 method approach in dedicated worktree.

```bash
git worktree add ../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude2 -b feat/12-integrate-workflow-secrets-claude2
cd ../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude2
```

**Status**: Work being completed in `../stharrold-templates.worktrees/feat/12-integrate-workflow-secrets-claude2/`

### [ ] 5. Prepare merge proposals
- [ ] Generate proposed changes for each target file
- [ ] Include before/after content previews
- [ ] Document insertion locations and rationale
- [ ] Flag conflicts requiring user input

### [ ] 6. Present merge plan for approval
- [ ] Show content distribution across guides
- [ ] Highlight potential conflicts
- [ ] Request user input on placement decisions
- [ ] Get approval before proceeding with changes

## Phase 3: Content Integration

### [ ] 7. Update YAML frontmatter
- [ ] Add cross-references between guides
- [ ] Update version numbers and timestamps
- [ ] Add content source attribution
- [ ] Maintain frontmatter consistency

### [ ] 8. Integrate content sections
- [ ] Insert content at planned locations (not append)
- [ ] Maintain consistent formatting and structure
- [ ] Preserve existing section organization
- [ ] Add internal cross-references where appropriate

### [ ] 9. Resolve flagged conflicts
- [ ] Address duplicate content issues
- [ ] Resolve contradictory information
- [ ] Implement user decisions on placement
- [ ] Document resolution rationale

## Phase 4: Quality Assurance

### [ ] 10. Validate integration
- [ ] Check all target files remain under 30KB
- [ ] Verify no duplicate content between guides
- [ ] Test all code examples are complete and accurate
- [ ] Validate cross-references work correctly

### [ ] 11. Content consistency review
- [ ] Ensure consistent terminology across guides
- [ ] Verify technical accuracy of merged content
- [ ] Check formatting consistency
- [ ] Validate YAML frontmatter structure

### [ ] 12. Run quality checks
- [ ] Run Codacy analysis on all modified files
- [ ] Address any issues found
- [ ] Verify analysis passes for all targets

## Phase 5: Completion

### [ ] 13. Archive source document
```bash
mv 00_draft-initial/09_workflow-secrets-mcp.md ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_09_workflow-secrets-mcp.md
```

### [ ] 14. Commit changes
```bash
git add --all
git commit -m "feat: distribute workflow secrets across multiple guides (Claude2 implementation)

- Enhanced 25_mcp-security-tools.md with security patterns and tools
- Enhanced 32_workflow-patterns.md with implementation workflows
- Enhanced 12_server-management.md with configuration examples
- Updated YAML frontmatter with cross-references
- Archived source document with UTC timestamp
- Claude2 multi-guide distribution approach

Closes #12

🤖 Generated with Claude Code (Claude2 Method)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

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
- [ ] Content logically distributed across 3 topical guides
- [ ] All target files under 30KB
- [ ] No content duplication between guides
- [ ] Clear cross-references between related sections
- [ ] All workflow examples functional
- [ ] Codacy analysis passes for all targets
- [ ] GitHub issue #12 closed