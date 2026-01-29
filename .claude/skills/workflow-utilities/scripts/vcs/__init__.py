#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""VCS provider abstraction for workflow scripts.

This module provides a unified interface for interacting with GitHub
through the gh CLI tool.

Usage:
    from vcs import get_vcs_adapter

    vcs = get_vcs_adapter()
    username = vcs.get_current_user()
    vcs.create_pull_request(source, target, title, body)
"""

from .base_adapter import BaseVCSAdapter
from .config import load_vcs_config
from .github_adapter import GitHubAdapter
from .provider import VCSProvider

__all__ = [
    "BaseVCSAdapter",
    "GitHubAdapter",
    "VCSProvider",
    "get_vcs_adapter",
]


def get_vcs_adapter() -> BaseVCSAdapter:
    """Get appropriate VCS adapter based on configuration and context.

    Detection order:
    1. Load .vcs_config.yaml if exists -> use specified provider
    2. Default to GitHub

    Returns:
        Configured VCS adapter instance

    Raises:
        ValueError: If provider configuration is invalid
    """
    # Try loading explicit configuration
    config = load_vcs_config()
    if config:
        provider = config.get("vcs_provider")
        if provider == "github":
            return GitHubAdapter()
        else:
            raise ValueError(f"Unknown VCS provider in config: {provider}")

    # Default to GitHub
    return GitHubAdapter()
