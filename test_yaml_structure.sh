#!/bin/bash
# T008: YAML frontmatter structure test

TARGET_FILE="10_draft-merged/20_credentials/25_mcp-security-tools.md"

if [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: Target file not found: $TARGET_FILE"
    exit 1
fi

echo "Testing YAML frontmatter structure in $TARGET_FILE"

# Extract YAML frontmatter (between --- lines)
yaml_content=$(sed -n '/^---$/,/^---$/p' "$TARGET_FILE" | sed '1d;$d')

if [ -z "$yaml_content" ]; then
    echo "FAIL: No YAML frontmatter found"
    exit 1
fi

# Check required fields
required_fields=("title" "version" "updated" "parent")
missing_fields=()

for field in "${required_fields[@]}"; do
    if ! echo "$yaml_content" | grep -q "^$field:"; then
        missing_fields+=("$field")
    fi
done

# Check version format (should be numeric)
version=$(echo "$yaml_content" | grep "^version:" | sed 's/version: *//')
if [[ ! $version =~ ^[0-9]+\.[0-9]+$ ]]; then
    echo "FAIL: Invalid version format: $version (should be X.Y)"
    exit 1
fi

# Check date format (should be YYYY-MM-DD)
updated=$(echo "$yaml_content" | grep "^updated:" | sed 's/updated: *//')
if [[ ! $updated =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "FAIL: Invalid date format: $updated (should be YYYY-MM-DD)"
    exit 1
fi

if [ ${#missing_fields[@]} -eq 0 ]; then
    echo "PASS: YAML structure is valid"
    echo "Version: $version"
    echo "Updated: $updated"
    exit 0
else
    echo "FAIL: Missing required fields: ${missing_fields[*]}"
    exit 1
fi