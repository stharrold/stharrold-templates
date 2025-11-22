---
title: MCP Installation & Setup
version: 3.2
updated: 2025-09-13
parent: ./CLAUDE.md
related:
  - ./12_servers.md
  - ../20_credentials/CLAUDE.md
  - ./15_troubleshooting.md
---

# MCP Installation & Setup

Complete installation guide for Model Context Protocol servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop App.

## Overview

MCP servers enable AI assistants to interact with external tools and data sources. This guide covers platform-specific installation, configuration, and auto-synchronization across all Claude Code environments.

**Key Benefits:**
- **Development Velocity**: 2-10x improvements reported by early adopters
- **Task Completion**: 55% faster completion rates (GitHub studies)
- **Documentation**: 70% reduction in manual documentation time
- **Context Efficiency**: 30-40% reduction in per-session token consumption

## Prerequisites

**Credentials Required**: Many MCP servers need API tokens.
→ **Set up credentials first**: [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md)

## Quick Start Workflow

1. **Setup Credentials**: Follow [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md) for your platform
2. **Add Servers**: Use `claude mcp add` commands or auto-sync setup below
3. **Validate Setup**: Run `/mcp` in Claude Code to verify servers
4. **Configure Auto-Sync**: Follow platform-specific sync setup

## Claude Code Installation & Setup

### Installation and Authentication

Claude Code operates as a command-line interface requiring Node.js 18 or newer:

```bash
# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Initialize in your project directory
claude
```

### Authentication Options

**Subscription-Based Authentication:**
- Claude Pro ($20/month): Basic usage limits
- Claude Max ($200/month): Higher limits but 5-hour session restrictions
- Enterprise SSO and domain capture for centralized team management

**Pay-Per-Use API Billing:**
- More predictable costs for intermittent usage
- No session time limits
- Ideal for enterprise deployments with usage-based budgeting

### Project Initialization Workflow

```bash
# Generate initial CLAUDE.md by analyzing codebase structure
claude /init

# This creates a starting template that should be customized with:
# - Project-specific conventions
# - Architectural patterns  
# - Workflow requirements
# - Explicit "do not" instructions
```

## Directory Structure by Platform

### macOS
```
~/
├── .claude.json                                    # Claude Code CLI configuration
├── bin/
│   └── sync-mcp.sh                                # Auto-sync script
└── Library/Application Support/
    ├── Code/User/
    │   └── mcp.json                               # VS Code MCP extension config
    └── Claude/
        └── config.json                             # Claude Desktop app config
```

### Windows
```
~/
├── .claude.json                                    # Claude Code CLI configuration
├── bin/
│   └── sync-mcp.sh                                # Auto-sync script
└── AppData/Roaming/
    ├── Code/User/
    │   └── mcp.json                               # VS Code MCP extension config
    └── Claude/
        └── config.json                             # Claude Desktop app config
```

### Linux
```
~/
├── .claude.json                                    # Claude Code CLI configuration
├── bin/
│   └── sync-mcp.sh                                # Auto-sync script
└── .config/
    ├── Code/User/
    │   └── mcp.json                               # VS Code MCP extension config
    └── claude/
        └── config.json                             # Claude Desktop app config
```

## Application Configuration

### Claude Code CLI

```bash
# Add servers via CLI
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /Users/stharrold
claude mcp add github npx @modelcontextprotocol/server-github
claude mcp add memory npx @modelcontextprotocol/server-memory

# List configured servers
claude mcp list
```

**Config Scopes:**
- **User scope**: `~/.claude.json` (global, all projects)
- **Project scope**: `.mcp.json` in project root (shared via git)
- **Local scope**: `~/.claude.json` with project-specific section

**Testing:**
- Open Claude Code: Command Palette → "Run Claude Code"
- Type `/mcp` to see configured servers
- Test: "List files in /Users/stharrold"

### VS Code MCP Extension

1. **Install Extension**: Search "MCP" in VS Code marketplace

