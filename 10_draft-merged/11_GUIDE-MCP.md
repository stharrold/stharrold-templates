# MCP (Model Context Protocol) Setup Guide

## Installation
```bash
# Download guide to home directory
curl -o ~/GUIDE-MCP.md [URL_TO_GUIDE]
# Or save manually from artifact

# Copy to all relevant locations
cp ~/GUIDE-MCP.md ~/.claude/GUIDE-MCP.md
cp ~/GUIDE-MCP.md ~/Documents/GitHub/GUIDE-MCP.md
cp ~/GUIDE-MCP.md ~/Library/Application\ Support/Claude/GUIDE-MCP.md
cp ~/GUIDE-MCP.md ~/Library/Application\ Support/Code/User/GUIDE-MCP.md
```

## Overview

MCP servers enable AI assistants to interact with external tools and data sources. This guide covers configuring MCP servers for VS Code extensions and Claude Code CLI.

**Key Benefits:**
- **Development Velocity**: 40-60% reduction in boilerplate code writing
- **Documentation**: 70% reduction in manual documentation time
- **Testing**: 50% reduction in test setup and maintenance time
- **Infrastructure**: 80% reduction in infrastructure provisioning time

**Important**: Many MCP servers require API tokens. See [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md) for secure credential setup before configuring servers.

## Quick Start Workflow

1. **Setup Credentials**: Follow [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md) for your platform
2. **Add Servers**: Use `mcp-manager.py --add` for interactive setup or `claude mcp add` commands
3. **Validate Setup**: Run `mcp-manager.py --check-credentials` and `mcp-manager.py --list`
4. **Test**: Use `/mcp` in Claude Code to verify servers are working

**For detailed implementation phases, see [GUIDE-IMPLEMENTATION.md](./GUIDE-IMPLEMENTATION.md)**

## Directory Structure

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

## Claude Code CLI Configuration

### 1. Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Add MCP Servers
```bash
# Add servers via CLI
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /Users/stharrold
claude mcp add github npx @modelcontextprotocol/server-github
claude mcp add memory npx @modelcontextprotocol/server-memory

# List configured servers
claude mcp list
```

### 3. Config Locations
Claude Code uses different scopes:
- **User scope**: `~/.claude.json` (global, all projects)
- **Project scope**: `.mcp.json` in project root (shared via git)
- **Local scope**: `~/.claude.json` with project-specific section

### 4. Test in VS Code
- Open Claude Code: Command Palette → "Run Claude Code"
- Type `/mcp` to see configured servers
- Test: "List files in /Users/stharrold"

## VS Code MCP Extension

### 1. Install Extension
Search "MCP" in VS Code marketplace.

### 2. Configure
Edit VS Code MCP configuration file:
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

## Claude Desktop App

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

## Auto-Sync Configuration

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

### Step 2: Create Launch Agent (macOS only)
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

**Note**: Launch Agents are macOS-specific. For Windows/Linux, use the application startup triggers instead.

### Step 3: Add Application Startup Triggers

#### VS Code - Auto-sync on startup
```bash
# Create tasks.json via script
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

#### Claude CLI - Auto-sync on every command
Add to shell config:
```bash
# For bash (~/.bashrc)
alias claude='~/bin/sync-mcp.sh 2>/dev/null && command claude'

# For zsh (~/.zshrc) 
alias claude='~/bin/sync-mcp.sh 2>/dev/null && command claude'
```

#### Claude Desktop - Auto-sync on launch
```bash
# Create launcher script
cat > /Applications/Claude-Synced.command << 'EOF'
#!/bin/bash
~/bin/sync-mcp.sh
open -a "Claude"
exit
EOF
chmod +x /Applications/Claude-Synced.command

