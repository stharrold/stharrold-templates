# TODO

## GitHub Issue Sync
Last sync: 2025-09-15 22:45 UTC (Issue #12 pending PR merge - BMAD implementation complete)

## Active Tasks

### Security Enhancements
- [ ] Implement mcp-secrets-plugin for cross-platform credential storage (#3)
- [ ] Deploy mcpauth OAuth 2.1 server (#4)
- [ ] Integrate Auth0 MCP Server for enterprise SSO (#5)

### Documentation
- [ ] Create user onboarding guide for MCP setup (#6)
- [ ] Document Podman migration best practices (#7)

### Testing & Quality
- [ ] Add DeepEval LLM testing suite (#8)
- [ ] Implement Hypothesis property-based tests (#9)

### Infrastructure
- [ ] Set up Prometheus/Grafana monitoring stack (#10)
- [ ] Configure OpenTelemetry distributed tracing (#11)

## Document Integration (Priority: Sequential Merge)

### High Priority - Security & State Management
- [ ] Integrate 09_workflow-secrets-mcp.md into security tools (#12) - BMAD Implementation Complete, PR Pending
      → [Speckit Plan](TODO_FOR_feat-12-integrate-workflow-secrets.md) | [Claude Plan](TODO_FOR_feat-12-integrate-workflow-secrets-claude.md) | [BMAD Plan](TODO_FOR_feat-12-integrate-workflow-secrets-bmad.md) | [Flow Plan](TODO_FOR_feat-12-integrate-workflow-secrets-flow.md) | [Claude2 Plan](TODO_FOR_feat-12-integrate-workflow-secrets-claude2.md)
      | [Claude Worktree: feat/12-integrate-workflow-secrets-claude (in progress)]
      | [Claude2 Worktree: feat/12-integrate-workflow-secrets-claude2 (multi-guide distribution - in progress)]
      | [Speckit Worktree: feat/12-integrate-workflow-secrets (completed, PR #25)]
      | [BMAD Worktree: feat/12-integrate-workflow-secrets-bmad (✅ completed - awaiting PR merge)]
      | [Flow Worktree: feat/12-integrate-workflow-secrets-flow (pending)]
- [ ] Integrate 20_claude-preserve-state-todo-compact.md into state management (#19)

### Medium Priority - Core Development Tools
- [ ] Integrate 11_report-embedding-model.md into AI/ML tools (#13)
- [ ] Integrate 19_jupyter-to-marimo-conversion-guide.md into development tools (#14)
- [ ] Integrate 12_report-baml-documentation-extractor.md into documentation patterns (#15)
- [ ] Integrate 13_report-baml-kuzu-graph-schema.md into database patterns (#16)
- [ ] Integrate 18_prompt-complexity-quantification.md into AI optimization (#17)
- [ ] Integrate 18-1_prompt-complexity-routing-claude-model.md into AI optimization (#18)
- [ ] Integrate 17_ai-model-lifecycle-directory-structure.md into project structures (#21)

### Low Priority - Complex Agent Architectures (Requires Splitting)
- [ ] Integrate 16_report-agent-20-30-confit-setup-train-serve.md into agent architectures (#20)
- [ ] Integrate 15_report-ai-agent-workflow-architecture-optimization.md into agent architectures (#22)
- [ ] Integrate 14_report-agents-autogen-bmad-speckit-dspy-baml.md into agent architectures (#23)
- [ ] Integrate 10_report-autogen-dspy-architecture.md into agent architectures (#24)

## Completed Tasks
- ⏳ **Issue #12**: Workflow secrets integration (BMAD implementation complete) - commits f687068, 880dd33
  - Source: `00_draft-initial/09_workflow-secrets-mcp.md` (to be archived in PR)
  - Target: Enhanced `10_draft-merged/20_credentials/25_mcp-security-tools.md` (29KB)
  - Implementation: Practical workflow examples, platform-specific verification, error handling
  - Status: Awaiting PR merge to main (will auto-close on merge)

See `ARCHIVED/20250914T*_TODO.md` for v4.0 migration history (13/13 complete)

## Sync Status
- **GitHub Issues**: 22 total (#3-#24) - all 22 open (Issue #12 awaiting PR merge)
- **TODO Items**: 22 pending (9 enhancements + 12 document integrations + 1 awaiting PR)
- **Action**: ✅ Synchronized
- **In Progress**: Issue #12 BMAD implementation complete, PR pending
- **Next Priority**: Issue #19 (state management integration)