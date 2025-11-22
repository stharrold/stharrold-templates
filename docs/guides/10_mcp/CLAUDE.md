---
title: MCP Configuration Context
version: 3.1
updated: 2025-09-12
parent: ../CLAUDE.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - mcp_servers
    - api_tokens
    - sync_strategy
agent_capabilities:
  mcp_enabled: true
  sub_agents: true
  parallel_execution: true
related:
  - ../20_credentials/CLAUDE.md
  - ../30_implementation/31_paradigm-shift.md
files:
  - 11_setup.md
  - 12_servers.md
  - 13_context-management.md
  - 14_enterprise-search.md
  - 15_troubleshooting.md
changelog:
  - Integrated CLAUDE.md project context template (v1.0)
  - Restructured from monolithic to hierarchical organization
  - Split 38KB file into 5 focused modules under 30KB each
  - Added cross-references for related concepts
---

# MCP Configuration Context

Model Context Protocol (MCP) setup and configuration for Claude Code development workflows.

**Benefits of MCP Integration:**
- **2-10x development velocity** improvements
- **55% faster task completion** rates
- **70% reduction** in manual documentation time
- **30-40% reduction** in per-session token consumption with proper context structuring

## Quick Navigation

Execute in order for comprehensive setup:

1. **[11_setup.md](./11_setup.md)** - Installation, authentication, directory structure
2. **[12_servers.md](./12_servers.md)** - Available servers by tier (Git, Podman, Database, etc.)
3. **[13_context-management.md](./13_context-management.md)** - CLAUDE.md workflow optimization patterns
4. **[14_enterprise-search.md](./14_enterprise-search.md)** - RAG architecture and search patterns
5. **[15_troubleshooting.md](./15_troubleshooting.md)** - Common issues and maintenance

## Prerequisites

**Credentials Required**: Many MCP servers require API tokens.
→ **Set up credentials first**: [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md)

## Related Concepts

- **Implementation patterns**: [../30_implementation/CLAUDE.md](../30_implementation/CLAUDE.md)
- **Security considerations**: [../20_credentials/23_enterprise-sso.md](../20_credentials/23_enterprise-sso.md)
- **Development workflows**: [../30_implementation/32_workflow-patterns.md](../30_implementation/32_workflow-patterns.md)

## Project Template Integration

This directory implements MCP-specific project template patterns:

### **Server Configuration Templates**
- Standard server sets by project type (web app, API, data analysis)
- Environment-specific configurations (dev, staging, prod)
- Team collaboration patterns

### **Context Management Patterns**
- CLAUDE.md hierarchical organization
- Token efficiency optimization
- Session management workflows

### **Integration Points**
- **Git workflows**: Multi-instance orchestration via worktrees
- **Credential management**: Secure token storage and rotation
- **Performance monitoring**: Context usage and optimization metrics

## Quick Start for Projects

1. **Assess project type** → Select relevant server tier from [12_servers.md](./12_servers.md)
2. **Configure credentials** → Follow [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md)
3. **Install MCP servers** → Follow [11_setup.md](./11_setup.md)
4. **Optimize context** → Implement patterns from [13_context-management.md](./13_context-management.md)
5. **Advanced features** → Configure enterprise search from [14_enterprise-search.md](./14_enterprise-search.md)

---

*Each file in this directory maintains the 30KB limit for optimal AI context processing. Cross-references provide navigation without context pollution.*