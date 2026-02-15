# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Shared environment detection utilities.

Provides functions for detecting CI and WSL environments,
used by both secrets_setup.py and secrets_run.py.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

__all__ = ["is_ci", "is_wsl", "get_wsl_win_project_root", "get_repo_root"]


def is_ci() -> bool:
    """Detect if running in a CI environment.

    Checks for common CI environment variables.
    """
    ci_vars = [
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "TF_BUILD",  # Azure DevOps
        "JENKINS_URL",
        "CIRCLECI",
        "TRAVIS",
        "BUILDKITE",
        "DRONE",
        "CODEBUILD_BUILD_ID",  # AWS CodeBuild
    ]
    return any(os.environ.get(var) for var in ci_vars)


def is_wsl() -> bool:
    """Detect if running inside Windows Subsystem for Linux.

    Checks /proc/version for Microsoft/WSL indicators.
    """
    try:
        content = Path("/proc/version").read_text()
        return "microsoft" in content.lower() or "wsl" in content.lower()
    except (OSError, PermissionError, FileNotFoundError):
        return False


def get_repo_root(target_path: Path | None = None) -> Path:
    """Get the repository root directory as an absolute path.

    Args:
        target_path: Optional manual override for the root path.
    """
    if target_path:
        return target_path.resolve()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except subprocess.CalledProcessError:
        # Fallback to script parent if not in git repo
        return Path(__file__).parent.parent.resolve()


def get_wsl_win_project_root() -> str | None:
    """Get the Windows path for the project root (for powershell.exe calls).

    Returns:
        Windows path string (e.g. 'D:\\Projects\\MyRepo') or None if wslpath fails.
    """
    import subprocess

    try:
        # Find repo root
        repo_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        # Convert to Windows path
        win_path = subprocess.run(
            ["wslpath", "-w", repo_root],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return win_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
