#!/bin/bash

# MCP Server Management Script for Claude Code
# Lists and removes all configured MCP servers from both global and project levels

# Usage function
show_usage() {
    echo "Usage: $0 [CONFIG_FILE]"
    echo ""
    echo "Manages MCP servers in Claude Code configuration files."
    echo ""
    echo "Arguments:"
    echo "  CONFIG_FILE    Path to the configuration file (optional)"
    echo "                 Default: \$HOME/.claude.json"
    echo ""
    echo "Examples:"
    echo "  $0                                                    # Use default ~/.claude.json"
    echo "  $0 ~/.claude.json                                    # Specify Claude Code config"
    echo "  $0 '\$HOME/Library/Application Support/Claude/config.json'"
    echo "  $0 '\$HOME/Library/Application Support/Code/User/mcp.json'"
    echo ""
}

# Handle command line arguments
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# Set config file path
if [ -n "$1" ]; then
    CONFIG_FILE="$1"
else
    CONFIG_FILE="$HOME/.claude.json"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== MCP Server Management for Claude Code ===${NC}"
echo -e "${BLUE}Using configuration file: $CONFIG_FILE${NC}\n"

# Validate config file
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file not found at $CONFIG_FILE${NC}"
    echo "Please check that the file exists and the path is correct."
    exit 1
fi

