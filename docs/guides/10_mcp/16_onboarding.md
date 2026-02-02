---
title: MCP Onboarding Quickstart
version: 1.0
updated: 2026-02-01
parent: ./CLAUDE.md
related:
  - ./11_setup.md
  - ./12_servers.md
  - ./15_troubleshooting.md
---

# MCP Onboarding Quickstart

Get your first MCP server running in under 5 minutes. This guide covers the shortest path from zero to a working MCP setup, then links to detailed guides for further configuration.

## Prerequisites

- **Node.js 18+**: Required for Claude Code and MCP servers
- **Claude Code CLI**: Installed and authenticated (see below)
- **API credentials** (optional): Some servers need tokens. See [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md) when ready.

## Step 1: Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Launch Claude Code in any project directory to authenticate:

```bash
cd ~/my-project
claude
```

Follow the on-screen prompts to complete authentication.

> For detailed authentication options (subscription vs. API billing, enterprise SSO), see [11_setup.md](./11_setup.md#authentication-options).

## Step 2: Add Your First MCP Server

The **filesystem** server is the simplest starting point -- no API keys required.

```bash
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem ~/
```

This gives Claude Code read/write access to files in your home directory.

### Platform-Specific Notes

**macOS:**
```bash
# Ensure Node.js is installed via Homebrew or nvm
brew install node
# Or: nvm install 18

# Add the filesystem server
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem ~/
```

**Windows (PowerShell):**
```powershell
# Ensure Node.js is installed (download from nodejs.org or use winget)
winget install OpenJS.NodeJS.LTS

# Add the filesystem server
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem $HOME
```

**Linux:**
```bash
# Ensure Node.js is installed via package manager or nvm
# Ubuntu/Debian:
sudo apt install nodejs npm
# Or use nvm:
nvm install 18

# Add the filesystem server
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem ~/
```

## Step 3: Verify the Setup

1. Open Claude Code:
   ```bash
   claude
   ```

2. Check that the server is registered:
   ```bash
   /mcp
   ```
   You should see `filesystem` listed with a `connected` status.

3. Test it with a prompt:
   ```
   List the files in my home directory
   ```

If the server responds with a file listing, your MCP setup is working.

## Step 4: Add More Servers (Optional)

Once the filesystem server is confirmed working, add servers for your workflow:

```bash
# GitHub integration (requires GITHUB_TOKEN)
claude mcp add github npx @modelcontextprotocol/server-github

# Persistent memory across sessions
claude mcp add memory npx @modelcontextprotocol/server-memory
```

List all configured servers at any time:

```bash
claude mcp list
```

> For the full server catalog organized by tier, see [12_servers.md](./12_servers.md).

## Troubleshooting Quick Checks

If `/mcp` does not show your server as connected:

1. **Check Node.js version**: `node --version` (must be 18+)
2. **Check npx is available**: `npx --version`
3. **Re-add the server**: `claude mcp remove filesystem && claude mcp add filesystem npx @modelcontextprotocol/server-filesystem ~/`
4. **Restart Claude Code**: Exit and relaunch `claude`

> For detailed troubleshooting, see [15_troubleshooting.md](./15_troubleshooting.md).

## Next Steps

Now that MCP is running, explore these guides based on your needs:

| Goal | Guide |
|------|-------|
| Full installation details and auto-sync setup | [11_setup.md](./11_setup.md) |
| Browse available MCP servers by category | [12_servers.md](./12_servers.md) |
| Optimize context and token usage | [13_context-management.md](./13_context-management.md) |
| Set up enterprise search and RAG | [14_enterprise-search.md](./14_enterprise-search.md) |
| Diagnose connection or configuration issues | [15_troubleshooting.md](./15_troubleshooting.md) |

---

*Onboarding complete. You now have a working MCP server connected to Claude Code.*
