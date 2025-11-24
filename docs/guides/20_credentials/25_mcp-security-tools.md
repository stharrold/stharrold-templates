---
title: MCP Security Tools & Ecosystem
version: 1.2
updated: 2025-09-16
parent: ./CLAUDE.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - security_tool_selection
    - oauth_server_config
    - integration_patterns
    - workflow_examples
security_level: Production-ready
target_audience: Security teams, DevOps engineers
related:
  - ./21_keychain-macos.md
  - ./22_credential-manager-win.md
  - ./23_enterprise-sso.md
  - ./24_audit-compliance.md
  - ../10_mcp/11_setup.md
  - ../10_mcp/12_servers.md
changelog:
  - 1.2: Added Node.js keytar alternative for JavaScript applications, enhanced tool selection matrix, advanced troubleshooting & recovery procedures, emergency credential access patterns, and automated health monitoring
  - 1.1: Enhanced with practical workflow examples, platform-specific verification commands, and step-by-step credential management workflows
  - 1.0: Initial version with production-ready MCP security tool implementations
---

# MCP Security Tools & Ecosystem

Production-ready implementations and tools for secure MCP credential management, including cross-platform credential storage, OAuth 2.1 servers, and enterprise authentication solutions.

## Overview

The MCP ecosystem has evolved to provide mature security solutions that address the critical vulnerabilities identified in early implementations. These tools offer immediate, production-ready security enhancements for MCP server deployments.

**Key Security Improvements:**
- **Elimination of plaintext credentials** through system-native secure storage
- **OAuth 2.1 compliance** with PKCE, resource indicators, and dynamic client registration
- **Enterprise-grade authentication** with comprehensive audit trails
- **Cross-platform compatibility** with consistent security models

## Production-Ready Security Tools

### mcp-secrets-plugin: Cross-Platform Credential Storage

**Overview:** Python-based plugin that replaces plaintext `.env` files with system-native secure storage using the keyring library.

**Key Features:**
- **Cross-platform support** for macOS Keychain, Windows Credential Manager, and Linux Secret Service
- **Simple API** for storing, retrieving, and managing credentials
- **CLI management** for team onboarding and credential rotation
- **Environment integration** that works seamlessly with existing MCP server configurations

**Installation and Setup:**

```bash
# Install the plugin
pip install mcp-secrets-plugin

# Or with pipx for isolated installation
pipx install mcp-secrets-plugin
```

**Basic Usage:**

```python
from mcp_secrets import SecretManager

# Initialize the secret manager
secrets = SecretManager()

# Store a credential securely
secrets.set_secret('github', 'token', 'ghp_your_actual_token_here')

# Retrieve a credential
github_token = secrets.get_secret('github', 'token')

# List stored credentials
stored_creds = secrets.list_secrets()
print(f"Stored credentials: {stored_creds}")
```

**CLI Management:**

```bash
# Store credentials via CLI
mcp-secrets set github token
# Prompts securely for the token value

# Retrieve credentials
mcp-secrets get github token

# List all stored services
mcp-secrets list

# Delete old credentials
mcp-secrets delete azure-devops token

# Export configuration for MCP servers
mcp-secrets export --format env > .env.secure
```

**MCP Integration Pattern:**

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["-c", "
        from mcp_secrets import SecretManager;
        import os;
        secrets = SecretManager();
        os.environ['GITHUB_TOKEN'] = secrets.get_secret('github', 'token');
        exec(open('mcp_github_server.py').read())
      "]
    }
  }
}
```

**Team Setup Script:**

```bash
#!/bin/bash
# Team onboarding script using mcp-secrets-plugin

echo "🔐 Setting up secure MCP credentials..."

# Install mcp-secrets-plugin
pipx install mcp-secrets-plugin

# Store common team credentials
echo "Setting up GitHub integration..."
mcp-secrets set github token

echo "Setting up Azure DevOps integration..."
mcp-secrets set azure-devops pat

echo "Setting up database credentials..."
mcp-secrets set database url

echo "✅ Secure credential setup complete!"
echo "💡 Credentials are stored in your system's secure credential store"
echo "🔄 Run 'mcp-secrets list' to view configured services"
```

**Step-by-Step Installation Workflow:**

Example workflow installing an MCP server that requires a GitHub Personal Access Token, using secure credential management:

```bash
# Step 1: Install mcp-secrets-plugin
pipx install mcp-secrets-plugin

