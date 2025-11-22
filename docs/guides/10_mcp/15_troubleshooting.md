---
title: MCP Troubleshooting & Maintenance
version: 3.1
updated: 2025-09-12
parent: ./CLAUDE.md
related:
  - ./11_setup.md
  - ../20_credentials/CLAUDE.md
  - ./13_context-management.md
---

# MCP Troubleshooting & Maintenance

Comprehensive troubleshooting guide for MCP server issues, security considerations, monitoring strategies, and maintenance best practices.

## Common Issues & Solutions

### MCP Not Found in Claude Code

**Symptoms:**
- `/mcp` command shows no servers
- Claude Code appears to ignore MCP configurations
- "No MCP servers available" messages

**Diagnosis:**
```bash
# List all configurations to see what's available
/usr/bin/python3 mcp_manager.py --list

# Check specific config file
cat ~/.claude.json | jq .mcpServers

# Verify Claude Code can access config
claude mcp list
```

**Solutions:**
```bash
# Add server using unified tool
/usr/bin/python3 mcp_manager.py --add

# Or add using Claude CLI directly
claude mcp add test npx @modelcontextprotocol/server-filesystem /tmp

# Restart Claude Code completely
# Command Palette → "Developer: Reload Window"
```

### Server Connection Failed

**Symptoms:**
- "Server connection failed" errors
- MCP servers appear in list but don't respond
- Timeout errors during tool execution

**Diagnosis:**
```bash
# Validate credentials first
/usr/bin/python3 mcp_manager.py --check-credentials

# Test server manually
npx @modelcontextprotocol/server-filesystem /path

# Check logs for errors
tail -f /tmp/sync-mcp.error.log
```

**Common Causes & Solutions:**
1. **Missing API tokens** → Follow [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md)
2. **Incorrect server paths or commands** → Verify installation with `npx` command
3. **Network connectivity issues** → Test with `curl` or `ping`
4. **Permission issues** → Check file/directory access permissions

### View MCP Tools

**In Claude Code:**
1. Type `/mcp`
2. Press Enter on server name
3. See available tools and their descriptions

**Command Line Verification:**
```bash
# List configured servers
claude mcp list

# Test specific server
claude /mcp
# Select server to see tools
```

### Auto-Sync Issues

**Service Management (macOS):**
```bash
# Check service status
launchctl list | grep sync-mcp

# Reload service (unload first to avoid errors)
launchctl unload ~/Library/LaunchAgents/com.user.sync-mcp.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.user.sync-mcp.plist

# Verify plist syntax
plutil -lint ~/Library/LaunchAgents/com.user.sync-mcp.plist

# Run sync manually to test
~/bin/sync-mcp.sh
```

**Common Sync Issues:**
- **File permissions**: Ensure sync script is executable (`chmod +x ~/bin/sync-mcp.sh`)
- **jq dependency**: Install jq with `brew install jq` (macOS) or equivalent
- **Path conflicts**: Use absolute paths in scripts and configurations
- **Lock file issues**: Remove `/tmp/mcp-merge.json` if sync hangs

### Import from Claude Desktop

**Automated Import:**
```bash
# If desktop config exists at standard location
claude mcp add-from-claude-desktop
```

**Manual Import by Platform:**
```bash
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

### Path Compatibility Issues

**Problems:**
- Windows paths fail silently on macOS/Linux
- Different directory structures between platforms
- Environment variable expansion differences

**Solutions:**
```bash
# Use environment variables for system-specific paths
"env": {
  "DATA_PATH": "${env:HOME}/data"  # Works across platforms
}

# Platform detection in scripts
case "$(uname -s)" in
    Darwin)  DATA_PATH="$HOME/Library/Application Support" ;;
    Linux)   DATA_PATH="$HOME/.config" ;;
    MINGW*)  DATA_PATH="$HOME/AppData/Roaming" ;;
esac
```

### Configuration Synchronization

**Shared Configuration Strategy:**
- Use relative paths where possible
- Leverage environment variables for system-specific values
- Implement platform detection in sync scripts
- Test configurations on all target platforms

## File Locations Reference

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

### Log Files (All Platforms)
```bash
/tmp/sync-mcp.log                                          # Sync output
/tmp/sync-mcp.error.log                                    # Error logs
```

## Security Considerations

### Recent Vulnerabilities

**CVE-2025-52882 (Claude Code Extension)**
- **Severity**: High (CVSS 8.8)
- **Impact**: WebSocket authentication bypass allowing unauthorized MCP server access
- **Status**: Fully resolved in versions 1.0.24+
- **Action Required**: Update Claude Code extensions to latest versions

**PostgreSQL MCP Server SQL Injection**
- **Impact**: Bypassing read-only restrictions and arbitrary SQL execution
- **Mitigation**: Use Postgres MCP Pro with proper access controls
- **Best Practice**: Use parameterized queries and restricted database users

### Security Best Practices

**Credential Management:**
- Use OS-native credential stores (Keychain on macOS, Credential Manager on Windows)
- Never store credentials in plain text configuration files
- Implement regular credential rotation schedules
- Monitor for credential exposure in logs or error messages

**Access Control:**
- Configure MCP servers with principle of least privilege
- Limit filesystem access to specific directories needed for development
- Use read-only access where possible
- Implement network access restrictions for remote servers

**Monitoring Integration:**
- Integration with Sentry for error tracking and security incident detection
- Codacy integration for continuous security scanning
- Regular security vulnerability scanning
- Automated alerting for suspicious activity patterns

For detailed credential security setup, see [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md).

## Monitoring & Maintenance

### Health Monitoring

**Automated Checks:**
```bash
# Create health check script
cat > ~/bin/mcp-health-check.sh << 'EOF'
#!/bin/bash
echo "=== MCP Health Check $(date) ==="