2. **Configure**: Edit platform-specific configuration file:
   - **macOS**: `~/Library/Application Support/Code/User/mcp.json`
   - **Windows**: `~/AppData/Roaming/Code/User/mcp.json`  
   - **Linux**: `~/.config/Code/User/mcp.json`

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path"]
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

### Claude Desktop App

Configuration file location:
- **macOS**: `~/Library/Application Support/Claude/config.json`
- **Windows**: `~/AppData/Roaming/Claude/config.json`
- **Linux**: `~/.config/claude/config.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path"]
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

## Security Architecture

### Layered Storage Architecture for Credential Management

Production MCP credential managers implement a four-layer architecture for robust, secure credential handling across diverse deployment environments:

```javascript
// Four-layer credential storage architecture
class LayeredCredentialManager {
  constructor() {
    this.layers = {
      detection: new StorageDetectionLayer(),
      abstraction: new UnifiedAPILayer(),
      storage: new PlatformStorageLayer(),
      fallback: new FallbackStorageLayer()
    };
  }

  async getCredential(service, account) {
    try {
      // Layer 1: Detection - Identify available storage backends
      const availableStorages = await this.layers.detection.detectStorages();

      // Layer 2: Abstraction - Unified API regardless of storage
      const storageAdapter = this.layers.abstraction.getAdapter(availableStorages[0]);

      // Layer 3: Storage - Platform-specific credential operations
      const credential = await this.layers.storage.retrieve(storageAdapter, service, account);

      return credential;
    } catch (error) {
      // Layer 4: Fallback - Degraded scenarios
      return await this.layers.fallback.handleFailure(service, account, error);
    }
  }
}

// Layer 1: Detection Layer
class StorageDetectionLayer {
  async detectStorages() {
    const detectedStorages = [];

    // macOS Keychain detection
    if (process.platform === 'darwin') {
      try {
        await execAsync('security -h');
        detectedStorages.push({ type: 'keychain', priority: 1 });
      } catch {}
    }

    // Windows Credential Manager detection
    if (process.platform === 'win32') {
      try {
        await execAsync('powershell Get-Module -ListAvailable -Name CredentialManager');
        detectedStorages.push({ type: 'credential_manager', priority: 1 });
      } catch {}
    }

    // Keytar cross-platform detection
    try {
      require.resolve('keytar');
      detectedStorages.push({ type: 'keytar', priority: 2 });
    } catch {}

    // Encrypted file fallback always available
    detectedStorages.push({ type: 'encrypted_file', priority: 3 });

    return detectedStorages.sort((a, b) => a.priority - b.priority);
  }
}

// Layer 2: Abstraction Layer
class UnifiedAPILayer {
  getAdapter(storageType) {
    const adapters = {
      keychain: new KeychainAdapter(),
      credential_manager: new CredentialManagerAdapter(),
      keytar: new KeytarAdapter(),
      encrypted_file: new EncryptedFileAdapter(),
      memory: new SecureMemoryAdapter()
    };

    return adapters[storageType.type] || adapters.encrypted_file;
  }
}

// Layer 3: Storage Layer - Platform-specific implementations
class KeychainAdapter {
  async store(service, account, credential) {
    const { execAsync } = require('child_process').promisify;
    await execAsync(`security add-generic-password -a "${account}" -s "${service}" -w "${credential}"`);
  }

  async retrieve(service, account) {
    const { execAsync } = require('child_process').promisify;
    const result = await execAsync(`security find-generic-password -a "${account}" -s "${service}" -w`);
    return result.stdout.trim();
  }
}

class CredentialManagerAdapter {
  async store(service, account, credential) {
    // PowerShell CredentialManager implementation
    const powershell = `
      $secureString = ConvertTo-SecureString "${credential}" -AsPlainText -Force;
      New-StoredCredential -Target "${service}" -UserName "${account}" -SecurePassword $secureString -Persist LocalMachine;
    `;
    await execAsync(`powershell -Command "${powershell}"`);
  }

