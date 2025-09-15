---
title: MCP Security Tools & Ecosystem
version: 1.0
updated: 2025-09-13
parent: ./CLAUDE.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - security_tool_selection
    - oauth_server_config
    - integration_patterns
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
# Method 1: Install via pip
pip install mcp-secrets-plugin

# Method 2: Install with pipx for isolated installation
pipx install mcp-secrets-plugin

# Method 3: Install from source (development)
git clone https://github.com/amirshk/mcp-secrets-plugin.git
cd mcp-secrets-plugin
pip install -e .

# Method 4: Install globally via npm (alternative)
npm install -g mcp-secrets-plugin
```

**Step-by-Step Setup Workflow:**

```bash
# Step 1: Install the credential manager MCP
npm install -g mcp-secrets-plugin

# Step 2: Configure mcp-secrets-plugin in Claude
# Add to Claude's configuration file (.claude.json or claude_desktop_config.json):
```

```json
{
  "mcpServers": {
    "mcp-secrets": {
      "command": "python",
      "args": ["-m", "mcp_secrets_plugin"],
      "env": {}
    }
  }
}
```

```bash
# Step 3: Install target MCP that needs credentials
npm install -g @modelcontextprotocol/server-github
# Or any MCP that requires API keys
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

# Alternative: Set with a single command
mcp-secrets set github token --value "ghp_xxxxxxxxxxxxxxxxxxxx"

# Retrieve credentials
mcp-secrets get github token

# List all stored services
mcp-secrets list
# Output: Available secrets:
#   - github_token (stored 2025-01-15)

# Delete old credentials
mcp-secrets delete azure-devops token

# Export configuration for MCP servers
mcp-secrets export --format env > .env.secure
```

**Credential Discovery Workflow:**

Before storing credentials, discover the required environment variable names:

```bash
# Method 1: Run without credentials to see error
npx @modelcontextprotocol/server-github
# Error: GITHUB_PERSONAL_ACCESS_TOKEN environment variable is required

# Method 2: Check documentation
npm info @modelcontextprotocol/server-github
open https://github.com/modelcontextprotocol/servers/tree/main/src/github

# Method 3: Inspect source code
grep -r "process.env" node_modules/@modelcontextprotocol/server-github/
# Output: process.env.GITHUB_PERSONAL_ACCESS_TOKEN

# Method 4: Check MCP manifest (if available)
cat node_modules/@modelcontextprotocol/server-github/mcp.json
```

**Value Format Discovery:**

```bash
# Each credential manager has its own pattern:
# mcp-secrets-plugin:     ${SECRET:github_token}
# mcpauth:                ${OAUTH:github}
# keytar-mcp:             ${KEYTAR:service/account}
# vault-mcp:              ${VAULT:secret/path}
# aws-secrets:            ${AWS_SECRET:arn}

# Without a manager (direct environment):
# Plain value:            "ghp_xxxxxxxxxxxx"
# System env:             "${GITHUB_TOKEN}"
```

**MCP Integration Pattern:**

```json
{
  "mcpServers": {
    "mcp-secrets": {
      "command": "python",
      "args": ["-m", "mcp_secrets_plugin"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${SECRET:github_token}"
      }
    }
  }
}
```

**Runtime Credential Injection:**

The credential injection process works automatically when Claude starts MCP servers:

```python
# mcp-secrets-plugin handles credential retrieval internally
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

**Team Setup Script:**

```bash
#!/bin/bash
# Team onboarding script using mcp-secrets-plugin

echo "🔐 Setting up secure MCP credentials..."

# Install mcp-secrets-plugin
echo "Installing mcp-secrets-plugin..."
pipx install mcp-secrets-plugin

# Verify installation
echo "Verifying installation..."
mcp-secrets --version

# Store common team credentials
echo "Setting up GitHub integration..."
echo "Please enter your GitHub Personal Access Token:"
mcp-secrets set github token

echo "Setting up Azure DevOps integration..."
echo "Please enter your Azure DevOps Personal Access Token:"
mcp-secrets set azure-devops pat

echo "Setting up database credentials..."
echo "Please enter your database connection URL:"
mcp-secrets set database url

# Verify stored credentials
echo "\n📋 Verifying stored credentials..."
mcp-secrets list

echo "\n✅ Secure credential setup complete!"
echo "💡 Credentials are stored in your system's secure credential store"
echo "🔄 Run 'mcp-secrets list' to view configured services"
echo "🔧 Run 'mcp-secrets get <service> <key>' to test retrieval"
echo "🔄 Run 'mcp-secrets update <service> <key>' to rotate credentials"
```

