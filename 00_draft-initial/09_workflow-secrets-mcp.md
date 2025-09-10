# Example Workflow: Installing MCP with Secure Credential Management

## Scenario

Installing an MCP that requires a GitHub Personal Access Token, using **mcp-secrets-plugin** (from the guide) for secure credential storage.

## Step 1: Install the credential manager MCP

```bash
# Install mcp-secrets-plugin globally
npm install -g mcp-secrets-plugin

# Or clone and install from GitHub
git clone https://github.com/amirshk/mcp-secrets-plugin.git
cd mcp-secrets-plugin
npm install
npm link
```

## Step 2: Configure mcp-secrets-plugin in Claude

Add to Claude's configuration file (`.claude.json` or `claude_desktop_config.json`):

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

## Step 3: Install the MCP that needs credentials

```bash
# Example: Install a GitHub integration MCP
npm install -g @modelcontextprotocol/server-github

# Or any MCP that requires API keys
npm install -g <mcp-that-needs-key>
```

## Step 3.5: Discover required environment variables

### Finding the environment variable NAME (json-key)

**Method 1: Run without credentials to see error**

```bash
$ npx @modelcontextprotocol/server-github
Error: GITHUB_PERSONAL_ACCESS_TOKEN environment variable is required
```

**Method 2: Check the documentation**

```bash
# View NPM package info
npm info @modelcontextprotocol/server-github

# Check GitHub README
open https://github.com/modelcontextprotocol/servers/tree/main/src/github
```

**Method 3: Inspect source code**

```bash
# Search for environment variable usage
grep -r "process.env" node_modules/@modelcontextprotocol/server-github/
# Output: process.env.GITHUB_PERSONAL_ACCESS_TOKEN

# Or for Python MCPs
grep -r "os.environ" /path/to/mcp-server/
```

**Method 4: Check MCP manifest (if available)**

```bash
cat node_modules/@modelcontextprotocol/server-github/mcp.json
```

```json
{
  "requiredEnv": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
  "optionalEnv": ["GITHUB_API_URL"]
}
```

### Finding the VALUE pattern (json-value format)

**Method 1: Check credential manager documentation**

```bash
# For mcp-secrets-plugin
mcp-secrets --help
# Output: Use ${SECRET:name} pattern in configuration

# View examples
cat $(npm root -g)/mcp-secrets-plugin/README.md | grep -A5 "Usage"
```

**Method 2: Test the credential manager's format**

```bash
# Each manager has its own pattern:
mcp-secrets-plugin:     ${SECRET:github_token}
mcpauth:                ${OAUTH:github}
keytar-mcp:             ${KEYTAR:service/account}
vault-mcp:              ${VAULT:secret/path}
aws-secrets:            ${AWS_SECRET:arn}

# Without a manager (direct environment):
Plain value:            "ghp_xxxxxxxxxxxx"
System env:             "${GITHUB_TOKEN}"
```

**Method 3: Check example configurations**

```bash
# Look for example configs in the credential manager
find $(npm root -g)/mcp-secrets-plugin -name "*.example.json" -o -name "*example*"
```

Common patterns by credential manager:
| Manager | Pattern | Example |
|---------|---------|---------|
| mcp-secrets-plugin | `${SECRET:name}` | `${SECRET:github_token}` |
| System environment | Direct value or `${VAR}` | `${GITHUB_TOKEN}` |
| No manager | Plaintext (insecure) | `"ghp_xxxxx"` |

## Step 4: Store credentials securely via mcp-secrets-plugin

```bash
# Using mcp-secrets-plugin CLI
$ mcp-secrets set github_token

# Terminal prompts user (input is masked)
Enter value for 'github_token': ************************************
✓ Credential stored in system keychain

# Alternative: Set with a single command
$ mcp-secrets set github_token --value "ghp_xxxxxxxxxxxxxxxxxxxx"
✓ Credential stored in system keychain
```

### What happens behind the scenes:

1. **mcp-secrets-plugin** uses Python's `keyring` library
2. User inputs the token (masked with asterisks if interactive)
3. The plugin stores the credential using OS-native storage:
   - **macOS**: Keychain Access via Security Framework
   - **Windows**: Windows Credential Manager via Win32 API
   - **Linux**: Secret Service API (GNOME Keyring/KWallet)
4. Credential is encrypted at rest by the OS

## Step 5: Configure the target MCP with credentials

Update Claude's configuration to use the stored secret:

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

## Step 6: Runtime credential injection

