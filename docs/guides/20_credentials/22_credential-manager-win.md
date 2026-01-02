---
title: Windows Credential Manager Setup
version: 3.2
updated: 2025-09-13
parent: ./GEMINI.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - credential_targets
    - powershell_profile_path
    - mcp_server_list
platform: Windows
security_level: OS-encrypted
related:
  - ./21_keychain-macos.md
  - ./23_enterprise-sso.md
  - ../10_mcp/12_servers.md
changelog:
  - Enhanced with Windows DPAPI technical details and native API integration patterns
  - Added project template integration patterns
  - Enhanced with PowerShell profile management
  - Improved cross-platform compatibility
---

# Windows Credential Manager Setup

Secure credential storage and management using Windows Credential Manager for MCP server authentication. Credential Manager provides OS-level encryption and secure access controls.

## Overview

Windows Credential Manager provides enterprise-grade credential storage through the Data Protection API (DPAPI) with per-user encryption contexts and Hardware-supported Virtualization-based Code Integrity (HVCI) protection on Windows 10/11. This approach ensures:

- **OS-level encryption** using DPAPI with per-user encryption contexts
- **User authentication** integrated with Windows logon and domain security
- **PowerShell integration** with environment variables and enterprise policies
- **Enterprise domain** compatibility for SSO environments and Group Policy management
- **Hardware security** through HVCI protection (Windows 10/11)

### DPAPI Architecture & Security

The Windows Data Protection API provides transparent encryption/decryption with these characteristics:

- **Per-User Encryption**: Each user account has unique encryption keys derived from logon credentials
- **Transparent Operation**: Automatic encryption on write, decryption on read without user intervention
- **Machine Binding**: Credentials tied to specific machine and user account combinations
- **Enterprise Integration**: Domain-roaming profiles support credential synchronization
- **HVCI Enhancement**: Windows 10/11 provide hardware-backed code integrity verification

### Native API Integration

For programmatic access, Windows provides these core credential management APIs:

- **CredWrite()**: Store credentials with specified persistence scope
- **CredRead()**: Retrieve stored credentials for authenticated user
- **CredDelete()**: Remove credentials permanently
- **CredEnumerate()**: List available credentials for current user

**Target Credential Type**: MCP servers should use `CRED_TYPE_GENERIC` with `CRED_PERSIST_LOCAL_MACHINE` persistence for service-level storage, ensuring credentials survive user session changes while maintaining security isolation.

## Cross-Platform Unification

### Keytar Library Integration

Just like macOS, Windows benefits from the **keytar** library (v7.9.0) for cross-platform credential management abstraction:

```javascript
// Windows-specific keytar implementation uses Credential Manager
const keytar = require('keytar');

class WindowsCredentialManager {
  async storeCredential(service, account, password) {
    // Maps to CredWrite() via keytar
    return await keytar.setPassword(service, account, password);
  }

  async getCredential(service, account) {
    // Maps to CredRead() via keytar
    return await keytar.getPassword(service, account);
  }

  async deleteCredential(service, account) {
    // Maps to CredDelete() via keytar
    return await keytar.deletePassword(service, account);
  }
}
```

### Alternative Integration Options

**For Node.js MCP Servers**: Use the **wincredmgr** npm package for direct Windows Credential Manager access without Electron dependencies:

```javascript
const wincred = require('wincredmgr');

// Store credential
wincred.setCredential({
  targetName: 'MCP_GITHUB_TOKEN',
  userName: 'token',
  credential: process.env.GITHUB_TOKEN,
  persist: 'local_machine'
});

// Retrieve credential
const stored = wincred.getCredential('MCP_GITHUB_TOKEN');
```

## Prerequisites

Install the PowerShell CredentialManager module:

```powershell
# Install the required module (run as Administrator)
Install-Module -Name CredentialManager -Force -Scope AllUsers

# Or install for current user only
Install-Module -Name CredentialManager -Force -Scope CurrentUser

# Import the module
Import-Module CredentialManager
```

## Store Credentials in Credential Manager

### Primary MCP Server Tokens
```powershell
# Store Azure DevOps Personal Access Token
$azureToken = ConvertTo-SecureString "your-token-here" -AsPlainText -Force
New-StoredCredential -Target "AZURE_DEVOPS_PAT" -UserName "token" -SecurePassword $azureToken -Persist LocalMachine

# Store GitHub Token
$githubToken = ConvertTo-SecureString "ghp_your_token" -AsPlainText -Force
New-StoredCredential -Target "GITHUB_TOKEN" -UserName "token" -SecurePassword $githubToken -Persist LocalMachine
```

