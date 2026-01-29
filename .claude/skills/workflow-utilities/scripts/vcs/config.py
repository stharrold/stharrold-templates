#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""VCS configuration loading and validation.

This module handles loading and validating .vcs_config.yaml files.

Constants:
- CONFIG_FILE_NAME: .vcs_config.yaml
  Rationale: Standard location for VCS provider configuration
- VALID_PROVIDERS: List of supported provider names
  Rationale: Validate configuration against supported providers
"""

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # Will be checked in functions that use it


# Constants
CONFIG_FILE_NAME = ".vcs_config.yaml"
VALID_PROVIDERS = ["github"]


def load_vcs_config(config_path: Path | None = None) -> dict[str, Any] | None:
    """Load VCS configuration from .vcs_config.yaml.

    Args:
        config_path: Optional path to config file (defaults to .vcs_config.yaml in cwd)

    Returns:
        Configuration dict or None if file doesn't exist

    Raises:
        ImportError: If PyYAML is not installed

    Example config:
        vcs_provider: github
    """
    if yaml is None:
        raise ImportError("PyYAML is required to load VCS configuration. Install it with: pip install pyyaml")

    if config_path is None:
        config_path = Path.cwd() / CONFIG_FILE_NAME

    if not config_path.exists():
        return None

    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            return None

        # Validate configuration
        validate_config(config)
        return config

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading config from {config_path}: {e}")


def validate_config(config: dict[str, Any]) -> None:
    """Validate VCS configuration.

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    if "vcs_provider" not in config:
        raise ValueError("Missing required field: vcs_provider")

    provider = config["vcs_provider"]
    if provider not in VALID_PROVIDERS:
        raise ValueError(f"Invalid vcs_provider: {provider}. Must be one of: {VALID_PROVIDERS}")

    # No provider-specific validation needed for GitHub (uses gh CLI auth)
