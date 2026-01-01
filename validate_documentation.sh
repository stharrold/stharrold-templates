#!/bin/bash
# T016: Documentation validation (alternative to Codacy)

TARGET_FILE="10_draft-merged/20_credentials/25_mcp-security-tools.md"

echo "Validating documentation quality for $TARGET_FILE"
errors=0

# Check 1: Valid markdown structure
echo "1. Checking markdown structure..."
if command -v markdown >/dev/null 2>&1; then
    markdown "$TARGET_FILE" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✓ Markdown structure is valid"
    else
        echo "   ✗ Markdown structure has issues"
        ((errors++))
    fi
else
    echo "   ⚠ Markdown validator not available, skipping"
fi

# Check 2: No trailing whitespace
echo "2. Checking for trailing whitespace..."
trailing_lines=$(grep -n '[[:space:]]$' "$TARGET_FILE" | wc -l)
if [ $trailing_lines -eq 0 ]; then
    echo "   ✓ No trailing whitespace found"
else
    echo "   ✗ Found $trailing_lines lines with trailing whitespace"
    ((errors++))
fi

# Check 3: Consistent heading structure
echo "3. Checking heading structure..."
if grep -q "^##[^#]" "$TARGET_FILE" && grep -q "^###[^#]" "$TARGET_FILE"; then
    echo "   ✓ Consistent heading hierarchy"
else
    echo "   ⚠ Check heading hierarchy manually"
fi

# Check 4: Code blocks are closed
echo "4. Checking code block closure..."
# Count all ``` markers (both opening like ```python and closing like ```)
# A balanced document has an even number of markers
all_start_blocks=$(grep -c '^```' "$TARGET_FILE")

# Code blocks should be pairs (start + end)
if [ $((all_start_blocks % 2)) -eq 0 ]; then
    expected_pairs=$((all_start_blocks / 2))
    echo "   ✓ Code blocks balanced: $all_start_blocks markers ($expected_pairs pairs)"
else
    echo "   ✗ Odd number of code block markers: $all_start_blocks (should be even)"
    ((errors++))
fi

# Summary
if [ $errors -eq 0 ]; then
    echo "✅ PASS: Documentation validation successful"
    exit 0
else
    echo "❌ FAIL: Found $errors issues"
    exit 1
fi
