# TODO

## GitHub Issue Sync
Last sync: 2025-09-14 19:40 UTC (verified complete - all 22 issues open pending merge to main)

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
- [ ] Integrate 09_workflow-secrets-mcp.md into security tools (#12)
      → [Speckit Plan](TODO_FOR_feat-12-integrate-workflow-secrets.md) | [Claude Plan](TODO_FOR_feat-12-integrate-workflow-secrets-claude.md)
      | [Claude Worktree: feat/12-integrate-workflow-secrets-claude (in progress)]
      | [Speckit Worktree: feat/12-integrate-workflow-secrets (completed, PR #25)]
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
See `ARCHIVED/20250914T*_TODO.md` for v4.0 migration history (13/13 complete)

## Sync Status
- **GitHub Issues**: 22 open (#3-#24) - all pending merge to main
- **TODO Items**: 22 pending (9 enhancements + 13 document integrations)
- **Action**: ✅ Synchronized
- **Work in Progress**: Issue #12 has two worktree implementations
- **Next Priority**: Complete and merge #12, then proceed with #19