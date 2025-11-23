# Contract: Documentation Updates

**Feature Branch**: `007-remove-redundant-todo`
**Date**: 2025-11-23

---

## Contract Purpose

Define the expected documentation state after removing TODO*.md references.

---

## CLAUDE.md Contract

### Section: Quality Gates Table

**Before**:
```markdown
| Gate | Description |
|------|-------------|
| 1. Coverage | ≥80% test coverage |
| 2. Tests | All pytest tests pass |
| 3. Build | `uv build` succeeds |
| 4. Linting | `ruff check .` clean |
| 5. TODO Frontmatter | All TODO*.md have valid YAML frontmatter |
| 6. AI Config Sync | CLAUDE.md → AGENTS.md synced |
```

**After**:
```markdown
| Gate | Description |
|------|-------------|
| 1. Coverage | ≥80% test coverage |
| 2. Tests | All pytest tests pass |
| 3. Build | `uv build` succeeds |
| 4. Linting | `ruff check .` clean |
| 5. AI Config Sync | CLAUDE.md → AGENTS.md synced |
```

---

### Section: TODO*.md YAML Frontmatter (REMOVED)

**Before** (entire section exists):
```markdown
## TODO*.md YAML Frontmatter (Required)

All TODO files must start with:
\`\`\`yaml
---
status: in_progress|completed|blocked
feature: feature-name
branch: feature/timestamp_slug
---
\`\`\`
```

**After**: Section completely removed

---

### Section: PR Workflow

**Before**:
```markdown
## PR Workflow (Enforced Sequence)

\`\`\`bash
# Step 1: PR feature → contrib (runs quality gates)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py finish-feature

# Step 2: Archive TODO after PR merge
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py archive-todo

# Step 3: Sync CLAUDE.md → AGENTS.md
...
```

**After**:
```markdown
## PR Workflow (Enforced Sequence)

\`\`\`bash
# Step 1: PR feature → contrib (runs quality gates)
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py finish-feature

# Step 2: Sync CLAUDE.md → AGENTS.md
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents

# Step 3: PR contrib → develop
...
```

---

### Section: Critical Guidelines

**Before** (contains TODO reference):
```markdown
- **TODO files require YAML frontmatter**: status, feature, branch fields
```

**After**: Line removed

---

## AGENTS.md Contract

**Requirement**: Must be synchronized copy of CLAUDE.md

**Validation**: After CLAUDE.md update, run sync script:
```bash
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/pr_workflow.py sync-agents
```

---

## Validation Tests

### Test: No TODO references in CLAUDE.md
```python
def test_claude_md_no_todo_refs():
    """CLAUDE.md should not reference TODO*.md system."""
    content = Path('CLAUDE.md').read_text()
    assert 'TODO Frontmatter' not in content
    assert 'TODO*.md YAML' not in content
    assert 'archive-todo' not in content
```

### Test: Quality gates shows 5 gates
```python
def test_claude_md_five_gates():
    """CLAUDE.md quality gates table should have 5 gates."""
    content = Path('CLAUDE.md').read_text()
    assert '| 5. AI Config Sync' in content
    assert '| 6.' not in content  # No gate 6
```

### Test: AGENTS.md synced
```python
def test_agents_md_synced():
    """AGENTS.md should match CLAUDE.md content."""
    claude = Path('CLAUDE.md').read_text()
    agents = Path('AGENTS.md').read_text()
    # Core content should match (headers may differ)
    assert 'TODO Frontmatter' not in agents
```
