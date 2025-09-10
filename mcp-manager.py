#!/usr/bin/env python3
"""
Multi-platform MCP server management tool.
Manages MCP servers across Claude Code CLI, VS Code MCP Extension, and Claude Desktop.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


def get_platform_config_paths() -> Dict[str, Path]:
    """Get platform-specific configuration file paths."""
    system = platform.system().lower()
    home = Path.home()
    
    if system == "darwin":  # macOS
        return {
            "claude_code": home / ".claude.json",
            "vscode": home / "Library" / "Application Support" / "Code" / "User" / "mcp.json",
            "claude_desktop": home / "Library" / "Application Support" / "Claude" / "config.json"
        }
    elif system == "windows":
        return {
            "claude_code": home / ".claude.json",
            "vscode": home / "AppData" / "Roaming" / "Code" / "User" / "mcp.json",
            "claude_desktop": home / "AppData" / "Roaming" / "Claude" / "config.json"
        }
    else:  # Linux and others
        return {
            "claude_code": home / ".claude.json",
            "vscode": home / ".config" / "Code" / "User" / "mcp.json",
            "claude_desktop": home / ".config" / "claude" / "config.json"
        }


def validate_credentials() -> Dict[str, bool]:
    """Validate common MCP server credentials."""
    credentials = {}
    
    # Check common environment variables
    common_env_vars = [
        'GITHUB_TOKEN',
        'AZURE_DEVOPS_PAT', 
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY'
    ]
    
    for var in common_env_vars:
        value = os.getenv(var)
        credentials[var] = bool(value and len(value.strip()) > 0)
    
    return credentials


def validate_platform_credentials() -> Dict[str, bool]:
    """Validate platform-specific credential storage."""
    system = platform.system().lower()
    results = {}
    
    if system == "darwin":
        # Check macOS Keychain
        try:
            for service in ['GITHUB_TOKEN', 'AZURE_DEVOPS_PAT']:
                cmd = ['security', 'find-generic-password', '-a', os.getenv('USER', ''), '-s', service, '-w']
                result = subprocess.run(cmd, capture_output=True, text=True)
                results[f"keychain_{service}"] = result.returncode == 0
        except Exception:
            results["keychain_error"] = True
            
    elif system == "windows":
        # Check Windows Credential Manager
        try:
            cmd = ['powershell', '-Command', 'Get-Module -ListAvailable -Name CredentialManager']
            result = subprocess.run(cmd, capture_output=True, text=True)
            results["credential_manager_module"] = result.returncode == 0
        except Exception:
            results["credential_manager_error"] = True
    
    return results


class MCPConfig:
    """Represents an MCP configuration file."""
    
    def __init__(self, name: str, path: Path, description: str):
        self.name = name
        self.path = path  
        self.description = description
        self.exists = path.exists()
        self.data: Optional[Dict] = None
        self.servers: List[Dict] = []
        
    def load(self) -> bool:
        """Load and validate the configuration file."""
        if not self.exists:
            return False
            
        try:
            with open(self.path, 'r') as f:
                self.data = json.load(f)
            self._extract_servers()
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading {self.path}: {e}")
            return False
            
    def _extract_servers(self) -> None:
        """Extract MCP servers from the configuration data."""
        if not self.data:
            return
            
        self.servers = []
        
        # Handle global mcpServers
        if 'mcpServers' in self.data:
            for name, config in self.data['mcpServers'].items():
                self.servers.append({
                    'name': name,
                    'config': config,
                    'scope': 'global',
                    'project': None
                })
        
        # Handle project-specific mcpServers
        if 'projects' in self.data:
            for project_path, project_config in self.data['projects'].items():
                if 'mcpServers' in project_config:
                    for name, config in project_config['mcpServers'].items():
                        self.servers.append({
                            'name': name,
                            'config': config,
                            'scope': 'project',
                            'project': project_path
                        })
    
    def backup(self) -> Optional[Path]:
        """Create a backup of the configuration file."""
        if not self.exists:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup_path = self.path.parent / f"{self.path.name}.backup.{timestamp}"
        
        try:
            shutil.copy2(self.path, backup_path)
            return backup_path
        except IOError as e:
            print(f"Error creating backup for {self.path}: {e}")
            return None
    
    def save(self) -> bool:
        """Save the configuration file."""
        if not self.data:
            return False
            
        try:
            with open(self.path, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving {self.path}: {e}")
            return False
    
    def remove_server(self, server_name: str, project_path: Optional[str] = None) -> bool:
        """Remove an MCP server from the configuration."""
        if not self.data:
            return False
            
        removed = False
        
        if project_path:
            # Remove from specific project
            if 'projects' in self.data and project_path in self.data['projects']:
                if 'mcpServers' in self.data['projects'][project_path]:
                    if server_name in self.data['projects'][project_path]['mcpServers']:
                        del self.data['projects'][project_path]['mcpServers'][server_name]
                        removed = True
        else:
            # Remove from global servers
            if 'mcpServers' in self.data:
                if server_name in self.data['mcpServers']:
                    del self.data['mcpServers'][server_name]
                    removed = True
        
        if removed:
            self._extract_servers()  # Refresh server list
            
        return removed
    
    def add_server(self, server_name: str, server_config: Dict[str, Any], project_path: Optional[str] = None) -> bool:
        """Add an MCP server to the configuration."""
        if not self.data:
            # Initialize empty config if needed
            self.data = {}
            
        added = False
        
        if project_path:
            # Add to specific project
            if 'projects' not in self.data:
                self.data['projects'] = {}
            if project_path not in self.data['projects']:
                self.data['projects'][project_path] = {}
            if 'mcpServers' not in self.data['projects'][project_path]:
                self.data['projects'][project_path]['mcpServers'] = {}
                
            self.data['projects'][project_path]['mcpServers'][server_name] = server_config
            added = True
        else:
            # Add to global servers
            if 'mcpServers' not in self.data:
                self.data['mcpServers'] = {}
                
            self.data['mcpServers'][server_name] = server_config
            added = True
        
        if added:
            self._extract_servers()  # Refresh server list
            
        return added


class MCPManager:
    """Main MCP server management class."""
    
    def __init__(self):
        paths = get_platform_config_paths()
        self.configs = [
            MCPConfig(
                "Claude Code CLI", 
                paths["claude_code"],
                "Claude Code command-line interface"
            ),
            MCPConfig(
                "VS Code MCP Extension",
                paths["vscode"],
                "Visual Studio Code MCP extension"
            ),
            MCPConfig(
                "Claude Desktop",
                paths["claude_desktop"], 
                "Claude Desktop application"
            )
        ]
        
    def detect_configs(self) -> List[MCPConfig]:
        """Detect and load available MCP configuration files."""
        available = []
        
        for config in self.configs:
            if config.load():
                available.append(config)
                
        return available
        
    def list_all_servers(self, configs: List[MCPConfig]) -> None:
        """List all MCP servers across all configuration files."""
        if not configs:
            print("No MCP configuration files found.")
            return
            
        total_servers = 0
        server_index = 1
        
        for config in configs:
            print(f"\n{'=' * 60}")
            print(f"Platform: {config.name}")
            print(f"Config: {config.path}")
            print(f"Status: Found ({len(config.servers)} servers)")
            print('=' * 60)
            
            if not config.servers:
                print("No MCP servers configured.")
                continue
                
            for server in config.servers:
                scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
                print(f"{server_index:2d}. {server['name']}{scope_info}")
                
                # Show server details
                server_config = server['config']
                if 'command' in server_config:
                    cmd = server_config['command']
                    if isinstance(cmd, list):
                        cmd = ' '.join(cmd)
                    print(f"    Command: {cmd}")
                elif 'url' in server_config:
                    print(f"    URL: {server_config['url']}")
                
                if 'args' in server_config and server_config['args']:
                    args = server_config['args']
                    if isinstance(args, list):
                        args = ' '.join(args)
                    print(f"    Args: {args}")
                    
                server_index += 1
                
            total_servers += len(config.servers)
            
        print(f"\nTotal: {total_servers} MCP servers across {len(configs)} platforms")
        
    def interactive_remove(self, configs: List[MCPConfig]) -> None:
        """Interactive MCP server removal."""
        if not any(config.servers for config in configs):
            print("No MCP servers found to remove.")
            return
            
        print("\nMCP Server Removal Options:")
        print("1. Remove specific servers (interactive selection)")
        print("2. Remove ALL servers from ALL platforms")
        print("3. Cancel")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            self._remove_specific_servers(configs)
        elif choice == "2":
            self._remove_all_servers(configs)
        elif choice == "3":
            print("Operation cancelled.")
        else:
            print("Invalid choice.")
    
    def _remove_specific_servers(self, configs: List[MCPConfig]) -> None:
        """Remove specific servers interactively."""
        # Build server index
        server_map = {}
        index = 1
        
        for config in configs:
            for server in config.servers:
                server_map[index] = (config, server)
                index += 1
        
        print(f"\nSelect servers to remove (1-{len(server_map)}, or 'q' to quit):")
        print("You can enter multiple numbers separated by spaces or commas.")
        
        selection = input("Enter selection: ").strip()
        if selection.lower() == 'q':
            return
            
        # Parse selection
        try:
            selected_indices = []
            for part in selection.replace(',', ' ').split():
                selected_indices.append(int(part))
        except ValueError:
            print("Invalid selection format.")
            return
            
        # Confirm removal
        servers_to_remove = []
        for idx in selected_indices:
            if idx in server_map:
                config, server = server_map[idx]
                servers_to_remove.append((config, server))
                scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
                print(f"  - {server['name']}{scope_info} from {config.name}")
        
        if not servers_to_remove:
            print("No valid servers selected.")
            return
            
        confirm = input(f"\nRemove {len(servers_to_remove)} servers? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
            
        # Create backups and remove servers
        backups_created = []
        for config, server in servers_to_remove:
            # Create backup if not already created
            if config not in [b[0] for b in backups_created]:
                backup_path = config.backup()
                if backup_path:
                    backups_created.append((config, backup_path))
                    
            # Remove server
            removed = config.remove_server(server['name'], server.get('project'))
            if removed:
                config.save()
                print(f"Removed: {server['name']} from {config.name}")
            else:
                print(f"Failed to remove: {server['name']} from {config.name}")
                
        # Show backup info
        if backups_created:
            print(f"\nBackups created:")
            for config, backup_path in backups_created:
                print(f"  {config.name}: {backup_path}")
    
    def _remove_all_servers(self, configs: List[MCPConfig]) -> None:
        """Remove all servers from all platforms."""
        total_servers = sum(len(config.servers) for config in configs)
        
        print(f"\nThis will remove ALL {total_servers} MCP servers from ALL platforms:")
        for config in configs:
            if config.servers:
                print(f"  - {config.name}: {len(config.servers)} servers")
                
        confirm = input("\nThis action cannot be easily undone. Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
            
        # Create backups and remove all servers
        backups_created = []
        for config in configs:
            if not config.servers:
                continue
                
            backup_path = config.backup()
            if backup_path:
                backups_created.append((config, backup_path))
                
            # Remove all servers
            if config.data:
                if 'mcpServers' in config.data:
                    config.data['mcpServers'] = {}
                    
                if 'projects' in config.data:
                    for project_config in config.data['projects'].values():
                        if 'mcpServers' in project_config:
                            project_config['mcpServers'] = {}
                            
                config.save()
                config._extract_servers()  # Refresh
                print(f"Removed all servers from {config.name}")
                
        # Show backup info
        if backups_created:
            print(f"\nBackups created:")
            for config, backup_path in backups_created:
                print(f"  {config.name}: {backup_path}")
                print(f"    Restore with: cp '{backup_path}' '{config.path}'")
    
    def show_credential_status(self) -> None:
        """Show credential validation status."""
        print("\n" + "=" * 60)
        print("Credential Validation Status")
        print("=" * 60)
        
        # Check environment variables
        env_creds = validate_credentials()
        print("\nEnvironment Variables:")
        for var, status in env_creds.items():
            status_str = "✓ Found" if status else "✗ Missing"
            print(f"  {var}: {status_str}")
        
        # Check platform-specific storage
        platform_creds = validate_platform_credentials()
        if platform_creds:
            print(f"\nPlatform-Specific Storage ({platform.system()}):")
            for key, status in platform_creds.items():
                if "error" in key:
                    print(f"  Error checking {key}")
                else:
                    status_str = "✓ Found" if status else "✗ Missing"
                    print(f"  {key}: {status_str}")
        
        # Recommendations
        missing_env = [var for var, status in env_creds.items() if not status]
        if missing_env:
            print(f"\nRecommendations:")
            print(f"  Missing credentials: {', '.join(missing_env)}")
            print(f"  See GUIDE-CREDENTIALS.md for secure setup instructions")
    
    def interactive_add(self, configs: List[MCPConfig]) -> None:
        """Interactive MCP server addition."""
        if not configs:
            print("No MCP configuration files found.")
            return
            
        print("\n" + "=" * 60)
        print("Add MCP Server")
        print("=" * 60)
        
        # Get server details
        server_name = input("Server name: ").strip()
        if not server_name:
            print("Server name is required.")
            return
            
        print("\nServer type:")
        print("1. NPX package (e.g., @modelcontextprotocol/server-github)")
        print("2. Direct command (e.g., python script.py)")
        print("3. SSE URL (e.g., http://localhost:3000/sse)")
        
        server_type = input("Choose type (1-3): ").strip()
        
        if server_type == "1":
            package = input("NPX package name: ").strip()
            args = input("Additional arguments (optional): ").strip()
            
            server_config = {
                "type": "stdio",
                "command": "npx",
                "args": [package] + (args.split() if args else [])
            }
        elif server_type == "2":
            command = input("Command: ").strip()
            args = input("Arguments (optional): ").strip()
            
            server_config = {
                "type": "stdio", 
                "command": command,
                "args": args.split() if args else []
            }
        elif server_type == "3":
            url = input("SSE URL: ").strip()
            
            server_config = {
                "type": "sse",
                "url": url
            }
        else:
            print("Invalid choice.")
            return
            
        # Ask about environment variables
        env_vars = {}
        while True:
            env_name = input("Environment variable name (or press Enter to finish): ").strip()
            if not env_name:
                break
            env_value = input(f"Value template for {env_name} (e.g., ${{env:GITHUB_TOKEN}}): ").strip()
            env_vars[env_name] = env_value
            
        if env_vars:
            server_config["env"] = env_vars
        
        # Choose target configurations
        print(f"\nAdd '{server_name}' to which configurations?")
        for i, config in enumerate(configs, 1):
            print(f"{i}. {config.name}")
        print(f"{len(configs) + 1}. All configurations")
        
        choices = input("Enter choices (comma-separated): ").strip()
        try:
            if choices == str(len(configs) + 1):
                target_configs = configs
            else:
                indices = [int(x.strip()) - 1 for x in choices.split(",")]
                target_configs = [configs[i] for i in indices if 0 <= i < len(configs)]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return
            
        # Add to selected configurations
        backups_created = []
        for config in target_configs:
            # Create backup
            backup_path = config.backup()
            if backup_path:
                backups_created.append((config, backup_path))
                
            # Add server
            added = config.add_server(server_name, server_config)
            if added:
                config.save()
                print(f"Added '{server_name}' to {config.name}")
            else:
                print(f"Failed to add '{server_name}' to {config.name}")
                
        # Show backup info
        if backups_created:
            print(f"\nBackups created:")
            for config, backup_path in backups_created:
                print(f"  {config.name}: {backup_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-platform MCP server management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-manager.py                    # List servers from all platforms  
  mcp-manager.py --add              # Interactive server addition
  mcp-manager.py --remove           # Interactive removal
  mcp-manager.py --file ~/.claude.json  # Work with specific file only
  mcp-manager.py --list             # List only, no changes
  mcp-manager.py --check-credentials # Validate credential setup
  mcp-manager.py --backup-only      # Create backups only
        """
    )
    
    parser.add_argument(
        '--file', 
        type=Path,
        help='Work with specific config file only (for compatibility)'
    )
    parser.add_argument(
        '--list', 
        action='store_true',
        help='List servers only, no removal options'
    )
    parser.add_argument(
        '--remove',
        action='store_true', 
        help='Start interactive removal process'
    )
    parser.add_argument(
        '--backup-only',
        action='store_true',
        help='Create backups without making changes'
    )
    parser.add_argument(
        '--check-credentials',
        action='store_true',
        help='Validate credential configuration'
    )
    parser.add_argument(
        '--add',
        action='store_true',
        help='Interactive server addition'
    )
    
    args = parser.parse_args()
    
    manager = MCPManager()
    
    # Handle single file mode (backward compatibility)
    if args.file:
        config = MCPConfig("Custom", args.file, f"Custom config: {args.file}")
        if config.load():
            configs = [config]
        else:
            print(f"Error: Could not load config file: {args.file}")
            sys.exit(1)
    else:
        # Multi-platform mode
        configs = manager.detect_configs()
        
        if not configs:
            print("No MCP configuration files found in standard locations:")
            for config in manager.configs:
                print(f"  {config.path} (not found)")
            sys.exit(1)
    
    # Show platform status
    if not args.file:
        print("MCP Configuration Status:")
        for config in manager.configs:
            status = "Found" if config in configs else "Not found"
            server_count = f" ({len(config.servers)} servers)" if config in configs else ""
            print(f"  {config.name}: {status}{server_count}")
    
    # Handle backup-only mode
    if args.backup_only:
        print("\nCreating backups...")
        for config in configs:
            backup_path = config.backup()
            if backup_path:
                print(f"Backup created: {backup_path}")
        return
    
    # Handle credential validation
    if args.check_credentials:
        manager.show_credential_status()
        return
        
    # Handle server addition
    if args.add:
        manager.interactive_add(configs)
        return
    
    # List servers
    manager.list_all_servers(configs)
    
    # Handle removal if requested
    if args.remove and not args.list:
        manager.interactive_remove(configs)
    elif not args.list and not args.remove:
        # Ask if user wants to remove servers
        if any(config.servers for config in configs):
            print("\nWould you like to remove any servers? (y/N): ", end="")
            if input().strip().lower() == 'y':
                manager.interactive_remove(configs)


if __name__ == "__main__":
    main()