# Step 2: Install the target MCP server (example: GitHub)
npm install -g @modelcontextprotocol/server-github

# Step 3: Store credentials securely via CLI
$ mcp-secrets set github token
Enter value for 'github_token': ************************************
✓ Credential stored in system keychain

# Step 4: Configure Claude to use the stored secret
# Add to claude.json:
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${SECRET:github_token}"
      }
    }
  }
}

# Step 5: Verify credential retrieval
$ mcp-secrets get github token
ghp_xxxxxxxxxxxxxxxxxxxx

# Step 6: Test MCP server functionality
$ claude-desktop --test-mcp github
✓ MCP server started successfully
✓ Authentication verified
✓ GitHub API accessible
```

**Runtime Credential Injection:**

When Claude starts the GitHub MCP server, mcp-secrets-plugin handles the credential retrieval automatically:

```python
# Behind the scenes credential resolution
import keyring
from typing import Dict, Any

class SecretsPlugin:
    def get_secret(self, secret_name: str) -> str:
        """Retrieve secret from OS keychain"""
        return keyring.get_password("mcp-secrets", secret_name)

    def resolve_environment(self, env: Dict[str, Any]) -> Dict[str, Any]:
        """Replace ${SECRET:name} placeholders with actual values"""
        resolved = {}
        for key, value in env.items():
            if isinstance(value, str) and value.startswith("${SECRET:"):
                secret_name = value[9:-1]  # Extract name from ${SECRET:name}
                resolved[key] = self.get_secret(secret_name)
            else:
                resolved[key] = value
        return resolved
```

### mcpauth: Complete OAuth 2.0 Server

**Overview:** Self-hostable OAuth 2.0 server designed specifically for MCP applications, providing enterprise-grade authentication with flexible integration options.

**Key Features:**
- **OAuth 2.1 compliance** with PKCE, resource indicators, and dynamic client registration
- **Multiple framework support** including Next.js and Express
- **Database flexibility** with Prisma and Drizzle ORM backends
- **Enterprise SSO integration** for centralized user management
- **Comprehensive audit logging** for compliance requirements

**Quick Start Installation:**

```bash
# Clone and setup mcpauth server
git clone https://github.com/mcpauth/mcpauth.git
cd mcpauth

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
npm run db:migrate

# Start the server
npm run start
```

**Configuration Example:**

```javascript
// mcpauth.config.js
module.exports = {
  server: {
    port: 3001,
    cors: {
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true
    }
  },

  oauth: {
    // Required OAuth 2.1 features
    pkceRequired: true,
    resourceIndicators: true,
    dynamicClientRegistration: true,

    // Token configuration
    accessTokenTTL: 3600, // 1 hour
    refreshTokenTTL: 86400 * 30, // 30 days

    // Security settings
    requireConsent: true,
    allowSilentConsent: false // Prevent confused deputy attacks
  },

  clients: {
    // MCP-specific client configuration
    'mcp-client': {
      name: 'MCP Client Application',
      allowedScopes: ['mcp:read', 'mcp:write', 'mcp:admin'],
      allowedRedirectUris: [
        'http://localhost:8080/auth/callback',
        'https://app.company.com/mcp/callback'
      ]
    }
  },

  providers: {
    // Enterprise SSO integration
    okta: {
      clientId: process.env.OKTA_CLIENT_ID,
      clientSecret: process.env.OKTA_CLIENT_SECRET,
      domain: process.env.OKTA_DOMAIN
    },
    azureAD: {
      clientId: process.env.AZURE_CLIENT_ID,
      clientSecret: process.env.AZURE_CLIENT_SECRET,
      tenantId: process.env.AZURE_TENANT_ID
    }
  }
};
```

**Enterprise Integration:**

```javascript
// Enterprise user mapping for mcpauth
class EnterpriseUserMapper {
  async mapUser(ssoProfile, provider) {
    const user = {
      id: ssoProfile.sub || ssoProfile.id,
      email: ssoProfile.email,
      name: ssoProfile.name,
      provider: provider,

      // Map enterprise roles to MCP scopes
      mcpScopes: this.mapRolesToScopes(ssoProfile.roles || [])
    };

    // Store user in database
    await this.userRepository.upsert(user);

    return user;
  }