# Drag Claude-Synced.command to dock instead of Claude.app
```

### Step 4: Load File Watch Service
```bash
# Always unload first to avoid "Input/output error"
launchctl unload ~/Library/LaunchAgents/com.user.sync-mcp.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.user.sync-mcp.plist
```

Service persists across restarts. Disable: `launchctl unload -w ~/Library/LaunchAgents/com.user.sync-mcp.plist`

## Available MCP Servers

### Tier 1: Essential Core Development Servers

#### Version Control & Code Management

**GitHub MCP Server**
- Repository management, PR analysis, and code review automation
- Issue tracking with natural language issue creation
- CI/CD workflow monitoring and GitHub Actions integration
```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
# Or: claude mcp add github npx @modelcontextprotocol/server-github  # Requires GITHUB_TOKEN
```

**Git MCP Server**
- Core version control operations (commit, branch, merge)
- Repository history analysis and commit searching
- Branch management and conflict resolution assistance

**Filesystem MCP Server**
- Secure file operations with configurable access controls
- Directory structure analysis and organization
```bash
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /path
```

#### Development & Testing Infrastructure

**Sequential Thinking MCP Server**
- Methodical problem-solving through structured thinking processes
- Complex refactoring workflow guidance
```bash
claude mcp add sequential-thinking npx -- -y @modelcontextprotocol/server-sequential-thinking
```

**Playwright MCP Server**
- Web automation and testing using structured accessibility trees
- Cross-browser testing automation
```bash
claude mcp add playwright npx -- @playwright/mcp@latest
```

**Context7 MCP Server**
- Real-time documentation fetching from source repositories
- Version-specific code examples and API documentation
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp
```

#### Database & Data Management

**PostgreSQL MCP Server**
- Natural language to SQL query translation
- Database schema analysis and optimization
```bash
# Multiple providers available
git clone https://github.com/crystaldba/postgres-mcp
```

**SQLite MCP Server**
- Lightweight database operations for development and testing
```bash
claude mcp add sqlite npx @modelcontextprotocol/server-sqlite /path/to/db
```

**Memory MCP Server**
- Session context retention across coding sessions
```bash
claude mcp add memory npx @modelcontextprotocol/server-memory
```

### Tier 2: High-Impact Productivity Servers

#### Code Quality & Security

**Codacy MCP Server**
- Integrated code quality analysis with SAST, secrets detection
- Required by repository guidelines for all file edits
```bash
claude mcp add codacy npx @codacy/codacy-mcp
```

**Sentry MCP Server**
- Error tracking and performance monitoring integration
- Intelligent debugging assistance with error pattern analysis
```bash
claude mcp add --transport sse sentry https://mcp.sentry.dev/mcp
```

#### CI/CD & DevOps

**Azure DevOps MCP Server**
- Comprehensive project management integration
- Build pipeline management and release orchestration
```bash
claude mcp add azure npx @azure-devops/mcp org-name  # Requires AZURE_DEVOPS_PAT
```

**Buildkite MCP Server**
- CI/CD pipeline data exposure and build management
- Build job analysis and failure investigation

#### Infrastructure as Code

**Terraform MCP Server**
- Infrastructure automation with natural language IaC generation
```bash
# Docker deployment recommended
docker run hashicorp/terraform-mcp-server
```

**AWS Cloud Control API MCP Server**
- Natural language AWS resource management
- CRUD operations on AWS services

**Kubernetes MCP Server**
- Container orchestration and cluster management
```bash
git clone https://github.com/Azure/mcp-kubernetes
```

### Tier 3: Advanced Collaboration & Analytics

#### Communication & Collaboration

**Slack MCP Server**
- Secure workspace integration with real Slack data access
```bash
# Via Composio platform
npx @composio/mcp@latest setup slack
```

**Notion MCP Server**
- Documentation management and project requirement tracking
- Task updates directly from Claude Code

**Atlassian MCP Server (Jira & Confluence)**
- Enterprise workflow integration with Jira issue management
- Confluence documentation automation

#### Analytics & Monitoring

**PostHog MCP Server**
- Product analytics and user behavior insights
- Feature flag configuration and management
```bash
claude mcp add --transport sse posthog https://mcp.posthog.com/sse
```

**Memory Bank MCP Server**
- Session context retention across coding sessions
- Decision history tracking and rationale preservation

#### Workflow Automation

**Zapier MCP Server**
- Cross-platform workflow automation across 500+ business applications
- Integration with Gmail, Trello, and productivity tools

**Figma MCP Server**
- Design-to-code conversion and UI component generation
- Design file analysis and component extraction

### Tier 4: Specialized Domain Servers

#### Multi-Database Support

**MongoDB MCP Server**
- NoSQL database operations and document management
- MongoDB Atlas, Community Edition, and Enterprise Advanced support

**Astra DB MCP Server**
- NoSQL collections and distributed database management
- Vector database operations for AI/ML workloads

#### Additional Cloud Platforms

**Azure Services MCP Servers**
- Microsoft cloud ecosystem integration
- Azure Resource Manager operations

