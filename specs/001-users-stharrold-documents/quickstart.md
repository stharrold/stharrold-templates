# Quickstart: Workflow Secrets Integration

**Phase**: 1 - Core Design
**Date**: 2025-09-14
**Purpose**: Step-by-step validation of the integration process

## Pre-Integration Setup

### Environment Validation
```bash
# Verify current working directory
pwd
# Should be: /Users/stharrold/Documents/GitHub/stharrold-templates.worktrees/feat/12-integrate-workflow-secrets

# Check current branch
git branch --show-current
# Should be: feat/12-integrate-workflow-secrets

# Verify file existence and sizes
ls -la 00_draft-initial/09_workflow-secrets-mcp.md
ls -la 10_draft-merged/20_credentials/25_mcp-security-tools.md

# Check initial file size
echo "Source size: $(wc -c < 00_draft-initial/09_workflow-secrets-mcp.md) bytes"
echo "Target size: $(wc -c < 10_draft-merged/20_credentials/25_mcp-security-tools.md) bytes"
echo "Available space: $((30000 - $(wc -c < 10_draft-merged/20_credentials/25_mcp-security-tools.md))) bytes"
```

**Expected Results**:
- Source file: ~11,600 bytes
- Target file: ~16,800 bytes
- Available space: ~13,200 bytes
- Integration space needed: ~8,800 bytes

## Content Analysis Phase

### Step 1: Analyze Source Content
```bash
# Extract unique content sections from source
grep -n "^##\|^###" 00_draft-initial/09_workflow-secrets-mcp.md

# Check for potential duplications
grep -i "mcp-secrets-plugin" 00_draft-initial/09_workflow-secrets-mcp.md | wc -l
grep -i "mcp-secrets-plugin" 10_draft-merged/20_credentials/25_mcp-security-tools.md | wc -l
```

**Expected Results**:
- Source contains detailed workflow examples not in target
- Minimal overlap with existing tool descriptions
- Unique content ready for integration

### Step 2: Map Integration Points
```bash
# Identify target sections for enhancement
grep -n "^## \|^### " 10_draft-merged/20_credentials/25_mcp-security-tools.md

# Check current structure
head -30 10_draft-merged/20_credentials/25_mcp-security-tools.md | grep -E "^(title|version|updated):"
```

**Expected Results**:
- Clear section structure identified
- Version tracking ready for update
- Integration points mapped

## Integration Execution Phase

### Step 3: Create Backup
```bash
# Backup original target file
cp 10_draft-merged/20_credentials/25_mcp-security-tools.md 10_draft-merged/20_credentials/25_mcp-security-tools.md.backup

# Verify backup
diff 10_draft-merged/20_credentials/25_mcp-security-tools.md 10_draft-merged/20_credentials/25_mcp-security-tools.md.backup
echo "Backup status: $?"  # Should be 0 (no differences)
```

### Step 4: Update YAML Frontmatter
```bash
# Update version and date in target file
sed -i '' 's/version: 1.0/version: 1.1/' 10_draft-merged/20_credentials/25_mcp-security-tools.md
sed -i '' 's/updated: 2025-09-13/updated: 2025-09-14/' 10_draft-merged/20_credentials/25_mcp-security-tools.md

# Verify changes
head -10 10_draft-merged/20_credentials/25_mcp-security-tools.md | grep -E "(version|updated):"
```

**Expected Results**:
- Version updated to 1.1
- Date updated to 2025-09-14
- Changelog ready for addition

### Step 5: Integrate Content Sections

#### 5a: Enhance mcp-secrets-plugin section
```bash
# Locate insertion point for workflow examples
grep -n "mcp-secrets-plugin" 10_draft-merged/20_credentials/25_mcp-security-tools.md

# Check section size before integration
sed -n '/### mcp-secrets-plugin/,/### mcpauth/p' 10_draft-merged/20_credentials/25_mcp-security-tools.md | wc -c
```