  mapRolesToScopes(roles) {
    const roleMapping = {
      'developer': ['mcp:read'],
      'senior-developer': ['mcp:read', 'mcp:write'],
      'admin': ['mcp:read', 'mcp:write', 'mcp:admin'],
      'security': ['mcp:audit', 'mcp:admin']
    };

    const scopes = new Set();
    roles.forEach(role => {
      const mappedScopes = roleMapping[role.toLowerCase()] || [];
      mappedScopes.forEach(scope => scopes.add(scope));
    });

    return Array.from(scopes);
  }
}
```

**Docker Deployment:**

```dockerfile
# Production mcpauth deployment
FROM node:18-alpine

# Security hardening
RUN adduser -S mcpauth -u 1001
USER mcpauth

WORKDIR /app
COPY --chown=mcpauth:mcpauth package*.json ./
RUN npm ci --only=production

COPY --chown=mcpauth:mcpauth . .

EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3001/health || exit 1

CMD ["node", "server.js"]
```

### Alternative: Node.js Keytar Integration

**Overview:** For JavaScript/Node.js applications, keytar provides native credential management without Python dependencies.

```javascript
// Cross-platform credential management with keytar
const keytar = require('keytar');

async function getSecureCredential(service, account, envVar = null) {
  try {
    const credential = await keytar.getPassword(service, account);
    if (credential) return credential;
  } catch (error) {
    console.warn(`Keytar failed: ${error.message}`);
  }

  // Fall back to environment variable
  if (envVar && process.env[envVar]) {
    console.warn(`Using environment variable ${envVar} as fallback`);
    return process.env[envVar];
  }

  throw new Error(`No credential found for ${service}/${account}`);
}

// Usage in MCP server
const githubToken = await getSecureCredential('github', 'token', 'GITHUB_TOKEN');
```

**Installation:** `npm install keytar` (requires build tools on some platforms)

### Auth0 MCP Server: Enterprise Reference Implementation

**Overview:** Production-grade reference implementation demonstrating enterprise OAuth patterns with device authorization flow and automatic token refresh.

**Key Features:**
- **Device authorization flow** for CLI and headless environments
- **Automatic token refresh** with seamless credential renewal
- **Scoped access controls** with fine-grained permissions
- **Comprehensive audit logging** for enterprise compliance
- **Multi-tenant support** for enterprise organizations

**Installation and Configuration:**

```bash
# Install Auth0 MCP server
npm install @auth0/mcp-server

# Configure environment variables
export AUTH0_DOMAIN="your-domain.auth0.com"
export AUTH0_CLIENT_ID="your-client-id"
export AUTH0_CLIENT_SECRET="your-client-secret"
export AUTH0_AUDIENCE="https://api.your-company.com"
```

**Device Flow Implementation:**

```javascript
// Auth0 device authorization flow for MCP
const { DeviceFlow } = require('@auth0/mcp-server');

class Auth0MCPIntegration {
  constructor(config) {
    this.auth0 = new DeviceFlow({
      domain: config.domain,
      clientId: config.clientId,
      clientSecret: config.clientSecret,
      audience: config.audience
    });
  }

  async authenticateDevice() {
    try {
      // Start device authorization
      const deviceAuth = await this.auth0.authorize({
        scope: 'mcp:read mcp:write offline_access'
      });

      console.log('🔐 MCP Authentication Required');
      console.log(`Visit: ${deviceAuth.verification_uri}`);
      console.log(`Enter code: ${deviceAuth.user_code}`);

      // Poll for authorization
      const tokens = await this.auth0.pollForTokens(deviceAuth.device_code);

      // Store tokens securely
      await this.storeTokens(tokens);

      console.log('✅ Authentication successful!');
      return tokens;

    } catch (error) {
      console.error('❌ Authentication failed:', error.message);
      throw error;
    }
  }

  async refreshTokens() {
    const storedTokens = await this.getStoredTokens();

    if (!storedTokens.refresh_token) {
      throw new Error('No refresh token available');
    }

    const newTokens = await this.auth0.refresh(storedTokens.refresh_token);
    await this.storeTokens(newTokens);

    return newTokens;
  }

