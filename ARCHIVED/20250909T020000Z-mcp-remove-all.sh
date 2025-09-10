#!/bin/bash

# MCP Server Management Script for Claude Code
# Lists and removes all configured MCP servers

CONFIG_FILE="$HOME/.config/claude-code/mcp-servers.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== MCP Server Management for Claude Code ===${NC}\n"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Warning: Configuration file not found at $CONFIG_FILE${NC}"
    echo "No MCP servers configured or Claude Code not installed."
    exit 1
fi

# Create backup before modification
BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}Creating backup: $BACKUP_FILE${NC}"
cp "$CONFIG_FILE" "$BACKUP_FILE"

# List current MCP servers
echo -e "\n${GREEN}Current MCP servers:${NC}"
if command -v jq &> /dev/null; then
    # If jq is installed, use it for pretty printing
    SERVERS=$(jq -r 'keys[]' "$CONFIG_FILE" 2>/dev/null)
    if [ -z "$SERVERS" ]; then
        echo "No MCP servers configured."
    else
        echo "$SERVERS" | while read -r server; do
            echo "  - $server"
            # Show command if available
            COMMAND=$(jq -r ".\"$server\".command // empty" "$CONFIG_FILE" 2>/dev/null)
            if [ -n "$COMMAND" ]; then
                echo "    Command: $COMMAND"
            fi
        done
    fi
else
    # Fallback if jq is not installed
    echo -e "${YELLOW}Note: Install 'jq' for better JSON parsing${NC}"
    cat "$CONFIG_FILE"
fi

# Confirm removal
echo -e "\n${YELLOW}This will remove ALL MCP servers from Claude Code.${NC}"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Remove all servers by replacing with empty object
    echo "{}" > "$CONFIG_FILE"
    echo -e "${GREEN}✓ All MCP servers have been removed.${NC}"
    echo -e "${GREEN}✓ Backup saved at: $BACKUP_FILE${NC}"
    
    # Verify removal
    if [ -f "$CONFIG_FILE" ]; then
        FILE_SIZE=$(stat -f%z "$CONFIG_FILE" 2>/dev/null || stat -c%s "$CONFIG_FILE" 2>/dev/null)
        if [ "$FILE_SIZE" -le 5 ]; then
            echo -e "${GREEN}✓ Configuration file successfully cleared.${NC}"
        fi
    fi
    
    echo -e "\n${YELLOW}Note: You may need to restart Claude Code for changes to take effect.${NC}"
    echo -e "To restore, run: ${GREEN}cp $BACKUP_FILE $CONFIG_FILE${NC}"
else
    echo -e "${RED}Operation cancelled. No changes made.${NC}"
    rm "$BACKUP_FILE"
    exit 0
fi