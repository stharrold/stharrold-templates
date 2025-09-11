---
title: Secure Credentials Management for MCP Servers
version: 2.0
updated: 2025-01-11
changelog:
  - Updated for enhanced security requirements
  - Maintained focus on credential security practices
---

# Secure Credentials Management for MCP Servers

This guide covers secure storage and management of API tokens for MCP servers. See [GUIDE-MCP.md](./GUIDE-MCP.md) for MCP server configuration after setting up credentials.

## Security Context

Proper credential management is critical for MCP server security. This guide emphasizes:
- **OS-native credential stores** for encrypted token storage
- **Regular credential rotation** to minimize exposure windows
- **Access auditing** to track credential usage
- **Principle of least privilege** for all tokens

Using plaintext credentials in configuration files is a severe security risk that can expose your entire development infrastructure.

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