  async makeAuthenticatedRequest(url, options = {}) {
    let tokens = await this.getStoredTokens();

    // Check if token needs refresh
    if (this.isTokenExpired(tokens.access_token)) {
      tokens = await this.refreshTokens();
    }

    return fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
  }
}
```

**Enterprise Multi-Tenant Configuration:**

```yaml
# Auth0 tenant configuration for MCP
auth0_tenants:
  production:
    domain: "company-prod.auth0.com"
    client_id: "${AUTH0_PROD_CLIENT_ID}"
    client_secret: "${AUTH0_PROD_CLIENT_SECRET}"
    audience: "https://api.company.com"
    scopes:
      - "mcp:read"
      - "mcp:write"
      - "mcp:admin"

  staging:
    domain: "company-staging.auth0.com"
    client_id: "${AUTH0_STAGING_CLIENT_ID}"
    client_secret: "${AUTH0_STAGING_CLIENT_SECRET}"
    audience: "https://staging-api.company.com"
    scopes:
      - "mcp:read"
      - "mcp:write"

  development:
    domain: "company-dev.auth0.com"
    client_id: "${AUTH0_DEV_CLIENT_ID}"
    client_secret: "${AUTH0_DEV_CLIENT_SECRET}"
    audience: "https://dev-api.company.com"
    scopes:
      - "mcp:read"
```

## Claude Desktop Native Integration

### Claude Desktop Extensions (DXT)

**Overview:** Native integration within Claude Desktop that automatically encrypts credentials marked as sensitive in configuration schemas.

**Key Features:**
- **Automatic encryption** using OS-native credential stores
- **One-click installation** with secure credential prompting
- **Template literal replacement** for secure credential injection
- **No manual configuration** required for basic setups

**Configuration Schema:**

```json
{
  "name": "secure-mcp-server",
  "version": "1.0.0",
  "description": "MCP server with secure credential handling",
  "schema": {
    "api_key": {
      "type": "string",
      "description": "API key for external service",
      "sensitive": true,
      "required": true
    },
    "database_url": {
      "type": "string",
      "description": "Database connection string",
      "sensitive": true,
      "required": true
    },
    "debug_mode": {
      "type": "boolean",
      "description": "Enable debug logging",
      "sensitive": false,
      "default": false
    }
  }
}
```

**Runtime Configuration:**

```json
{
  "mcpServers": {
    "secure-server": {
      "command": "python",
      "args": ["secure_mcp_server.py"],
      "env": {
        "API_KEY": "${user_config.api_key}",
        "DATABASE_URL": "${user_config.database_url}",
        "DEBUG": "${user_config.debug_mode}"
      }
    }
  }
}
```

**Installation Experience:**

1. **Extension Installation**: User installs MCP server extension
2. **Credential Prompting**: Claude Desktop automatically prompts for sensitive fields
3. **Secure Storage**: Credentials encrypted using OS keychain/credential manager
4. **Template Replacement**: `${user_config.*}` syntax replaced with decrypted values
5. **Zero Configuration**: Server works immediately without manual setup

## Environment Variable Discovery Methods

When configuring MCP servers that require credentials, you often need to discover what environment variables are required and what format to use. Here are systematic methods for identifying these requirements:

### Finding Required Environment Variable Names

**Method 1: Run without credentials to see error messages**

The quickest way to discover required environment variables is to run the MCP server without credentials:

```bash
$ npx @modelcontextprotocol/server-github
Error: GITHUB_PERSONAL_ACCESS_TOKEN environment variable is required
```

**Method 2: Check documentation and package information**

```bash
# View NPM package info
npm info @modelcontextprotocol/server-github

# Check GitHub repository README
open https://github.com/modelcontextprotocol/servers/tree/main/src/github
```

**Method 3: Inspect source code for environment variables**

```bash
# Search for environment variable usage in Node.js MCPs
grep -r "process.env" node_modules/@modelcontextprotocol/server-github/
# Output: process.env.GITHUB_PERSONAL_ACCESS_TOKEN

# For Python MCPs
grep -r "os.environ" /path/to/mcp-server/
```

**Method 4: Check MCP manifest file (if available)**

```bash
cat node_modules/@modelcontextprotocol/server-github/mcp.json
```

```json
{
  "requiredEnv": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
  "optionalEnv": ["GITHUB_API_URL"]
}
```

### Finding Credential Value Patterns

**Method 1: Check credential manager documentation**

```bash
# For mcp-secrets-plugin
mcp-secrets --help
# Output: Use ${SECRET:name} pattern in configuration