**Verification Workflow:**

```bash
# Test credential retrieval workflow
echo "Testing credential storage and retrieval..."

# List stored secrets
mcp-secrets list
# Expected output:
# Available secrets:
#   - github_token (stored 2025-01-15)
#   - azure-devops_pat (stored 2025-01-15)
#   - database_url (stored 2025-01-15)

# Test credential retrieval
echo "Testing GitHub token retrieval..."
mcp-secrets get github token
# Should display: ghp_xxxxxxxxxxxxxxxxxxxx

# Verify MCP integration works
echo "Testing MCP server functionality..."
claude-desktop --test-mcp github
# Expected output:
# ✓ MCP server started successfully
# ✓ Authentication verified
# ✓ GitHub API accessible
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
# Method 1: Quick setup via npm
npm install -g mcpauth
mcpauth init

# Method 2: Clone and setup from source
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

**OAuth 2.1 Workflow Implementation:**

```bash
# Step 1: Configure mcpauth server
mcpauth init

# Step 2: Add to Claude configuration
```

```json
{
  "mcpServers": {
    "mcpauth": {
      "command": "mcpauth",
      "args": ["server"],
      "env": {}
    }
  }
}
```

```bash
# Step 3: Authenticate via OAuth
mcpauth login github

# Opens browser for OAuth flow
# Opening browser for authentication...
# Please authorize the application.

# After user authorizes:
# ✓ Authentication successful
# ✓ Token stored securely in system keychain
# ✓ Refresh token saved for automatic renewal
```

**OAuth Token Storage with Metadata:**

```python
# mcpauth stores OAuth tokens with comprehensive metadata
import json
import keyring

keyring.set_password(
    "mcpauth",
    "github_oauth",
    json.dumps({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "scope": "repo,user"
    })
)
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

## Tool Selection Guidelines

### Security Requirements Matrix

| Tool | Cross-Platform | Enterprise SSO | OAuth 2.1 | Audit Logging | Container Ready |
|------|---------------|----------------|-----------|---------------|-----------------|
| **mcp-secrets-plugin** | ✅ | ❌ | ❌ | Basic | ✅ |
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

  async executeWithCredentials(request, credentials) {
    // Inject credentials into environment for MCP execution
    const env = { ...process.env };

    Object.entries(credentials).forEach(([service, creds]) => {
      Object.entries(creds).forEach(([key, value]) => {
        const envKey = `${service.toUpperCase()}_${key.toUpperCase()}`;
        env[envKey] = value;
      });
    });

    // Execute MCP server with secured environment
    return await this.mcpExecutor.run(request, { env });
  }
}
```

**Real-World Implementation Benefits:**

Based on production deployments, the integrated security tools provide:

1. **Zero plaintext storage** - Credentials never touch disk unencrypted
2. **OS-level security** - Leverages platform's native keychain/credential manager
3. **Python keyring abstraction** - Unified API across macOS, Windows, and Linux
4. **Simple CLI interface** - Easy credential management via terminal
5. **MCP ecosystem integration** - Designed specifically for MCP servers
6. **Automatic fallback** - Supports multiple credential sources
7. **Production-ready** - Used by multiple MCP implementations
8. **Enterprise compliance** - Audit trails and security logging included

## Platform-Specific Verification

### macOS Keychain Verification

```bash
# View stored credential (requires user password)
security find-generic-password -s "mcp-secrets" -a "github-token" -w
# [Keychain Access prompt appears]

# Credential is stored at:
# ~/Library/Keychains/login.keychain-db

# Programmatic verification
python -c "import keyring; print(keyring.get_password('mcp-secrets', 'github_token'))"
```

### Windows Credential Manager Verification

```powershell
# View stored credential
PS> cmdkey /list:mcp-secrets:github-token

