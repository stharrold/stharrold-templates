#!/bin/bash
# T004: File size compliance test - must be < 30KB

TARGET_FILE="10_draft-merged/20_credentials/25_mcp-security-tools.md"
MAX_SIZE=30000  # 30KB limit

if [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: Target file not found: $TARGET_FILE"
    exit 1
fi

current_size=$(wc -c < "$TARGET_FILE")
echo "Current file size: $current_size bytes"
echo "Size limit: $MAX_SIZE bytes"

if [ $current_size -gt $MAX_SIZE ]; then
    echo "FAIL: File size exceeds limit by $((current_size - MAX_SIZE)) bytes"
    exit 1
else
    echo "PASS: File size within limit ($(($MAX_SIZE - current_size)) bytes remaining)"
    exit 0
fi
