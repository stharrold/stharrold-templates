#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Test script to verify the deduplication fix for mcp_manager.py"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to the path to import mcp_manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_remove_duplicate_servers():
    """Test the remove_duplicate_servers method to reproduce and verify the fix."""

    # Import MCPConfig using standard Python import
    import mcp_manager

    mcp_config_class = mcp_manager.MCPConfig

    # Create a temporary config file with duplicates
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "mcpServers": {
                "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
                "DISABLED_github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
                "filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"]},
            }
        }
        json.dump(test_config, f)
        temp_path = Path(f.name)

    try:
        # Create MCPConfig instance
        config = mcp_config_class("Test Platform", temp_path, "Test config for deduplication")

        # Load the config
        assert config.load(), "Failed to load test config"

        # Try to run remove_duplicate_servers
        config.remove_duplicate_servers()

        # Verify the duplicate was removed (active version removed, DISABLED kept)
        assert "github" not in config.data["mcpServers"], "Active 'github' server was not removed"
        assert "DISABLED_github" in config.data["mcpServers"], "DISABLED_github server was not kept"

    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    print("Testing MCPConfig.remove_duplicate_servers() method")
    print("=" * 60)

    try:
        test_remove_duplicate_servers()
        print("\n" + "=" * 60)
        print("✅ TEST PASSED: Deduplication works correctly")
        sys.exit(0)
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
