#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["keyring>=24.0.0"]
# ///
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Interactive keyring setup for secrets management.

This script helps configure secrets in the OS keyring for local development.
It reads secret definitions from secrets.toml and prompts for values.

Usage:
    uv run scripts/secrets_setup.py           # Interactive setup
    uv run scripts/secrets_setup.py --check   # Verify secrets exist

Example:
    $ uv run scripts/secrets_setup.py
    [INFO] Setting up secrets for service: stharrold-templates

    Setting up required secrets:
    DB_PASSWORD: [exists] Keep existing value? [Y/n]:
    API_KEY: Enter value: ********

    [OK] All secrets configured successfully
"""

from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

import keyring


def get_script_dir() -> Path:
    """Get the directory containing this script."""
    return Path(__file__).parent.resolve()


def get_repo_root() -> Path:
    """Get the repository root directory."""
    return get_script_dir().parent


def load_secrets_config() -> dict:
    """Load secrets configuration from secrets.toml.

    Returns:
        Dictionary with 'required', 'optional', and 'service' keys.
    """
    config_path = get_repo_root() / "secrets.toml"
    if not config_path.exists():
        print("[FAIL] secrets.toml not found at:", config_path)
        sys.exit(1)

    # Parse TOML manually (no external dependency)
    config: dict = {"required": [], "optional": [], "service": "default"}
    current_section = None

    with open(config_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Handle list values
                if value.startswith("[") and value.endswith("]"):
                    items = value[1:-1].split(",")
                    value = [item.strip().strip('"').strip("'") for item in items if item.strip()]
                else:
                    value = value.strip('"').strip("'")

                if current_section == "secrets":
                    if key == "required":
                        config["required"] = value if isinstance(value, list) else [value]
                    elif key == "optional":
                        config["optional"] = value if isinstance(value, list) else [value]
                elif current_section == "keyring":
                    if key == "service":
                        config["service"] = value

    return config


def is_ci() -> bool:
    """Detect if running in a CI environment."""
    ci_vars = [
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "TF_BUILD",
        "JENKINS_URL",
        "CIRCLECI",
        "TRAVIS",
    ]
    return any(os.environ.get(var) for var in ci_vars)


def is_container() -> bool:
    """Detect if running inside a container."""
    if Path("/.dockerenv").exists():
        return True
    if Path("/run/.containerenv").exists():
        return True
    cgroup_path = Path("/proc/1/cgroup")
    if cgroup_path.exists():
        try:
            content = cgroup_path.read_text()
            if "docker" in content or "kubepods" in content:
                return True
        except (OSError, PermissionError):
            pass
    return False


def get_secret(service: str, name: str) -> str | None:
    """Get a secret from keyring.

    Args:
        service: Keyring service name.
        name: Secret name.

    Returns:
        Secret value or None if not found.
    """
    try:
        return keyring.get_password(service, name)
    except Exception:
        return None


def set_secret(service: str, name: str, value: str) -> bool:
    """Set a secret in keyring.

    Args:
        service: Keyring service name.
        name: Secret name.
        value: Secret value.

    Returns:
        True if successful, False otherwise.
    """
    try:
        keyring.set_password(service, name, value)
        return True
    except Exception as e:
        print(f"[FAIL] Error setting {name}: {e}")
        return False


def check_secrets(config: dict) -> int:
    """Check if all secrets exist in keyring.

    Args:
        config: Secrets configuration.

    Returns:
        Exit code (0 if all present, 1 if any missing).
    """
    service = config["service"]
    all_secrets = config["required"] + config["optional"]
    missing: list[str] = []

    print(f"[INFO] Checking secrets for service: {service}")
    print()

    for name in all_secrets:
        value = get_secret(service, name)
        if value:
            print(f"[OK] {name}: configured")
        else:
            print(f"[FAIL] {name}: not found")
            missing.append(name)

    print()
    if missing:
        print(f"[FAIL] Missing {len(missing)} secret(s)")
        print("Run 'uv run scripts/secrets_setup.py' to configure.")
        return 1
    else:
        print("[OK] All secrets configured")
        return 0


def setup_secret(service: str, name: str, is_optional: bool = False) -> bool:
    """Interactively set up a single secret.

    Args:
        service: Keyring service name.
        name: Secret name.
        is_optional: Whether the secret is optional.

    Returns:
        True if secret is now configured, False otherwise.
    """
    existing = get_secret(service, name)
    optional_tag = " (optional)" if is_optional else ""

    if existing:
        print(f"{name}{optional_tag}: [exists]", end=" ")
        response = input("Keep existing value? [Y/n]: ").strip().lower()
        if response in ("", "y", "yes"):
            print("  -> Kept existing value")
            return True
    else:
        print(f"{name}{optional_tag}: ", end="")

    if is_optional:
        response = input("Enter value (or press Enter to skip): ")
        if not response:
            print("  -> Skipped")
            return True  # Optional secrets can be skipped
    else:
        response = getpass.getpass("Enter value: ")
        if not response:
            print("  -> [FAIL] Required secret cannot be empty")
            return False

    if set_secret(service, name, response):
        print("  -> [OK] Saved to keyring")
        return True
    return False


def interactive_setup(config: dict) -> int:
    """Run interactive setup for all secrets.

    Args:
        config: Secrets configuration.

    Returns:
        Exit code (0 if successful, 1 if any required secrets failed).
    """
    service = config["service"]
    print(f"[INFO] Setting up secrets for service: {service}")
    print()

    failed_required: list[str] = []

    # Setup required secrets
    if config["required"]:
        print("Setting up required secrets:")
        for name in config["required"]:
            if not setup_secret(service, name, is_optional=False):
                failed_required.append(name)
        print()

    # Setup optional secrets
    if config["optional"]:
        print("Setting up optional secrets:")
        for name in config["optional"]:
            setup_secret(service, name, is_optional=True)
        print()

    # Verify configuration
    print("-" * 40)
    if failed_required:
        print(f"[FAIL] Failed to configure {len(failed_required)} required secret(s):")
        for name in failed_required:
            print(f"  - {name}")
        return 1
    else:
        print("[OK] All secrets configured successfully")
        print()
        print("You can now run commands with secrets:")
        print("  uv run scripts/run.py <command>")
        return 0


def print_usage() -> None:
    """Print usage information."""
    print("Usage: uv run scripts/secrets_setup.py [--check]")
    print()
    print("Options:")
    print("  --check    Verify secrets exist without modifying")
    print("  --help     Show this help message")
    print()
    print("Examples:")
    print("  uv run scripts/secrets_setup.py          # Interactive setup")
    print("  uv run scripts/secrets_setup.py --check  # Verify secrets")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Check for CI/container environment
    if is_ci():
        print("[WARN] Running in CI environment.")
        print("Keyring setup is not applicable in CI.")
        print("Configure secrets as environment variables in your CI workflow.")
        return 1

    if is_container():
        print("[WARN] Running in container environment.")
        print("Keyring setup is not applicable in containers.")
        print("Inject secrets via -e flags or --secret mounts.")
        return 1

    # Parse arguments
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print_usage()
        return 0

    # Load configuration
    config = load_secrets_config()

    if "--check" in args:
        return check_secrets(config)
    else:
        return interactive_setup(config)


if __name__ == "__main__":
    sys.exit(main())
