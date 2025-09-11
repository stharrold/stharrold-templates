#!/bin/bash
VS_CODE_MCP="/Users/stharrold/Library/Application Support/Code/User/mcp.json"
CLAUDE_CODE_CONFIG="/Users/stharrold/.claude.json"
CLAUDE_DESKTOP="/Users/stharrold/Library/Application Support/Claude/config.json"

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
