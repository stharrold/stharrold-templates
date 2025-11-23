# Quickstart: Worktree-Aware Workflow

**Feature Branch**: `006-make-the-entire`
**Date**: 2025-11-23

---

## Prerequisites

- Podman and podman-compose installed
- Git repository with `.claude/skills/` structure
- Python 3.11+ (via container)

---

## Quick Verification

### 1. Test Worktree Detection

```bash
# From main repository
podman-compose run --rm dev python -c "
from pathlib import Path
import subprocess

# Get worktree root
root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()

# Check if in worktree
git_path = Path('.git')
is_worktree = git_path.is_file()

print(f'Worktree root: {root}')
print(f'Is worktree: {is_worktree}')
"
```

**Expected Output (main repo)**:
```
Worktree root: /workspace
Is worktree: False
```

### 2. Test State Directory Creation

```bash
podman-compose run --rm dev python -c "
from pathlib import Path
import subprocess
import hashlib

root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
worktree_id = hashlib.sha256(root.encode()).hexdigest()[:12]

state_dir = Path(root) / '.claude-state'
state_dir.mkdir(exist_ok=True)

# Create gitignore
gitignore = state_dir / '.gitignore'
if not gitignore.exists():
    gitignore.write_text('*\n')

# Write worktree ID
id_file = state_dir / '.worktree-id'
id_file.write_text(worktree_id)

print(f'State directory: {state_dir}')
print(f'Worktree ID: {worktree_id}')
print(f'Contents: {list(state_dir.iterdir())}')
"
```

**Expected Output**:
```
State directory: /workspace/.claude-state
Worktree ID: a1b2c3d4e5f6
Contents: [PosixPath('.gitignore'), PosixPath('.worktree-id')]
```

### 3. Test Worktree Creation with State

```bash
# Create a test worktree
podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/create_worktree.py feature test-worktree contrib/stharrold

# Verify state isolation (run from new worktree when created)
```

---

## Integration Test Flow

### Scenario: Two Concurrent Features

```bash
# Terminal 1: Feature A
cd /path/to/repo_feature_a
podman-compose run --rm dev python -c "
from worktree_context import get_state_dir, get_worktree_id
print(f'Worktree A ID: {get_worktree_id()}')
print(f'State dir: {get_state_dir()}')
"

# Terminal 2: Feature B
cd /path/to/repo_feature_b
podman-compose run --rm dev python -c "
from worktree_context import get_state_dir, get_worktree_id
print(f'Worktree B ID: {get_worktree_id()}')
print(f'State dir: {get_state_dir()}')
"
```

**Expected**: Different worktree IDs and state directories for each.

---

## Validation Checklist

- [ ] `get_worktree_context()` returns correct values
- [ ] `.claude-state/` directory created automatically
- [ ] `.gitignore` prevents state from being tracked
- [ ] Worktree ID is stable across invocations
- [ ] Different worktrees have different IDs
- [ ] AgentDB uses worktree-specific database path
- [ ] Workflow progress stored in state directory

---

## Cleanup

```bash
# Remove test state directory
rm -rf .claude-state/

# Remove test worktree
git worktree remove ../repo_feature_test-worktree
git worktree prune
```

---