# View usage examples
cat $(npm root -g)/mcp-secrets-plugin/README.md | grep -A5 "Usage"
```

**Method 2: Test credential manager patterns**

```bash
# Each manager has its own syntax:
mcp-secrets-plugin:     ${SECRET:github_token}
mcpauth:                ${OAUTH:github}
keytar-mcp:             ${KEYTAR:service/account}
vault-mcp:              ${VAULT:secret/path}
aws-secrets:            ${AWS_SECRET:arn}

# Without a manager (direct environment):
Plain value:            "ghp_xxxxxxxxxxxx"
System env:             "${GITHUB_TOKEN}"
```

**Method 3: Find example configurations**

```bash
# Look for example configs in credential manager packages
find $(npm root -g)/mcp-secrets-plugin -name "*.example.json" -o -name "*example*"
```

### Common Patterns by Credential Manager

| Manager | Pattern | Example |
|---------|---------|---------|
| **mcp-secrets-plugin** | `${SECRET:name}` | `${SECRET:github_token}` |
| **System environment** | Direct value or `${VAR}` | `${GITHUB_TOKEN}` |
| **No manager** | Plaintext (insecure) | `"ghp_xxxxx"` |

**Security Note**: Always use a credential manager pattern rather than plaintext values to maintain security best practices.

## Platform-Specific Credential Verification

After storing credentials using a credential manager, you can verify they are properly stored using platform-specific commands:

### macOS Keychain Verification

```bash
# View stored credential (requires user password)
$ security find-generic-password -s "mcp-secrets" -a "github-token" -w
[Keychain Access prompt appears]

# List all mcp-secrets entries
$ security dump-keychain | grep "mcp-secrets"

# Credential storage location:
~/Library/Keychains/login.keychain-db
```

### Windows Credential Manager Verification

```powershell
# View stored credential
PS> cmdkey /list:mcp-secrets:github-token

# List all stored credentials
PS> cmdkey /list

# Access via GUI:
# Control Panel > User Accounts > Credential Manager > Windows Credentials
```

### Linux Secret Service Verification

```bash
# View stored credential (GNOME)
$ secret-tool lookup service mcp-secrets account github-token

# List all stored secrets
$ secret-tool search --all service mcp-secrets

# For KDE Wallet
$ kwalletcli -f kdewallet -e github-token

# Credential storage locations:
# GNOME Keyring: ~/.local/share/keyrings/
# KDE Wallet: ~/.kde/share/apps/kwallet/
```

### Cross-Platform Python Verification

```python
import keyring

# Test credential retrieval
try:
    token = keyring.get_password("mcp-secrets", "github-token")
    if token:
        print("✓ Credential found and accessible")
        print(f"Token length: {len(token)} characters")
    else:
        print("✗ Credential not found")
except Exception as e:
    print(f"✗ Error accessing credential: {e}")

# List available backends
print("Available keyring backends:", keyring.backend.get_all_keyring())
```

## Tool Selection Guidelines

### Security Requirements Matrix

| Tool | Cross-Platform | Enterprise SSO | OAuth 2.1 | Audit Logging | Container Ready |
|------|---------------|----------------|-----------|---------------|-----------------|
| **mcp-secrets-plugin** | ✅ | ❌ | ❌ | Basic | ✅ |
| **Node.js keytar** | ✅ | ❌ | ❌ | Basic | ✅ |
| **mcpauth** | ✅ | ✅ | ✅ | Comprehensive | ✅ |
| **Auth0 MCP Server** | ✅ | ✅ | ✅ | Enterprise | ✅ |
| **Claude Desktop DXT** | ✅ | ❌ | ❌ | Basic | ❌ |

### Recommended Implementation Strategy

**Phase 1: Basic Security (Week 1)**
- Deploy `mcp-secrets-plugin` to eliminate plaintext credentials
- Configure basic audit logging
- Establish credential rotation procedures

**Phase 2: Authentication (Weeks 2-3)**
- Implement `mcpauth` or Auth0 integration for OAuth 2.1 compliance
- Configure enterprise SSO integration
- Establish scoped access controls

**Phase 3: Enterprise Features (Weeks 4-6)**
- Deploy comprehensive audit logging and monitoring
- Implement automated threat detection
- Establish incident response procedures

**Phase 4: Production Hardening (Weeks 7-8)**
- Container security hardening
- Network isolation and service mesh integration
- Comprehensive security testing and validation

## Integration Patterns

### Hybrid Tool Deployment

```yaml
# Production deployment combining multiple security tools
mcp_security_stack:
  credential_storage:
    primary: "mcp-secrets-plugin"
    fallback: "encrypted-files"

  authentication:
    oauth_server: "mcpauth"
    enterprise_sso: "okta"
    device_flow: "auth0-mcp-server"

  desktop_integration:
    claude_desktop: "native-dxt"
    vs_code: "mcp-secrets-plugin"
    cli: "mcp-secrets-plugin"

  monitoring:
    audit_logging: "comprehensive"
    anomaly_detection: "ml-based"
    threat_response: "automated"
