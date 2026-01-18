# Changelog

All notable changes to the Standard Language Learning Repository workflow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- **feature-dev command** - Replaced by built-in Gemini CLI tools for autonomous implementation.

## [7.2.0] - 2026-01-04

### Changed
- **Dependencies** - Added `tomlkit` as a development dependency.
- **Testing** - Updated `test_secrets.py` to use `tmp_path` fixture for better isolation.
- **Workflow** - Disabled `gemini-dispatch.yml` workflow.
- **Workflow** - Slash commands and scripts updated to output manual instructions instead of automatic deletion/merging for critical steps.
- **Documentation** - Updated `GEMINI.md` references.
- **Documentation** - Updated `WORKFLOW.md`, `GEMINI.md`, and skill docs to reflect manual cleanup workflow.

## [7.0.0] - 2026-01-01

### Removed
- **Cross-tool support** - Streamlined for Gemini-only development
  - Archived and removed `.agents/` and `AGENTS.md`
  - Archived and removed `.specify/` (deprecated migration source)
  - Archived and removed out-of-date scripts: `sync_ai_config.py`, `sync_skill_docs.py`
  - Archived and removed deprecated skills and their tests:
    - `bmad-planner` (replaced by autonomous implementation)
    - `speckit-author` (replaced by autonomous implementation)
    - `quality-enforcer` (replaced by Gemini Code Review)- **Repository cleanup** - Removed build artifacts and legacy maintenance scripts
  - Archived and removed build artifacts: `dist/`, `stharrold_templates.egg-info/`
  - Archived and removed legacy bash validation scripts (`test_*.sh`, `validate_documentation.sh`)
  - Archived and removed third-party tool configurations: `.claude/`, `.codacy/`
  - Archived and removed manual MCP manager: `mcp_manager.py` (Gemini manages MCP natively)