### Additional Common Tokens
```powershell
# Database credentials
$dbUrl = ConvertTo-SecureString "postgresql://user:password@host:5432/dbname" -AsPlainText -Force
New-StoredCredential -Target "DATABASE_URL" -UserName "token" -SecurePassword $dbUrl -Persist LocalMachine

# AWS credentials
$awsKeyId = ConvertTo-SecureString "AKIA..." -AsPlainText -Force
New-StoredCredential -Target "AWS_ACCESS_KEY_ID" -UserName "token" -SecurePassword $awsKeyId -Persist LocalMachine

$awsSecret = ConvertTo-SecureString "your-secret-key" -AsPlainText -Force
New-StoredCredential -Target "AWS_SECRET_ACCESS_KEY" -UserName "token" -SecurePassword $awsSecret -Persist LocalMachine

# Slack token for team integrations
$slackToken = ConvertTo-SecureString "xoxb-your-slack-token" -AsPlainText -Force
New-StoredCredential -Target "SLACK_TOKEN" -UserName "token" -SecurePassword $slackToken -Persist LocalMachine
```

## Load Credentials on PowerShell Startup

Add to your PowerShell profile (`$PROFILE`). If the profile doesn't exist, create it:

```powershell
# Check if profile exists
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force
}

# Edit profile
notepad $PROFILE
```

Add this content to your PowerShell profile:

```powershell
# Load MCP server credentials from Credential Manager
function Load-MCPCredentials {
    try {
        # Load Azure DevOps token
        $cred = Get-StoredCredential -Target "AZURE_DEVOPS_PAT" -ErrorAction SilentlyContinue
        if ($cred) {
            $env:AZURE_DEVOPS_PAT = $cred.GetNetworkCredential().Password
        }

        # Load GitHub token
        $ghCred = Get-StoredCredential -Target "GITHUB_TOKEN" -ErrorAction SilentlyContinue
        if ($ghCred) {
            $env:GITHUB_TOKEN = $ghCred.GetNetworkCredential().Password
        }

        # Load database URL
        $dbCred = Get-StoredCredential -Target "DATABASE_URL" -ErrorAction SilentlyContinue
        if ($dbCred) {
            $env:DATABASE_URL = $dbCred.GetNetworkCredential().Password
        }

        # Load AWS credentials
        $awsKeyCred = Get-StoredCredential -Target "AWS_ACCESS_KEY_ID" -ErrorAction SilentlyContinue
        if ($awsKeyCred) {
            $env:AWS_ACCESS_KEY_ID = $awsKeyCred.GetNetworkCredential().Password
        }

        $awsSecretCred = Get-StoredCredential -Target "AWS_SECRET_ACCESS_KEY" -ErrorAction SilentlyContinue
        if ($awsSecretCred) {
            $env:AWS_SECRET_ACCESS_KEY = $awsSecretCred.GetNetworkCredential().Password
        }

        # Load Slack token
        $slackCred = Get-StoredCredential -Target "SLACK_TOKEN" -ErrorAction SilentlyContinue
        if ($slackCred) {
            $env:SLACK_TOKEN = $slackCred.GetNetworkCredential().Password
        }
    }
    catch {
        Write-Warning "Failed to load some MCP credentials: $($_.Exception.Message)"
    }
}

# Load credentials automatically
Load-MCPCredentials

# Optional: Create alias for reloading credentials
Set-Alias -Name Reload-MCPCreds -Value Load-MCPCredentials
```

**Important**: After saving the profile, restart PowerShell or run `. $PROFILE` to load the credentials.

## Update Stored Tokens

When tokens expire or need rotation:

```powershell
# Remove old credential
Remove-StoredCredential -Target "AZURE_DEVOPS_PAT"

# Add new credential
$newToken = ConvertTo-SecureString "new-token-value" -AsPlainText -Force
New-StoredCredential -Target "AZURE_DEVOPS_PAT" -UserName "token" -SecurePassword $newToken -Persist LocalMachine
```

## Configure %USERPROFILE%\.gemini.json (Gemini Code CLI)

