# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""JSON repair utilities for handling malformed LLM outputs.

Uses the `json-repair` package (PyPI) for robust repair, plus custom cleanup
for schema-specific issues (nested entity fields, empty nodes).

Usage:
    from utils.json_repair import repair_json, clean_json

    raw = '{"summary": "test", "entities": [{"name": "foo"'
    result, repairs = repair_json(raw)
    # result = {"summary": "test", "entities": [{"name": "foo"}]}
    # repairs = ["json-repair: fixed malformed JSON"]

    cleaned = clean_json(result)
    # Removes empty strings, null values, empty lists, nested "entity" fields
"""

import json
import logging

from json_repair import repair_json as _lib_repair_json

logger = logging.getLogger(__name__)


def repair_json(raw: str) -> tuple[dict | None, list[str]]:
    """Attempt to repair malformed JSON from LLM output.

    Uses the json-repair library which handles:
    - Truncated JSON (unclosed brackets/braces)
    - Trailing commas
    - Missing quotes around keys
    - Single quotes instead of double quotes
    - Unescaped characters in strings
    - And many more edge cases

    Returns:
        (parsed_dict, list_of_repairs_applied)
        If repair fails, returns (None, ["error: ..."])
    """
    repairs = []

    if not raw or not raw.strip():
        return None, ["error: empty input"]

    text = raw.strip()

    # Step 1: Try direct parse first (no repair needed)
    try:
        return json.loads(text), []
    except json.JSONDecodeError:
        pass

    # Step 2: Use json-repair library
    try:
        repaired = _lib_repair_json(text)

        # json-repair returns a string or parsed object depending on version
        if isinstance(repaired, str):
            result = json.loads(repaired)
        else:
            result = repaired

        repairs.append("json-repair: fixed malformed JSON")
        return result, repairs

    except Exception as e:
        repairs.append(f"error: json-repair failed: {e}")
        return None, repairs


def clean_json(data: dict) -> dict:
    """Remove empty/null nodes from JSON structure.

    Removes:
    - Empty strings ""
    - None/null values
    - Empty lists []
    - Empty dicts {}
    - Nested "entity" fields (schema drift from model)

    Keeps:
    - Zero values (0, 0.0)
    - False boolean
    """
    if not isinstance(data, dict):
        return data

    cleaned = {}

    for key, value in data.items():
        # Skip nested "entity" fields (model schema drift)
        if key == "entity" and isinstance(value, dict):
            continue

        # Recursively clean nested structures
        if isinstance(value, dict):
            cleaned_value = clean_json(value)
            if cleaned_value:  # Skip empty dicts
                cleaned[key] = cleaned_value
        elif isinstance(value, list):
            cleaned_list = []
            for item in value:
                if isinstance(item, dict):
                    cleaned_item = clean_json(item)
                    if cleaned_item:  # Skip empty dicts in lists
                        cleaned_list.append(cleaned_item)
                elif item is not None and item != "":
                    cleaned_list.append(item)
            if cleaned_list:  # Skip empty lists
                cleaned[key] = cleaned_list
        elif value is not None and value != "":
            cleaned[key] = value

    return cleaned


def repair_and_clean(raw: str) -> tuple[dict | None, list[str]]:
    """Convenience function: repair then clean JSON.

    Returns:
        (cleaned_dict, list_of_operations)
    """
    result, repairs = repair_json(raw)

    if result is None:
        return None, repairs

    cleaned = clean_json(result)
    if cleaned != result:
        repairs.append("cleaned: removed empty/null nodes or schema drift")

    return cleaned, repairs


# Regression test reference
REGRESSION_TEST_EMAIL = {
    "message_id": "000000001B4AEAFDD4E30C4689D7A388B3CA73CE0700F2C96C0130B50149A6B9F53DC3D0B6800000000001470000F2C96C0130B50149A6B9F53DC3D0B680000187432C260000",
    "subject": "RE: cpsc access and throughput validation",
    "failure_mode": "JSON truncation at num_predict=150 tokens",
    "raw_truncated_sample": '{ "summary": "...", "entities": [ { "name": "Pediatrics", "type": "Department", "confidence": 0.90, "entity": {',
    "notes": "Model generates nested 'entity' fields (schema drift) and needs ~300 tokens for full response",
}


if __name__ == "__main__":
    # Self-test with truncated JSON samples
    test_cases = [
        # Truncated mid-object
        ('{"summary": "test", "entities": [{"name": "foo"', "truncated"),
        # Trailing comma
        ('{"summary": "test", "entities": [],}', "trailing comma"),
        # Nested entity (schema drift)
        (
            '{"summary": "test", "entities": [{"name": "foo", "type": "Topic", "entity": {"name": "bar"}}]}',
            "nested entity",
        ),
        # Valid JSON
        ('{"summary": "test", "entities": []}', "valid"),
        # Missing quotes on keys
        ('{summary: "test"}', "unquoted key"),
        # Single quotes
        ("{'summary': 'test'}", "single quotes"),
    ]

    for raw, desc in test_cases:
        result, repairs = repair_and_clean(raw)
        status = "OK" if result else "FAIL"
        print(f"{desc:20} | {status} | repairs: {repairs}")
        if result:
            print(f"                     | result: {json.dumps(result)}")