**Google Cloud MCP Servers**
- GCP resource management and service integration
- BigQuery data analysis and machine learning operations

#### Design & API Development

**Apidog MCP Server**
- API specification integration with OpenAPI/Swagger support
- Client code generation based on API contracts

**Cal.com MCP Server**
- Scheduling and booking management automation
- Calendar integration and availability management

**Note**: Servers marked with credential requirements need tokens configured. See [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md) for detailed setup instructions.

## Configuration Schema Differences

Different MCP clients use slightly different configuration schemas. Understanding these differences helps when manually editing configs or troubleshooting:

### Claude Code CLI (`~/.claude.json`)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "command",
      "args": ["arg1", "arg2"],
      "env": {
        "VAR": "${env:VAR}"
      }
    }
  }
}
```

### VS Code MCP Extension (`mcp.json`)
```json
{
  "servers": {
    "server-name": {
      "command": "command", 
      "args": ["arg1", "arg2"],
      "env": {
        "VAR": "${env:VAR}"
      }
    }
  }
}
```

### Claude Desktop (`config.json`)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "command",
      "args": ["arg1", "arg2"],
      "env": {
        "VAR": "${env:VAR}"
      }
    }
  }
}
```

### Key Differences

| Feature | Claude Code CLI | VS Code Extension | Claude Desktop |
|---------|----------------|-------------------|----------------|
| Root key | `mcpServers` | `servers` | `mcpServers` |
| Type field | Optional | Optional | Optional |
| Env variables | `${env:VAR}` | `${env:VAR}` | `${env:VAR}` |
| Project scope | Supported | Not supported | Not supported |

### Type Field Usage

The `type` field is automatically managed:
- **stdio**: For command-line tools (default for `command` configs)
- **sse**: For Server-Sent Events URLs (default for `url` configs)

The sync script (`sync-mcp.sh`) automatically adds appropriate `type` fields when syncing between platforms.

## Unified MCP Management Workflow

### Using mcp-manager.py (Recommended)

The `mcp-manager.py` tool provides cross-platform management of all MCP configurations:

```bash
# List all servers across all platforms
/usr/bin/python3 mcp-manager.py --list

# Add a new server interactively  
/usr/bin/python3 mcp-manager.py --add

# Validate credentials
/usr/bin/python3 mcp-manager.py --check-credentials

# Remove servers interactively
/usr/bin/python3 mcp-manager.py --remove

# Create backups
/usr/bin/python3 mcp-manager.py --backup-only
```

### Using Claude Code CLI

```bash
# Add servers to Claude Code specifically
claude mcp add github npx @modelcontextprotocol/server-github
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /path

# List Claude Code servers
claude mcp list

# Remove servers
claude mcp remove github
```

### Complete Setup Example

```bash
# 1. Setup credentials (choose your platform)
# macOS: Follow GUIDE-CREDENTIALS.md keychain setup
# Windows: Follow GUIDE-CREDENTIALS.md credential manager setup

# 2. Add GitHub server using mcp-manager.py
/usr/bin/python3 mcp-manager.py --add
# Enter: github, 1 (NPX), @modelcontextprotocol/server-github
# Add GITHUB_TOKEN env var: ${env:GITHUB_TOKEN}
# Choose: All configurations

# 3. Validate everything is working
/usr/bin/python3 mcp-manager.py --check-credentials
/usr/bin/python3 mcp-manager.py --list

# 4. Test in Claude Code
# Type: /mcp
# Should see: github server with tools available
```

## Troubleshooting

### MCP Not Found in Claude Code
```bash
# List all configurations to see what's available
/usr/bin/python3 mcp-manager.py --list

# Check specific config file
cat ~/.claude.json | jq .mcpServers

# Add server using unified tool
/usr/bin/python3 mcp-manager.py --add

# Or add using Claude CLI directly
claude mcp add test npx @modelcontextprotocol/server-filesystem /tmp
```

### Server Connection Failed
```bash
# Validate credentials first
/usr/bin/python3 mcp-manager.py --check-credentials

# Test server manually
npx @modelcontextprotocol/server-filesystem /path

# Check logs
tail -f /tmp/sync-mcp.error.log
```

Common causes:
- Missing API tokens (see [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md))
- Incorrect server paths or commands
- Network connectivity issues

### View MCP Tools
In Claude Code:
1. Type `/mcp`
2. Press Enter on server name
3. See available tools