# Credential is stored at:
# Control Panel > User Accounts > Credential Manager > Windows Credentials

# PowerShell verification
$cred = Get-StoredCredential -Target "mcp-secrets:github-token"
$cred.Password
```

### Linux Secret Service Verification

```bash
# View stored credential
secret-tool lookup service mcp-secrets account github-token

# Credential is stored in:
# GNOME Keyring or KDE Wallet

# Python verification
python -c "import keyring; print(keyring.get_password('mcp-secrets', 'github_token'))"
```

## Error Handling and Troubleshooting

### Common Issues and Solutions

**Issue: Credential retrieval fails**

```python
# Robust error handling pattern for MCP servers
import os
import sys
import keyring

class GitHubMCP:
    def __init__(self):
        # Try environment variable first
        self.token = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')

        # Fall back to keyring
        if not self.token:
            try:
                self.token = keyring.get_password("mcp-secrets", "github_token")
            except Exception as e:
                print(f"Failed to retrieve GitHub token: {e}", file=sys.stderr)
                print("Run: mcp-secrets set github_token", file=sys.stderr)
                sys.exit(1)

        if not self.token:
            print("No GitHub token found in environment or keychain", file=sys.stderr)
            print("Run: mcp-secrets set github_token", file=sys.stderr)
            sys.exit(1)
```

**Issue: Cross-platform compatibility**

```javascript
// Node.js cross-platform credential storage using keytar
const keytar = require("keytar");

async function storeCredential(service, account, password) {
  await keytar.setPassword(service, account, password);
  console.log("✓ Credential stored in system keychain");
}

async function getCredential(service, account) {
  const password = await keytar.getPassword(service, account);
  if (!password) {
    throw new Error(`No credential found for ${service}/${account}`);
  }
  return password;
}

// Usage in MCP initialization
async function initializeMCP() {
  try {
    const token = await getCredential("mcp-github", "api-token");
    process.env.GITHUB_TOKEN = token;
  } catch (error) {
    console.error("Please run: npm run setup-credentials");
    process.exit(1);
  }
}
```

### Emergency Response Patterns

**Credential Rotation Workflow:**

```bash
# Step 1: Update the credential
mcp-secrets update github_token
# ⚠ This will replace the existing token
# Enter new value: ************************************
# ✓ Credential updated in system keychain
# ✓ All MCPs using this credential will get the new token

# Step 2: Verify update
mcp-secrets get github_token
# Displays new token value

# Step 3: Test MCP functionality
claude-desktop --test-mcp github
# ✓ MCP server started successfully
# ✓ Authentication verified
# ✓ GitHub API accessible
```

**Emergency Credential Removal:**

```bash
# Remove compromised credentials immediately
mcp-secrets delete github_token
# ⚠ This will remove the credential permanently
# Continue? (y/N): y
# ✓ Removed from system keychain
# ✓ MCPs using this credential will fail at runtime

# Verify removal
mcp-secrets list
# Available secrets: (empty)
```

## Next Steps

1. **Assess current security posture** - Identify plaintext credentials and security gaps
2. **Select appropriate tools** - Choose based on enterprise requirements and existing infrastructure
3. **Implement in phases** - Follow the recommended 4-phase deployment strategy
4. **Monitor and optimize** - Continuous security monitoring and improvement
5. **Team training** - Establish security-first development practices

## Additional Resources

From the MCP security ecosystem:

- **mcp-secrets-plugin**: https://github.com/amirshk/mcp-secrets-plugin
- **mcpauth**: https://github.com/mcpauth/mcpauth
- **keytar**: https://www.npmjs.com/package/keytar (664+ projects using cross-platform keychain access)
- **Auth0 MCP Server**: Enterprise-grade OAuth implementation example
- **MCP Specification**: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization

**Production Implementations:**
- Cross-platform credential storage using Python keyring
- Complete OAuth 2.0 server for MCP authentication
- Node.js library for cross-platform keychain access
- Enterprise-grade OAuth implementation patterns

---

*This module provides comprehensive guidance for production MCP security tool deployment. Enhanced with step-by-step installation workflows, credential discovery methods, platform-specific verification, and emergency response patterns. For platform-specific setup, see related credential management guides.*