When Claude starts the GitHub MCP server:

```python
# mcp-secrets-plugin handles credential retrieval
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

## Step 7: Verification and usage

```bash
# List stored secrets
$ mcp-secrets list
Available secrets:
  - github_token (stored 2025-01-15)

# Test credential retrieval
$ mcp-secrets get github_token
ghp_xxxxxxxxxxxxxxxxxxxx

# Verify MCP is working
$ claude-desktop --test-mcp github
✓ MCP server started successfully
✓ Authentication verified
✓ GitHub API accessible
```

Claude can now use the GitHub MCP:

```
User: "Create an issue in my repo about the bug we discussed"
Claude: I'll create that issue for you using the GitHub integration...
```

## Alternative: Using mcpauth for OAuth-based authentication

For OAuth flows, you can use **mcpauth** (also from the guide):

```bash
# Install mcpauth
npm install -g mcpauth

# Configure mcpauth server
mcpauth init

# Add to Claude configuration
{
  "mcpServers": {
    "mcpauth": {
      "command": "mcpauth",
      "args": ["server"],
      "env": {}
    }
  }
}

# Authenticate via OAuth
$ mcpauth login github

# Opens browser for OAuth flow
Opening browser for authentication...
Please authorize the application.

# After user authorizes:
✓ Authentication successful
✓ Token stored securely in system keychain
✓ Refresh token saved for automatic renewal
```

The OAuth tokens are stored using the same OS keychain mechanisms but with additional metadata:

```python
# mcpauth stores OAuth tokens with metadata
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

## Security features in action

### Credential rotation

```bash
$ mcp-secrets update github_token
⚠ This will replace the existing token
Enter new value: ************************************
✓ Credential updated in system keychain
✓ All MCPs using this credential will get the new token
```

### Credential removal

```bash
$ mcp-secrets delete github_token
⚠ This will remove the credential permanently
Continue? (y/N): y

✓ Removed from system keychain
✓ MCPs using this credential will fail at runtime
```

### Direct keyring access (Python)

```python
# You can also interact with mcp-secrets-plugin programmatically
import keyring

# Store a secret
keyring.set_password("mcp-secrets", "api_key", "secret_value")

# Retrieve a secret
api_key = keyring.get_password("mcp-secrets", "api_key")

# Delete a secret
keyring.delete_password("mcp-secrets", "api_key")
```

## Platform-specific implementation details

### macOS Keychain storage

```bash
# View stored credential (requires user password)
$ security find-generic-password -s "mcp-secrets" -a "github-token" -w
[Keychain Access prompt appears]

# Credential is stored at:
~/Library/Keychains/login.keychain-db
```

### Windows Credential Manager storage

```powershell
# View stored credential
PS> cmdkey /list:mcp-secrets:github-token

# Credential is stored at:
# Control Panel > User Accounts > Credential Manager > Windows Credentials
```

### Linux libsecret storage

```bash
# View stored credential
$ secret-tool lookup service mcp-secrets account github-token

# Credential is stored in:
# GNOME Keyring or KDE Wallet
```

## Error handling

If credential retrieval fails:

```python
# Example from a Python-based MCP server
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

## Cross-platform library usage (keytar alternative)

For Node.js MCPs, use **keytar** (mentioned in the guide):

```javascript
// Using keytar for cross-platform credential storage
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

// Usage in MCP
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

## Benefits of using mcp-secrets-plugin approach

1. **Zero plaintext storage** - Credentials never touch disk unencrypted
2. **OS-level security** - Leverages platform's native keychain/credential manager
3. **Python keyring abstraction** - Unified API across macOS, Windows, and Linux
4. **Simple CLI interface** - Easy credential management via terminal
5. **MCP ecosystem integration** - Designed specifically for MCP servers
6. **Automatic fallback** - Supports multiple credential sources
7. **Production-ready** - Used by multiple MCP implementations

## Real-world implementations from the guide

- **mcp-secrets-plugin**: Cross-platform credential storage using Python keyring
- **mcpauth**: Complete OAuth 2.0 server for MCP authentication
- **keytar**: Node.js library for cross-platform keychain access (664+ projects)
- **Auth0 MCP Server**: Enterprise-grade OAuth implementation example

## Additional resources

- mcp-secrets-plugin: https://github.com/amirshk/mcp-secrets-plugin
- mcpauth: https://github.com/mcpauth/mcpauth
- keytar: https://www.npmjs.com/package/keytar
- MCP Specification: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