  async retrieve(service, account) {
    const powershell = `
      $cred = Get-StoredCredential -Target "${service}";
      $cred.GetNetworkCredential().Password;
    `;
    const result = await execAsync(`powershell -Command "${powershell}"`);
    return result.stdout.trim();
  }
}

// Layer 4: Fallback Layer
class FallbackStorageLayer {
  async handleFailure(service, account, error) {
    console.warn(`Primary storage failed for ${service}:${account}:`, error.message);

    // Try encrypted file storage
    try {
      return await this.encryptedFileRetrieve(service, account);
    } catch (fileError) {
      console.warn('Encrypted file storage also failed:', fileError.message);

      // Last resort: secure in-memory session storage
      return await this.sessionStorageRetrieve(service, account);
    }
  }

  async encryptedFileRetrieve(service, account) {
    // AES-256 encrypted file implementation
    const crypto = require('crypto');
    const fs = require('fs').promises;

    const credentialsFile = path.join(os.homedir(), '.mcp', 'encrypted_credentials.json');
    const data = await fs.readFile(credentialsFile);

    // Decrypt using user-derived key
    const decipher = crypto.createDecipher('aes-256-cbc', this.getUserDerivedKey());
    const decrypted = decipher.update(data) + decipher.final();
    const credentials = JSON.parse(decrypted);

    return credentials[`${service}:${account}`];
  }

  async sessionStorageRetrieve(service, account) {
    // In-memory session storage as absolute fallback
    const sessionKey = `${service}:${account}`;
    return process.env[`SESSION_CRED_${sessionKey.toUpperCase().replace(':', '_')}`];
  }
}
```

### Inter-Process Communication Security

**Unix Domain Sockets (Preferred IPC Method):**

```javascript
// Secure IPC implementation using Unix domain sockets
const net = require('net');
const fs = require('fs');
const crypto = require('crypto');

class SecureIPCServer {
  constructor(socketPath = '/tmp/mcp-secure.sock') {
    this.socketPath = socketPath;
    this.server = null;
    this.clients = new Map();
  }

  async start() {
    // Remove existing socket file
    try {
      await fs.promises.unlink(this.socketPath);
    } catch {}

    this.server = net.createServer((client) => {
      this.handleNewClient(client);
    });

    this.server.listen(this.socketPath);

    // Set owner-only permissions for security
    await fs.promises.chmod(this.socketPath, 0o600);

    console.log(`Secure MCP IPC server listening on ${this.socketPath}`);
  }

  handleNewClient(client) {
    // Generate unique session ID for this client
    const sessionId = crypto.randomUUID();
    this.clients.set(sessionId, {
      socket: client,
      authenticated: false,
      connectedAt: new Date(),
      lastActivity: new Date()
    });

    // Verify client process ownership
    this.verifyClientOwnership(client, sessionId);

    client.on('data', (data) => {
      this.handleClientMessage(sessionId, data);
    });

    client.on('close', () => {
      this.clients.delete(sessionId);
      console.log(`Client ${sessionId} disconnected`);
    });

    client.on('error', (error) => {
      console.error(`Client ${sessionId} error:`, error);
      this.clients.delete(sessionId);
    });
  }

  verifyClientOwnership(client, sessionId) {
    // On Unix systems, verify the connecting process belongs to same user
    try {
      const stats = fs.statSync(`/proc/${client.pid}`);
      if (stats.uid !== process.getuid()) {
        console.warn(`Rejecting connection from PID ${client.pid} - different user`);
        client.destroy();
        this.clients.delete(sessionId);
        return;
      }

      // Mark as authenticated after ownership verification
      const clientInfo = this.clients.get(sessionId);
      if (clientInfo) {
        clientInfo.authenticated = true;
      }
    } catch (error) {
      console.error('Failed to verify client ownership:', error);
      client.destroy();
      this.clients.delete(sessionId);
    }
  }

