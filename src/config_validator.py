# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Lightweight JSON schema validator for config.{env}.json files.

Validates configuration files against config.schema.json without
requiring the jsonschema library. Uses simple type and constraint checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_schema() -> dict[str, Any]:
    """Load the JSON schema from config.schema.json.

    Returns:
        Schema dictionary.

    Raises:
        FileNotFoundError: If config.schema.json is missing.
    """
    schema_path = Path(__file__).parent.parent / "config" / "config.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        result: dict[str, Any] = json.load(f)
        return result


def validate_config(config: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Validate a config dict against the schema.

    Args:
        config: Configuration dictionary to validate.
        schema: JSON schema dictionary.

    Returns:
        List of error messages. Empty list means valid.
    """
    errors: list[str] = []
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Check required fields
    for field in required:
        if field not in config:
            errors.append(f"Missing required field: '{field}'")

    # Check additionalProperties
    if not schema.get("additionalProperties", True):
        allowed = set(properties.keys())
        for key in config:
            if key not in allowed:
                errors.append(f"Unknown field: '{key}'")

    # Validate each property
    for key, value in config.items():
        prop_schema = properties.get(key)
        if prop_schema is None:
            continue

        expected_type = prop_schema.get("type")
        if expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{key}' must be a string, got {type(value).__name__}")
                continue
            min_len = prop_schema.get("minLength")
            if min_len is not None and len(value) < min_len:
                errors.append(f"Field '{key}' must be at least {min_len} characters")
            enum_values = prop_schema.get("enum")
            if enum_values is not None and value not in enum_values:
                errors.append(f"Field '{key}' must be one of {enum_values}, got '{value}'")

        elif expected_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"Field '{key}' must be an integer, got {type(value).__name__}")
                continue
            minimum = prop_schema.get("minimum")
            if minimum is not None and value < minimum:
                errors.append(f"Field '{key}' must be >= {minimum}, got {value}")
            maximum = prop_schema.get("maximum")
            if maximum is not None and value > maximum:
                errors.append(f"Field '{key}' must be <= {maximum}, got {value}")

    return errors


def validate_config_file(config: dict[str, Any] | Any) -> None:
    """Validate a config dict and raise on errors.

    Args:
        config: Configuration dictionary to validate.

    Raises:
        ValueError: If the config is invalid.
        FileNotFoundError: If the schema file is missing.
    """
    schema = load_schema()
    errors = validate_config(config, schema)
    if errors:
        raise ValueError(
            "Config validation failed:\n  - " + "\n  - ".join(errors)
        )
