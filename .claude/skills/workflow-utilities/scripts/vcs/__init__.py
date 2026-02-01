#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""VCS interface for workflow scripts (GitHub only).

This module provides an interface for interacting with GitHub
through the gh CLI tool.

Usage:
    from vcs import get_vcs_adapter

    vcs = get_vcs_adapter()
    username = vcs.get_current_user()
    vcs.create_pull_request(source, target, title, body)
"""

from .github_adapter import GitHubAdapter
from .provider import VCSProvider

__all__ = [
    "GitHubAdapter",
    "VCSProvider",
    "get_vcs_adapter",
]


def get_vcs_adapter() -> GitHubAdapter:
    """Get the GitHub VCS adapter.

    Returns:
        GitHubAdapter instance
    """
    return GitHubAdapter()
