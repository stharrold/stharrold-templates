---
title: Enterprise SSO & Authentication
version: 3.2
updated: 2025-09-13
parent: ./CLAUDE.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - sso_provider
    - domain_configuration
    - cost_optimization_strategy
security_level: Enterprise-grade
target_audience: Enterprise teams
related:
  - ./21_keychain-macos.md
  - ./22_credential-manager-win.md
  - ./24_audit-compliance.md
  - ../30_implementation/32_workflow-patterns.md
changelog:
  - Enhanced with OAuth 2.1 security implementation and vulnerability mitigation patterns
  - Enhanced with enterprise search security considerations
  - Added multi-source credential management patterns
  - Integrated template security guidelines and sensitive areas
  - Added API billing optimization strategies
---

# Enterprise SSO & Authentication

Advanced authentication patterns for enterprise teams using Claude Code with MCP servers, including SSO integration, multi-source credential management, and enterprise search security.

## Enterprise Search Data Security

Enterprise search systems require additional security considerations beyond standard MCP credential management, particularly when dealing with sensitive corporate knowledge bases and multi-source data integration.

### Multi-Source Credential Management

Enterprise search typically integrates multiple data sources, each requiring secure credential handling with isolation and audit capabilities.

#### Credential Isolation Strategy

**Security Architecture:**
- **Separate credential stores per data source** to minimize breach impact
- **Service-specific tokens** with minimum required permissions
- **Time-bounded access tokens** with automatic refresh capabilities
- **Audit logging** for all credential access and usage

#### Implementation Examples

**Confluence Integration:**
```bash
# macOS Keychain
security add-generic-password \
  -a "$USER" \
  -s "CONFLUENCE_API_TOKEN" \
  -l "Confluence API Access" \
  -w "your-confluence-token"

# Windows Credential Manager
$confluenceToken = ConvertTo-SecureString "your-confluence-token" -AsPlainText -Force
New-StoredCredential -Target "CONFLUENCE_API_TOKEN" -UserName "token" -SecurePassword $confluenceToken -Persist LocalMachine
```

**SharePoint Integration:**
```bash
# macOS Keychain
security add-generic-password \
  -a "$USER" \
  -s "SHAREPOINT_CLIENT_SECRET" \
  -l "SharePoint Client Secret" \
  -w "your-sharepoint-secret"

# Windows Credential Manager
$sharePointSecret = ConvertTo-SecureString "your-sharepoint-secret" -AsPlainText -Force
New-StoredCredential -Target "SHAREPOINT_CLIENT_SECRET" -UserName "token" -SecurePassword $sharePointSecret -Persist LocalMachine
```

**Knowledge Graph Database:**
```bash
# Neo4j/Graph database credentials
security add-generic-password \
  -a "$USER" \
  -s "NEO4J_PASSWORD" \
  -l "Neo4j Graph Database" \
  -w "your-neo4j-password"
```

### Access Control for Sensitive Enterprise Data

#### Fine-Grained Permission Management

**Security Controls:**
- **Document-level access controls** that respect source system permissions
- **Role-based query filtering** based on user identity and clearance level
- **Confidentiality classification enforcement** (Public, Internal, Confidential, Restricted)
- **Data sovereignty compliance** for regulatory requirements (GDPR, HIPAA, SOX)

#### Implementation Pattern
```bash
# Configure access control MCP server
claude mcp add access-control "python -m enterprise_acl" \
  --env USER_DIRECTORY="ldap://company.ldap" \
  --env CLASSIFICATION_SERVICE="./data_classification.json" \
  --env COMPLIANCE_MODE="GDPR,HIPAA"
```

#### Confidentiality Rules Configuration
```yaml
# confidentiality_rules.yaml
classification_rules:
  - pattern: "customer_data|financial_records|employee_info"
    classification: "confidential"
    external_lookup: false
    retention_days: 2555  # 7 years
    audit_level: "detailed"

  - pattern: "public_documentation|marketing_content"
    classification: "public"
    external_lookup: true
    retention_days: 365
    audit_level: "summary"

  - pattern: "trade_secrets|strategic_plans|m&a_documents"
    classification: "restricted"
    external_lookup: false
    retention_days: 3650  # 10 years
    audit_level: "forensic"
```

### Confidentiality Filters and External Lookups

Prevent sensitive information leakage when using external enrichment sources or third-party integrations.

#### Security Gates Implementation

**Pre-Query Screening Process:**
1. **Sensitive term identification** using NLP and pattern matching
2. **Confidentiality classification** of all retrieved content
3. **External lookup restrictions** based on data classification
4. **Audit trail logging** for all external data requests

