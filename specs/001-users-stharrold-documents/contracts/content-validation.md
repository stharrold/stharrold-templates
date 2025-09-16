# Content Validation Contract

**Phase**: 1 - Core Design
**Date**: 2025-09-14
**Contract Type**: Quality Assurance

## Content Integration Rules

### Duplication Detection Contract

**MUST detect and prevent**:
- Identical code examples
- Repeated installation instructions
- Duplicate tool descriptions
- Redundant configuration examples

**Detection Method**:
```bash
# Content similarity check
diff -u source_section target_section
grep -f source_keywords target_file
wc -c target_file  # Size monitoring
```

**Resolution Strategy**:
- **Identical content**: Skip integration, reference existing
- **Similar content**: Enhance existing with unique elements
- **Complementary content**: Integrate with clear differentiation

### Content Quality Standards

#### Workflow Examples
**MUST meet standards**:
- [ ] All commands are executable and tested
- [ ] Input/output examples are accurate
- [ ] Error conditions are documented
- [ ] Platform variations are complete
- [ ] Security best practices followed

**Example Validation**:
```bash
# Command testing
bash -n script_commands.sh  # Syntax check
shellcheck script_commands.sh  # Quality check
```

#### CLI Examples
**MUST include**:
- [ ] Exact command syntax with full paths
- [ ] Interactive prompts with input masking
- [ ] Success and failure output examples
- [ ] Context and explanation for each command

**Validation Schema**:
```yaml
cli_example:
  command: string (required)
  description: string (required)
  input_required: boolean
  input_masked: boolean (if input_required)
  expected_output: string (required)
  error_conditions: array[string]
  platform_specific: boolean
  platforms: array[string] (if platform_specific)
```

#### Platform Commands
**MUST verify**:
- [ ] Commands work on specified platforms
- [ ] Output examples match current versions
- [ ] Error conditions are reproducible
- [ ] Recovery procedures are effective

**Platform Testing Matrix**:
| Command | macOS | Windows | Linux | Verified |
|---------|-------|---------|-------|----------|
| keychain access | ✓ | N/A | N/A | [ ] |
| credential manager | N/A | ✓ | N/A | [ ] |
| secret service | N/A | N/A | ✓ | [ ] |

### File Size Monitoring Contract

**Size Constraints**:
- **Maximum**: 30,000 bytes (hard limit)
- **Current**: 16,803 bytes
- **Available**: 13,197 bytes
- **Planned**: 8,800 bytes integration
- **Safety**: 4,397 bytes margin

**Monitoring Process**:
```bash
# Real-time size checking during integration
wc -c target_file
echo "Size: $(wc -c < target_file) / 30000 bytes"
```

**Size Optimization Rules**:
1. **Prioritize unique content** over redundant examples
2. **Use concise command examples** without excessive verbosity
3. **Reference existing sections** rather than repeat content
4. **Remove unnecessary whitespace** and formatting

### Cross-Reference Integrity Contract

#### Existing References (MUST preserve):
```markdown
# Parent orchestrator
parent: ./CLAUDE.md

# Related files
- ./21_keychain-macos.md
- ./22_credential-manager-win.md
- ./23_enterprise-sso.md
- ./24_audit-compliance.md

# Internal navigation
- [Tool Selection Guidelines](#tool-selection-guidelines)
- [Integration Patterns](#integration-patterns)
```

#### New References (MUST add):
```markdown
# Workflow navigation
- [Installation Workflow](#step-by-step-installation-workflow)
- [Environment Discovery](#environment-variable-discovery-methods)
- [Error Handling](#error-handling-and-recovery-patterns)

# Platform-specific links
- [macOS Verification](#macos-keychain-storage)
- [Windows Verification](#windows-credential-manager-storage)
- [Linux Verification](#linux-libsecret-storage)
```

**Link Validation**:
```bash
# Check internal links
grep -o '\[.*\](#.*)'target_file | while read link; do
  anchor=$(echo "$link" | sed 's/.*#//')
  grep -q "^#.*$anchor" target_file || echo "Broken link: $link"
done
```

