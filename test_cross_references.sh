#!/bin/bash
# T005: Cross-reference integrity test

TARGET_FILE="10_draft-merged/20_credentials/25_mcp-security-tools.md"

if [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: Target file not found: $TARGET_FILE"
    exit 1
fi

echo "Testing internal links in $TARGET_FILE"
errors=0

# Extract internal links and check if targets exist
while IFS= read -r link; do
    if [[ $link =~ \[(.*)\]\((#.*)\) ]]; then
        link_text="${BASH_REMATCH[1]}"
        anchor="${BASH_REMATCH[2]#\#}"  # Remove leading #

        # Convert anchor to expected format (lowercase, spaces to dashes)
        expected_anchor=$(echo "$anchor" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

        # Check if anchor exists in file
        if ! grep -qi "^##.*$expected_anchor\|id=\"$expected_anchor\"" "$TARGET_FILE"; then
            echo "BROKEN LINK: [$link_text]($anchor)"
            ((errors++))
        fi
    fi
done < <(grep -o '\[.*\](#[^)]*)' "$TARGET_FILE")

# Check external file references
while IFS= read -r ref; do
    if [[ $ref =~ \[(.*)\]\((\.\/.*\.md)\) ]]; then
        file_path="${BASH_REMATCH[2]#./}"
        full_path="10_draft-merged/20_credentials/$file_path"

        if [ ! -f "$full_path" ]; then
            echo "MISSING EXTERNAL FILE: $file_path"
            ((errors++))
        fi
    fi
done < <(grep -o '\[.*\](\.\/.*\.md)' "$TARGET_FILE")

if [ $errors -eq 0 ]; then
    echo "PASS: All cross-references are valid"
    exit 0
else
    echo "FAIL: Found $errors broken references"
    exit 1
fi