**Example Configuration:**
```bash
# Data Loss Prevention MCP Server
claude mcp add dlp-monitor "python -m data_loss_prevention" \
  --env SCAN_PATTERNS="./pii_patterns.json" \
  --env ALERT_WEBHOOK="https://security-alerts.company.com/webhook" \
  --env COMPLIANCE_OFFICER="security@company.com"
```

## OAuth 2.1 Security Implementation

### MCP OAuth 2.1 Compliance Requirements

The Model Context Protocol mandates OAuth 2.1 for HTTP-based servers with specific security requirements that address common vulnerabilities in enterprise environments:

**Mandatory Security Features:**
- **PKCE Implementation**: Proof Key for Code Exchange with dynamically generated code verifiers
- **Resource Indicators**: Token binding to specific MCP servers per RFC 8707
- **Dynamic Client Registration**: Eliminates manual configuration overhead and reduces attack surface
- **Token Audience Validation**: Prevents token confusion attacks across MCP server instances
- **Automatic Token Refresh**: Seamless credential renewal without service interruption

### Critical Vulnerability Prevention

#### Confused Deputy Problem Mitigation

MCP proxy servers acting as single OAuth clients create the **confused deputy vulnerability** where malicious clients can abuse server privileges:

```javascript
// SECURE: Per-client OAuth registration
class SecureMCPProxy {
  async registerClient(clientRequest) {
    // Each client gets unique OAuth registration
    const clientId = await this.oauthProvider.createClient({
      name: `MCP-Client-${uuidv4()}`,
      redirectUris: [clientRequest.redirectUri],
      scopes: clientRequest.requestedScopes
    });

    // Require explicit consent for new redirect URIs
    return { clientId, requiresConsent: true };
  }

  // NEVER allow silent consent skips
  async handleAuthRequest(clientId, redirectUri) {
    const client = await this.getClient(clientId);
    if (!client.redirectUris.includes(redirectUri)) {
      throw new SecurityError('Redirect URI not registered for client');
    }
    // Force user consent even for previously authorized URIs
    return this.showConsentScreen(clientId, redirectUri);
  }
}
```

#### Token Passthrough Prevention

**Vulnerability**: Servers blindly forwarding client-provided tokens enable privilege escalation.

```javascript
// SECURE: Token audience validation and exchange
class SecureTokenHandler {
  async validateAndExchangeToken(incomingToken, targetService) {
    // Verify token audience matches this server
    const decoded = jwt.verify(incomingToken, publicKey);
    if (decoded.aud !== this.serverId) {
      throw new SecurityError('Token audience mismatch');
    }

    // Use OAuth 2.0 Token Exchange (RFC 8644) for downstream access
    const exchangedToken = await this.oauthClient.tokenExchange({
      subjectToken: incomingToken,
      audience: targetService,
      scope: 'mcp:read mcp:write'
    });

    return exchangedToken;
  }
}
```

#### Session Hijacking Prevention

**Security Pattern**: Non-deterministic session management with user binding.

```javascript
// SECURE: Session security implementation
class SecureSessionManager {
  createSession(userId, clientId) {
    const sessionId = crypto.randomUUID();
    const boundSession = `${userId}:${sessionId}:${crypto.randomBytes(16).toString('hex')}`;

    return {
      sessionId: boundSession,
      expires: Date.now() + (8 * 60 * 60 * 1000), // 8 hours
      userId,
      clientId,
      createdAt: Date.now()
    };
  }

  rotateOnPrivilegeEscalation(session, newPrivileges) {
    // Force session rotation when permissions change
    this.invalidateSession(session.sessionId);
    return this.createSession(session.userId, session.clientId);
  }

  enforceAbsoluteTimeout(session) {
    const maxSession = 24 * 60 * 60 * 1000; // 24 hours absolute
    if (Date.now() - session.createdAt > maxSession) {
      this.invalidateSession(session.sessionId);
      throw new SecurityError('Session exceeded absolute timeout');
    }
  }
}
```

### Production Deployment Security

#### Container Security Hardening

MCP servers in production require comprehensive security hardening:

```dockerfile
# Secure container deployment
FROM node:18-alpine

# Create non-root user with specific UID
RUN adduser -S mcpuser -u 1001 && \
    addgroup -S mcpgroup && \
    adduser mcpuser mcpgroup

# Use read-only root filesystem
USER mcpuser
WORKDIR /app
COPY --chown=mcpuser:mcpgroup package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY --chown=mcpuser:mcpgroup . .

# Remove package managers and unnecessary tools
USER root
RUN apk del npm && rm -rf /var/cache/apk/*
USER mcpuser

# Health check with proper timeouts
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

EXPOSE 3000
CMD ["node", "server.js"]
```

#### Network Isolation and Service Mesh

