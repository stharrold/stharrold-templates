#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["keyring>=24.0.0"]
# ///
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Universal secrets injector for cross-platform secret management.

This script injects secrets into the environment before running a command.
It supports multiple secret sources with the following precedence:

1. Environment variable already set -> use it (allows external injection)
2. CI detected -> require env vars, skip keyring
3. Container detected -> require env vars, skip keyring
4. Local development -> fetch from OS keyring

Usage:
    uv run scripts/run.py <command> [args...]

Example:
    uv run scripts/run.py uv run pytest
    uv run scripts/run.py python main.py --debug
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Lazy import keyring only when needed (CI/containers don't need it)
keyring = None


def load_keyring() -> None:
    """Lazily import keyring module."""
    global keyring
    if keyring is None:
        import keyring as kr

        keyring = kr


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


def is_container() -> bool:
    """Detect if running inside a container.

    Checks for Docker, Podman, and Kubernetes indicators.
    """
    # Docker
    if Path("/.dockerenv").exists():
        return True

    # Podman
    if Path("/run/.containerenv").exists():
        return True

    # Check cgroup for container indicators
    cgroup_path = Path("/proc/1/cgroup")
    if cgroup_path.exists():
        try:
            content = cgroup_path.read_text()
            if "docker" in content or "kubepods" in content or "containerd" in content:
                return True
        except (OSError, PermissionError):
            pass

    return False


def get_secret_from_keyring(service: str, name: str) -> str | None:
    """Fetch a secret from the OS keyring.

    Args:
        service: Keyring service/namespace.
        name: Secret name (used as username in keyring).

    Returns:
        Secret value or None if not found.
    """
    load_keyring()
    try:
        return keyring.get_password(service, name)
    except Exception as e:
        print(f"[WARN] Keyring error for {name}: {e}")
        return None


def resolve_secret(name: str, service: str, in_ci: bool, in_container: bool) -> tuple[str | None, str]:
    """Resolve a secret from available sources.

    Args:
        name: Secret name.
        service: Keyring service name.
        in_ci: Whether running in CI.
        in_container: Whether running in container.

    Returns:
        Tuple of (value, source) where source describes where the value came from.
    """
    # Check environment first (highest precedence)
    if name in os.environ:
        return os.environ[name], "environment"

    # In CI/container, keyring is not available
    if in_ci or in_container:
        return None, "not set (CI/container mode)"

    # Try keyring for local development
    value = get_secret_from_keyring(service, name)
    if value:
        return value, "keyring"

    return None, "not found"


def inject_secrets(config: dict) -> tuple[list[str], list[str]]:
    """Inject secrets into the environment.

    Args:
        config: Secrets configuration dictionary.

    Returns:
        Tuple of (missing_required, missing_optional) secret names.
    """
    in_ci = is_ci()
    in_container = is_container()
    service = config["service"]

    env_type = "CI" if in_ci else ("container" if in_container else "local")
    print(f"[INFO] Environment: {env_type}")

    missing_required: list[str] = []
    missing_optional: list[str] = []

    # Process required secrets
    for name in config["required"]:
        value, source = resolve_secret(name, service, in_ci, in_container)
        if value:
            os.environ[name] = value
            print(f"[OK] {name}: loaded from {source}")
        else:
            missing_required.append(name)
            print(f"[FAIL] {name}: {source}")

    # Process optional secrets
    for name in config["optional"]:
        value, source = resolve_secret(name, service, in_ci, in_container)
        if value:
            os.environ[name] = value
            print(f"[OK] {name}: loaded from {source}")
        else:
            missing_optional.append(name)
            print(f"[WARN] {name}: {source} (optional)")

    return missing_required, missing_optional


def print_usage() -> None:
    """Print usage information."""
    print("Usage: uv run scripts/run.py <command> [args...]")
    print()
    print("Injects secrets from keyring/environment, then runs the command.")
    print()
    print("Examples:")
    print("  uv run scripts/run.py uv run pytest")
    print("  uv run scripts/run.py python main.py")
    print()
    print("Setup (local development):")
    print("  uv run scripts/secrets_setup.py")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    if len(sys.argv) < 2:
        print_usage()
        return 1

    # Load configuration
    config = load_secrets_config()

    # Inject secrets
    missing_required, _ = inject_secrets(config)

    # Fail if required secrets are missing
    if missing_required:
        print()
        print("[FAIL] Missing required secrets:")
        for name in missing_required:
            print(f"  - {name}")
        print()
        if is_ci():
            print("In CI: Set these as repository secrets and map to env vars in workflow.")
        elif is_container():
            print("In container: Inject via -e flags or --secret mounts.")
        else:
            print("Local: Run 'uv run scripts/secrets_setup.py' to configure keyring.")
        return 1

    # Execute the command
    print()
    cmd = sys.argv[1:]
    print(f"[INFO] Running: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