#### 5b: Add Environment Variable Discovery section
```bash
# Find insertion point after tool descriptions
grep -n "Tool Selection Guidelines\|Integration Patterns" 10_draft-merged/20_credentials/25_mcp-security-tools.md
```

#### 5c: Add Error Handling section
```bash
# Plan placement before "Next Steps"
grep -n "Next Steps\|^## " 10_draft-merged/20_credentials/25_mcp-security-tools.md | tail -5
```

### Step 6: Size Monitoring During Integration
```bash
# Monitor file size continuously
watch -n 1 'echo "Current size: $(wc -c < 10_draft-merged/20_credentials/25_mcp-security-tools.md) / 30000 bytes"'

# Check progress
current_size=$(wc -c < 10_draft-merged/20_credentials/25_mcp-security-tools.md)
echo "Size progress: $current_size bytes"
if [ $current_size -gt 25000 ]; then
  echo "WARNING: Approaching size limit"
elif [ $current_size -gt 30000 ]; then
  echo "ERROR: Size limit exceeded"
  exit 1
fi
```

## Content Validation Phase

### Step 7: Duplicate Content Check
```bash
# Check for unintentional duplication
./scripts/check-duplicates.sh 10_draft-merged/20_credentials/25_mcp-security-tools.md

# Validate unique content integration
diff -u 10_draft-merged/20_credentials/25_mcp-security-tools.md.backup 10_draft-merged/20_credentials/25_mcp-security-tools.md | wc -l
```

**Expected Results**:
- No duplicate content detected
- Changes only in planned sections
- Unique workflow examples successfully integrated

### Step 8: Cross-Reference Validation
```bash
# Test all internal links
grep -o '\[.*\](#.*)'10_draft-merged/20_credentials/25_mcp-security-tools.md | while read link; do
  anchor=$(echo "$link" | sed 's/.*#//' | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
  if ! grep -q "^#.*$anchor\|id=\"$anchor\"" 10_draft-merged/20_credentials/25_mcp-security-tools.md; then
    echo "Potential broken link: $link"
  fi
done

# Check external references
grep -o '\[.*\](\.\/.*\.md)' 10_draft-merged/20_credentials/25_mcp-security-tools.md | while read ref; do
  file_path=$(echo "$ref" | sed 's/.*(\.\///' | sed 's/).*//')
  if [ ! -f "10_draft-merged/20_credentials/$file_path" ]; then
    echo "Missing referenced file: $file_path"
  fi
done
```

**Expected Results**:
- All internal links functional
- External references valid
- Navigation structure preserved

### Step 9: Platform Command Testing
```bash
# Test macOS commands (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
  security find-generic-password -s "test" 2>/dev/null || echo "macOS keychain accessible"
fi

# Test command syntax
grep -A 3 -B 1 '```bash' 10_draft-merged/20_credentials/25_mcp-security-tools.md | while read cmd; do
  if [[ $cmd == "$ "* ]]; then
    command_only=$(echo "$cmd" | sed 's/^\$ //')
    bash -n <<< "$command_only" || echo "Syntax error in: $cmd"
  fi
done
```

**Expected Results**:
- Platform-specific commands appropriate for environment
- All bash commands have valid syntax
- Examples are executable and safe

## Quality Assurance Phase

### Step 10: File Size Final Check
```bash
# Final size validation
final_size=$(wc -c < 10_draft-merged/20_credentials/25_mcp-security-tools.md)
echo "Final file size: $final_size bytes"
echo "Size limit: 30,000 bytes"
echo "Compliance: $((final_size <= 30000 ? "PASS" : "FAIL"))"

if [ $final_size -gt 30000 ]; then
  echo "ERROR: File size exceeds limit by $((final_size - 30000)) bytes"
  exit 1
fi
```

### Step 11: Codacy Analysis
```bash
# Run code quality analysis
./.codacy/cli.sh analyze 10_draft-merged/20_credentials/25_mcp-security-tools.md