```

### Security Tool API Integration

```javascript
// Unified security tool API wrapper
class MCPSecurityStack {
  constructor() {
    this.credentialStore = new MCPSecretsPlugin();
    this.oauthServer = new MCPAuth();
    this.auditLogger = new ComprehensiveAuditLogger();
  }

  async securelyExecuteRequest(request) {
    try {
      // 1. Authenticate request
      const authResult = await this.oauthServer.validateToken(request.token);

      // 2. Retrieve required credentials
      const credentials = await this.credentialStore.getCredentials(
        authResult.client_id,
        request.required_services
      );

      // 3. Execute request with secured credentials
      const response = await this.executeWithCredentials(request, credentials);

      // 4. Log successful operation
      await this.auditLogger.logSuccess({
        user: authResult.user_id,
        operation: request.operation,
        resources: request.required_services,
        timestamp: new Date().toISOString()
      });

      return response;

    } catch (error) {
      // Log security events
      await this.auditLogger.logSecurityEvent({
        type: 'request_failure',
        error: error.message,
        request: this.sanitizeRequest(request)
      });

      throw error;
    }
  }
}
```

## Error Handling and Recovery Patterns

When credential retrieval fails during MCP server startup, implement these fallback strategies to maintain service reliability:

### Layered Credential Resolution

Implement multiple credential sources with graceful degradation:

```python
# Example from a Python-based MCP server
import os
import sys
import keyring

class GitHubMCP:
    def __init__(self):
        # Layer 1: Try environment variable first
        self.token = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')

        # Layer 2: Fall back to keyring
        if not self.token:
            try:
                self.token = keyring.get_password("mcp-secrets", "github_token")
            except Exception as e:
                print(f"Failed to retrieve GitHub token: {e}", file=sys.stderr)
                print("Run: mcp-secrets set github_token", file=sys.stderr)
                sys.exit(1)

        # Layer 3: Final validation
        if not self.token:
            print("No GitHub token found in environment or keychain", file=sys.stderr)
            print("Run: mcp-secrets set github_token", file=sys.stderr)
            sys.exit(1)
```

### Common Error Scenarios and Solutions

**Keyring Backend Not Available:**
```bash
# Error: No suitable keyring backend found
# Solution: Install platform-specific backend
pip install keyring[keyrings.alt]  # Alternative backends
```

**Permission Denied:**
```bash
# Error: Permission denied accessing keychain
# macOS Solution: Re-authorize keychain access
security unlock-keychain ~/Library/Keychains/login.keychain

# Linux Solution: Check secret service
systemctl --user status gnome-keyring-daemon
```

**Credential Not Found:**
```bash
# Error: Credential not found in keyring
# Solution: Re-store the credential
mcp-secrets set github token
# Or check credential name spelling
mcp-secrets list
```

### Emergency Credential Access

For critical systems, implement emergency access patterns:

```python
def get_emergency_credentials():
    """Last resort credential access with security warnings."""
    emergency_token = input("Enter emergency token (will not be stored): ")
    print("WARNING: Using emergency token. Configure proper storage ASAP!")
    return emergency_token

class RobustMCP:
    def __init__(self):
        try:
            self.token = self.get_secure_token()
        except CredentialError:
            print("EMERGENCY MODE: Secure credentials unavailable")
            self.token = get_emergency_credentials()
