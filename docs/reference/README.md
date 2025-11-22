# Workflow Reference Documentation

Reference documentation from german workflow system v5.3.0 (2025-11-18).

## Purpose

These are reference materials for understanding the german workflow architecture and design decisions. The stharrold-templates repository uses a **selective subset** of tools from this workflow, not the complete system.

## Files

### german-workflow-v5.3.0.md
Complete 6-phase workflow guide (2,000+ lines):
- Phase 0: Initial setup and prerequisites
- Phase 1: Planning with BMAD (requirements + architecture)
- Phase 2: Feature development in isolated worktrees
- Phase 3: Quality assurance (tests, coverage, linting, types)
- Phase 4: Integration via pull requests
- Phase 5: Production releases with semantic versioning
- Phase 6: Hotfix workflow

**Complete python project development workflow with interactive planning tools.**

### WORKFLOW-INIT-PROMPT.md
Navigation guide for workflow system (~500 tokens):
- Quick start for new Claude instances
- Progressive skill loading patterns
- Context management strategies
- Critical pitfalls to avoid

**Efficient workflow navigation for AI agents.**

## What's Integrated in stharrold-templates

From the complete german workflow system, we integrated:

✅ **Integrated:**
- CI/CD pipelines (GitHub Actions + Azure Pipelines)
- Workflow automation tools (archive manager, directory validator, version checker)
- Git helpers (semantic versioning, worktree creation)
- Development tools (uv, pyproject.toml, pytest, ruff, mypy)
- Quality standards (CONTRIBUTING.md)
- Enhanced .gitignore

❌ **NOT Integrated:**
- BMAD planner (interactive planning Q&A for Python projects)
- SpecKit author (specification generation for features)
- Quality enforcer with pytest gates (overkill for documentation)
- AgentDB state manager (DuckDB external dependency)
- Full 6-phase workflow orchestrator (Python development focus)
- planning/ and specs/ directory structure (incompatible with templates lifecycle)

## Integration Philosophy

**stharrold-templates maintains its core identity:**
- **Purpose**: MCP server configuration and documentation management
- **Dependencies**: Stdlib-only for core tools (dev tools optional)
- **Document lifecycle**: docs/research → docs/guides → docs/archived
- **Testing**: Manual validation scripts (not automated pytest)
- **Workflow**: GitHub issue sync, not TODO-driven phases

**German workflow provides:**
- Automation tools where valuable (archive management, semantic versioning)
- Development infrastructure (CI/CD, quality tooling)
- Reference architecture for complex projects

## When to Reference German Workflow

**Use these references when:**
- Planning a Python project with complex feature development
- Need interactive planning tools (BMAD) for stakeholder alignment
- Want automated specification generation (SpecKit)
- Require test coverage enforcement (≥80% gates)
- Building multi-phase development workflows
- Need structured TODO/workflow tracking

**Don't use for:**
- Simple documentation repositories (like templates)
- Projects requiring zero external dependencies
- Quick prototypes or experiments
- Cross-platform configuration management (templates' focus)

## Related Documentation

**In stharrold-templates:**
- `CLAUDE.md` - Main repository guide with workflow integration section
- `CONTRIBUTING.md` - Contributor guidelines adapted for templates
- `tools/README.md` - Integrated workflow tools documentation
- `pyproject.toml` - Development dependencies configuration

**External:**
- German workflow repository: (reference implementation)
- Claude Code official docs: https://docs.claude.com/en/docs/claude-code/

## Version Information

- **German Workflow Version**: 5.3.0
- **Release Date**: 2025-11-18
- **Integration Date**: 2025-11-18
- **templates Repository Version**: 5.0.0+

## Questions?

For questions about:
- **Integrated tools**: See `tools/README.md` or `CONTRIBUTING.md`
- **MCP management**: See main `CLAUDE.md`
- **German workflow concepts**: Read `german-workflow-v5.3.0.md` in this directory