echo "Codacy analysis status: $?"
```

**Expected Results**:
- File size under 30KB
- Codacy analysis passes
- No quality issues detected

### Step 12: Content Coherence Review
```bash
# Check section flow and navigation
echo "=== DOCUMENT STRUCTURE ==="
grep -n "^#" 10_draft-merged/20_credentials/25_mcp-security-tools.md

# Verify changelog updated
echo "=== CHANGELOG ==="
grep -A 5 "changelog:" 10_draft-merged/20_credentials/25_mcp-security-tools.md
```

**Expected Results**:
- Logical section progression maintained
- Changelog includes integration details
- Navigation structure clear and functional

## Completion Phase

### Step 13: Archive Source File
```bash
# Move source to archive with UTC timestamp
archive_name="ARCHIVED/$(date -u +"%Y%m%dT%H%M%SZ")_09_workflow-secrets-mcp.md"
mv 00_draft-initial/09_workflow-secrets-mcp.md "$archive_name"

# Verify archive
ls -la "$archive_name"
echo "Source archived successfully: $archive_name"
```

### Step 14: Update Tracking Documents
```bash
# Update TODO.md to mark issue complete
grep -n "issue: 12" TODO.md || echo "Issue tracking needs update"

# Prepare commit message
cat << EOF > commit_message.txt
feat: integrate workflow secrets patterns into security tools

- Enhanced 25_mcp-security-tools.md with practical workflow examples
- Added mcp-secrets-plugin installation and usage patterns
- Included environment variable discovery methods
- Added platform-specific credential verification steps
- Integrated error handling and recovery patterns
- Archived source document with UTC timestamp

Closes #12

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
```

### Step 15: Final Validation
```bash
# Run complete validation suite
echo "=== INTEGRATION VALIDATION SUMMARY ==="
echo "File size: $(wc -c < 10_draft-merged/20_credentials/25_mcp-security-tools.md) / 30000 bytes"
echo "Source archived: $(ls ARCHIVED/*09_workflow-secrets-mcp.md | wc -l) files"
echo "Cross-references: $(grep -o '\[.*\](#.*)'10_draft-merged/20_credentials/25_mcp-security-tools.md | wc -l) internal links"
echo "New sections: $(grep -c "Environment Variable Discovery\|Error Handling and Recovery" 10_draft-merged/20_credentials/25_mcp-security-tools.md) added"

# Success criteria checklist
cat << EOF
=== SUCCESS CRITERIA VALIDATION ===
[ ] File size under 30KB
[ ] Source content integrated without duplication
[ ] Cross-references functional
[ ] Platform commands tested
[ ] Codacy analysis passes
[ ] Source archived with timestamp
[ ] Ready for commit and issue closure
EOF
```

## Rollback Procedure (if needed)

### Emergency Rollback
```bash
# If integration fails, restore backup
if [ -f "10_draft-merged/20_credentials/25_mcp-security-tools.md.backup" ]; then
  cp 10_draft-merged/20_credentials/25_mcp-security-tools.md.backup 10_draft-merged/20_credentials/25_mcp-security-tools.md
  echo "Rollback completed - original file restored"
fi

# Restore source file if archived prematurely
if [ -f "ARCHIVED/*_09_workflow-secrets-mcp.md" ]; then
  mv ARCHIVED/*_09_workflow-secrets-mcp.md 00_draft-initial/09_workflow-secrets-mcp.md
  echo "Source file restored to draft area"
fi
```

## Success Metrics

**Integration Success**:
- ✅ Enhanced documentation with practical examples
- ✅ File size maintained under 30KB
- ✅ No duplicate content
- ✅ Cross-references functional
- ✅ Platform commands verified

**Quality Success**:
- ✅ Codacy analysis passes
- ✅ Content flows logically
- ✅ User experience enhanced
- ✅ Security best practices maintained

**Process Success**:
- ✅ Source properly archived
- ✅ Version tracking updated
- ✅ Issue #12 ready for closure
- ✅ Documentation lifecycle complete