if [ ! -r "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file at $CONFIG_FILE is not readable${NC}"
    echo "Please check file permissions."
    exit 1
fi

# Basic JSON validation
if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
    echo -e "${RED}Error: Configuration file at $CONFIG_FILE is not valid JSON${NC}"
    echo "Please check the file format."
    exit 1
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: 'jq' is required for this script.${NC}"
    echo "Please install jq:"
    echo "  macOS: brew install jq"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    exit 1
fi

# List current MCP servers
echo -e "${GREEN}Current MCP servers:${NC}"

# Collect all servers with their paths
declare -a SERVER_LIST
declare -a SERVER_PATHS
SERVER_COUNT=0

# List global MCP servers
GLOBAL_SERVERS=$(jq -r '.mcpServers // {} | keys[]' "$CONFIG_FILE" 2>/dev/null)
if [ -n "$GLOBAL_SERVERS" ]; then
    echo -e "\n${BLUE}Global MCP Servers:${NC}"
    echo "$GLOBAL_SERVERS" | while read -r server; do
        echo "  [$((++SERVER_COUNT))] $server"
        # Show command or URL
        COMMAND=$(jq -r ".mcpServers.\"$server\".command // empty" "$CONFIG_FILE" 2>/dev/null)
        URL=$(jq -r ".mcpServers.\"$server\".url // empty" "$CONFIG_FILE" 2>/dev/null)
        TYPE=$(jq -r ".mcpServers.\"$server\".type // empty" "$CONFIG_FILE" 2>/dev/null)
        if [ -n "$COMMAND" ]; then
            echo "      Command: $COMMAND"
        elif [ -n "$URL" ]; then
            echo "      URL: $URL"
        fi
        [ -n "$TYPE" ] && echo "      Type: $TYPE"
    done
fi

# List project-specific MCP servers
PROJECTS=$(jq -r '.projects // {} | keys[]' "$CONFIG_FILE" 2>/dev/null)
if [ -n "$PROJECTS" ]; then
    echo "$PROJECTS" | while read -r project; do
        PROJECT_SERVERS=$(jq -r ".projects.\"$project\".mcpServers // {} | keys[]" "$CONFIG_FILE" 2>/dev/null)
        if [ -n "$PROJECT_SERVERS" ]; then
            echo -e "\n${BLUE}Project: $project${NC}"
            echo "$PROJECT_SERVERS" | while read -r server; do
                echo "  [$((++SERVER_COUNT))] $server"
                # Show command or URL
                COMMAND=$(jq -r ".projects.\"$project\".mcpServers.\"$server\".command // empty" "$CONFIG_FILE" 2>/dev/null)
                URL=$(jq -r ".projects.\"$project\".mcpServers.\"$server\".url // empty" "$CONFIG_FILE" 2>/dev/null)
                TYPE=$(jq -r ".projects.\"$project\".mcpServers.\"$server\".type // empty" "$CONFIG_FILE" 2>/dev/null)
                if [ -n "$COMMAND" ]; then
                    echo "      Command: $COMMAND"
                elif [ -n "$URL" ]; then
                    echo "      URL: $URL"
                fi
                [ -n "$TYPE" ] && echo "      Type: $TYPE"
            done
        fi
    done
fi

# Check if any servers exist
TOTAL_SERVERS=$(jq -r '
    ((.mcpServers // {}) | length) + 
    ((.projects // {} | to_entries | map(.value.mcpServers // {} | length) | add) // 0)
' "$CONFIG_FILE")

if [ "$TOTAL_SERVERS" -eq 0 ]; then
    echo "No MCP servers configured in $CONFIG_FILE."
    exit 0
fi

# Removal options
echo -e "\n${YELLOW}Select removal option:${NC}"
echo "  [a] Remove ALL servers"
echo "  [i] Remove servers incrementally (select which ones)"
echo "  [N] None - exit without changes (default)"
echo
read -p "Your choice [a/i/N]: " -r CHOICE
CHOICE=${CHOICE:-N}

case "$CHOICE" in
    [aA])
        # Remove all servers
        echo -e "\n${YELLOW}This will remove ALL MCP servers from Claude Code.${NC}"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Create backup
            BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
            echo -e "${GREEN}Creating backup: $BACKUP_FILE${NC}"
            cp "$CONFIG_FILE" "$BACKUP_FILE"
            
            # Remove all MCP servers
            jq 'del(.mcpServers) | 
                if .projects then 
                    .projects |= with_entries(.value |= del(.mcpServers))
                else . end' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
            
            echo -e "${GREEN}✓ All MCP servers have been removed.${NC}"
            echo -e "${GREEN}✓ Backup saved at: $BACKUP_FILE${NC}"
            echo -e "\n${YELLOW}Note: Restart Claude Code for changes to take effect.${NC}"
            echo -e "To restore: ${GREEN}cp $BACKUP_FILE $CONFIG_FILE${NC}"
        else
            echo -e "${RED}Operation cancelled.${NC}"
        fi
        ;;
        
    [iI])
        # Incremental removal
        echo -e "\n${GREEN}Incremental removal mode${NC}"
        
        # Create backup first
        BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}Creating backup: $BACKUP_FILE${NC}"
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        
        # Build server list for selection
        declare -a ALL_SERVERS
        declare -a ALL_PATHS
        INDEX=1
        
        # Add global servers
        if [ -n "$GLOBAL_SERVERS" ]; then
            echo "$GLOBAL_SERVERS" | while read -r server; do
                ALL_SERVERS[$INDEX]="$server"
                ALL_PATHS[$INDEX]="global"
                ((INDEX++))
            done
        fi
        
        # Add project servers
        if [ -n "$PROJECTS" ]; then
            echo "$PROJECTS" | while read -r project; do
                PROJECT_SERVERS=$(jq -r ".projects.\"$project\".mcpServers // {} | keys[]" "$CONFIG_FILE" 2>/dev/null)
                if [ -n "$PROJECT_SERVERS" ]; then
                    echo "$PROJECT_SERVERS" | while read -r server; do
                        ALL_SERVERS[$INDEX]="$server"
                        ALL_PATHS[$INDEX]="$project"
                        ((INDEX++))
                    done
                fi
            done
        fi
        
        # Interactive removal loop
        TEMP_CONFIG="$CONFIG_FILE"
        while true; do
            echo -e "\n${YELLOW}Enter server name to remove (or 'done' to finish):${NC}"
            read -p "> " SERVER_NAME
            
            if [ "$SERVER_NAME" = "done" ] || [ -z "$SERVER_NAME" ]; then
                break
            fi
            
            # Check if it's a global server
            HAS_GLOBAL=$(jq -r ".mcpServers.\"$SERVER_NAME\" // empty" "$TEMP_CONFIG")
            if [ -n "$HAS_GLOBAL" ]; then
                jq "del(.mcpServers.\"$SERVER_NAME\")" "$TEMP_CONFIG" > "${TEMP_CONFIG}.tmp" && mv "${TEMP_CONFIG}.tmp" "$TEMP_CONFIG"
                echo -e "${GREEN}✓ Removed global server: $SERVER_NAME${NC}"
            else
                # Check projects
                FOUND=false
                echo "$PROJECTS" | while read -r project; do
                    HAS_PROJECT=$(jq -r ".projects.\"$project\".mcpServers.\"$SERVER_NAME\" // empty" "$TEMP_CONFIG")
                    if [ -n "$HAS_PROJECT" ]; then
                        jq ".projects.\"$project\".mcpServers |= del(.\"$SERVER_NAME\")" "$TEMP_CONFIG" > "${TEMP_CONFIG}.tmp" && mv "${TEMP_CONFIG}.tmp" "$TEMP_CONFIG"
                        echo -e "${GREEN}✓ Removed from project '$project': $SERVER_NAME${NC}"
                        FOUND=true
                        break
                    fi
                done
                
                if [ "$FOUND" = false ]; then
                    echo -e "${RED}Server '$SERVER_NAME' not found${NC}"
                fi
            fi
        done
        
        echo -e "\n${GREEN}✓ Individual removal complete.${NC}"
        echo -e "${GREEN}✓ Backup saved at: $BACKUP_FILE${NC}"
        echo -e "\n${YELLOW}Note: Restart Claude Code for changes to take effect.${NC}"
        echo -e "To restore: ${GREEN}cp $BACKUP_FILE $CONFIG_FILE${NC}"
        ;;
        
    *)
        # Default: No action
        echo -e "${GREEN}No changes made. Exiting.${NC}"
        exit 0
        ;;
esac

# Final verification
if [ "$CHOICE" != "N" ] && [ "$CHOICE" != "n" ]; then
    REMAINING=$(jq -r '
        ((.mcpServers // {}) | length) + 
        ((.projects // {} | to_entries | map(.value.mcpServers // {} | length) | add) // 0)
    ' "$CONFIG_FILE")
    echo -e "\n${BLUE}Remaining MCP servers: $REMAINING${NC}"
fi