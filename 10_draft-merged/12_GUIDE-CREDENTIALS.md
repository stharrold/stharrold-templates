---
title: Secure Credentials Management for MCP Servers
version: 3.1
updated: 2025-09-12
changelog:
  - Merged Claude Code enterprise authentication patterns
  - Added SSO integration and role-based permissions management
  - Enhanced security review requirements for AI-generated code
  - Added model-specific pricing and API billing options
  - Updated vulnerability statistics and security best practices
  - Added enterprise search security considerations from Graph RAG Kuzu report
---

# Secure Credentials Management for MCP Servers

This guide covers secure storage and management of API tokens for MCP servers, including enterprise search security considerations. See [GUIDE-MCP.md](./GUIDE-MCP.md) for MCP server configuration after setting up credentials.

## Security Context

Proper credential management is critical for MCP server security. This guide emphasizes:
- **OS-native credential stores** for encrypted token storage
- **Regular credential rotation** to minimize exposure windows
- **Access auditing** to track credential usage
- **Principle of least privilege** for all tokens

Using plaintext credentials in configuration files is a severe security risk that can expose your entire development infrastructure.

## Enterprise Search Data Security

Enterprise search systems require additional security considerations beyond standard MCP credential management, particularly when dealing with sensitive corporate knowledge bases and multi-source data integration.

### Multi-Source Credential Management

Enterprise search typically integrates multiple data sources, each requiring secure credential handling:

**Credential Isolation Strategy:**
- **Separate credential stores per data source** to minimize breach impact
- **Service-specific tokens** with minimum required permissions
- **Time-bounded access tokens** with automatic refresh capabilities
- **Audit logging** for all credential access and usage

```bash
# Example: Secure multi-source setup
# Confluence credentials
security add-generic-password \
  -a "$USER" \
  -s "CONFLUENCE_API_TOKEN" \
  -l "Confluence API Access" \
  -w "your-confluence-token"

# SharePoint credentials  
security add-generic-password \
  -a "$USER" \
  -s "SHAREPOINT_CLIENT_SECRET" \
  -l "SharePoint Client Secret" \
  -w "your-sharepoint-secret"

# Knowledge graph database credentials
security add-generic-password \
  -a "$USER" \
  -s "NEO4J_PASSWORD" \
  -l "Neo4j Graph Database" \
  -w "your-neo4j-password"
```

### Access Control for Sensitive Enterprise Data

**Fine-Grained Permission Management:**
- **Document-level access controls** that respect source system permissions
- **Role-based query filtering** based on user identity and clearance level
- **Confidentiality classification enforcement** (Public, Internal, Confidential, Restricted)
- **Data sovereignty compliance** for regulatory requirements

**Implementation Pattern:**
```bash
# Configure access control MCP server
claude mcp add access-control "python -m enterprise_acl" \
  --env USER_DIRECTORY="ldap://company.ldap" \
  --env CLASSIFICATION_SERVICE="./data_classification.json"
```

### Confidentiality Filters and External Lookups

Prevent sensitive information leakage when using external enrichment sources:

**Security Gates:**
1. **Pre-query screening** to identify sensitive terms and entities
2. **Confidentiality classification** of all retrieved content
3. **External lookup restrictions** based on data classification
4. **Audit trail logging** for all external data requests

```yaml
# confidentiality_rules.yaml
classification_rules:
  - pattern: "customer_data|financial_records|employee_info"
    classification: "confidential"
    external_lookup: false
  - pattern: "public_documentation|marketing_content"
    classification: "public"
    external_lookup: true
```

### Audit Trails for Enterprise Knowledge Base Access

**Comprehensive Logging Requirements:**
- **Query audit logs** with user identity, timestamp, and search terms
- **Document access tracking** including retrieved content and usage context
- **Permission escalation alerts** for unusual access patterns
- **Data export monitoring** to prevent unauthorized knowledge extraction

**Audit MCP Server Configuration:**
```bash
# Enterprise audit logging
claude mcp add audit-logger "python -m enterprise_audit" \
  --env LOG_LEVEL="detailed" \
  --env RETENTION_DAYS="2555"  # 7 years for compliance
  --env ALERT_THRESHOLDS="./security_thresholds.json"
```