### Sync Issues
```bash
# Check service
launchctl list | grep sync-mcp

# Reload (unload first to avoid errors)
launchctl unload ~/Library/LaunchAgents/com.user.sync-mcp.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.user.sync-mcp.plist

# Verify plist syntax
plutil -lint ~/Library/LaunchAgents/com.user.sync-mcp.plist

# Run manually
~/bin/sync-mcp.sh
```

### Import from Claude Desktop
```bash
# If desktop config exists at standard location
claude mcp add-from-claude-desktop

# Manual import if needed (adjust path for your platform)
# macOS
jq '.mcpServers' "$HOME/Library/Application Support/Claude/config.json" | \
  jq -r 'to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"'

# Windows  
jq '.mcpServers' "$HOME/AppData/Roaming/Claude/config.json" | \
  jq -r 'to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"'

# Linux
jq '.mcpServers' "$HOME/.config/claude/config.json" | \
  jq -r 'to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"'
```

## Cross-System Compatibility

For shared configs:
- Windows paths fail silently on macOS
- Use environment variables for system-specific paths
- Sync script removes `type` fields automatically

## File Locations Summary

### Universal (All Platforms)
```bash
~/.claude.json                        # Claude Code CLI user config
./.mcp.json                          # Claude Code CLI project config
~/bin/sync-mcp.sh                    # Sync script
```

### Platform-Specific Configurations

#### macOS
```bash
~/Library/Application Support/Code/User/mcp.json           # VS Code MCP
~/Library/Application Support/Claude/config.json           # Claude Desktop
~/Library/LaunchAgents/com.user.sync-mcp.plist            # Auto-run service
```

#### Windows
```bash
~/AppData/Roaming/Code/User/mcp.json                       # VS Code MCP
~/AppData/Roaming/Claude/config.json                       # Claude Desktop
```

#### Linux
```bash
~/.config/Code/User/mcp.json                               # VS Code MCP
~/.config/claude/config.json                               # Claude Desktop
```

### Logs (All Platforms)
```bash
/tmp/sync-mcp.log                                          # Sync output
/tmp/sync-mcp.error.log                                    # Errors
```

## Security Considerations

### Recent Vulnerabilities

**CVE-2025-52882 (Claude Code Extension)**
- **Severity**: High (CVSS 8.8)
- **Impact**: WebSocket authentication bypass allowing unauthorized MCP server access
- **Status**: Fully resolved in versions 1.0.24+
- **Mitigation**: Ensure Claude Code extensions are updated to latest versions

**PostgreSQL MCP Server SQL Injection**
- **Impact**: Bypassing read-only restrictions and arbitrary SQL execution
- **Mitigation**: Use Postgres MCP Pro with proper access controls

### Security Best Practices

- Use OS-native credential stores (Keychain on macOS, Credential Manager on Windows)
- Configure MCP servers with principle of least privilege
- Regular credential rotation and access auditing
- Integration with Sentry for error tracking and security incident detection
- Codacy integration for continuous security scanning

For detailed credential security setup, see [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md).

## Monitoring & Maintenance

### Health Monitoring
- Regular MCP server availability and performance checks
- Token expiration monitoring and automated renewal
- Security vulnerability scanning and patch management
- Usage analytics and optimization recommendations

### Update Management
- Automated MCP server version monitoring
- Staged rollout of server updates
- Rollback procedures for problematic updates
- Change impact assessment for server modifications

### Performance Optimization
- Regular review of server usage patterns
- Optimization of token limits and rate limiting
- Performance tuning based on development workflow metrics
- Removal of unused or underutilized servers

## Best Practices

1. **Secure Credentials**: Follow [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md) for secure token storage using OS credential stores
2. **Permissions**: Limit filesystem access to specific directories
3. **Testing**: Use `/mcp` in Claude Code to verify servers
4. **Backups**: Sync script creates timestamped backups
5. **Validation**: Use `mcp-manager.py --check-credentials` to verify credential setup
6. **Implementation Strategy**: Follow [GUIDE-IMPLEMENTATION.md](./GUIDE-IMPLEMENTATION.md) for phased rollout

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [MCP Community Servers](https://github.com/modelcontextprotocol/servers)
- [Implementation Strategy Guide](./GUIDE-IMPLEMENTATION.md)
- [Credential Security Guide](./GUIDE-CREDENTIALS.md)