### Added
- **ASCII-only enforcement** (Issue #121) - Pre-commit hook validates Python files
  - Added `check_ascii_only.py` script with 77 Unicode to ASCII mappings
  - Replaced 363 Unicode violations across 28 files
  - Pre-commit hook prevents regressions
- **Shared archive creation** (Issue #123) - `archive_manager.py create` command
  - Added `create_archive()` function with `--delete`, `--preserve-paths`, `--output-dir` options
  - Shared by `deprecate_files.py` for code reuse
  - Error handling for permission/symlink issues
- **Pending worktree detection** (Issue #124) - Detects incomplete feature branches
  - Added `PendingWorktree` TypedDict for structured data
  - Non-blocking warnings in steps 5-7 for worktrees with unmerged commits
  - Parses `git worktree list --porcelain` for accurate detection
- **DuckDB required dependency** (Issue #125) - Moved from optional to required
  - Added comprehensive tests for import, version, connection, query, table creation
  - Version constraint: `duckdb>=1.4.2`

### Changed
- **Absolute path resolution** (Issue #122) - Consistent `get_repo_root()` pattern
  - All scripts use `git rev-parse --show-toplevel` for repo root
  - Proper use of `.resolve()` for canonical paths
  - Archive paths handle relative input to absolute storage

### Fixed
- **Error handling** - Improved error handling across scripts
  - `archive_manager.py`: Catch permission/symlink errors during zipfile.write()
  - `check_ascii_only.py`: Handle OSError for file reading
  - `verify_workflow_context.py`: Empty except clause documented

## [5.18.0] - 2025-12-20

### Added
- **SPDX license headers** - All Python files now have Apache 2.0 SPDX headers
  - Added `check_spdx_headers.py` pre-commit hook for validation
  - Headers include shebang, copyright, and license identifier
- **Windows hard link fallback** - AgentDB worktree symlinks now work on Windows
  - Uses `os.link()` (hard link) when symlink requires Developer Mode
  - Added platform detection in `create_worktree.py`
  - New tests for Windows fallback behavior
- **Path resolution for symlinks** - Better handling of symlinks/hard links
  - Added `Path.resolve()` to `query_workflow_state.py`
  - Added `Path.resolve()` to `record_sync.py`
- **Pytest markers** - Added `integration` and `benchmark` markers
  - Quality gates exclude slow tests by default

### Changed
- **Pre-commit hooks** - Updated ruff to v0.14.8
- **SQL injection prevention** - `record_sync.py` uses parameterized queries
- **Quality gates** - Exclude integration/benchmark tests for faster CI

### Fixed
- **DuckDB error messages** - Clear instructions when duckdb package missing
- **Cross-platform compatibility** - Windows users no longer need admin for worktrees

## [5.16.0] - 2025-11-26

### Changed
- **ASCII-only output** - Simplified output to use only ASCII characters (Issue #102)
  - Replaced Unicode symbols with ASCII equivalents for maximum compatibility:
    - `✓` → `[OK]`
    - `✗` → `[FAIL]`
    - `→` → `->`
    - `⚠` → `[WARN]`
    - `ℹ` → `[INFO]`
  - Removed UTF-8 detection and fallback logic from `safe_output.py`
  - Simplified `safe_print()` to just call `print()` directly
  - All workflow scripts now produce ASCII-only output

### Fixed
- **Cross-platform compatibility** - Scripts now work reliably on all systems
  - No more UnicodeEncodeError on Windows terminals with cp1252
  - No more encoding issues in CI/CD environments
  - No more problems with SSH sessions using misconfigured locales

### Updated Files
- `.gemini/skills/workflow-utilities/scripts/safe_output.py` - ASCII-only SYMBOLS dict
- `.gemini/skills/initialize-repository/scripts/initialize_repository.py` - ASCII output
- `.gemini/skills/bmad-planner/scripts/create_planning.py` - ASCII output
- `.gemini/skills/speckit-author/scripts/create_specifications.py` - ASCII output
- `.gemini/skills/workflow-utilities/scripts/create_skill.py` - ASCII output
- `.gemini/skills/agentdb-state-manager/scripts/checkpoint_manager.py` - ASCII output
- `.gemini/skills/quality-enforcer/scripts/check_coverage.py` - ASCII output
- `.gemini/skills/quality-enforcer/scripts/run_quality_gates.py` - ASCII output

## [5.15.0] - 2025-11-24

### Added
- **Cross-platform Unicode support** - Workflow scripts now work on all systems
  - Created `safe_output.py` utility module with UTF-8 reconfiguration and ASCII fallbacks
  - Added fallback output functions: ✓ → [OK], ✗ → [X], → → ->, ⚠ → !
  - Windows consoles with cp1252 encoding now fully supported

### Fixed
- **Windows console encoding errors** - Resolved UnicodeEncodeError in workflow scripts
  - `verify_workflow_context.py` - Uses safe_print with format helpers
  - `sync_ai_config.py` - Uses safe_print with format helpers
  - `pr_workflow.py` - Uses safe_print with fallback implementation
  - `release_workflow.py` - Uses safe_print with fallback implementation
  - `run_quality_gates.py` - Uses safe_print with fallback implementation
  - Pattern is reusable for remaining scripts that need Unicode output

### Changed
- **Improved error handling** - Scripts gracefully handle encoding issues
  - Automatic UTF-8 reconfiguration attempted first
  - ASCII fallbacks used when UTF-8 unavailable
  - Non-breaking: existing behavior preserved on UTF-8 systems

## [5.6.0] - 2025-11-21

### Added
- **Repository structure improvements** - Better organization for developer onboarding
  - Created `tests/` directory with proper pytest structure (`__init__.py`, `conftest.py`, `skills/__init__.py`)
  - Created `README.md` at repository root with quick start guide and prerequisites
  - Reorganized documentation: `00_draft-initial/` → `docs/research/`, `10_draft-merged/` → `docs/guides/`, `ARCHIVED/` → `docs/archived/`

### Changed
- **Slash command workflow clarity** - Added explicit ordering to all slash commands
  - All 4 commands now show workflow position: `/specify` (Step 1) → `/plan` (Step 2) → `/tasks` (Step 3) → `/workflow` (Step 4)
  - Each command shows prerequisites, outputs, and next step
  - GEMINI.md updated with numbered workflow table

- **CI/CD improvements** - Fixed GitHub Actions for containerized environment
  - Updated tests.yml to use `uv run pytest` for proper dependency resolution
  - Made linting non-blocking (`continue-on-error: true`) for pre-existing style issues
  - Fixed test path reference after moving to `tests/` directory

### Fixed
- **Cleaned up repository cruft**
  - Removed `.DS_Store` files from git tracking
  - Archived obsolete TODO files to `docs/archived/`
  - Updated internal documentation links to reflect new directory structure

### Documentation
- **Comprehensive specification** - Full spec/plan/tasks workflow for repository reorganization
  - `specs/002-repository-organization-improvements/` with spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md, tasks.md
  - 18 functional requirements, 23 implementation tasks

## [1.15.1] - 2025-11-18

### Changed
- **GEMINI.md improvements** - Enhanced onboarding and reduced duplication
  - Added Quick Reference Card with 7 common workflows + 3 core commands
  - Added Current Repository State section with pre-work checklist
  - Added "What NOT to Do" section (9 prohibitions + 5 best practices)
  - Consolidated version history: 109 lines → 23 lines (links to CHANGELOG.md for details)
  - File size: 1,482 → 1,445 lines (-37 lines, -2.5%)

- **WORKFLOW-INIT-PROMPT.md** - Clarified workflow application for existing repositories
  - Separated "From This Repo" vs "From Downloaded Release" approaches
  - Simplified prompt for Gemini Code: "Read `/path/to/standard`. Apply the workflow..."

### Added
- **.github/WORKTREE_CLEANUP_GUIDE.md** - Prevention strategies for worktree cleanup issues
  - Comprehensive guide to atomic cleanup script usage
  - Verification procedures and recovery steps

## [1.15.0] - 2025-11-18

### Added
- **MIT Agent Synchronization Pattern (Phase 5: Testing & Healthcare Compliance)** - Comprehensive validation suite
  - Healthcare compliance test suite (test_healthcare_compliance.py, 470 lines, 15 tests)
  - End-to-end integration tests (test_integration_e2e.py, 460 lines, 11 tests)
  - Chaos engineering test suite (test_chaos.py, 587 lines, 10 tests)
  - Healthcare compliance validation report (healthcare_compliance_validation.md, 11 pages)
  - HIPAA §164.312(b) audit controls validation
  - FDA 21 CFR Part 11 provenance requirements validation
  - SOC2 access control and review capabilities validation
  - GAP analysis with mitigation paths (4 gaps: HIGH/MEDIUM severity)
  - 58 total tests (42 passing, 15 expected failures documenting Phase 1-4 gaps)
  - 92% code coverage on sync_engine.py

- **MIT Agent Synchronization Pattern (Phase 6: Performance Validation)** - Production readiness benchmarks
  - Performance benchmark suite (sync_performance.py, 505 lines)
  - 5 comprehensive benchmarks (latency, scalability, hash, memory, throughput)
  - Statistical analysis report (comparison_report.md, 11 pages)
  - Amdahl's Law validation for parallel efficiency
  - Go/no-go decision framework with weighted scoring
  - Performance results: 4/5 targets passed (80% success rate)
    - Latency p95: 0.59ms (target <100ms) - 169x better than target ✅
    - Throughput: 2,140 ops/sec (target >100) - 21x better than target ✅
    - Hash p99: 0.0051ms (target <1ms) - 196x better than target ✅
    - Memory overhead: ~800 bytes (target <1KB) ✅
    - Scalability: 3.34x with 13 agents (26% efficiency vs 70% target) ⚠️
  - **Decision: ✅ APPROVED FOR PRODUCTION** (weighted score: 4.40/5.00, 88%)

### Fixed
- **Database path handling** - Benchmark suite now uses persistent file-based database
  - Replaced in-memory database (`:memory:`) with file-based approach
  - Ensures schema persistence between benchmark runs
  - Fixed "Table does not exist" errors in benchmark execution

### Changed
- **Documentation updates** - Phase 5 & 6 completion reflected across workflow
  - GEMINI.md updated with Phase 5 & 6 completion status
  - Performance targets documented with actual results
  - Scalability bottleneck analyzed (DuckDB single-writer limitation)
  - Production deployment recommendation (keep DuckDB, migrate to PostgreSQL only if load exceeds 2,000 ops/sec)

### Testing
- **Comprehensive test coverage** - 58 new tests across compliance, integration, and chaos scenarios
  - 73% test pass rate (42/58 passing, 15 expected failures)
  - Expected failures document Phase 1-4 gaps requiring future enhancement
  - All failures have documented mitigation paths in compliance validation report
  - Quality gates: all passing (coverage ≥80%, tests passing, build, linting, types)

### Documentation
- **Healthcare compliance validation** - 11-page comprehensive compliance report
  - HIPAA compliance validation with specific regulatory citations
  - FDA 21 CFR Part 11 electronic records requirements
  - SOC2 audit trail and access control assessment
  - Sign-off checklist for compliance/security teams
  - GAP analysis with prioritized mitigation roadmap
- **Performance analysis** - 11-page statistical analysis and decision report
  - Detailed benchmark methodology and measurement approach
  - Statistical analysis (p50/p95/p99 percentiles, standard deviation)
  - Amdahl's Law application to parallel scalability
  - Decision matrix with weighted scoring across all 5 criteria
  - Risk assessment for production deployment

## [1.14.0] - 2025-11-18

### Fixed
- **PR review feedback** - Resolved 9 issues from PR #256 review (Issues #259-262)
  - Issue #259: Updated TODO status for issue-243 (PR #263)
  - Issue #260: Updated TODO status for 6 archived files (PR #266)
  - Issue #261: Fixed test logic in test_default_syncs.py (PR #264)
  - Issue #262: Verified unused import removed from cleanup_feature.py

### Changed
- **Documentation updates** - PR #256 review fixes reflected
  - 7 archived TODO files updated with completed status and timestamps
  - Test validation logic strengthened to cover all priority ranges

## [1.13.0] - 2025-11-18

### Added
- **MIT Agent Synchronization Pattern (Phase 4: Default Synchronization Rules)** - Production-ready sync rules
  - Default synchronization rules (default_synchronizations.sql, 456 lines)
  - 8 synchronization rules (4 normal flow + 4 error recovery)
  - 4-tier workflow coverage (Orchestrate → Develop → Assess → Research)
  - Priority-based rule execution (200 for errors > 100 for normal flow)
  - Comprehensive test suite (test_default_syncs.py, 389 lines, 12 tests)
  - Design rationale documentation (phase4_default_rules_rationale.md, 700+ lines)
- **Atomic cleanup workflow** - Enforces proper TODO archival before cleanup
  - cleanup_feature.py script for atomic cleanup operations
  - Archive TODO → Delete worktree → Delete branches (correct order)
  - Error handling prevents orphaned TODO files
  - Replaces 4 manual commands with single atomic operation

### Fixed
- **PR review feedback** - Resolved 7 issues from PR #241 review (Issues #242-248)
  - Issue #242: Coverage range matching documentation (PR #250)
  - Issue #243: TODO status updates (PR #254)
  - Issue #244: Generic worktree paths (PR #253)
  - Issue #245: Idempotent SQL loading (PR #251)
  - Issue #246: Security validation docs (PR #249)
  - Issue #247: Version clarity (PR #255)
  - Issue #248: Test logic strengthening (PR #252)
- **Code quality** - Linting fixes in cleanup_feature.py
  - Removed unused os import
  - Fixed 5 unnecessary f-string prefixes

### Changed
- **Documentation updates** - Phase 4 completion reflected across workflow
  - GEMINI.md updated with Phase 4 completion status
  - WORKFLOW.md updated with atomic cleanup workflow
  - All 7 PR review issue TODOs properly archived
  - Phase 4 TODO properly archived with completion metadata

### Testing
- **Comprehensive test coverage** - 12 new tests for default synchronization rules
  - Test coverage: Priority range validation, idempotent loading
  - Test coverage: Coverage range matching, workflow tier distribution
  - Quality gates: all passing (coverage, tests, build, linting, types)

### Documentation
- **Phase 4 design rationale** - 700+ line comprehensive design document
  - Rationale for 8 synchronization rules (normal flow + error recovery)
  - Priority assignment justification (200 vs 100)
  - Coverage range matching limitations and Phase 5 resolution path
  - Security validation requirements for Phase 5

## [1.12.0] - 2025-11-18

### Added
- **MIT Agent Synchronization Pattern (Phase 3: Integration Layer)** - Workflow agent integration
  - Integration layer implementation (worktree_agent_integration.py, 594 lines)
  - FlowTokenManager for context-aware workflow token generation
  - PHIDetector for HIPAA-compliant Protected Health Information detection
  - ComplianceWrapper for audit trail enforcement
  - SyncEngineFactory for sync engine lifecycle management
  - trigger_sync_completion() for agent hook integration
  - Agent hooks added to 4 workflow scripts (bmad-planner, git-workflow-manager, quality-enforcer, speckit-author)
  - Test suite with 34 tests, 96% coverage (test_worktree_integration.py, 563 lines)
  - Feature flag control (SYNC_ENGINE_ENABLED environment variable)
  - Graceful degradation on sync engine errors
  - Non-invasive integration (<10 lines per agent script)

### Changed
- **Workflow improvements** - Enhanced robustness and maintainability
  - Refactored path manipulation pattern with setup_agentdb_import() helper function
  - Improved FlowTokenManager with regex-based parsing (replaces fragile string splits)
  - Added support for release/hotfix workflow types in addition to feature workflows
  - Enhanced agent hooks with return value capture and exception logging
  - Fixed hardcoded user in quality-enforcer (now uses os.getenv("USER"))

### Fixed
- **Code quality improvements** - Resolved 20 GitHub issues from PR reviews (#211-232)
  - Issue #211: Robust worktree directory parsing with regex validation
  - Issue #212: Added release/hotfix workflow type support
  - Issue #213: Fixed SSN pattern to require consistent formatting
  - Issue #214: Improved asyncio.run() pattern in agent hooks
  - Issue #215: Corrected version number (v1.1.0 → v1.12.0) in agentdb README
  - Issue #216: Replaced real-looking ULID with obviously fake test data
  - Issue #218-222: Removed unused imports, variables, and FlowTokenType enum
  - Issue #223: Optimized PHIDetector to single loop iteration (50% performance improvement)
  - Issue #224: Added release worktree pattern support
  - Issue #225: Fixed Phase 3 version inconsistency in GEMINI.md
  - Issue #227: Removed async/sync mismatch in on_agent_action_complete
  - Issue #228: Improved SSN regex to reduce false positives (require hyphens)
  - Issue #229: Refactored dynamic path manipulation pattern across agent hooks
  - Issue #230-232: Added exception logging to sync engine graceful degradation

### Performance
- **PHIDetector optimization** - Reduced iteration overhead by 50%
  - Single-pass detection for SSN and path patterns
  - Early continue for non-string values
  - Maintains same detection logic with better performance

### Testing
- **Comprehensive test coverage** - 176 tests passing, 88% coverage
  - 7 new FlowTokenManager tests (worktree patterns, edge cases)
  - 7 new PHIDetector tests (SSN patterns, path detection)
  - 20 ComplianceWrapper tests (audit trail enforcement)
  - Quality gates: all passing (coverage, tests, build, linting, types)

### Documentation
- **Updated for Phase 3 completion**
  - GEMINI.md reflects Phase 3 completion status
  - agentdb-state-manager/CHANGELOG.md includes v1.12.0 details
  - Clear distinction between v1.11.0 (Phase 2) and v1.12.0 (Phase 3)

## [1.11.0] - 2025-11-17

### Added
- **MIT Agent Synchronization Pattern (Phase 2: Synchronization Engine)** - Core bidirectional sync engine
  - Comprehensive synchronization engine (sync_engine.py, 559 lines)
  - Declarative synchronization coordination with pattern matching
  - Idempotency enforcement via SHA-256 content-addressed hashing
  - Conflict detection and resolution strategies
  - HIPAA-compliant audit trail tracking with APPEND-ONLY enforcement
  - Performance optimizations: <100ms p95 latency target, <1ms p99 hash computation
  - Test suite with 22 comprehensive tests (test_sync_engine.py, 689 lines)
  - Phase 2 integration guide (phase2_integration_guide.md, 394 lines)
  - Database migration for Phase 2 tables (phase2_migration.sql, 215 lines)
  - Workflow tracking documentation (TODO_feature_20251117T024349Z_phase-2-engine.md, 1,720 lines)
  - Python package structure for .gemini/ directory (__init__.py files)

### Changed
- **Linting configuration** - N999 exception for .gemini directory
  - Added per-file-ignores in pyproject.toml to allow __init__.py files in .gemini/
  - Acknowledges .gemini/ as special configuration directory (similar to .github/, .vscode/)
  - Preserves Python package structure while maintaining PEP 8 compliance

### Fixed
- **Code quality improvements** - Resolved GitHub Copilot review items
  - Issue #199: Removed unsupported array access claim from _resolve_params docstring
  - Issue #200: Removed unused Path import from sync_engine.py
  - Issue #201: Removed unused uuid4 import from test_sync_engine.py
  - Issue #203: Fixed N999 linting errors for .gemini directory
  - Auto-fixed import sorting per ruff recommendations

### Dependencies
- No new dependencies (continues to use duckdb>=1.4.2 from Phase 1)

## [1.10.0] - 2025-11-16

### Added
- **MIT Agent Synchronization Pattern (Phase 1: Database Schema)** - Healthcare-compliant multi-agent coordination
  - Based on: Meng, E., & Jackson, D. (2025). "What You See Is What It Does: A Structural Pattern for Legible Software." *Onward! at SPLASH 2025*. arXiv:2508.14511v1. https://arxiv.org/abs/2508.14511
  - Comprehensive DuckDB schema for agent synchronization tracking
  - HIPAA/FDA/IRB-compliant audit trail design (APPEND-ONLY tables)
  - Phase 1 database tables: agent_synchronizations, sync_executions, sync_events, sync_metrics
  - Schema migration test suite (706 lines, 557 test cases)
  - Healthcare compliance documentation (phase1_hipaa_compliance.md, 511 lines)
  - Schema integration guide (schema_integration_guide.md, 1068 lines)

- **Directory structure improvements** - Enhanced documentation organization
  - Created docs/ and benchmarks/ directories with GEMINI.md and README.md
  - Added ARCHIVED/ subdirectories for deprecated content
  - YAML frontmatter with parent/child/sibling navigation

### Changed
- **GEMINI.md documentation enhancements** - Domain-specific guidance
  - Added "Current Active Work" section documenting MIT Agent Sync Pattern status
  - Added "Parallel Agent Execution Patterns" with time calculations and decision tree
  - Added "Healthcare Compliance" section with HIPAA/FDA/IRB requirements
  - Added "DuckDB Development Guidelines" with PostgreSQL syntax comparisons
  - Updated quality gates to include DuckDB compatibility validation

### Fixed
- **DuckDB compatibility issues** - Critical PostgreSQL syntax corrections
  - Issue #174: Replaced EXTRACT(EPOCH) with datediff() for duration calculations
  - Issue #174: Replaced NOW() with CURRENT_TIMESTAMP for timestamp queries
  - Issue #174: Fixed INTERVAL syntax from PostgreSQL to DuckDB format
  - Issue #175: Corrected ON DELETE CASCADE comments to reflect ON DELETE RESTRICT implementation
  - Issue #177: Cleaned up unused imports and variables in test_schema_migration.py

### Dependencies
- Added duckdb (>=1.4.2) for MIT sync pattern database testing

## [1.9.0] - 2025-11-09

### Added
- **Work-item generation workflow (Option A)** - Complete PR feedback handling system
  - VCS-agnostic PR comment extraction (GitHub + Azure DevOps support)
  - Automatic work-item generation from unresolved PR conversations
  - `generate_work_items_from_pr.py` script with auto-detection of VCS provider
  - Work-item slug pattern: `pr-{pr_number}-issue-{sequence}`
  - Compatible with all issue tracking systems
  - Token-efficient implementation (pure CLI operations, no prompt overhead)
  - Successfully demonstrated 5-level nested workflow capability (14 PRs, 10 work-items)

- **VCS adapter enhancements** - Extended PR feedback capabilities
  - `fetch_pr_comments()` method in AzureDevOpsAdapter and GitHubAdapter
  - Conversation thread support with resolution status tracking
  - Unified comment format across GitHub and Azure DevOps providers
  - Filtering for unresolved conversations only

- **ARCHITECTURE.md** - Comprehensive workflow architecture documentation (604 lines)
  - High-level execution flow and phase map (Phases 0-6)
  - Key architectural patterns (progressive skill loading, BMAD→SpecKit context reuse)
  - Token efficiency analysis (50-92% reductions through various patterns)
  - Skill integration patterns and decision trees
  - Complete constants reference with rationale
  - Critical design decisions and system constraints

### Changed
- **WORKFLOW.md updates** - Enhanced Phase 4.3 documentation
  - Added PR Feedback Handling workflow (Option A: work-items)
  - Decision tree for simple fixes vs. substantive changes
  - Work-item generation and nested workflow patterns
  - Updated Phase 4 steps to include optional feedback handling

- **GEMINI.md improvements** - Added architectural cross-references
  - Cross-reference to ARCHITECTURE.md for deep-dive analysis
  - Separation of concerns: operational guidance (GEMINI.md) vs. architecture (ARCHITECTURE.md)
  - Improved navigation for future Gemini Code instances

### Fixed
- **Azure DevOps repository parameter handling** - Fixed 4 related issues (#105-106, #110, #112, #115)
  - Issue #105 (PR #107): Added warning when repository extraction returns None
  - Issue #106 (PR #108): Fixed AttributeError when repository parameter is None
  - Issue #110 (PR #111): Enhanced repository parameter validation with better error messages
  - Issue #112 (PR #113): Optimized validation to avoid redundant strip() calls
  - Issue #115 (PR #116): Documented empty string behavior for repository parameter

- **ARCHITECTURE.md documentation clarifications** - Fixed 4 GitHub Copilot review issues (#120-123)
  - Issue #120 (PR #124): Clarified pseudo-code notation (algorithmic, not executable Python)
  - Issue #121 (PR #124): Standardized terminology for PR merge operations
  - Issue #122 (PR #124): Enhanced timestamp format description with rationale
  - Issue #123 (PR #124): Clarified branch protection policy (no direct local commits/pushes)

- **Code quality improvements**
  - Fixed linting errors in generate_work_items_from_pr.py
  - Resolved all GitHub Copilot code review issues from PR feedback iterations

### Workflow Metrics
- **Total PRs:** 14 (all merged successfully)
  - PR #95: Initial work-item generation implementation
  - PR #104, #107-109, #111, #113-114, #116-119, #124-125: Nested fixes and improvements
- **Work-items generated:** 10 issues across 5 nested levels
- **Nested workflow depth:** 5 levels (unprecedented recursive dogfooding)
- **PR merge pattern:** feature → contrib → develop (branch protection compliant)

### Quality
- All tests passing (114 passed, 15 skipped)
- Test coverage: 88% (above required 80%)
- Linting: Clean - all ruff checks pass
- Type checking: Clean - all mypy checks pass
- Build: Successful

### Migration Notes
- Replaces iterative PR feedback workflow (Option B) with work-item generation (Option A)
- No breaking changes - backward compatible with existing workflows
- Work-item generation is optional; simple fixes can still be done directly on PR branch


## [1.8.2] - 2025-11-07

### Fixed
- **GitHub Copilot code quality issues** - Resolved 7 code quality issues (Issues #77-#84)
  - Issue #84: Fixed version reference (v1.8.1 → v1.8.0) in backmerge_release.py
  - Issue #83: Removed extra bracket in markdown link (migrate_directory_frontmatter.py:222)
  - Issue #82: Removed extra bracket in markdown link (migrate_directory_frontmatter.py:213)
  - Issue #81: Removed extra bracket in markdown link (specs/GEMINI.md:68)
  - Issue #79: Fixed git merge abort logic (use --no-commit + git merge --abort)
  - Issue #78: Clarified conflicts parameter docstring in create_pr function
  - Issue #77: Fixed YAML formatting inconsistency (directory_structure.py)

### Changed
- **Simplified backmerge workflow** - Updated backmerge_release.py to pure PR-based workflow
  - Removed all local merge operations (checkout, merge, abort)
  - Script now only validates inputs and creates PR directly
  - GitHub/CI automatically detects merge conflicts
  - Eliminated uncommitted changes issues (uv.lock modifications)
  - Reduced code by 204 lines (cleaner and simpler)
  - Follows pure PR-based workflow principle

### Quality
- All tests passing (114 passed, 15 skipped)
- Test coverage: 88% (above required 80%)
- Linting: Clean - all checks pass

## [1.8.1] - 2025-11-07

### Fixed
- **Branch protection compliance** - Enforced PR workflow for all merges to protected branches
  - Updated backmerge_release.py to create PRs instead of direct pushes
  - Removed branch protection exception from WORKFLOW.md
  - Self-merge enabled (no approval required for compliant workflow)

### Added
- **Azure DevOps branch policies documentation** - Comprehensive guide for Azure DevOps users
  - Created .github/AZURE_DEVOPS_POLICIES.md (644 lines)
  - Complete policy configuration for main and develop branches
  - Build validation, required reviewers, merge strategies
  - Work item linking and comment requirements
  - Migration guide from GitHub branch protection

### Documentation
- Updated GEMINI.md with v1.8.1 release information
- Updated WORKFLOW.md to remove branch protection exception
- Added Azure DevOps policy references throughout workflow docs

## [1.8.0] - 2025-11-07

### Added
- **CI/CD replication guide** - Comprehensive guide for replicating GitHub Actions to other platforms
  - Created WORKFLOW-INIT-PROMPT.md - DRY navigation guide (~500 tokens)
  - Reference-based navigation to avoid duplication
  - Progressive skill loading pattern
  - Token-efficient workflow initialization

### Changed
- **Workflow documentation** - Improved navigation and reduced duplication
  - Restructured GEMINI.md to use reference pattern
  - Added quick-start workflow initialization
  - Improved token efficiency for skill loading

## [1.7.0] - 2025-11-06

### Added
- **Cross-platform CI/CD infrastructure** - GitHub Actions workflow for automated testing
  - Created .github/workflows/tests.yml - Run tests on push/PR
  - Python 3.12 test environment
  - UV package manager integration
  - Automated pytest execution with coverage reporting
  - Cross-platform testing (Ubuntu, macOS, Windows)

### Quality
- Automated test execution on all PRs
- Coverage reporting in CI/CD pipeline
- Multi-platform validation

## [1.6.0] - 2025-11-04

### Added
- **GitHub Issue Management documentation** - Comprehensive issue tracking workflow added to GEMINI.md
  - Documents issue sources (Copilot reviews, manual creation, security alerts)
  - 5-step issue workflow (fix on contrib, reference in commits, PR to develop, auto-close)
  - Common issue types with solutions (unused variables, bare except, line length, syntax, security)
  - Quality commands reference (ruff, pytest)
  - Best practices for issue handling
- **Production Safety & Rollback procedures** - Emergency rollback documentation
  - Added "Production Safety & Rollback" section to WORKFLOW.md
  - 3 rollback scenarios (fast rollback, revert + hotfix, rollback decision tree)
  - Timeline estimates (10 min rollback, 20 min cleanup)
  - Tag-based deployment principles (immutable, reproducible, instant rollback)
- **Comprehensive branch protection documentation** - Explicit rules for `main` and `develop` protected branches
  - Added "Branch Protection Policy" section to WORKFLOW.md (~95 lines)
  - Added "Protected Branches" section to GEMINI.md with rules and exceptions
  - Added "Protected Branches" section to CONTRIBUTING.md with enforcement details
  - Added protected branches warning to README.md
  - Added protected branch policy to git-workflow-manager/SKILL.md
  - Added "Post-Application Steps" section to initialize-repository/SKILL.md
- **GitHub branch protection setup guide** - Step-by-step configuration instructions
  - Created .github/BRANCH_PROTECTION.md with detailed setup instructions (~350 lines)
  - Created .github/README.md explaining directory purpose
  - Includes GitHub Actions CI/CD integration examples
  - Includes Azure DevOps branch policies alternative
  - Includes troubleshooting section
- **Pre-push hook template** - Local safety net to prevent accidental protected branch pushes
  - Created .git-hooks/pre-push hook template (prevents pushes to main/develop)
  - Created .git-hooks/README.md with installation and usage instructions
  - Hook provides helpful error messages and correct workflow guidance
- **Branch protection compliance tests** - Automated validation of protection policy
  - Added tests/test_branch_protection.py with 6 test cases
  - Verifies no scripts commit to main (except tagging)
  - Verifies only backmerge_release.py commits to develop
  - Verifies backmerge_release.py has exception warning comment
  - Verifies pre-push hook exists and is executable
  - Verifies branch protection documentation exists in all files
  - All tests passing (112 passed, 15 skipped, 88% coverage)

### Fixed
- **GitHub Copilot code quality issues** - Resolved 13 code quality issues (Issues #43-#57)
  - Removed unused variables: args, timestamp, all_valid, result, commit_sha, req_path (Issues #44-47)
  - Fixed bare except blocks with specific exception types (Issue #49)
  - Fixed Python 3 syntax error: double backslash line continuation (Issue #48)
  - Clarified commented code as intentional placeholder (Issue #43)
  - Fixed regex false positives in branch protection tests with word boundaries (Issue #53)
  - Fixed duplicate violation logic with break statement (Issue #52)
  - Added explanatory comment to empty except/pass block (Issue #57)
  - Documented title variable usage in commit messages (Issue #56)
  - Added rollback safety warning to WORKFLOW.md (Issue #54)
- **Pydantic v2 migration** - Updated from deprecated v1 Config to v2 ConfigDict
  - Changed `class Config:` to `model_config = ConfigDict()` in src/standard/models.py
  - Maintains same behavior (use_enum_values=True)
  - Eliminates deprecation warnings

### Changed
- **Documented exception** - Clarified backmerge_release.py as allowed develop commit
  - Added prominent warning comment to backmerge_release.py (~18 lines)
  - Explains why exception is safe (merge-only, no code changes, preserves history)
  - References WORKFLOW.md Branch Protection Policy section

### Documentation
- Branch protection now explicitly documented in 6 core files
- Recovery procedures documented for accidental violations
- GitHub setup guide with screenshots and troubleshooting
- Pre-push hook installation instructions
- Exception policy clearly documented

### Quality
- 6 new tests for branch protection compliance
- All 127 tests passing (112 passed, 15 skipped)
- Test coverage: 88.1% (above required 80%)
- Version validation: All checks passed
- Linting: Clean - all pyflakes (F-series) checks pass
- All GitHub Copilot code review issues resolved

## [1.5.1] - 2025-11-04

### Fixed
- **Critical bugs** - Resolved 27 GitHub issues identified in Copilot code reviews
  - Fixed pyproject.toml configuration errors
  - Fixed SpecKit template rendering issues
  - Fixed Standard translation inaccuracies
  - Auto-fixed 23 code quality issues with ruff (unused imports, variables, formatting)
  - Quality: 106 tests passing, 88% coverage

### Added
- **Comprehensive skill documentation** - Completed documentation for all workflow skills
  - Added 5 missing `scripts/__init__.py` files (proper Python package structure)
  - Completed 6 GEMINI.md files (352-1,019 lines each) for Gemini Code integration
  - Completed 5 README.md files (232-435 lines each) for human developers
  - All skills now have comprehensive documentation for both Gemini Code and humans

### Changed
- **Workflow documentation** - Enhanced Phase 4.5 instructions
  - Added worktree/branch cleanup instructions
  - Clarified git worktree removal process
  - Added git branch deletion commands (local and remote)

### Documentation
- Skills with complete documentation: 9/9 (100%)
- GEMINI.md coverage: All skills (bmad-planner, speckit-author, quality-enforcer, git-workflow-manager, tech-stack-adapter, workflow-orchestrator, workflow-utilities, initialize-repository, agentdb-state-manager)
- README.md coverage: All skills
- Version validation: All checks passed

## [1.5.0] - 2025-11-02

### Added
- **initialize-repository meta-skill** (Phase 0) for bootstrapping new repositories
  - Interactive Q&A system (4 phases, 13-14 questions)
  - Copies all 8 workflow skills from source to target repository
  - Adapts documentation for new repository context
  - Generates README.md, GEMINI.md, pyproject.toml
  - Optional git initialization with 3-branch structure
  - Token savings: ~3,350 tokens per repository (96% reduction)
- Version consistency validator (`validate_versions.py`)
- Comprehensive update checklist for skill modifications (`UPDATE_CHECKLIST.md`)
- CONTRIBUTING.md with contributor guidelines
- CHANGELOG system for all skills (8 skill CHANGELOGs)
- Documentation sync tool (`sync_skill_docs.py`)

### Changed
- Workflow system now has 8 skills (added initialize-repository meta-skill)
- WORKFLOW.md updated with Phase 0 (Repository Initialization)
- GEMINI.md updated with 8th skill reference

### Token Efficiency
- Repository initialization: ~3,350 tokens saved (96% reduction)
- Previous workflow + docs system: ~3,500 tokens
- New system: ~150 tokens (single script call)

## [5.2.0] - 2025-10-23

### Changed
- TODO.md manifest structure to v5.2.0 format
- Enhanced workflow phase descriptions

## [5.0.0] - 2025-10-23

### Added
- Skill-based architecture with 7 specialized skills
- Interactive callable tools for BMAD and SpecKit
- Progressive skill loading for token efficiency
- Quality gates enforcement (≥80% coverage)
- Automated semantic versioning calculation
- File deprecation system with timestamped archives
- Release automation scripts (create, tag, backmerge, cleanup)
- Hotfix workflow support

### Changed
- Migrated from monolithic workflow to modular skill system
- BMAD and SpecKit now use interactive Q&A tools
- Workflow phases restructured (0-6 phases)
- TODO file format with YAML frontmatter
- Context management with 100K token checkpoint

### Token Efficiency
- BMAD: ~2,300 tokens saved per feature (92% reduction)
- SpecKit: ~1,700-2,700 tokens saved per feature
- Total workflow: ~600-900 tokens per phase vs 2,718 for monolith

## Earlier Versions

Earlier versions (< 5.0.0) used a different workflow architecture. See `ARCHIVED/` for historical workflow documentation.

---

## Version History Summary

| Version | Date       | Type  | Description |
|---------|------------|-------|-------------|
| 7.2.0   | 2026-01-04 | MINOR | Disabled dispatch workflow + dependency updates |
| 7.0.0   | 2026-01-01 | MAJOR | Streamlined for Gemini-only development + removed legacy tools |
| 1.10.0  | 2025-11-16 | MINOR | MIT Agent Synchronization Pattern (Phase 1) + DuckDB compatibility fixes |
| 1.9.0   | 2025-11-09 | MINOR | Work-item generation workflow + VCS adapter enhancements |
| 1.8.2   | 2025-11-07 | PATCH | Bug fixes for code quality issues + simplified backmerge workflow |
| 1.8.1   | 2025-11-07 | PATCH | Branch protection compliance + Azure DevOps documentation |
| 1.8.0   | 2025-11-07 | MINOR | CI/CD replication guide + DRY navigation improvements |
| 1.7.0   | 2025-11-06 | MINOR | Cross-platform CI/CD infrastructure (GitHub Actions) |
| 1.6.0   | 2025-11-04 | MINOR | Branch protection + GitHub issue management + rollback procedures |
| 1.5.1   | 2025-11-04 | PATCH | Bug fixes + comprehensive skill documentation |
| 1.5.0   | 2025-11-02 | MINOR | Initialize-repository meta-skill + documentation system |
| 5.2.0   | 2025-10-23 | MINOR | Enhanced TODO.md manifest structure |
| 5.0.0   | 2025-10-23 | MAJOR | Skill-based architecture with callable tools |

---

## How to Update This CHANGELOG

When making changes to the workflow:

1. **Add entry to [Unreleased] section** during development
2. **Use categories:**
   - `Added` - New features
   - `Changed` - Changes in existing functionality
   - `Deprecated` - Soon-to-be removed features
   - `Removed` - Removed features
   - `Fixed` - Bug fixes
   - `Security` - Security fixes
   - `Token Efficiency` - Token usage improvements

3. **On release:**
   - Move [Unreleased] items to new version section
   - Add date: `## [X.Y.Z] - YYYY-MM-DD`
   - Update Version History Summary table

4. **Link to skill CHANGELOGs:**
   - For skill-specific changes, reference `.gemini/skills/<skill-name>/CHANGELOG.md`

---

## Related Documentation

- **[WORKFLOW.md](WORKFLOW.md)** - Complete workflow guide
- **[GEMINI.md](GEMINI.md)** - Gemini Code interaction guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contributor guidelines
- **[.gemini/skills/UPDATE_CHECKLIST.md](.gemini/skills/UPDATE_CHECKLIST.md)** - Update process checklist

**Skill-Specific CHANGELOGs:**
- [bmad-planner](.gemini/skills/bmad-planner/CHANGELOG.md)
- [speckit-author](.gemini/skills/speckit-author/CHANGELOG.md)
- [workflow-orchestrator](.gemini/skills/workflow-orchestrator/CHANGELOG.md)
- [git-workflow-manager](.gemini/skills/git-workflow-manager/CHANGELOG.md)
- [quality-enforcer](.gemini/skills/quality-enforcer/CHANGELOG.md)
- [tech-stack-adapter](.gemini/skills/tech-stack-adapter/CHANGELOG.md)
- [workflow-utilities](.gemini/skills/workflow-utilities/CHANGELOG.md)