Create or update your Gemini Code configuration file at `%USERPROFILE%\.gemini.json`:

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
    },
    "postgres": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${env:DATABASE_URL}"
      }
    },
    "slack": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_TOKEN": "${env:SLACK_TOKEN}"
      }
    }
  }
}
```

**Note**: On Windows, use `npx.cmd` instead of `npx` for proper command execution.

## Configure VS Code MCP Extension (Windows)

For VS Code users on Windows, configure the MCP extension:

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
    },
    "postgres": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${env:DATABASE_URL}"
      }
    },
    "slack": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_TOKEN": "${env:SLACK_TOKEN}"
      }
    }
  }
}
```

## Automated Setup Script

Save this as `Setup-Credentials.ps1` for quick team onboarding:

```powershell
#Requires -Version 5.1
<#
.SYNOPSIS
    MCP Credential Setup Script for Windows
.DESCRIPTION
    Securely stores MCP server credentials in Windows Credential Manager
    and configures PowerShell profile for automatic loading.
#>

[CmdletBinding()]
param()

Write-Host "🔐 MCP Credential Setup for Windows" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Install CredentialManager module if not present
if (!(Get-Module -ListAvailable -Name CredentialManager)) {
    Write-Host "Installing CredentialManager module..." -ForegroundColor Yellow
    try {
        Install-Module -Name CredentialManager -Force -Scope CurrentUser
        Write-Host "✅ CredentialManager module installed" -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install CredentialManager module: $($_.Exception.Message)"
        exit 1
    }
}

Import-Module CredentialManager -ErrorAction Stop

# Function to securely prompt for token
function Add-MCPCredential {
    param(
        [Parameter(Mandatory)]
        [string]$Target,

        [Parameter(Mandatory)]
        [string]$Description
    )

    Write-Host ""
    $token = Read-Host "Enter $Description" -AsSecureString

    if ($token.Length -gt 0) {
        try {
            New-StoredCredential -Target $Target -UserName "token" -SecurePassword $token -Persist LocalMachine -ErrorAction Stop
            Write-Host "✅ $Description stored securely" -ForegroundColor Green
        }
        catch {
            Write-Warning "Failed to store $Description : $($_.Exception.Message)"
        }
    }
    else {
        Write-Host "⚠️  Skipping empty $Description" -ForegroundColor Yellow
    }
}

# Store common MCP server credentials
Add-MCPCredential -Target "AZURE_DEVOPS_PAT" -Description "Azure DevOps PAT"
Add-MCPCredential -Target "GITHUB_TOKEN" -Description "GitHub Token"
Add-MCPCredential -Target "DATABASE_URL" -Description "PostgreSQL Database URL"
Add-MCPCredential -Target "SLACK_TOKEN" -Description "Slack Bot Token"

# Configure PowerShell profile
$profileContent = @'
# Load MCP server credentials from Credential Manager
function Load-MCPCredentials {
    try {
        $cred = Get-StoredCredential -Target "AZURE_DEVOPS_PAT" -ErrorAction SilentlyContinue
        if ($cred) { $env:AZURE_DEVOPS_PAT = $cred.GetNetworkCredential().Password }

        $ghCred = Get-StoredCredential -Target "GITHUB_TOKEN" -ErrorAction SilentlyContinue
        if ($ghCred) { $env:GITHUB_TOKEN = $ghCred.GetNetworkCredential().Password }

        $dbCred = Get-StoredCredential -Target "DATABASE_URL" -ErrorAction SilentlyContinue
        if ($dbCred) { $env:DATABASE_URL = $dbCred.GetNetworkCredential().Password }

        $slackCred = Get-StoredCredential -Target "SLACK_TOKEN" -ErrorAction SilentlyContinue
        if ($slackCred) { $env:SLACK_TOKEN = $slackCred.GetNetworkCredential().Password }
    }
    catch {
        Write-Warning "Failed to load some MCP credentials: $($_.Exception.Message)"
    }
}

Load-MCPCredentials
Set-Alias -Name Reload-MCPCreds -Value Load-MCPCredentials
'@

# Add to PowerShell profile if not present
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force | Out-Null
    Write-Host "✅ Created PowerShell profile at: $PROFILE" -ForegroundColor Green
}

if (!(Select-String -Path $PROFILE -Pattern "Load-MCPCredentials" -Quiet)) {
    Add-Content -Path $PROFILE -Value $profileContent
    Write-Host "✅ Environment variable loading added to profile" -ForegroundColor Green
}
else {
    Write-Host "✅ Profile already configured for MCP credentials" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Restart PowerShell or run: . `$PROFILE" -ForegroundColor White
