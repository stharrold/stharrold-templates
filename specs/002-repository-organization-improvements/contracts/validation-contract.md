# Validation Contract: Repository Organization

**Feature**: 002-repository-organization-improvements
**Date**: 2025-11-21

## Contract Type

File structure validation (no API contracts - this is a reorganization task)

## Pre-Conditions

- Repository is on branch `002-repository-organization-improvements`
- All current tests pass
- Quality gates pass

## Post-Conditions

### PC-1: Test Directory Exists
```bash
# MUST pass
test -d tests/
test -f tests/__init__.py
test -f tests/conftest.py
```

### PC-2: Test Discovery Works
```bash
# MUST discover at least 1 test
podman-compose run --rm dev pytest --collect-only | grep "test session starts"
```

### PC-3: No .DS_Store Files Tracked
```bash
# MUST return empty
git ls-files | grep -c ".DS_Store" | grep "^0$"
```

### PC-4: .gitignore Updated
```bash
# MUST contain patterns
grep -q ".DS_Store" .gitignore
grep -q ".tmp/" .gitignore
```

### PC-5: Documentation Structure
```bash
# MUST exist
test -d docs/research/
test -d docs/guides/
test -d docs/archived/
```

### PC-6: Old Directories Removed
```bash
# MUST NOT exist
test ! -d 00_draft-initial/
test ! -d 10_draft-merged/
```

### PC-7: README.md Exists
```bash
# MUST exist with required sections
test -f README.md
grep -q "Quick Start" README.md
grep -q "Prerequisites" README.md
```

### PC-8: Single TODO at Root
```bash
# MUST have exactly 1 TODO*.md at root (TODO.md only)
ls -1 TODO*.md 2>/dev/null | wc -l | grep "^1$"
```

### PC-9: Quality Gates Pass
```bash
# MUST pass all 6 gates
podman-compose run --rm dev python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
```

## Invariants

1. Git history preserved (use `git mv` for renames)
2. No data loss (archive before delete)
3. Internal documentation links updated
4. pyproject.toml test configuration unchanged

## Error Handling

| Failure | Recovery |
|---------|----------|
| Test discovery fails | Check `tests/__init__.py` exists |
| Quality gates fail | Fix issues before proceeding |
| Link broken | Update reference to new path |

## Contract Test Script

```bash
#!/bin/bash
# Run all post-condition checks
set -e

echo "PC-1: Test directory exists..."
test -d tests/ && test -f tests/__init__.py

echo "PC-2: Test discovery works..."
podman-compose run --rm dev pytest --collect-only 2>/dev/null | grep -q "test"

echo "PC-3: No .DS_Store tracked..."
[ "$(git ls-files | grep -c ".DS_Store")" -eq 0 ]

echo "PC-4: .gitignore updated..."
grep -q ".DS_Store" .gitignore

echo "PC-5: Documentation structure..."
test -d docs/research/ && test -d docs/guides/

echo "PC-7: README.md exists..."
test -f README.md

echo "PC-9: Quality gates..."
podman-compose run --rm dev python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py

echo "All contracts validated!"
```