### Content Coherence Contract

#### Narrative Flow Requirements:
- [ ] Introduction → Tools → Workflows → Verification → Troubleshooting
- [ ] Each section builds on previous knowledge
- [ ] Examples increase in complexity appropriately
- [ ] Consistent terminology throughout

#### Tone and Style Standards:
- [ ] Professional but accessible language
- [ ] Consistent code formatting
- [ ] Clear section headings and navigation
- [ ] Actionable instructions with clear outcomes

### Security Standards Contract

#### Credential Handling:
**MUST ensure**:
- [ ] No plaintext credentials in examples
- [ ] All sensitive data properly masked
- [ ] Secure storage methods demonstrated
- [ ] Recovery procedures maintain security

**Security Review Checklist**:
- [ ] Examples follow principle of least privilege
- [ ] Credential rotation procedures included
- [ ] Access auditing guidance provided
- [ ] Emergency response procedures documented

#### Example Security Pattern:
```bash
# GOOD: Masked credential input
$ mcp-secrets set github token
Enter value for 'github_token': ************************************
✓ Credential stored in system keychain

# BAD: Plaintext credential exposure
$ export GITHUB_TOKEN="ghp_actual_token_here"  # NEVER do this
```

## Validation Pipeline Contract

### Phase 1: Pre-Integration Validation
```bash
# Content analysis
source_size=$(wc -c < source_file)
target_size=$(wc -c < target_file)
available_space=$((30000 - target_size))

echo "Source: ${source_size} bytes"
echo "Target: ${target_size} bytes"
echo "Available: ${available_space} bytes"

# Duplication check
unique_content_size=$(estimate_unique_content)
echo "Unique content: ${unique_content_size} bytes"
```

### Phase 2: Integration Validation
```bash
# Size monitoring during integration
while integrating; do
  current_size=$(wc -c < target_file)
  if [ $current_size -gt 30000 ]; then
    echo "ERROR: Size limit exceeded: $current_size bytes"
    exit 1
  fi
  echo "Progress: $current_size / 30000 bytes"
done
```

### Phase 3: Post-Integration Validation
```bash
# Comprehensive validation
./validate_documentation.sh target_file
./check_cross_references.sh target_file
./test_example_commands.sh target_file
./.codacy/cli.sh analyze target_file
```

## Quality Gates Contract

### Gate 1: Content Quality
**MUST pass before integration**:
- [ ] All workflow examples tested
- [ ] Platform commands verified
- [ ] Security standards met
- [ ] Duplication analysis complete

### Gate 2: Size Compliance
**MUST pass during integration**:
- [ ] File size continuously monitored
- [ ] Integration stops if approaching limit
- [ ] Content prioritization applied if needed

### Gate 3: Integration Integrity
**MUST pass after integration**:
- [ ] All cross-references functional
- [ ] Navigation structure preserved
- [ ] Content coherence maintained
- [ ] Version tracking updated

### Gate 4: Final Validation
**MUST pass before completion**:
- [ ] Codacy analysis passes
- [ ] File size under 30KB
- [ ] All examples work as documented
- [ ] User experience enhanced

## Failure Recovery Contract

### Size Limit Exceeded:
1. **Prioritize content** by user value
2. **Remove redundant examples**
3. **Optimize formatting** for space
4. **Reference external content** if needed

### Cross-Reference Broken:
1. **Identify broken links** with validation script
2. **Update anchor references** to match content
3. **Add missing sections** if referenced
4. **Test navigation flow** end-to-end

### Quality Standards Failed:
1. **Document specific failures** for remediation
2. **Fix content issues** before proceeding
3. **Re-run validation** to confirm fixes
4. **Update validation checklist** if needed

### Content Duplication Detected:
1. **Analyze duplication type** (identical vs similar)
2. **Choose integration strategy** (skip, enhance, reference)
3. **Implement chosen strategy** consistently
4. **Verify duplication removed** with re-analysis