Write-Host "   2. Configure MCP servers: ../10_mcp/GEMINI.md" -ForegroundColor White
Write-Host "   3. Test with: `$env:GITHUB_TOKEN.Substring(0,10)" -ForegroundColor White
```

Run the script:
```powershell
.\Setup-Credentials.ps1
```

## Manual Verification

### List Stored Credentials
```powershell
# List all stored credentials
Get-StoredCredential | Select-Object Target, UserName

# Check specific credential exists
Get-StoredCredential -Target "AZURE_DEVOPS_PAT"
```

### Verify Environment Variables
```powershell
# Check that environment variables are loaded (show first 10 characters only)
if ($env:AZURE_DEVOPS_PAT) {
    $env:AZURE_DEVOPS_PAT.Substring(0,10)
} else {
    Write-Warning "AZURE_DEVOPS_PAT not loaded"
}

if ($env:GITHUB_TOKEN) {
    $env:GITHUB_TOKEN.Substring(0,10)
} else {
    Write-Warning "GITHUB_TOKEN not loaded"
}

# Test if variables are accessible
if ($env:GITHUB_TOKEN) {
    Write-Host "✅ GitHub token loaded successfully" -ForegroundColor Green
} else {
    Write-Host "❌ GitHub token not found - check credential manager and profile" -ForegroundColor Red
}
```

### Test MCP Server Connection
```powershell
# Test GitHub MCP server (requires Node.js)
npx @modelcontextprotocol/server-github --help

# Verify credentials work with API call (using Invoke-RestMethod)
$headers = @{
    "Authorization" = "token $env:GITHUB_TOKEN"
    "User-Agent" = "PowerShell-MCP-Test"
}
try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
    Write-Host "✅ GitHub API authentication successful" -ForegroundColor Green
    Write-Host "Authenticated as: $($response.login)" -ForegroundColor Cyan
}
catch {
    Write-Host "❌ GitHub API authentication failed: $($_.Exception.Message)" -ForegroundColor Red
}
```

## Common Commands Reference

```powershell
# Development workflow commands
. $PROFILE                         # Reload PowerShell profile after changes
Get-StoredCredential              # Query credential manager for stored credentials
Remove-StoredCredential -Target   # Remove outdated credentials
$env:TOKEN_NAME.Substring(0,10)   # Safely verify token is loaded

# Credential rotation commands
.\Setup-Credentials.ps1           # Re-run setup for token updates
New-StoredCredential             # Add new or updated credential
git config --global credential.helper manager  # Git credential manager integration

# Troubleshooting commands
Get-ChildItem Env: | Where-Object Name -like "*TOKEN*"  # List all token environment variables
Load-MCPCredentials              # Manually reload credentials
Reload-MCPCreds                  # Alias for credential reload
Test-Path $PROFILE               # Check if PowerShell profile exists
```

## Integration with Project Templates

### Development Workflow
- **Session Start**: Automatically load credentials via PowerShell profile
- **Credential Rotation**: Use setup script for periodic token updates
- **Team Onboarding**: Share setup script for consistent Windows configuration

### Security Best Practices
- **Enterprise compliance** with Windows domain security policies
- **DPAPI encryption** for credential storage
- **Regular rotation** following organizational security guidelines
- **Audit access** using Windows Event Log

### Error Handling
- **Silent failures** with `-ErrorAction SilentlyContinue` for missing credentials
- **Verification commands** to test credential loading
- **Clear error messages** in setup script with colored output

### Cross-Platform Compatibility
- **Parallel structure** with macOS Keychain approach
- **Consistent environment variable** names across platforms
- **Platform-specific commands** (npx.cmd vs npx)

## Enterprise Integration

### Domain Environments
```powershell
# For domain-joined machines, credentials can be shared across domain profile
New-StoredCredential -Target "SHARED_TOKEN" -Persist Enterprise

# Query domain credential policies
gpresult /r | Select-String "credential"
```

### Group Policy Integration
- Configure credential policies via Group Policy
- Automate MCP credential deployment for enterprise teams
- Integrate with existing Windows credential management workflows

## Next Steps

1. **Test the setup**: Run verification commands above
2. **Configure MCP servers**: Follow [../10_mcp/11_setup.md](../10_mcp/11_setup.md)
3. **Set rotation reminders**: Use Windows Task Scheduler for automated rotation
4. **Document team procedures**: Customize setup script for your organization's security policies

---

*This module focuses specifically on Windows implementation. For macOS setup, see [21_keychain-macos.md](./21_keychain-macos.md).*
