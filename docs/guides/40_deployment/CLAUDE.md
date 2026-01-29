---
type: claude-context
directory: docs/guides/40_deployment
purpose: Deployment and application documentation for stharrold-templates
parent: ../../CLAUDE.md
children: []
sibling_readme: README.md
---

# Deployment Documentation

This directory contains guides for deploying stharrold-templates to target repositories.

## Contents

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start |
| `version-mapping.md` | Version numbering guide |
| `decision-matrix.md` | Method selection guide |
| `application-guide.md` | Step-by-step instructions |
| `project-inventory.md` | Current project status |

## Quick Reference

**Apply to new repository:**
```bash
python .claude/skills/initialize-repository/scripts/initialize_repository.py \
  D:\Projects\stharrold-templates D:\Projects\target-repo
```

**Batch apply to multiple existing repositories:**
```bash
cd D:\Projects
bash apply-workflow-batch.sh
```

**Verify installation:**
```bash
bash verify-workflow.sh
```

## Related Documentation

- **[README.md](README.md)** - Human-readable documentation for this directory
- **[../CLAUDE.md](../CLAUDE.md)** - Parent directory: guides
