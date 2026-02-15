---
title: Project Context Orchestrator
version: 3.2
updated: 2025-09-13
template_version: 1.0
context_constraints:
  max_file_size_bytes: 30000
  auto_compact_at: 95
  prefer_streaming: true
  encoding: utf-8
agent_capabilities:
  mcp_enabled: true
  sub_agents: true
  parallel_execution: true
  multi_agent_orchestration: true
  framework_integration: true
  enterprise_deployment: true
project_template:
  name: "PROJECT_NAME"
  type: "web_application"
  stage: "development"
  primary_language: "python"
  framework: "django"
  database: "postgresql"
  purpose: "[BRIEF_DESCRIPTION]"
  critical_systems: "[authentication|payments|user_data|none]"
tech_stack:
  languages: ["python", "javascript", "sql"]
  frameworks: ["django", "react", "tailwind"]
  tools: ["podman", "redis", "nginx"]
  services: ["aws", "stripe", "sendgrid"]
  testing: ["jest", "pytest", "react_testing_library"]
  ci_cd: ["github_actions", "jenkins"]
  infrastructure: ["aws", "podman", "kubernetes"]
hierarchy:
  subdirectories:
    - 10_mcp/
    - 20_credentials/
    - 30_implementation/
  execution_order:
    - 10_mcp/CLAUDE.md
    - 20_credentials/CLAUDE.md
    - 30_implementation/CLAUDE.md
changelog:
  - 3.2: Enhanced with multi-agent orchestration, framework integration, and enterprise deployment capabilities
  - 3.1: Integrated CLAUDE.md project context template (v1.0)
  - Restructured monolithic guides into hierarchical modular structure
  - Defined universal context constraints (30KB file limit)
  - Added cross-referencing system for related concepts
---

# Project Context Orchestrator

This directory contains modular guides for Claude Code development workflows. All files follow the context constraints defined above, with each file limited to 30KB for optimal AI context processing.

## Universal Context Management

- **File Size Limit**: 30KB per file (30,000 bytes)
- **Auto-Compact**: When files reach 95% of limit
- **Streaming**: Preferred for large responses
- **Encoding**: UTF-8 standard

## Directory Structure

### **10_mcp/**: MCP Server Configuration
Model Context Protocol setup, server configurations, and context optimization.
→ Start here: [10_mcp/CLAUDE.md](./10_mcp/CLAUDE.md)

### **20_credentials/**: Security & Credential Management
Secure storage, authentication patterns, and enterprise security considerations.
→ Start here: [20_credentials/CLAUDE.md](./20_credentials/CLAUDE.md)

### **30_implementation/**: Development Strategy & Patterns
Implementation approaches, workflow patterns, development paradigms, framework integration, team collaboration, enterprise deployment, and multi-agent orchestration.
→ Start here: [30_implementation/CLAUDE.md](./30_implementation/CLAUDE.md)

## Navigation Strategy

1. **Hierarchical Discovery**: Each directory has its own CLAUDE.md orchestrator
2. **Cross-References**: Related concepts linked without loading full content
3. **Lexicographical Order**: Numbered files show execution progression
4. **Focused Context**: Load only what's needed for current task

## Project Template Integration

This structure integrates project context template patterns:

- **Project Overview**: Business context and value proposition templates
- **Architecture**: Code structure and design decision frameworks
- **Development Standards**: Code style, Git workflow, testing patterns
- **Security Guidelines**: Critical security practices and sensitive areas
- **Domain Knowledge**: Business terminology and integration patterns
- **Session Management**: AI workflow optimization and maintenance tasks

## Quick Start Workflow

For new projects using this template structure:

1. **Customize project metadata** in this file's frontmatter
2. **Configure MCP servers**: Follow [10_mcp/CLAUDE.md](./10_mcp/CLAUDE.md)
3. **Set up credentials**: Follow [20_credentials/CLAUDE.md](./20_credentials/CLAUDE.md)
4. **Choose implementation strategy**: Follow [30_implementation/CLAUDE.md](./30_implementation/CLAUDE.md)

## Context Efficiency Benefits

- **30-40% token reduction** through hierarchical organization
- **Faster AI responses** with focused, relevant context
- **Maintainable structure** with single-responsibility files
- **Progressive disclosure** from overview to detailed implementation

---

*This orchestrator defines the architectural foundation for all subdirectory guides. Update project metadata above to customize for specific projects.*

## Related Documentation

- **[../CLAUDE.md](../CLAUDE.md)** - Parent directory: docs

**Child Directories:**
- **[10_mcp/CLAUDE.md](10_mcp/CLAUDE.md)** - 10 Mcp
- **[20_credentials/CLAUDE.md](20_credentials/CLAUDE.md)** - 20 Credentials
- **[30_implementation/CLAUDE.md](30_implementation/CLAUDE.md)** - 30 Implementation
- **[40_deployment/CLAUDE.md](40_deployment/CLAUDE.md)** - 40 Deployment