  handleClientMessage(sessionId, data) {
    const clientInfo = this.clients.get(sessionId);
    if (!clientInfo || !clientInfo.authenticated) {
      console.warn(`Rejecting message from unauthenticated client ${sessionId}`);
      return;
    }

    try {
      const message = JSON.parse(data.toString());

      // Update last activity
      clientInfo.lastActivity = new Date();

      // Handle the request securely
      this.processSecureRequest(sessionId, message);
    } catch (error) {
      console.error(`Invalid message from client ${sessionId}:`, error);
    }
  }

  processSecureRequest(sessionId, message) {
    // Process authenticated credential requests
    const { type, service, account } = message;

    if (type === 'get_credential') {
      this.handleCredentialRequest(sessionId, service, account);
    } else {
      console.warn(`Unknown request type: ${type}`);
    }
  }
}
```

**Mutual TLS for Network-Based IPC:**

```javascript
// mTLS implementation for remote MCP server communication
const tls = require('tls');
const fs = require('fs');
const crypto = require('crypto');

class SecureMTLSClient {
  constructor(options) {
    this.options = {
      host: options.host,
      port: options.port,
      key: fs.readFileSync(options.clientKeyPath),
      cert: fs.readFileSync(options.clientCertPath),
      ca: fs.readFileSync(options.caPath),
      rejectUnauthorized: true,
      ...options
    };
  }

  async connect() {
    return new Promise((resolve, reject) => {
      const socket = tls.connect(this.options, () => {
        // Verify certificate pinning
        const cert = socket.getPeerCertificate();
        const expectedFingerprint = process.env.EXPECTED_CERT_FINGERPRINT;

        if (expectedFingerprint) {
          const actualFingerprint = crypto
            .createHash('sha256')
            .update(cert.raw)
            .digest('hex');

          if (expectedFingerprint !== actualFingerprint) {
            socket.destroy();
            reject(new Error('Certificate pinning failure'));
            return;
          }
        }

        console.log('Secure mTLS connection established');
        resolve(socket);
      });

      socket.on('error', reject);
    });
  }
}
```

This layered architecture provides:
- **Graceful degradation** from OS-native keychains to encrypted file storage
- **Cross-platform compatibility** with automatic storage detection
- **Security isolation** through proper IPC mechanisms
- **Fallback resilience** ensuring MCP functionality even when primary storage fails

## Auto-Sync Configuration

Maintain synchronized MCP server configurations across all applications automatically.

### Step 1: Create Sync Script

```bash
mkdir -p ~/bin
cat > ~/bin/sync-mcp.sh << 'EOF'
#!/bin/bash

# Detect platform and set paths
case "$(uname -s)" in
    Darwin)
        VS_CODE_MCP="$HOME/Library/Application Support/Code/User/mcp.json"
        CLAUDE_DESKTOP="$HOME/Library/Application Support/Claude/config.json"
        ;;
    MINGW*|CYGWIN*|MSYS*)
        VS_CODE_MCP="$HOME/AppData/Roaming/Code/User/mcp.json"
        CLAUDE_DESKTOP="$HOME/AppData/Roaming/Claude/config.json"
        ;;
    *)
        VS_CODE_MCP="$HOME/.config/Code/User/mcp.json"
        CLAUDE_DESKTOP="$HOME/.config/claude/config.json"
        ;;
esac

CLAUDE_CODE_CONFIG="$HOME/.claude.json"

# Create backups
for file in "$VS_CODE_MCP" "$CLAUDE_CODE_CONFIG" "$CLAUDE_DESKTOP"; do
    if [ -f "$file" ]; then
        cp "$file" "$file.backup"
    fi
done

# Initialize empty servers if files don't exist
[ ! -f "$VS_CODE_MCP" ] && echo '{"servers":{}}' > "$VS_CODE_MCP"
[ ! -f "$CLAUDE_CODE_CONFIG" ] && echo '{"mcpServers":{}}' > "$CLAUDE_CODE_CONFIG"
[ ! -f "$CLAUDE_DESKTOP" ] && echo '{"mcpServers":{}}' > "$CLAUDE_DESKTOP"

