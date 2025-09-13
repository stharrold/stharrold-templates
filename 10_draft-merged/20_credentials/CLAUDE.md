---
title: Credentials Management Context
version: 3.1
updated: 2025-09-12
parent: ../CLAUDE.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - api_tokens
    - credential_storage
    - security_policies
agent_capabilities:
  mcp_enabled: true
  sub_agents: true
  parallel_execution: true
related:
  - ../10_mcp/CLAUDE.md
  - ../30_implementation/CLAUDE.md
files:
  - 21_keychain-macos.md
  - 22_credential-manager-win.md
  - 23_enterprise-sso.md
  - 24_audit-compliance.md
changelog:
  - Integrated CLAUDE.md project context template (v1.0)
  - Restructured from monolithic to hierarchical organization
  - Split 18.8KB file into 4 focused modules under 30KB each
  - Added template security patterns and maintenance workflows
---

# Credentials Management Context

Secure storage and management of API tokens for MCP servers, including OS-native credential stores, enterprise SSO integration, and security compliance requirements.

**Security-First Approach:**
- **OS-native credential stores** for encrypted token storage
- **Regular credential rotation** to minimize exposure windows  
- **Access auditing** to track credential usage
- **Principle of least privilege** for all tokens

> **Critical Security Warning**: Using plaintext credentials in configuration files is a severe security risk that can expose your entire development infrastructure.

## Quick Navigation

Execute in recommended order for comprehensive security:

1. **[21_keychain-macos.md](./21_keychain-macos.md)** - macOS Keychain credential storage and management
2. **[22_credential-manager-win.md](./22_credential-manager-win.md)** - Windows Credential Manager setup and configuration
3. **[23_enterprise-sso.md](./23_enterprise-sso.md)** - Enterprise authentication, SSO integration, and cost management
4. **[24_audit-compliance.md](./24_audit-compliance.md)** - Security auditing, compliance, and vulnerability management

## MCP Server Credential Requirements

| Server | Token Type | Environment Variable | Setup Complexity | Scope Required |
|--------|------------|---------------------|------------------|----------------|
| GitHub | Personal Access Token | `GITHUB_TOKEN` | Low | repo, workflow, read:org |
| Azure DevOps | Personal Access Token | `AZURE_DEVOPS_PAT` | Medium | Code, Build, Release, Work Items |
| Slack | OAuth Token | `SLACK_TOKEN` | High | channels:read, chat:write, users:read |
| PostgreSQL | Connection String | `DATABASE_URL` | Medium | Read/Write on specific schemas |
| AWS | Access Keys | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | High | Service-specific IAM policies |
| Sentry | Auth Token | `SENTRY_AUTH_TOKEN` | Low | project:read, event:read |
| PostHog | API Key | `POSTHOG_API_KEY` | Low | Read access to analytics |
| MongoDB | Connection String | `MONGODB_URI` | Medium | readWrite on databases |
| Terraform | Cloud Token | `TF_TOKEN` | Medium | Plan and apply permissions |
| Kubernetes | Kubeconfig | `KUBECONFIG` | High | Namespace-specific RBAC |
| Notion | Integration Token | `NOTION_TOKEN` | Medium | Read/write workspace access |
| Atlassian | API Token | `JIRA_TOKEN`, `CONFLUENCE_TOKEN` | Medium | Project access, space admin |
| Figma | Personal Access Token | `FIGMA_TOKEN` | Low | File read access |
| Zapier | API Key | `ZAPIER_API_KEY` | Medium | Zap execution permissions |
| Composio | API Key | `COMPOSIO_API_KEY` | Medium | Platform integration access |

**Security Principle**: Always use the minimum required scope for each token to follow the principle of least privilege.

## Cross-Platform Verification

### Using MCP Manager
```bash
# Validate all credentials at once
/usr/bin/python3 mcp-manager.py --check-credentials
```

## Prerequisites

**Before starting MCP server configuration:**
→ **Complete credential setup first** before proceeding to [../10_mcp/CLAUDE.md](../10_mcp/CLAUDE.md)

## Related Concepts

- **MCP server configuration**: [../10_mcp/CLAUDE.md](../10_mcp/CLAUDE.md)
- **Implementation strategies**: [../30_implementation/CLAUDE.md](../30_implementation/CLAUDE.md)
- **Development workflows**: [../30_implementation/32_workflow-patterns.md](../30_implementation/32_workflow-patterns.md)

## Project Template Integration

This directory implements credential management template patterns:

### **Security-First Configuration**
- OS-native encrypted storage (Keychain/Credential Manager)
- Environment variable integration with `${env:VARIABLE_NAME}` syntax
- Automated setup scripts for both macOS and Windows
- Enterprise-grade SSO and domain capture support

### **Development Workflow Integration**
- Session-based credential loading
- Automated credential rotation reminders
- Cross-platform verification tools
- Emergency response procedures

### **Compliance & Auditing**
- Comprehensive audit trail logging
- Data classification and retention policies
- Vulnerability monitoring and mitigation
- AI-generated code security review requirements

## Critical Security Notes

- Tokens are encrypted by the OS (Keychain/Credential Manager)
- Never commit tokens to version control
- The `${env:VARIABLE_NAME}` syntax in claude.json reads from environment variables
- Restart your terminal after setup to load credentials
- Rotate tokens regularly for security
- Monitor security advisories for MCP server vulnerabilities
- Use dedicated tokens for MCP servers (not your personal tokens)

## Next Steps After Credential Setup

1. Configure MCP servers using [../10_mcp/CLAUDE.md](../10_mcp/CLAUDE.md)
2. Use `mcp-manager.py --check-credentials` to validate setup
3. Test servers with `/mcp` command in Claude Code
4. Review [../30_implementation/CLAUDE.md](../30_implementation/CLAUDE.md) for phased rollout strategy
5. Set up credential rotation reminders
6. Document your team's credential management procedures

---

*Each file in this directory maintains the 30KB limit for optimal AI context processing. Cross-references provide navigation without context pollution.*