```yaml
# Kubernetes NetworkPolicy for MCP server isolation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-server-isolation
spec:
  podSelector:
    matchLabels:
      app: mcp-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: claude-code
    ports:
    - protocol: TCP
      port: 3000
  egress:
  - to: []  # Allow external API calls with explicit rules
    ports:
    - protocol: TCP
      port: 443  # HTTPS only
```

### Inter-Process Communication Security

#### Unix Domain Sockets (Preferred)

```javascript
// Secure IPC via Unix domain sockets
const net = require('net');
const fs = require('fs');

const socket = net.createServer((client) => {
  // Verify client process ownership
  const stats = fs.statSync(`/proc/${client.pid}`);
  if (stats.uid !== process.getuid()) {
    client.destroy();
    return;
  }

  // Handle secure communication
  client.on('data', (data) => {
    // Process encrypted/authenticated messages
  });
});

const socketPath = '/tmp/mcp-secure.sock';
socket.listen(socketPath);

// Set owner-only permissions
fs.chmod(socketPath, 0o600);
```

#### Mutual TLS for Network IPC

```javascript
// mTLS implementation for network-based IPC
const tls = require('tls');
const crypto = require('crypto');

const options = {
  key: fs.readFileSync('server-key.pem'),
  cert: fs.readFileSync('server-cert.pem'),
  ca: fs.readFileSync('ca-cert.pem'),
  requestCert: true,
  rejectUnauthorized: true,
  // Certificate pinning
  checkServerIdentity: (hostname, cert) => {
    const expectedFingerprint = process.env.EXPECTED_CERT_FINGERPRINT;
    const actualFingerprint = crypto
      .createHash('sha256')
      .update(cert.raw)
      .digest('hex');

    if (expectedFingerprint !== actualFingerprint) {
      throw new Error('Certificate pinning failure');
    }
  }
};

const server = tls.createServer(options, (socket) => {
  // Secure authenticated communication
});
```

## Enterprise Authentication & SSO Integration

### Centralized Authentication Management

Enterprise teams can leverage centralized authentication through SSO and domain capture, ensuring consistent access management across development teams.

#### SSO Integration Benefits
- **Single sign-on** across all Claude Code instances
- **Centralized user provisioning** and deprovisioning
- **compliance with enterprise identity management** policies
- **Audit trail integration** with existing security systems
- **Multi-factor authentication** enforcement
- **Conditional access policies** based on device/location

#### Domain Capture Configuration

**Administrative Setup:**
```bash
# Enterprise administrators configure domain-wide settings
claude config set-enterprise-domain company.com
claude config set-sso-provider okta  # or azure-ad, ping, auth0, etc.
claude config set-mfa-requirement enforced
claude config set-session-timeout 480  # 8 hours in minutes
```

**Supported SSO Providers:**
- **Okta**: Full SAML 2.0 and OpenID Connect support
- **Azure Active Directory**: Native Microsoft 365 integration
- **Ping Identity**: Enterprise federation capabilities
- **Auth0**: Developer-friendly configuration
- **Google Workspace**: G Suite integration
- **OneLogin**: Comprehensive enterprise features

#### Role-Based Permissions Management

**Organizational Roles:**
- **Developer roles**: Limited MCP server access, read-only on sensitive data
- **Senior Developer roles**: Full MCP server access, limited administrative functions
- **Admin roles**: Full configuration capabilities, user management
- **Security roles**: Audit access, compliance reporting, incident response
- **Project-specific permissions**: Fine-grained control per repository/project

**Implementation Example:**
```json
{
  "enterprise_roles": {
    "developer": {
      "mcp_servers": ["github", "postgres", "slack"],
      "data_classification_access": ["public", "internal"],
      "session_duration": 240
    },
    "senior_developer": {
      "mcp_servers": ["github", "postgres", "slack", "aws", "terraform"],
      "data_classification_access": ["public", "internal", "confidential"],
      "session_duration": 480
    },
    "admin": {
      "mcp_servers": "*",
      "data_classification_access": "*",
      "session_duration": 240,
      "administrative_functions": true
    }
  }
}
```

### API Billing & Cost Management

Strategic cost optimization for enterprise Claude Code deployments with intelligent model selection and usage optimization.

#### Pay-Per-Use API Billing Options

**Model-Specific Pricing (2025 rates):**
- **Claude Sonnet 4**: $3/million input tokens (optimal for 80% of development tasks)
- **Claude Opus 4**: $15/million input tokens (complex architectural decisions)
- **Claude Haiku**: $0.80/million input tokens (simple, repetitive tasks)

