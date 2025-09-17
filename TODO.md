# TODO

## GitHub Issue Sync
Last sync: 2025-09-16 22:30 UTC (Issue #12 status updated in TODO.md, all 32 issues synchronized)

## Active Tasks

### Code Review Feedback (Immediate Priority)
- [ ] Fix missing imports for datetime and os modules (#44)
- [ ] Use user-accessible log location instead of /var/log/ for emergency logging (#43)
- [ ] Restore formatting and explanatory text in Python code blocks (#42)
- [ ] Maintain consistent spacing between document sections (#41)
- [ ] Add explanation of ARCHIVED/ location and extraction methods (#39)
- [ ] Add status indicators to priority list for better tracking (#38)
- [ ] Sanitize sensitive error information in logging functions (#35)
- [ ] Reorganize worktree cleanup commands in logical workflow order (#34)
- [ ] Fix regex pattern spacing in cross-reference validation (#32)
- [ ] Correct code block end marker counting logic (#31)

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
- [ ] Integrate 20_claude-preserve-state-todo-compact.md into state management (#19)

### Medium Priority - Core Development Tools
- [ ] Integrate 11_report-embedding-model.md into AI/ML tools (#13)
      → [Implementation Plan](TODO_FOR_issue-13-merge-11-embedding.md) | [Worktree: issue/13-merge-11-embedding (in progress)]
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
- ✅ **Issue #12**: Workflow secrets integration (closed 2025-09-16) - commits f687068, 880dd33
  - Source: `00_draft-initial/09_workflow-secrets-mcp.md` (archived)
  - Target: Enhanced `10_draft-merged/20_credentials/25_mcp-security-tools.md` (29KB)
  - Implementation: Practical workflow examples, platform-specific verification, error handling
  - Status: Closed and merged to main

See `ARCHIVED/20250914T*_TODO.md` for v4.0 migration history (13/13 complete)

## Sync Status
- **GitHub Issues**: 32 total (#3-24, #31-35, #38-39, #41-44) - 31 open, 1 closed (#12)
- **TODO Items**: 31 pending (10 code review + 9 enhancements + 12 document integrations)
- **Action**: ✅ Synchronized (2025-09-16 22:30 UTC)
- **Immediate Priority**: Code review feedback issues (#31-35, #38-39, #41-44)
- **Next Major Priority**: Issue #19 (state management integration)