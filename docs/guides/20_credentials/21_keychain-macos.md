---
title: macOS Keychain Credential Management
version: 3.2
updated: 2025-09-13
parent: ./CLAUDE.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - keychain_service_names
    - shell_profile_path
    - mcp_server_list
platform: macOS
security_level: OS-encrypted
related:
  - ./22_credential-manager-win.md
  - ./23_enterprise-sso.md
  - ../10_mcp/12_servers.md
changelog:
  - Enhanced with macOS Security Framework technical details and cross-platform integration patterns
  - Added project template integration patterns
  - Enhanced with common commands and workflow integration
  - Improved error handling and verification procedures
---

# macOS Keychain Credential Management

Secure credential storage and management using macOS Keychain for MCP server authentication. Keychain provides OS-level encryption and secure access controls.

## Overview

macOS Keychain provides military-grade security for storing API tokens locally, implementing AES-256-GCM encryption with per-application access controls through the Security Framework. This approach ensures:

- **OS-level encryption** using AES-256-GCM with per-application access controls
- **User authentication** integrated with macOS logon and keychain locking
- **System integration** with environment variables and automatic timeout-based locking
- **Secure token rotation** without exposing plaintext credentials
- **Cross-platform compatibility** via keytar library abstraction

### Security Framework Architecture

The macOS Security Framework provides enterprise-grade credential protection:

- **Encryption**: AES-256-GCM with hardware-backed key derivation when available
- **Access Control**: Per-application ACLs with user consent prompts
- **Storage Location**: User-specific keychains at `~/Library/Keychains/`
- **Automatic Locking**: Configurable timeout-based keychain locking
- **API Integration**: SecItem* APIs for programmatic access without GUI dependencies

## Security Framework Integration

### Programmatic Access via SecItem APIs

For MCP servers requiring programmatic credential access, the Security Framework provides these core APIs:

- **SecItemAdd()**: Store new credentials with specified access controls
- **SecItemCopyMatching()**: Retrieve credentials with proper authentication
- **SecItemUpdate()**: Modify existing credentials securely
- **SecItemDelete()**: Remove credentials permanently

### Terminal-Based Access

The `/usr/bin/security` command-line utility enables direct keychain manipulation without GUI dependencies, making it ideal for terminal-based MCP servers and CI/CD environments.

### Cross-Platform Unification with Keytar

**Keytar Library (v7.9.0)**: Despite being archived, keytar remains the de facto standard for cross-platform credential management with 664+ dependent projects. It abstracts OS-specific APIs behind a unified interface:

```javascript
// Example keytar integration for MCP servers
const keytar = require('keytar');

class SecureCredentialManager {
  async storeCredential(service, account, password) {
    return await keytar.setPassword(service, account, password);
  }

  async getCredential(service, account) {
    return await keytar.getPassword(service, account);
  }

  async deleteCredential(service, account) {
    return await keytar.deletePassword(service, account);
  }
}
```

**Alternative**: Electron's **safeStorage** API offers a modern alternative for Electron-based MCP clients, providing built-in OS-level encryption without external dependencies.

## Store Credentials in Keychain

### Primary MCP Server Tokens
```bash
# Store Azure DevOps Personal Access Token
security add-generic-password \
  -a "$USER" \
  -s "AZURE_DEVOPS_PAT" \
  -l "Azure DevOps PAT" \
  -w "your-actual-token-here"

# Store GitHub Token
security add-generic-password \
  -a "$USER" \
  -s "GITHUB_TOKEN" \
  -l "GitHub Token" \
  -w "ghp_your_actual_token"
```

### Additional Common Tokens
```bash
# Database credentials
security add-generic-password \
  -a "$USER" \
  -s "DATABASE_URL" \
  -l "PostgreSQL Database URL" \
  -w "postgresql://user:password@host:5432/dbname"

# AWS credentials
security add-generic-password \
  -a "$USER" \
  -s "AWS_ACCESS_KEY_ID" \
  -l "AWS Access Key ID" \
  -w "AKIA..."

security add-generic-password \
  -a "$USER" \
  -s "AWS_SECRET_ACCESS_KEY" \
  -l "AWS Secret Access Key" \
  -w "your-secret-key"

# Slack token for team integrations
security add-generic-password \
  -a "$USER" \
  -s "SLACK_TOKEN" \
  -l "Slack Bot Token" \
  -w "xoxb-your-slack-token"
```