**Enterprise Volume Discounts:**
- **>$10K/month**: 15% discount across all models
- **>$50K/month**: 25% discount + dedicated success manager
- **>$100K/month**: 35% discount + custom SLA + priority support

#### Cost Optimization Strategies

**Advanced Optimization Techniques:**
- **Prompt Caching**: 90% cost reduction for repeated patterns and common workflows
- **Cache Hits**: $0.30/million tokens versus $3.00/million for fresh calls
- **Batch Processing**: 50% discount for headless mode operations
- **Strategic Model Selection**: Dynamic switching based on task complexity analysis
- **Context Optimization**: Hierarchical file structure reduces token usage by 30-40%

**Implementation Commands:**
```bash
# Real-time cost monitoring
claude /cost --breakdown-by-model --time-period=24h

# Dynamic model switching based on complexity
claude /model sonnet-4    # For most development tasks
claude /model opus-4      # For complex architecture work
claude /model haiku       # For simple operations

# Enable intelligent cost optimization
claude config set-cost-optimization aggressive
claude config set-model-switching automatic
claude config set-cache-strategy aggressive
```

**Cost Monitoring Dashboard:**
```bash
# Enterprise cost analytics
claude /cost --team-summary --export-csv
claude /cost --predict-monthly --alert-threshold=5000
claude /cost --efficiency-report --compare-last-month
```

## Template Security Guidelines Integration

### Critical Security Rules (from Project Template)

**Mandatory Security Practices:**
1. **Never commit secrets** - Use environment variables and OS credential stores only
2. **Validate all inputs** - Assume all user input and API responses are potentially malicious
3. **Parameterize queries** - Prevent SQL injection in database MCP servers
4. **Sanitize outputs** - Prevent XSS attacks when displaying retrieved content
5. **Check dependencies** - Run security audits on all MCP server dependencies regularly

### Sensitive Areas Identification

**High-Risk Components requiring additional scrutiny:**
- **Authentication logic** - SSO integration, token handling, session management
- **Payment processing** - Billing integration, cost management APIs
- **Environment configuration** - `.env` files, credential storage, API keys
- **Enterprise search** - Multi-source data access, confidentiality filtering
- **Audit systems** - Log collection, compliance reporting, access tracking

### Implementation Integration

**Enhanced Security Workflow:**
```bash
# Pre-deployment security checklist
claude security-scan --include-mcp-servers
claude audit-credentials --rotation-check
claude compliance-report --export-format=json

# Automated security monitoring
claude config set-security-alerts enabled
claude config set-vulnerability-scanning daily
claude config set-compliance-reporting weekly
```

## Enterprise Integration Patterns

### Active Directory Integration
```powershell
# PowerShell integration for Windows environments
Import-Module ActiveDirectory
$userGroups = Get-ADPrincipalGroupMembership -Identity $env:USERNAME
$mcpPermissions = Get-MCPPermissionsFromAD -Groups $userGroups
Set-MCPUserContext -Permissions $mcpPermissions
```

### LDAP Integration
```bash
# LDAP user context for Unix/Linux environments
claude mcp add ldap-auth "python -m enterprise_ldap" \
  --env LDAP_SERVER="ldap://company.ldap:389" \
  --env BIND_DN="cn=mcp-service,ou=services,dc=company,dc=com" \
  --env USER_BASE_DN="ou=users,dc=company,dc=com"
```

### Kubernetes Service Mesh Integration
```yaml
# ServiceAccount for MCP server pods
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-service-account
  namespace: claude-code
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: mcp-secrets-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
```

## Performance and Scalability

### Multi-Tenant Architecture
- **Isolated credential namespaces** per organization/team
- **Resource quotas** and rate limiting per tenant
- **Cross-tenant data leakage prevention**
- **Tenant-specific audit trails**

### High-Availability Configuration
```yaml
# Enterprise MCP server deployment
enterprise_config:
  redundancy: multi-region
  failover: automatic
  backup_frequency: hourly
  disaster_recovery: cross-cloud
  sla_target: 99.95%
```

## Next Steps for Enterprise Deployment

1. **Assess current identity infrastructure** - Evaluate existing SSO/LDAP systems
2. **Plan credential migration strategy** - Move from individual to centralized management
3. **Configure audit and compliance** - Set up logging and monitoring per [24_audit-compliance.md](./24_audit-compliance.md)
4. **Implement cost optimization** - Deploy intelligent model selection and caching
5. **Train development teams** - Establish enterprise workflow patterns
6. **Monitor and optimize** - Continuous improvement of security and cost efficiency

---

*This module focuses on enterprise-grade authentication and security. For platform-specific credential storage, see [21_keychain-macos.md](./21_keychain-macos.md) and [22_credential-manager-win.md](./22_credential-manager-win.md).*
