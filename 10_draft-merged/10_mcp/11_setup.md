---
title: MCP Installation & Setup
version: 3.1
updated: 2025-09-12
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