### Data Classification and Retention

**Automated Classification:**
- **Content scanning** for sensitive patterns (SSN, credit cards, PII)
- **Metadata-based classification** using document source and author
- **ML-based sensitivity detection** for unstructured content
- **Retention policy enforcement** with automatic purging

**Security Monitoring:**
```bash
# Data loss prevention monitoring
claude mcp add dlp-monitor "python -m data_loss_prevention" \
  --env SCAN_PATTERNS="./pii_patterns.json" \
  --env ALERT_WEBHOOK="https://security-alerts.company.com/webhook"
```

This layered security approach ensures that enterprise search capabilities don't compromise organizational data security or regulatory compliance requirements.

## Enterprise Authentication & SSO Integration

### Centralized Authentication Management

Enterprise teams can leverage centralized authentication through SSO and domain capture, ensuring consistent access management across development teams. This approach provides:

**SSO Integration Benefits:**
- Single sign-on across all Claude Code instances
- Centralized user provisioning and deprovisioning
- Compliance with enterprise identity management policies
- Audit trail integration with existing security systems

**Domain Capture Configuration:**
```bash
# Enterprise administrators can configure domain-wide settings
claude config set-enterprise-domain company.com
claude config set-sso-provider okta  # or azure-ad, ping, etc.
```

**Role-Based Permissions Management:**
- Developer roles with limited MCP server access
- Admin roles with full configuration capabilities
- Audit roles with read-only access to usage data
- Project-specific permissions for fine-grained control

### API Billing & Cost Management

**Pay-Per-Use API Billing Options:**
- **Claude Sonnet 4**: $3/million input tokens (optimal for 80% of development tasks)
- **Claude Opus 4**: $15/million input tokens (complex architectural decisions)
- **Claude Haiku**: $0.80/million input tokens (simple, repetitive tasks)

**Cost Optimization Strategies:**
- **Prompt Caching**: 90% cost reduction for repeated patterns
- **Cache Hits**: $0.30/million tokens versus $3.00/million for fresh calls
- **Batch Processing**: 50% discount for headless mode operations
- **Strategic Model Selection**: Dynamic switching based on task complexity

```bash
# Monitor real-time costs
claude /cost

# Switch models based on task requirements
claude /model sonnet-4    # For most development tasks
claude /model opus-4      # For complex architecture work
claude /model haiku       # For simple operations
```

## macOS - Keychain Method

### Store Credentials
```bash
# Store token in Keychain
security add-generic-password \
  -a "$USER" \
  -s "AZURE_DEVOPS_PAT" \
  -l "Azure DevOps PAT" \
  -w "your-actual-token-here"

# Store GitHub token
security add-generic-password \
  -a "$USER" \
  -s "GITHUB_TOKEN" \
  -l "GitHub Token" \
  -w "ghp_your_actual_token"
```

### Load on Shell Startup
Add to `~/.zshrc` or `~/.bash_profile`:
```bash
# Load credentials from Keychain
export AZURE_DEVOPS_PAT=$(security find-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT" -w 2>/dev/null)
export GITHUB_TOKEN=$(security find-generic-password -a "$USER" -s "GITHUB_TOKEN" -w 2>/dev/null)
```

### Update Token
```bash
# Delete old
security delete-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT"

# Add new
security add-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT" -w "new-token"
```