```

### Credential Rotation Handling

Handle expired or rotated credentials gracefully:

```python
def test_credential_validity(token):
    """Test if credential is still valid."""
    try:
        # Test API call with token
        response = requests.get("https://api.github.com/user",
                              headers={"Authorization": f"token {token}"})
        return response.status_code == 200
    except:
        return False

def handle_expired_credential():
    """Handle expired credential scenarios."""
    print("Credential appears invalid or expired")
    print("1. Check if token has been rotated in your account")
    print("2. Run: mcp-secrets set github token")
    print("3. Restart the MCP server")
```

## Advanced Troubleshooting & Recovery

### Comprehensive Error Diagnosis

When MCP servers fail to start due to credential issues, use this systematic diagnosis approach:

```bash
# Step 1: Verify credential storage backend
python3 -c "import keyring; print('Backend:', keyring.get_keyring())"

# Step 2: Test credential retrieval
python3 -c "
import keyring
try:
    token = keyring.get_password('mcp-secrets', 'github_token')
    print(f'Token found: {len(token) if token else 0} chars')
except Exception as e:
    print(f'Error: {e}')
"

# Step 3: Verify environment variable expansion
echo "Testing pattern: \${SECRET:github_token}"
mcp-secrets test github_token

# Step 4: Check MCP server logs
tail -f ~/.local/share/claude/logs/mcp.log
```

### Platform-Specific Recovery Procedures

**macOS Keychain Recovery:**
```bash
# Reset keychain if corrupted
security delete-keychain ~/Library/Keychains/mcp-credentials.keychain
security create-keychain -p "" mcp-credentials.keychain

# Re-add to search list
security list-keychains -s $(security list-keychains | sed 's/"//g') mcp-credentials.keychain

# Restore credentials
mcp-secrets restore-backup
```

**Windows Credential Manager Recovery:**
```powershell
# Clear corrupted entries
cmdkey /delete:mcp-secrets:*

# Verify clean state
cmdkey /list | findstr mcp-secrets

# Restore from backup
mcp-secrets.exe restore --platform windows
```

**Linux Secret Service Recovery:**
```bash
# Restart keyring daemon
systemctl --user restart gnome-keyring-daemon

# Clear and rebuild keyring
rm -rf ~/.local/share/keyrings/mcp-secrets.keyring
secret-tool store --label="MCP Secrets" service mcp-secrets account github_token

# Test access
secret-tool lookup service mcp-secrets account github_token
```

### Emergency Credential Access Patterns

For critical production systems, implement these emergency access patterns:

```python
def emergency_credential_handler():
    """Emergency credential access with audit logging."""
    import logging
    import getpass

    logging.warning("EMERGENCY CREDENTIAL ACCESS INITIATED")

    # Log emergency access
    with open("/var/log/mcp-emergency.log", "a") as f:
        f.write(f"{datetime.now()}: Emergency credential access by {os.getlogin()}\n")

    # Secure temporary input
    emergency_token = getpass.getpass("Emergency token (hidden): ")

    print("⚠️  SECURITY WARNING: Emergency credential in use")
    print("   → Restore secure storage immediately after incident")
    print("   → This session is being audited")

    return emergency_token
```

### Automated Health Monitoring

```bash
# credential-health-monitor.sh - Run via cron
check_credential_health() {
    local service=$1
    if ! mcp-secrets get "$service" token >/dev/null 2>&1; then
        logger "ERROR: $service credential failed"
        return 1
    fi
    logger "INFO: $service credential healthy"
}

check_credential_health "github"
check_credential_health "slack"
```

## Next Steps

1. **Assess current security posture** - Identify plaintext credentials and security gaps
2. **Select appropriate tools** - Choose based on enterprise requirements and existing infrastructure
3. **Implement in phases** - Follow the recommended 4-phase deployment strategy
4. **Set up monitoring** - Deploy automated credential health monitoring
5. **Train emergency procedures** - Establish and practice emergency credential recovery
6. **Monitor and optimize** - Continuous security monitoring and improvement
7. **Team training** - Establish security-first development practices

---

*This module provides comprehensive guidance for production MCP security tool deployment. For platform-specific setup, see related credential management guides.*
