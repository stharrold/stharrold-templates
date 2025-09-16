#!/bin/bash
# T006: Content duplication detection test

SOURCE_FILE="00_draft-initial/09_workflow-secrets-mcp.md"
TARGET_FILE="10_draft-merged/20_credentials/25_mcp-security-tools.md"

if [ ! -f "$SOURCE_FILE" ] || [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: Source or target file not found"
    exit 1
fi

echo "Testing for content duplication between source and target"
duplicates=0

# Check for identical lines (ignoring whitespace)
while IFS= read -r line; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

    # Check if line exists in target (case insensitive, allowing for minor differences)
    if grep -Fqi "$line" "$TARGET_FILE" 2>/dev/null; then
        echo "POTENTIAL DUPLICATE: $line"
        ((duplicates++))
    fi
done < "$SOURCE_FILE"

# Check for similar tool descriptions
echo "Checking for overlapping tool descriptions..."
overlap_score=0

# Count mentions of key terms in both files
for term in "mcp-secrets-plugin" "mcpauth" "oauth" "credential" "keyring"; do
    source_count=$(grep -ci "$term" "$SOURCE_FILE")
    target_count=$(grep -ci "$term" "$TARGET_FILE")

    if [ $source_count -gt 0 ] && [ $target_count -gt 0 ]; then
        echo "Overlap on '$term': Source($source_count) Target($target_count)"
        overlap_score=$((overlap_score + 1))
    fi
done

echo "Content overlap analysis:"
echo "- Duplicate lines found: $duplicates"
echo "- Tool overlap score: $overlap_score/5"

# Consider it a problem if too many duplicates
if [ $duplicates -gt 10 ]; then
    echo "FAIL: Too many duplicate lines ($duplicates > 10)"
    exit 1
elif [ $overlap_score -eq 5 ]; then
    echo "WARN: High overlap detected, deduplication needed during integration"
    exit 0
else
    echo "PASS: Acceptable overlap level for integration"
    exit 0
fi