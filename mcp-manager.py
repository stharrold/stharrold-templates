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
        
        # Handle global mcpServers (skip disabled ones)
        if 'mcpServers' in self.data:
            for name, config in self.data['mcpServers'].items():
                if not name.startswith("DISABLED_"):
                    self.servers.append({
                        'name': name,
                        'config': config,
                        'scope': 'global',
                        'project': None
                    })
        
        # Handle project-specific mcpServers (skip disabled ones)
        if 'projects' in self.data:
            for project_path, project_config in self.data['projects'].items():
                if 'mcpServers' in project_config:
                    for name, config in project_config['mcpServers'].items():
                        if not name.startswith("DISABLED_"):
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
    
    def disable_server(self, server_name: str, project_path: Optional[str] = None) -> bool:
        """Disable an MCP server by renaming it with DISABLED_ prefix."""
        if not self.data:
            return False
            
        disabled = False
        disabled_name = f"DISABLED_{server_name}"
        
        if project_path:
            # Disable in specific project
            if 'projects' in self.data and project_path in self.data['projects']:
                if 'mcpServers' in self.data['projects'][project_path]:
                    if server_name in self.data['projects'][project_path]['mcpServers']:
                        # Rename the server key
                        self.data['projects'][project_path]['mcpServers'][disabled_name] = \
                            self.data['projects'][project_path]['mcpServers'].pop(server_name)
                        disabled = True
        else:
            # Disable in global servers
            if 'mcpServers' in self.data:
                if server_name in self.data['mcpServers']:
                    # Rename the server key
                    self.data['mcpServers'][disabled_name] = self.data['mcpServers'].pop(server_name)
                    disabled = True
        
        if disabled:
            self._extract_servers()  # Refresh server list
            
        return disabled
    
    def enable_server(self, disabled_server_name: str, project_path: Optional[str] = None) -> bool:
        """Enable a disabled MCP server by removing DISABLED_ prefix."""
        if not self.data:
            return False
            
        if not disabled_server_name.startswith("DISABLED_"):
            return False
            
        enabled = False
        original_name = disabled_server_name[9:]  # Remove "DISABLED_" prefix
        
        if project_path:
            # Enable in specific project
            if 'projects' in self.data and project_path in self.data['projects']:
                if 'mcpServers' in self.data['projects'][project_path]:
                    if disabled_server_name in self.data['projects'][project_path]['mcpServers']:
                        # Rename the server key back
                        self.data['projects'][project_path]['mcpServers'][original_name] = \
                            self.data['projects'][project_path]['mcpServers'].pop(disabled_server_name)
                        enabled = True
        else:
            # Enable in global servers
            if 'mcpServers' in self.data:
                if disabled_server_name in self.data['mcpServers']:
                    # Rename the server key back
                    self.data['mcpServers'][original_name] = self.data['mcpServers'].pop(disabled_server_name)
                    enabled = True
        
        if enabled:
            self._extract_servers()  # Refresh server list
            
        return enabled
    
    def get_disabled_servers(self) -> List[Dict]:
        """Get list of disabled servers."""
        if not self.data:
            return []
            
        disabled_servers = []
        
        # Check global mcpServers
        if 'mcpServers' in self.data:
            for name, config in self.data['mcpServers'].items():
                if name.startswith("DISABLED_"):
                    disabled_servers.append({
                        'name': name,
                        'original_name': name[9:],  # Remove "DISABLED_" prefix
                        'config': config,
                        'scope': 'global',
                        'project': None
                    })
        
        # Check project-specific mcpServers
        if 'projects' in self.data:
            for project_path, project_config in self.data['projects'].items():
                if 'mcpServers' in project_config:
                    for name, config in project_config['mcpServers'].items():
                        if name.startswith("DISABLED_"):
                            disabled_servers.append({
                                'name': name,
                                'original_name': name[9:],  # Remove "DISABLED_" prefix
                                'config': config,
                                'scope': 'project',
                                'project': project_path
                            })
        
        return disabled_servers


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
        
        # Platform name mapping for command-line arguments
        self.platform_map = {
            "claude-code": "Claude Code CLI",
            "vscode": "VS Code MCP Extension", 
            "claude-desktop": "Claude Desktop"
        }
    
    def select_target_platform(self, platform_name: Optional[str] = None) -> Optional[MCPConfig]:
        """Select target platform configuration."""
        available_configs = self.detect_configs()
        
        if not available_configs:
            return None
            
        if platform_name:
            # Find specific platform
            target_name = self.platform_map.get(platform_name)
            if not target_name:
                print(f"Error: Unknown platform '{platform_name}'. Available: {', '.join(self.platform_map.keys())}")
                return None
                
            for config in available_configs:
                if config.name == target_name:
                    return config
                    
            print(f"Error: Platform '{platform_name}' not found or not configured.")
            print("Available platforms:")
            for config in available_configs:
                platform_key = {v: k for k, v in self.platform_map.items()}.get(config.name, config.name.lower())
                print(f"  {platform_key}: {config.path}")
            return None
        else:
            # Auto-detect first available platform
            return available_configs[0] if available_configs else None
        
    def detect_configs(self) -> List[MCPConfig]:
        """Detect and load available MCP configuration files."""
        available = []
        
        for config in self.configs:
            if config.load():
                available.append(config)
                
        return available
    
    def show_platform_status(self) -> None:
        """Show status of all MCP platforms."""
        print("MCP Configuration Status:")
        configs = self.detect_configs()
        
        for config in self.configs:
            platform_key = {v: k for k, v in self.platform_map.items()}.get(config.name, config.name.lower())
            if config in configs:
                disabled_count = len(config.get_disabled_servers())
                server_info = f" ({len(config.servers)} active"
                if disabled_count > 0:
                    server_info += f", {disabled_count} disabled"
                server_info += ")"
                print(f"  {platform_key}: Found{server_info}")
            else:
                print(f"  {platform_key}: Not found ({config.path})")
        
        if configs:
            print(f"\nUse --platform <name> to work with a specific platform")
            print(f"Available platforms: {', '.join(self.platform_map.keys())}")
        
    def list_platform_servers(self, config: MCPConfig) -> None:
        """List MCP servers for a specific platform."""
        disabled_servers = config.get_disabled_servers()
        
        print(f"\n{'=' * 60}")
        print(f"Platform: {config.name}")
        print(f"Config: {config.path}")
        print(f"Status: {len(config.servers)} active, {len(disabled_servers)} disabled")
        print('=' * 60)
        
        # Show active servers
        if config.servers:
            print("\nActive servers:")
            for i, server in enumerate(config.servers, 1):
                scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
                print(f"{i:2d}. {server['name']}{scope_info}")
                
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
        
        # Show disabled servers
        if disabled_servers:
            print("\nDisabled servers:")
            for server in disabled_servers:
                scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
                print(f"    {server['original_name']}{scope_info} [DISABLED]")
                
                # Show server details
                server_config = server['config']
                if 'command' in server_config:
                    cmd = server_config['command']
                    if isinstance(cmd, list):
                        cmd = ' '.join(cmd)
                    print(f"        Command: {cmd}")
                elif 'url' in server_config:
                    print(f"        URL: {server_config['url']}")
                
                if 'args' in server_config and server_config['args']:
                    args = server_config['args']
                    if isinstance(args, list):
                        args = ' '.join(args)
                    print(f"        Args: {args}")
        
        if not config.servers and not disabled_servers:
            print("No MCP servers configured.")
        
        print(f"\nTotal: {len(config.servers)} active, {len(disabled_servers)} disabled servers")
        
    def interactive_remove(self, config: MCPConfig) -> None:
        """Interactive MCP server removal."""
        if not config.servers:
            print("No MCP servers found to remove.")
            return
            
        print(f"\n{'=' * 60}")
        print(f"Remove MCP Servers from {config.name}")
        print("=" * 60)
        
        print("\nAvailable servers:")
        for i, server in enumerate(config.servers, 1):
            scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
            print(f"{i:2d}. {server['name']}{scope_info}")
        
        print(f"\nRemoval options:")
        print(f"1. Remove specific servers (interactive selection)")
        print(f"2. Remove ALL servers from {config.name}")
        print(f"3. Cancel")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            self._remove_specific_servers(config)
        elif choice == "2":
            self._remove_all_servers(config)
        elif choice == "3":
            print("Operation cancelled.")
        else:
            print("Invalid choice.")
    
    def _remove_specific_servers(self, config: MCPConfig) -> None:
        """Remove specific servers interactively."""
        print(f"\nSelect servers to remove (1-{len(config.servers)}, or 'q' to quit):")
        print("You can enter multiple numbers separated by spaces or commas.")
        
        selection = input("Enter selection: ").strip()
        if selection.lower() == 'q':
            return
            
        # Parse selection
        try:
            selected_indices = []
            for part in selection.replace(',', ' ').split():
                idx = int(part)
                if 1 <= idx <= len(config.servers):
                    selected_indices.append(idx - 1)  # Convert to 0-based index
                else:
                    print(f"Invalid selection: {idx}. Must be between 1 and {len(config.servers)}")
                    return
        except ValueError:
            print("Invalid selection format.")
            return
            
        # Confirm removal
        servers_to_remove = []
        print("\nServers to remove:")
        for idx in selected_indices:
            server = config.servers[idx]
            servers_to_remove.append(server)
            scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
            print(f"  - {server['name']}{scope_info}")
        
        if not servers_to_remove:
            print("No valid servers selected.")
            return
            
        confirm = input(f"\nRemove {len(servers_to_remove)} servers? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
            
        # Create backup and remove servers
        backup_path = config.backup()
        
        # Remove servers
        for server in servers_to_remove:
            removed = config.remove_server(server['name'], server.get('project'))
            if removed:
                print(f"Removed: {server['name']}")
            else:
                print(f"Failed to remove: {server['name']}")
        
        config.save()
                
        # Show backup info
        if backup_path:
            print(f"\nBackup created: {backup_path}")
    
    def _remove_all_servers(self, config: MCPConfig) -> None:
        """Remove all servers from platform."""
        print(f"\nThis will remove ALL {len(config.servers)} MCP servers from {config.name}")
        
        for server in config.servers:
            scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
            print(f"  - {server['name']}{scope_info}")
                
        confirm = input("\nThis action cannot be easily undone. Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
            
        # Create backup and remove all servers
        backup_path = config.backup()
        
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
        if backup_path:
            print(f"\nBackup created: {backup_path}")
            print(f"Restore with: cp '{backup_path}' '{config.path}'")
    
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
    
    def interactive_disable(self, config: MCPConfig) -> None:
        """Interactive MCP server disabling."""
        if not config.servers:
            print("No active MCP servers found to disable.")
            return
            
        print("\n" + "=" * 60)
        print(f"Disable servers in {config.name}")
        print("=" * 60)
        
        print("\nActive servers:")
        for i, server in enumerate(config.servers, 1):
            scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
            print(f"  {i:2d}. {server['name']}{scope_info}")
        
        print(f"\nSelect servers to disable (1-{len(config.servers)}, or 'q' to quit):")
        print("You can enter multiple numbers separated by spaces or commas.")
        
        selection = input("Enter selection: ").strip()
        if selection.lower() == 'q':
            return
            
        # Parse selection
        try:
            selected_indices = []
            for part in selection.replace(',', ' ').split():
                idx = int(part)
                if 1 <= idx <= len(config.servers):
                    selected_indices.append(idx - 1)  # Convert to 0-based index
                else:
                    print(f"Invalid selection: {idx}. Must be between 1 and {len(config.servers)}")
                    return
        except ValueError:
            print("Invalid selection format.")
            return
            
        # Confirm disabling
        servers_to_disable = []
        print("\nServers to disable:")
        for idx in selected_indices:
            server = config.servers[idx]
            servers_to_disable.append(server)
            scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
            print(f"  - {server['name']}{scope_info}")
        
        if not servers_to_disable:
            print("No valid servers selected.")
            return
            
        confirm = input(f"\nDisable {len(servers_to_disable)} servers? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
            
        # Create backup and disable servers
        backup_path = config.backup()
        
        for server in servers_to_disable:
            # Disable server
            disabled = config.disable_server(server['name'], server.get('project'))
            if disabled:
                print(f"Disabled: {server['name']}")
            else:
                print(f"Failed to disable: {server['name']}")
        
        config.save()
                
        # Show backup info
        if backup_path:
            print(f"\nBackup created: {backup_path}")
    
    def interactive_enable(self, config: MCPConfig) -> None:
        """Interactive MCP server enabling."""
        disabled_servers = config.get_disabled_servers()
        
        if not disabled_servers:
            print("No disabled MCP servers found to enable.")
            return
        
        print("\n" + "=" * 60)
        print(f"Enable servers in {config.name}")
        print("=" * 60)
        
        print("\nDisabled servers:")
        for i, server in enumerate(disabled_servers, 1):
            scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
            print(f"  {i:2d}. {server['original_name']}{scope_info} [DISABLED]")
        
        print(f"\nSelect servers to enable (1-{len(disabled_servers)}, or 'q' to quit):")
        print("You can enter multiple numbers separated by spaces or commas.")
        
        selection = input("Enter selection: ").strip()
        if selection.lower() == 'q':
            return
            
        # Parse selection
        try:
            selected_indices = []
            for part in selection.replace(',', ' ').split():
                idx = int(part)
                if 1 <= idx <= len(disabled_servers):
                    selected_indices.append(idx - 1)  # Convert to 0-based index
                else:
                    print(f"Invalid selection: {idx}. Must be between 1 and {len(disabled_servers)}")
                    return
        except ValueError:
            print("Invalid selection format.")
            return
            
        # Confirm enabling
        servers_to_enable = []
        print("\nServers to enable:")
        for idx in selected_indices:
            server = disabled_servers[idx]
            servers_to_enable.append(server)
            scope_info = f" [{server['scope']}" + (f": {server['project']}" if server['project'] else "") + "]"
            print(f"  - {server['original_name']}{scope_info}")
        
        if not servers_to_enable:
            print("No valid servers selected.")
            return
            
        confirm = input(f"\nEnable {len(servers_to_enable)} servers? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
            
        # Create backup and enable servers
        backup_path = config.backup()
        
        for server in servers_to_enable:
            # Enable server
            enabled = config.enable_server(server['name'], server.get('project'))
            if enabled:
                print(f"Enabled: {server['original_name']}")
            else:
                print(f"Failed to enable: {server['original_name']}")
        
        config.save()
                
        # Show backup info
        if backup_path:
            print(f"\nBackup created: {backup_path}")
    
    def interactive_add(self, config: MCPConfig) -> None:
        """Interactive MCP server addition."""
        print("\n" + "=" * 60)
        print(f"Add MCP Server to {config.name}")
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
        
        # Confirm addition
        print(f"\nAdding '{server_name}' to {config.name}")
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
            
        # Create backup and add server
        backup_path = config.backup()
        
        # Add server
        added = config.add_server(server_name, server_config)
        if added:
            config.save()
            print(f"Successfully added '{server_name}' to {config.name}")
        else:
            print(f"Failed to add '{server_name}' to {config.name}")
            
        # Show backup info
        if backup_path:
            print(f"Backup created: {backup_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-platform MCP server management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-manager.py                           # List servers from first available platform
  mcp-manager.py --platform claude-code   # Work with Claude Code CLI only
  mcp-manager.py --platform vscode --add  # Add server to VS Code MCP Extension
  mcp-manager.py --platform claude-desktop --remove  # Remove servers from Claude Desktop
  mcp-manager.py --status                  # Show all platform statuses
  mcp-manager.py --disable                 # Interactive server disabling (auto-detect platform)
  mcp-manager.py --enable                  # Interactive server enabling (auto-detect platform)
  mcp-manager.py --file ~/.claude.json    # Work with specific file only
  mcp-manager.py --check-credentials       # Validate credential setup
  mcp-manager.py --backup-only             # Create backups only
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
        '--disable',
        action='store_true',
        help='Start interactive disable process'
    )
    parser.add_argument(
        '--enable',
        action='store_true',
        help='Start interactive enable process'
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
    parser.add_argument(
        '--platform',
        choices=['claude-code', 'vscode', 'claude-desktop'],
        help='Target platform (claude-code, vscode, claude-desktop). If not specified, auto-detects first available platform.'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show status of all MCP platforms'
    )
    
    args = parser.parse_args()
    
    manager = MCPManager()
    
    # Handle platform status display
    if args.status:
        manager.show_platform_status()
        return
    
    # Handle credential validation (cross-platform feature)
    if args.check_credentials:
        manager.show_credential_status()
        return
    
    # Handle single file mode (backward compatibility)
    if args.file:
        config = MCPConfig("Custom", args.file, f"Custom config: {args.file}")
        if config.load():
            pass  # Use this config
        else:
            print(f"Error: Could not load config file: {args.file}")
            sys.exit(1)
    else:
        # Platform selection mode
        config = manager.select_target_platform(args.platform)
        
        if not config:
            print("No MCP configuration files found.")
            manager.show_platform_status()
            sys.exit(1)
        
        # Show which platform we're working with
        if not args.platform:
            platform_key = {v: k for k, v in manager.platform_map.items()}.get(config.name, config.name.lower())
            print(f"Auto-detected platform: {platform_key} ({config.name})")
            print(f"Use --platform <name> to specify a different platform\n")
    
    # Handle backup-only mode
    if args.backup_only:
        print(f"Creating backup for {config.name}...")
        backup_path = config.backup()
        if backup_path:
            print(f"Backup created: {backup_path}")
        return
        
    # Handle server addition
    if args.add:
        manager.interactive_add(config)
        return
    
    # Handle server disabling
    if args.disable:
        manager.interactive_disable(config)
        return
    
    # Handle server enabling
    if args.enable:
        manager.interactive_enable(config)
        return
    
    # Handle removal if requested
    if args.remove:
        manager.interactive_remove(config)
        return
    
    # Default: List servers for the platform
    manager.list_platform_servers(config)
    
    # Ask if user wants to perform additional operations (only if not using --list)
    if not args.list and config.servers:
        print("\nWould you like to perform additional operations? (y/N): ", end="")
        if input().strip().lower() == 'y':
            print("\nAvailable operations:")
            print("1. Add server")
            print("2. Remove servers")
            print("3. Disable servers")
            print("4. Enable servers")
            print("5. Cancel")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                manager.interactive_add(config)
            elif choice == "2":
                manager.interactive_remove(config)
            elif choice == "3":
                manager.interactive_disable(config)
            elif choice == "4":
                manager.interactive_enable(config)
            elif choice == "5":
                print("Operation cancelled.")
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    main()