### Configure ~/.claude.json (Claude Code CLI)
```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@azure-devops/mcp", "org-name"],
      "env": {
        "AZURE_DEVOPS_PAT": "${env:AZURE_DEVOPS_PAT}"
      }
    },
    "github": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

### Configure VS Code MCP Extension
```json
{
  "servers": {
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@azure-devops/mcp", "org-name"],
      "env": {
        "AZURE_DEVOPS_PAT": "${env:AZURE_DEVOPS_PAT}"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

## MCP Server Credential Requirements

Different MCP servers require various types of credentials. Here's a comprehensive reference:

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

**Note**: Always use the minimum required scope for each token to follow the principle of least privilege.

## Windows - Credential Manager Method

### Store Credentials (PowerShell)
```powershell
# Install module
Install-Module -Name CredentialManager -Force

# Store Azure DevOps token
$token = ConvertTo-SecureString "your-token-here" -AsPlainText -Force
New-StoredCredential -Target "AZURE_DEVOPS_PAT" -UserName "token" -SecurePassword $token -Persist LocalMachine

# Store GitHub token
$ghToken = ConvertTo-SecureString "ghp_your_token" -AsPlainText -Force
New-StoredCredential -Target "GITHUB_TOKEN" -UserName "token" -SecurePassword $ghToken -Persist LocalMachine
```

### Load on PowerShell Startup
Add to PowerShell profile (`$PROFILE`):
```powershell
# Load Azure DevOps token
$cred = Get-StoredCredential -Target "AZURE_DEVOPS_PAT"
if ($cred) {
    $env:AZURE_DEVOPS_PAT = $cred.GetNetworkCredential().Password
}

# Load GitHub token
$ghCred = Get-StoredCredential -Target "GITHUB_TOKEN"
if ($ghCred) {
    $env:GITHUB_TOKEN = $ghCred.GetNetworkCredential().Password
}
```

### Update Token
```powershell
# Remove old
Remove-StoredCredential -Target "AZURE_DEVOPS_PAT"

# Add new
$newToken = ConvertTo-SecureString "new-token" -AsPlainText -Force
New-StoredCredential -Target "AZURE_DEVOPS_PAT" -UserName "token" -SecurePassword $newToken -Persist LocalMachine
```

### Configure %USERPROFILE%\.claude.json (Claude Code CLI)
```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx.cmd",
      "args": ["-y", "@azure-devops/mcp", "org-name"],
      "env": {
        "AZURE_DEVOPS_PAT": "${env:AZURE_DEVOPS_PAT}"
      }
    },
    "github": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

### Configure VS Code MCP Extension (Windows)
```json
{
  "servers": {
    "azure-devops": {
      "command": "npx.cmd",
      "args": ["-y", "@azure-devops/mcp", "org-name"],
      "env": {
        "AZURE_DEVOPS_PAT": "${env:AZURE_DEVOPS_PAT}"
      }
    },
    "github": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

## Quick Setup Scripts

### macOS Setup Script
```bash
#!/bin/bash
# Save as setup-credentials.sh

echo "Enter Azure DevOps PAT:"
read -s AZURE_PAT
security add-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT" -w "$AZURE_PAT"

echo "Enter GitHub Token:"
read -s GH_TOKEN
security add-generic-password -a "$USER" -s "GITHUB_TOKEN" -w "$GH_TOKEN"

# Add to shell profile if not already present
grep -q "AZURE_DEVOPS_PAT" ~/.zshrc || cat >> ~/.zshrc << 'EOF'
export AZURE_DEVOPS_PAT=$(security find-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT" -w 2>/dev/null)
export GITHUB_TOKEN=$(security find-generic-password -a "$USER" -s "GITHUB_TOKEN" -w 2>/dev/null)
EOF

echo "Credentials stored. Restart terminal or run: source ~/.zshrc"
```

### Windows Setup Script
```powershell
# Save as Setup-Credentials.ps1

# Install module if needed
if (!(Get-Module -ListAvailable -Name CredentialManager)) {
    Install-Module -Name CredentialManager -Force
}

# Store credentials
$azurePat = Read-Host "Enter Azure DevOps PAT" -AsSecureString
New-StoredCredential -Target "AZURE_DEVOPS_PAT" -UserName "token" -SecurePassword $azurePat -Persist LocalMachine

$githubToken = Read-Host "Enter GitHub Token" -AsSecureString
New-StoredCredential -Target "GITHUB_TOKEN" -UserName "token" -SecurePassword $githubToken -Persist LocalMachine

# Add to profile if not present
$profileContent = @'
$cred = Get-StoredCredential -Target "AZURE_DEVOPS_PAT"
if ($cred) { $env:AZURE_DEVOPS_PAT = $cred.GetNetworkCredential().Password }

$ghCred = Get-StoredCredential -Target "GITHUB_TOKEN"
if ($ghCred) { $env:GITHUB_TOKEN = $ghCred.GetNetworkCredential().Password }
'@

if (!(Test-Path $PROFILE)) { New-Item -Path $PROFILE -ItemType File -Force }
if (!(Select-String -Path $PROFILE -Pattern "AZURE_DEVOPS_PAT" -Quiet)) {
    Add-Content -Path $PROFILE -Value $profileContent
}

Write-Host "Credentials stored. Restart PowerShell to load them."
```

## Verification

### Using MCP Manager (Cross-Platform)
```bash
# Validate all credentials at once
/usr/bin/python3 mcp-manager.py --check-credentials
```

### Manual Verification

#### macOS
```bash
# List stored credentials
security find-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT"

# Verify environment variable
echo $AZURE_DEVOPS_PAT | cut -c1-10
```

#### Windows
```powershell
# List stored credentials
Get-StoredCredential | Select-Object Target

# Verify environment variable
$env:AZURE_DEVOPS_PAT.Substring(0,10)
```

## Security Warnings & Vulnerability Mitigation

### Recent Security Vulnerabilities

**CVE-2025-52882 (Critical)**
- **Impact**: WebSocket authentication bypass in Claude Code Extension
- **Affected Versions**: < 1.0.24
- **Mitigation**: Update to latest Claude Code version immediately
- **Check**: `claude --version` should show 1.0.24 or higher

**PostgreSQL MCP Server SQL Injection**
- **Impact**: Potential for arbitrary SQL execution
- **Mitigation**: Use parameterized queries and read-only database users
- **Best Practice**: Create dedicated MCP database users with minimal permissions

### AI-Generated Code Security Review Requirements

**Critical Security Statistics:**
- Research indicates **27-50% of AI-generated code contains vulnerabilities**
- Security review is **mandatory rather than optional** for all AI-generated code
- Teams must implement **tiered review processes** where code touching authentication, payments, or sensitive data requires additional scrutiny

**Security Review Implementation:**
```bash
# All AI-generated code must be clearly labeled
git commit -m "feat: add user authentication
  
AI-Generated: Claude Code assisted implementation
Security-Review: Required for authentication logic"
```

**Mandatory Security Practices:**
1. **Code Labeling**: All AI-generated code must be clearly marked in comments and commits
2. **Automated Scanning**: Static analysis tools run automatically on Claude-generated code
3. **Dynamic Testing**: Runtime behavior validation for all AI contributions
4. **Multi-Model Review**: Different AI models for generation versus review to avoid blind spots
5. **Human Oversight**: "Never trust, always verify" principle - treat AI code as untested contributions

**Integration with Security Platforms:**
- Codacy MCP Server: Required for all file edits per repository guidelines
- Sentry integration: Error tracking and security incident detection
- SSO integration and role-based permissions
- Detailed audit logging with programmatic access via Compliance API

**For implementation strategy and competitive analysis, see [GUIDE-IMPLEMENTATION.md](./GUIDE-IMPLEMENTATION.md).**

### Token Security Best Practices

1. **Token Rotation Schedule**
   - GitHub tokens: Every 90 days
   - Database credentials: Every 60 days
   - Cloud provider keys: Every 30 days
   - API keys: Based on provider recommendations

2. **Access Auditing**
   ```bash
   # macOS: Check keychain access log
   log show --predicate 'subsystem == "com.apple.security"' --last 1h
   
   # Windows: Review credential access
   Get-EventLog -LogName Security -InstanceId 4648
   ```

3. **Emergency Response**
   - If a token is compromised, revoke it immediately
   - Generate new token with different name
   - Update all MCP configurations
   - Review access logs for unauthorized usage

## Important Notes

- Tokens are encrypted by the OS (Keychain/Credential Manager)
- Never commit tokens to version control
- The `${env:VARIABLE_NAME}` syntax in claude.json reads from environment variables
- Restart your terminal after setup to load credentials
- Rotate tokens regularly for security
- Monitor security advisories for MCP server vulnerabilities
- Use dedicated tokens for MCP servers (not your personal tokens)

## Next Steps

After setting up credentials:
1. Configure MCP servers using [GUIDE-MCP.md](./GUIDE-MCP.md)
2. Use `mcp-manager.py --check-credentials` to validate setup
3. Test servers with `/mcp` command in Claude Code
4. Review [GUIDE-IMPLEMENTATION.md](./GUIDE-IMPLEMENTATION.md) for phased rollout strategy
5. Set up credential rotation reminders
6. Document your team's credential management procedures