# Tasks: Integrate Workflow Secrets MCP

**Input**: Design documents from `/specs/001-users-stharrold-documents/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Markdown documentation with YAML frontmatter
   → Structure: Single documentation enhancement project
2. Load design documents:
   → data-model.md: 4 entities (Workflow Examples, Security Patterns, Platform Commands, Error Handling)
   → contracts/: Documentation structure and content validation contracts
   → quickstart.md: 15 validation steps for integration process
3. Generate tasks by category:
   → Setup: Environment validation, content analysis
   → Tests: Size validation, cross-reference tests, content tests
   → Core: YAML updates, content integration, section enhancement
   → Integration: Cross-reference updates, navigation maintenance
   → Polish: Quality assurance, archive, tracking updates
4. Apply task rules:
   → Different validation scripts = mark [P] for parallel
   → Same file edits = sequential (no [P])
   → Validation tests before integration (Documentation TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate parallel execution examples
7. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files/operations, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Source file**: `00_draft-initial/09_workflow-secrets-mcp.md`
- **Target file**: `10_draft-merged/20_credentials/25_mcp-security-tools.md`
- **Archive destination**: `ARCHIVED/YYYYMMDDTHHMMSSZ_09_workflow-secrets-mcp.md`
- **Repository root**: `/Users/stharrold/Documents/GitHub/stharrold-templates.worktrees/feat/12-integrate-workflow-secrets/`

## Phase 3.1: Setup & Analysis

- [ ] **T001** Validate environment and file existence
  - Verify current branch: `feat/12-integrate-workflow-secrets`
  - Check source file: `00_draft-initial/09_workflow-secrets-mcp.md` exists (~11.6KB)
  - Check target file: `10_draft-merged/20_credentials/25_mcp-security-tools.md` exists (~16.8KB)
  - Calculate available space: 30,000 - target_size = ~13.2KB available

- [ ] **T002** [P] Analyze source content for unique sections
  - Extract section headers from `00_draft-initial/09_workflow-secrets-mcp.md`
  - Identify unique workflow examples not in target file
  - Map content integration points to target file structure
  - Estimate content size after deduplication (~8.8KB expected)

- [ ] **T003** Create backup of target file
  - Copy `10_draft-merged/20_credentials/25_mcp-security-tools.md` to `.backup` suffix
  - Verify backup integrity with diff comparison
  - Document backup location for rollback if needed

## Phase 3.2: Validation Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY integration**

- [ ] **T004** [P] File size compliance test
  - Create validation script to check file size < 30KB
  - Test current target file (should pass at ~16.8KB)
  - Test with simulated content addition (should fail when >30KB)
  - Document size monitoring commands for continuous checking

- [ ] **T005** [P] Cross-reference integrity test
  - Create script to validate all internal links in target file
  - Test existing cross-references (should pass)
  - Test broken link detection (should catch missing anchors)
  - Validate external file references to related guides

- [ ] **T006** [P] Content duplication detection test
  - Create script to detect duplicate content between source and target
  - Test with known duplicates (should detect mcp-secrets-plugin mentions)
  - Validate unique content identification algorithm
  - Document deduplication strategy for integration

- [ ] **T007** [P] Platform command syntax validation
  - Create script to validate bash command syntax in code blocks
  - Test existing commands in target file (should pass)
  - Test malformed commands (should fail)
  - Validate platform-specific command variations

- [ ] **T008** [P] YAML frontmatter structure test
  - Create script to validate YAML frontmatter format
  - Test current target file structure (should pass)
  - Test version increment validation
  - Test changelog format requirements

## Phase 3.3: Core Integration (ONLY after tests are failing)

- [ ] **T009** Update YAML frontmatter in target file
  - Increment version from 1.0 to 1.1 in `10_draft-merged/20_credentials/25_mcp-security-tools.md`
  - Update date from 2025-09-13 to 2025-09-14
  - Add changelog entry: "Enhanced with practical workflow examples and platform-specific verification commands"
  - Add new customizable field: `workflow_examples`

- [ ] **T010** Enhance mcp-secrets-plugin section with workflow examples
  - Add "Step-by-Step Installation Workflow" subsection
  - Insert CLI management examples with masked input prompts
  - Add platform-specific verification commands subsection
  - Include runtime credential injection examples from source lines 181-205

- [ ] **T011** Add Environment Variable Discovery Methods section
  - Create new section after Production-Ready Security Tools
  - Add Method 1: Error message analysis (source lines 50-55)
  - Add Method 2: Documentation review (source lines 57-65)
  - Add Method 3: Source code inspection (source lines 67-76)
  - Add Method 4: MCP manifest checking (source lines 78-89)
  - Include common patterns table (source lines 126-132)

- [ ] **T012** Add platform-specific verification commands
  - Create macOS Keychain verification subsection (source lines 325-334)
  - Create Windows Credential Manager subsection (source lines 337-344)
  - Create Linux libsecret verification subsection (source lines 347-354)
  - Ensure commands are tested and accurate for each platform

- [ ] **T013** Add error handling and recovery patterns section
  - Create new section before "Next Steps"
  - Add error detection patterns (source lines 356-384)
  - Include fallback strategies and recovery procedures
  - Add troubleshooting guidance for common failure modes

- [ ] **T014** Update cross-references and internal navigation
  - Add links to new workflow sections in table of contents
  - Update Tool Selection Guidelines to reference workflow examples
  - Add navigation between discovery methods and security tools
  - Preserve all existing cross-references and external links

- [ ] **T015** Monitor file size during integration
  - Run size check after each content addition (T010-T014)
  - Alert if approaching 28KB (warning threshold)
  - Stop integration if exceeds 30KB hard limit
  - Document final file size and remaining capacity

## Phase 3.4: Quality Assurance

- [ ] **T016** [P] Run Codacy analysis on enhanced file
  - Execute `./.codacy/cli.sh analyze 10_draft-merged/20_credentials/25_mcp-security-tools.md`
  - Fix any quality issues detected
  - Verify analysis passes without errors
  - Document analysis results

- [ ] **T017** [P] Test example commands and workflows
  - Verify bash command syntax in all code blocks
  - Test platform-specific commands on available systems
  - Validate masked input examples are properly formatted
  - Check that workflow examples are complete and executable

- [ ] **T018** [P] Verify all cross-references and navigation
  - Test all internal links resolve to correct sections
  - Verify external file references are valid
  - Check navigation flow between related sections
  - Validate table of contents reflects new structure

## Phase 3.5: Completion

- [ ] **T019** Archive source file with UTC timestamp
  - Move `00_draft-initial/09_workflow-secrets-mcp.md` to `ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_09_workflow-secrets-mcp.md`
  - Verify archive file integrity
  - Document archive location and timestamp
  - Clean up draft-initial directory

- [ ] **T020** Update tracking documents and close issue
  - Update `TODO.md` to mark issue #12 as complete
  - Prepare commit message referencing issue closure
  - Update `TODO_FOR_feat-12-integrate-workflow-secrets.md` status
  - Create commit with proper format including Claude Code attribution

## Dependencies

### Sequential Dependencies
- **Setup before Tests**: T001-T003 must complete before T004-T008
- **Tests before Integration**: T004-T008 must FAIL before T009-T015
- **Integration Sequence**: T009 → T010 → T011 → T012 → T013 → T014 → T015 (same file edits)
- **QA after Integration**: T016-T018 after T015 completes
- **Completion after QA**: T019-T020 after T016-T018 pass

### Parallel Opportunities
- **Analysis Phase**: T002 can run parallel with T001, T003
- **Test Creation**: T004-T008 can all run in parallel (different scripts)
- **Quality Assurance**: T016-T018 can run in parallel (independent validation)

## Parallel Execution Examples

### Phase 3.2: Create all validation tests together
```bash
# Launch T004-T008 together:
Task: "File size compliance test - create validation script for 30KB limit"
Task: "Cross-reference integrity test - validate all internal links"
Task: "Content duplication detection test - identify unique vs duplicate content"
Task: "Platform command syntax validation - verify bash commands"
Task: "YAML frontmatter structure test - validate metadata format"
```

### Phase 3.4: Run all quality checks together
```bash
# Launch T016-T018 together:
Task: "Run Codacy analysis on enhanced documentation file"
Task: "Test example commands and workflow completeness"
Task: "Verify all cross-references and navigation integrity"
```

## Success Criteria

### Content Integration Success
- [ ] Enhanced file size remains under 30KB (target: ~25.6KB)
- [ ] All unique workflow examples successfully integrated
- [ ] No duplicate content between source and target
- [ ] All cross-references functional and navigation preserved

### Quality Assurance Success
- [ ] Codacy analysis passes without issues
- [ ] All example commands tested and verified
- [ ] Platform-specific variations complete and accurate
- [ ] Integration enhances user experience with practical examples

### Process Completion Success
- [ ] Source file properly archived with UTC timestamp
- [ ] Issue #12 closed with proper commit attribution
- [ ] Documentation version incremented and changelog updated
- [ ] All validation tests pass after integration

## Notes
- This is a **documentation enhancement project**, not code implementation
- **Documentation TDD**: Validation tests must fail before integration
- **File size monitoring** is critical - stop if approaching 30KB limit
- **Content deduplication** ensures no redundant information
- **Cross-reference preservation** maintains navigation integrity
- Commit after each major phase completion
- Use `.backup` file for rollback if integration fails

## Task Generation Rules Applied
- **Different files/scripts**: Marked [P] for parallel execution
- **Same file edits**: Sequential to avoid conflicts
- **Tests before implementation**: Documentation TDD approach
- **Dependencies clearly mapped**: Phase gates prevent premature execution
- **Specific file paths**: All tasks include exact file locations
- **Measurable outcomes**: Clear success criteria for each task
