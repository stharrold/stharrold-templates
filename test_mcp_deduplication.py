#!/usr/bin/env python3
"""Test script to verify the deduplication fix for mcp-manager.py"""

import json
import tempfile
from pathlib import Path
import sys
import os

# Add the current directory to the path to import mcp-manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_remove_duplicate_servers():
    """Test the remove_duplicate_servers method to reproduce and verify the fix."""
    
    # Import MCPConfig after adding to path
    # Import from the actual file
    import importlib.util
    spec = importlib.util.spec_from_file_location("mcp_manager", "mcp-manager.py")
    mcp_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mcp_manager)
    MCPConfig = mcp_manager.MCPConfig
    
    # Create a temporary config file with duplicates
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            "mcpServers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"]
                },
                "DISABLED_github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"]
                },
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"]
                }
            }
        }
        json.dump(test_config, f)
        temp_path = Path(f.name)
    
    try:
        # Create MCPConfig instance
        config = MCPConfig("Test Platform", temp_path, "Test config for deduplication")
        
        # Load the config
        if not config.load():
            print("❌ Failed to load test config")
            return False
        
        print(f"✓ Loaded test config with {len(config.servers)} active servers")
        print(f"  Config data keys: {list(config.data.keys())}")
        
        # Try to run remove_duplicate_servers - this should fail with AttributeError before fix
        print("\nAttempting deduplication...")
        try:
            result = config.remove_duplicate_servers()
            print(f"✓ Deduplication completed successfully: {result}")
            
            # Verify the duplicate was removed
            if 'github' not in config.data['mcpServers']:
                print("✓ Active 'github' server was correctly removed")
            else:
                print("❌ Active 'github' server was not removed")
                
            if 'DISABLED_github' in config.data['mcpServers']:
                print("✓ DISABLED_github server was correctly kept")
            else:
                print("❌ DISABLED_github server was not kept")
                
            return True
            
        except AttributeError as e:
            print(f"❌ AttributeError occurred: {e}")
            print(f"   This is expected before the fix is applied")
            return False
            
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()
            print(f"\n✓ Cleaned up temp file: {temp_path}")

if __name__ == "__main__":
    print("Testing MCPConfig.remove_duplicate_servers() method")
    print("=" * 60)
    
    success = test_remove_duplicate_servers()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Deduplication works correctly")
        sys.exit(0)
    else:
        print("❌ TEST FAILED: Deduplication has errors")
        sys.exit(1)