## Load Credentials on Shell Startup

Add to your shell profile (`~/.zshrc` for zsh or `~/.bash_profile` for bash):

```bash
# Load MCP server credentials from Keychain
export AZURE_DEVOPS_PAT=$(security find-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT" -w 2>/dev/null)
export GITHUB_TOKEN=$(security find-generic-password -a "$USER" -s "GITHUB_TOKEN" -w 2>/dev/null)
export DATABASE_URL=$(security find-generic-password -a "$USER" -s "DATABASE_URL" -w 2>/dev/null)
export AWS_ACCESS_KEY_ID=$(security find-generic-password -a "$USER" -s "AWS_ACCESS_KEY_ID" -w 2>/dev/null)
export AWS_SECRET_ACCESS_KEY=$(security find-generic-password -a "$USER" -s "AWS_SECRET_ACCESS_KEY" -w 2>/dev/null)
export SLACK_TOKEN=$(security find-generic-password -a "$USER" -s "SLACK_TOKEN" -w 2>/dev/null)

# Suppress error messages for tokens that don't exist
# The 2>/dev/null redirect handles cases where tokens aren't stored yet
```

**Important**: After adding these lines, restart your terminal or run `source ~/.zshrc` (or `source ~/.bash_profile`) to load the credentials.

## Update Stored Tokens

When tokens expire or need rotation:

```bash
# Delete old token
security delete-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT"

# Add new token
security add-generic-password \
  -a "$USER" \
  -s "AZURE_DEVOPS_PAT" \
  -l "Azure DevOps PAT" \
  -w "new-token-value"
```

## Configure ~/.claude.json (Claude Code CLI)

Create or update your Claude Code configuration file:

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
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${env:DATABASE_URL}"
      }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_TOKEN": "${env:SLACK_TOKEN}"
      }
    }
  }
}
```

**Note**: The `${env:VARIABLE_NAME}` syntax tells Claude Code to read the value from environment variables loaded by your shell profile.

## Configure VS Code MCP Extension

For VS Code users, create or update the MCP extension settings:

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
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${env:DATABASE_URL}"
      }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_TOKEN": "${env:SLACK_TOKEN}"
      }
    }
  }
}
```

## Secure Terminal Prompting

### Modern Credential Input Patterns

For MCP servers requiring secure credential input, use modern terminal libraries that provide proper masking and validation:

**Using @inquirer/password (v4.0.15)**:
```javascript
import { password } from "@inquirer/prompts";

const credential = await password({
  message: "Enter your API key:",
  mask: true,
  validate: (input) =>
    input.length >= 32 || "API key must be at least 32 characters",
});
```

**Lightweight alternative with password-prompt**:
```javascript
const prompt = require('password-prompt');

const credential = await prompt('Enter API key: ', {
  method: 'mask',
  replace: '*'
});
```

### Memory Protection Strategies

Sensitive credentials require specialized handling to prevent memory disclosure:

```javascript
class SecureString {
  constructor(value) {
    this.buffer = Buffer.alloc(value.length);
    this.buffer.write(value);
    value = null; // Clear original reference
  }

  getValue() {
    return this.buffer.toString();
  }

  clear() {
    crypto.randomFillSync(this.buffer); // Overwrite with random data
    this.buffer.fill(0); // Then zero
  }
}

// Usage in MCP servers
const secureToken = new SecureString(process.env.API_TOKEN);
try {
  // Use secureToken.getValue() for API calls
} finally {
  secureToken.clear(); // Always clear after use
}
```

## Automated Setup Script

Save this as `setup-credentials-macos.sh` for quick team onboarding:

```bash
#!/bin/bash
# macOS Credential Setup Script for MCP Servers

set -e

echo "🔐 MCP Credential Setup for macOS"
echo "=================================="

# Function to securely prompt for token
prompt_token() {
    local service_name="$1"
    local label="$2"
    local token
    
    echo
    echo "Enter $label:"
    read -s token
    
    if [ -n "$token" ]; then
        security add-generic-password -a "$USER" -s "$service_name" -l "$label" -w "$token"
        echo "✅ $label stored securely"
    else
        echo "⚠️  Skipping empty $label"
    fi
}

# Store common MCP server credentials
prompt_token "AZURE_DEVOPS_PAT" "Azure DevOps PAT"
prompt_token "GITHUB_TOKEN" "GitHub Token"
prompt_token "DATABASE_URL" "PostgreSQL Database URL"
prompt_token "SLACK_TOKEN" "Slack Bot Token"

# Add environment variable loading to shell profile
SHELL_PROFILE=""
if [ "$SHELL" = "/bin/zsh" ] || [ "$SHELL" = "/usr/bin/zsh" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ "$SHELL" = "/bin/bash" ] || [ "$SHELL" = "/usr/bin/bash" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
fi

if [ -n "$SHELL_PROFILE" ]; then
    if ! grep -q "AZURE_DEVOPS_PAT" "$SHELL_PROFILE" 2>/dev/null; then
        cat >> "$SHELL_PROFILE" << 'EOF'

# MCP Server Credentials (loaded from Keychain)
export AZURE_DEVOPS_PAT=$(security find-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT" -w 2>/dev/null)
export GITHUB_TOKEN=$(security find-generic-password -a "$USER" -s "GITHUB_TOKEN" -w 2>/dev/null)
export DATABASE_URL=$(security find-generic-password -a "$USER" -s "DATABASE_URL" -w 2>/dev/null)
export SLACK_TOKEN=$(security find-generic-password -a "$USER" -s "SLACK_TOKEN" -w 2>/dev/null)
EOF
        echo "✅ Environment variables added to $SHELL_PROFILE"
    else
        echo "✅ Environment variables already configured"
    fi
fi

echo
echo "🎉 Setup complete!"
echo "📋 Next steps:"
echo "   1. Restart terminal or run: source $SHELL_PROFILE"
echo "   2. Configure MCP servers: ../10_mcp/CLAUDE.md"
echo "   3. Test with: echo \$GITHUB_TOKEN | head -c 10"
```

Make the script executable:
```bash
chmod +x setup-credentials-macos.sh
./setup-credentials-macos.sh
```

## Manual Verification

### List Stored Credentials
```bash
# Check if specific credential exists
security find-generic-password -a "$USER" -s "AZURE_DEVOPS_PAT"

# List all stored credentials (shows account and service names only)
security dump-keychain -d login.keychain | grep "0x00000007"
```

### Verify Environment Variables
```bash
# Check that environment variables are loaded (show first 10 characters only)
echo $AZURE_DEVOPS_PAT | cut -c1-10
echo $GITHUB_TOKEN | cut -c1-10

# Test if variables are accessible
if [ -n "$GITHUB_TOKEN" ]; then
    echo "✅ GitHub token loaded successfully"
else
    echo "❌ GitHub token not found - check keychain and shell profile"
fi
```

### Test MCP Server Connection
```bash
# Test GitHub MCP server (requires Node.js)
npx @modelcontextprotocol/server-github --help

# Verify credentials work with actual API call
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

## Common Commands Reference

```bash
# Development workflow commands
source ~/.zshrc                    # Reload shell profile after changes
security find-generic-password     # Query keychain for stored credentials
security delete-generic-password   # Remove outdated credentials
echo $TOKEN_NAME | head -c 10     # Safely verify token is loaded

# Credential rotation commands  
./setup-credentials-macos.sh      # Re-run setup for token updates
security add-generic-password     # Add new or updated token
git config --global credential.helper osxkeychain  # Git keychain integration

# Troubleshooting commands
env | grep TOKEN                  # List all loaded token environment variables
security unlock-keychain          # Unlock keychain if access fails
launchctl setenv VARIABLE value   # Set environment variable system-wide
```

## Integration with Project Templates

### Development Workflow
- **Session Start**: Automatically load credentials via shell profile
- **Credential Rotation**: Use setup script for periodic token updates
- **Team Onboarding**: Share setup script for consistent configuration

### Security Best Practices
- **Never commit** `.env` files or hardcoded tokens
- **Regular rotation** following token-specific schedules
- **Audit access** using keychain access logs
- **Minimum scope** for all tokens (principle of least privilege)

### Error Handling
- Silent failures with `2>/dev/null` for missing tokens
- Verification commands to test credential loading
- Clear error messages in setup script

## Next Steps

1. **Test the setup**: Run verification commands above
2. **Configure MCP servers**: Follow [../10_mcp/11_setup.md](../10_mcp/11_setup.md)
3. **Set rotation reminders**: Add calendar events for token expiration
4. **Document team procedures**: Customize setup script for your organization

---

*This module focuses specifically on macOS implementation. For Windows setup, see [22_credential-manager-win.md](./22_credential-manager-win.md).*