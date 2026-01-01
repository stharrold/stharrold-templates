#!/bin/bash
# T007: Platform command syntax validation

TARGET_FILE="10_draft-merged/20_credentials/25_mcp-security-tools.md"

if [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: Target file not found: $TARGET_FILE"
    exit 1
fi

echo "Testing bash command syntax in $TARGET_FILE"
errors=0
commands_tested=0

# Extract bash commands from code blocks
in_bash_block=false
while IFS= read -r line; do
    if [[ $line == '```bash' ]]; then
        in_bash_block=true
        continue
    elif [[ $line == '```' ]] && [ "$in_bash_block" = true ]; then
        in_bash_block=false
        continue
    elif [ "$in_bash_block" = true ] && [[ $line =~ ^\$ ]]; then
        # Extract command after $ prompt
        command=$(echo "$line" | sed 's/^\$ *//')

        # Skip empty commands or comments
        [[ -z "$command" || "$command" =~ ^# ]] && continue

        ((commands_tested++))

        # Test command syntax (without executing)
        if ! bash -n <<< "$command" 2>/dev/null; then
            echo "SYNTAX ERROR in command: $command"
            ((errors++))
        fi
    fi
done < "$TARGET_FILE"

echo "Commands tested: $commands_tested"
echo "Syntax errors found: $errors"

if [ $errors -eq 0 ]; then
    echo "PASS: All bash commands have valid syntax"
    exit 0
else
    echo "FAIL: Found $errors syntax errors"
    exit 1
fi