# Merge all MCP servers from all sources and add type fields
jq -s '
    # Extract servers from each source
    (.[0].servers // {}) as $vscode |
    (.[1].mcpServers // {}) as $claude_code |
    (.[2].mcpServers // {}) as $claude_desktop |
    
    # Merge all servers (later sources override earlier)
    ($vscode + $claude_code + $claude_desktop) as $merged |
    
    # Add type fields where missing
    ($merged | with_entries(
        .value |= (
            if .url then 
                .type = "sse"
            elif .command then 
                .type = "stdio"
            else . end
        )
    )) as $typed |
    
    # Return all three configs
    [
        {servers: $typed},
        (.[1] | .mcpServers = $typed),
        (.[2] | .mcpServers = $typed)
    ]
' "$VS_CODE_MCP" "$CLAUDE_CODE_CONFIG" "$CLAUDE_DESKTOP" > /tmp/mcp-merge.json

# Write back to all locations
jq '.[0]' /tmp/mcp-merge.json > /tmp/vscode.json && mv /tmp/vscode.json "$VS_CODE_MCP"
jq '.[1]' /tmp/mcp-merge.json > /tmp/claude-code.json && mv /tmp/claude-code.json "$CLAUDE_CODE_CONFIG"
jq '.[2]' /tmp/mcp-merge.json > /tmp/claude-desktop.json && mv /tmp/claude-desktop.json "$CLAUDE_DESKTOP"

# Clean up
rm -f /tmp/mcp-merge.json

echo "MCP configs synced across all locations at $(date)"
EOF

chmod +x ~/bin/sync-mcp.sh
```

### Step 2: Create File Watch Service (macOS)

```bash
cat > ~/Library/LaunchAgents/com.user.sync-mcp.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.sync-mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/bin/sync-mcp.sh</string>
    </array>
    <key>WatchPaths</key>
    <array>
        <string>$HOME/Library/Application Support/Code/User/mcp.json</string>
        <string>$HOME/.claude.json</string>
        <string>$HOME/Library/Application Support/Claude/config.json</string>
    </array>
    <key>StandardOutPath</key>
    <string>/tmp/sync-mcp.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/sync-mcp.error.log</string>
</dict>
</plist>
EOF
```

### Step 3: Application Startup Triggers

#### VS Code Auto-sync
```bash
# Create tasks.json for auto-sync on folder open
mkdir -p .vscode
cat > .vscode/tasks.json << 'EOF'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Sync MCP on startup",
      "type": "shell",
      "command": "~/bin/sync-mcp.sh",
      "runOptions": {
        "runOn": "folderOpen"
      },
      "presentation": {
        "reveal": "silent",
        "panel": "new"
      }
    }
  ]
}
EOF
```

#### Claude CLI Auto-sync
Add to shell configuration:
```bash
# For bash (~/.bashrc) or zsh (~/.zshrc)
alias claude='~/bin/sync-mcp.sh 2>/dev/null && command claude'
```

#### Claude Desktop Auto-sync
```bash
# Create launcher script
cat > /Applications/Claude-Synced.command << 'EOF'
#!/bin/bash
~/bin/sync-mcp.sh
open -a "Claude"
exit
EOF
chmod +x /Applications/Claude-Synced.command

# Use Claude-Synced.command instead of Claude.app
```

### Step 4: Load File Watch Service

```bash
# Always unload first to avoid conflicts
launchctl unload ~/Library/LaunchAgents/com.user.sync-mcp.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.user.sync-mcp.plist
```

Service persists across restarts. To disable: 
```bash
launchctl unload -w ~/Library/LaunchAgents/com.user.sync-mcp.plist
```

## Next Steps

1. **Configure MCP Servers** → [12_servers.md](./12_servers.md)
2. **Optimize Context Management** → [13_context-management.md](./13_context-management.md)
3. **Troubleshoot Issues** → [15_troubleshooting.md](./15_troubleshooting.md)

---

*Installation complete. All MCP configurations now synchronized across Claude Code CLI, VS Code, and Claude Desktop.*