#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""VCS provider detection and enumeration.

This module provides VCS provider detection from git remotes and configuration.

Constants:
- VCS URL patterns for GitHub
  Rationale: Enable automatic provider detection from git remote URLs
"""

import re
import subprocess
from enum import Enum


class VCSProvider(Enum):
    """Supported VCS providers."""

    GITHUB = "github"


# URL patterns for provider detection
GITHUB_PATTERNS = [
    r"github\.com[:/]",  # https://github.com/user/repo or git@github.com:user/repo
]


def detect_from_remote() -> VCSProvider | None:
    """Detect VCS provider from git remote URL.

    Returns:
        VCSProvider if detected, None otherwise

    Example URLs:
        GitHub:
        - https://github.com/user/repo.git
        - git@github.com:user/repo.git
    """
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True, timeout=5)
        remote_url = result.stdout.strip()

        # Check GitHub patterns
        for pattern in GITHUB_PATTERNS:
            if re.search(pattern, remote_url):
                return VCSProvider.GITHUB

        return None

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def detect_provider() -> VCSProvider:
    """Detect VCS provider with fallback to GitHub.

    Detection order:
    1. Try detect from git remote
    2. Default to GitHub

    Returns:
        VCSProvider (defaults to GitHub for backward compatibility)
    """
    detected = detect_from_remote()
    if detected:
        return detected

    # Default to GitHub for backward compatibility
    return VCSProvider.GITHUB