# Check server availability
claude mcp list | grep -q "filesystem" || echo "WARNING: filesystem server missing"

# Check credentials
/usr/bin/python3 mcp_manager.py --check-credentials

# Check sync service (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    launchctl list | grep -q sync-mcp || echo "WARNING: sync service not running"
fi

# Check log files for errors
if [[ -f /tmp/sync-mcp.error.log ]]; then
    recent_errors=$(tail -100 /tmp/sync-mcp.error.log | grep -c "ERROR")
    if [[ $recent_errors -gt 0 ]]; then
        echo "WARNING: $recent_errors recent errors in sync log"
    fi
fi

echo "=== Health Check Complete ==="
EOF

chmod +x ~/bin/mcp-health-check.sh
```

**Performance Monitoring:**
- Track MCP server response times
- Monitor token usage and rate limits
- Check for memory leaks in long-running servers
- Analyze usage patterns for optimization opportunities

### Update Management

**Server Version Monitoring:**
```bash
# Check for outdated MCP servers
npm outdated -g | grep "@modelcontextprotocol"

# Update specific server
npm update -g @modelcontextprotocol/server-filesystem
```

**Update Strategy:**
1. **Development Environment**: Test updates immediately
2. **Staging Environment**: Deploy after dev validation
3. **Production Environment**: Staged rollout with rollback plan

**Rollback Procedures:**
```bash
# Restore from backup if needed
cp ~/.claude.json.backup ~/.claude.json

# Restart services
~/bin/sync-mcp.sh
```

### Performance Optimization

**Regular Maintenance Tasks:**
```bash
# Clean up old log files
find /tmp -name "*mcp*" -type f -mtime +7 -delete

# Review server usage patterns
grep "server usage" ~/.claude/logs/* | sort | uniq -c

# Remove unused servers
claude mcp remove unused-server-name
```

**Optimization Strategies:**
- Regular review of server usage patterns
- Optimization of token limits and rate limiting
- Performance tuning based on development workflow metrics
- Removal of unused or underutilized servers

## Known Issues & Common Pitfalls

### Current Known Issues
- [ ] **Sync script fails on network drives**: Use local filesystem for config files
- [ ] **MCP servers timeout with large datasets**: Implement pagination for data-heavy operations
- [ ] **VS Code extension conflicts**: Disable conflicting extensions that intercept MCP commands

### Common Pitfalls

**Configuration Issues:**
- MCP server paths must be absolute or use environment variables
- JSON syntax errors in config files cause silent failures
- Mixed platform path separators break cross-platform sync

**Performance Issues:**
- Too many concurrent MCP servers can cause resource exhaustion
- Large MCP responses can exceed Claude Code token limits
- Network latency affects remote MCP server performance

**Integration Issues:**
- Git worktree paths must be correctly configured for multi-instance orchestration
- Environment variables must be available to all applications (Code, Desktop, CLI)
- File permissions can prevent automatic sync operations

## Maintenance Schedule

### Daily Tasks
- Check error logs: `tail -f /tmp/sync-mcp.error.log`
- Monitor MCP server performance in Claude Code
- Verify credential expiration status

### Weekly Tasks
- Update MCP servers: `npm update -g @modelcontextprotocol/*`
- Run comprehensive health check: `~/bin/mcp-health-check.sh`
- Review and clean log files

### Monthly Tasks
- Security audit of MCP configurations and credentials
- Performance analysis and optimization review
- Documentation update for configuration changes
- Backup validation and restore testing

## Best Practices Summary

1. **Secure Credentials**: Follow [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md) for secure token storage
2. **Least Privilege**: Limit filesystem and network access to minimum required
3. **Regular Testing**: Use `/mcp` in Claude Code to verify server functionality
4. **Automated Backups**: Sync script creates timestamped configuration backups
5. **Credential Validation**: Use `mcp_manager.py --check-credentials` regularly
6. **Staged Rollouts**: Test configuration changes in development before production
7. **Performance Monitoring**: Track server response times and resource usage
8. **Documentation**: Maintain current documentation for team configurations

## Resources & Support

### Documentation
- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [MCP Community Servers](https://github.com/modelcontextprotocol/servers)

### Internal Resources
- [Implementation Strategy](../30_implementation/CLAUDE.md)
- [Credential Security](../20_credentials/CLAUDE.md)
- [Context Management](./13_context-management.md)

### Community Support
- [MCP GitHub Discussions](https://github.com/modelcontextprotocol/python-sdk/discussions)
- [Claude Code Community](https://community.anthropic.com/)
- [Stack Overflow - MCP Tag](https://stackoverflow.com/questions/tagged/model-context-protocol)

---

*Effective troubleshooting requires systematic diagnosis, comprehensive monitoring, and proactive maintenance. Document solutions for recurring issues to build team knowledge.*