# Bundle System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make stharrold-templates a portable toolkit where users clone it into any repo and apply specific workflow bundles (git, secrets, ci, or full) via a single Claude command or script invocation.

**Architecture:** A `BUNDLES.md` manifest (Claude reads for understanding) + `scripts/apply_bundle.py` (deterministic execution). Bundles are coarse-grained groups of skills/scripts/configs. The script is idempotent — same command handles first install and updates.

**Tech Stack:** Python 3.11+, shutil, tomllib, argparse. No new dependencies.

**Depends on:** v8.0.0 Tasks 2 (#173 extract environment_utils), 4 (#166 .gemini->.claude rename), and 8 (#169 run.py->secrets_run.py rename) must complete first.

---

## Bundle Definitions

| Bundle | Contents |
|--------|----------|
| **git** | Skills: `git-workflow-manager`, `workflow-orchestrator`, `workflow-utilities`. Commands: `.claude/commands/workflow/`. Docs: `WORKFLOW.md`, `CONTRIBUTING.md`. Merge: `.gitignore`. |
| **secrets** | Scripts: `secrets_setup.py`, `secrets_run.py`, `environment_utils.py`. Config: `secrets.toml`. Merge: `pyproject.toml` (adds keyring, tomlkit). |
| **ci** | Workflows: `tests.yml`, `claude-code-review.yml`, `secrets-example.yml`. Containers: `Containerfile`, `podman-compose.yml`. Hooks: `.pre-commit-config.yaml`. Merge: `pyproject.toml` (adds ruff, pytest, pre-commit). |
| **full** | All of the above + skills: `tech-stack-adapter`, `agentdb-state-manager`, `initialize-repository`. Docs: `docs/` structure, `CLAUDE.md` template. |

## File Ownership Model (Update Behavior)

| Ownership | Files | First install | Update |
|-----------|-------|---------------|--------|
| Template-owned | Skills, commands, scripts, `WORKFLOW.md`, `CONTRIBUTING.md`, `Containerfile`, workflows | Copy | Replace |
| User-owned | `pyproject.toml`, `.gitignore` | Create/copy | Merge only |
| User-owned (skip) | `secrets.toml`, `.pre-commit-config.yaml` | Copy | Skip + warn |
| Override | All of the above | — | `--force` replaces everything |

---

## Task 1: Create `BUNDLES.md` manifest

**Files:**
- Create: `BUNDLES.md`

**Step 1: Write the manifest**

Create `BUNDLES.md` at repo root with:
- Usage section showing the clone-and-apply pattern
- Script invocation examples
- Bundle definitions (git, secrets, ci, full) with exact file paths
- Update/brownfield notes

**Step 2: Commit**

```bash
git add BUNDLES.md
git commit -m "docs: add BUNDLES.md manifest for portable bundle system"
```

---

## Task 2: Create `scripts/apply_bundle.py`

**Files:**
- Create: `scripts/apply_bundle.py`

**Step 1: Write failing test**

```python
# tests/unit/test_apply_bundle.py
import subprocess
def test_apply_bundle_help_exits_zero():
    result = subprocess.run(
        ["python", "scripts/apply_bundle.py", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "bundle" in result.stdout.lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_apply_bundle.py::test_apply_bundle_help_exits_zero -v`
Expected: FAIL with FileNotFoundError or returncode != 0

**Step 3: Write the script**

Create `scripts/apply_bundle.py` with:
- `BUNDLE_DEFINITIONS` dict (source of truth for what each bundle contains)
- `validate_source()` and `validate_target()` (reimplement cleanly — no import from old apply_workflow.py)
- `copy_tree(source, target, rel_dir, force)` — for skill/command dirs
- `copy_files(source, target, rel_paths, force, skip_existing)` — for individual files
- `merge_pyproject_deps(target, deps)` — append missing dev dependencies
- `merge_gitignore(target, patterns)` — append missing patterns
- `resolve_bundles(names)` — expand "full" into constituent bundles, deduplicate
- CLI: `--bundle` (repeatable), `--force`, `--dry-run`
- Ownership logic: template-owned files get replaced; user-owned files get merged or skipped with warning

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_apply_bundle.py::test_apply_bundle_help_exits_zero -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/apply_bundle.py tests/unit/test_apply_bundle.py
git commit -m "feat: add scripts/apply_bundle.py for portable bundle application"
```

---

## Task 3: Add unit tests for bundle definitions

**Files:**
- Modify: `tests/unit/test_apply_bundle.py`

**Step 1: Write tests**

```python
def test_bundle_definitions_have_required_keys():
    """Every bundle has valid structure."""

def test_full_bundle_includes_all_others():
    """full is a superset of git + secrets + ci."""

def test_all_referenced_paths_exist():
    """Every file/dir in BUNDLE_DEFINITIONS exists in repo."""

def test_no_overlapping_skills_between_non_full_bundles():
    """secrets and ci don't accidentally pull skills (except via git)."""

def test_dry_run_makes_no_changes(tmp_path):
    """--dry-run leaves target untouched."""
```

**Step 2: Run tests**

Run: `uv run pytest tests/unit/test_apply_bundle.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/test_apply_bundle.py
git commit -m "test: add unit tests for bundle definitions"
```

---

## Task 4: Add integration tests for apply flow

**Files:**
- Create: `tests/integration/test_apply_bundle.py`

**Step 1: Write tests**

Each test creates a tmp git repo via `tmp_path` + `git init`:

```python
def test_apply_git_bundle_to_empty_repo(tmp_path):
    """Skills, commands, docs land in correct locations."""

def test_apply_secrets_bundle_copies_scripts(tmp_path):
    """scripts/ files copied correctly."""

def test_apply_multiple_bundles(tmp_path):
    """--bundle git --bundle secrets applies both."""

def test_update_replaces_template_owned_files(tmp_path):
    """Apply twice — skills get replaced with fresh copies."""

def test_update_preserves_user_owned_pyproject(tmp_path):
    """Modify pyproject.toml between applies — user changes survive."""

def test_secrets_toml_skipped_on_update(tmp_path):
    """Customized secrets.toml not clobbered on second apply."""

def test_force_overwrites_user_owned_files(tmp_path):
    """--force replaces even user-owned files."""
```

**Step 2: Run tests**

Run: `uv run pytest tests/integration/test_apply_bundle.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_apply_bundle.py
git commit -m "test: add integration tests for bundle apply and update flows"
```

---

## Task 5: Delete `apply_workflow.py`

**Files:**
- Delete: `.claude/skills/initialize-repository/scripts/apply_workflow.py`
- Modify: `.claude/skills/initialize-repository/scripts/CLAUDE.md` — remove apply_workflow.py reference
- Modify: `.claude/skills/initialize-repository/CLAUDE.md` — remove apply_workflow.py section

**Step 1: Delete the file and update docs**

Remove `apply_workflow.py` and all references to it in the initialize-repository skill docs.

**Step 2: Run tests to verify nothing breaks**

Run: `uv run pytest -v`
Expected: PASS (no tests import apply_workflow.py)

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: delete apply_workflow.py, replaced by scripts/apply_bundle.py"
```

---

## Task 6: Update root docs

**Files:**
- Modify: `CLAUDE.md` — add pointer to `BUNDLES.md`
- Modify: `README.md` — add bundle usage to quick-start

**Step 1: Edit CLAUDE.md**

Add under Key Context or a new section:
```markdown
## Bundles

This repo provides installable workflow bundles. See [BUNDLES.md](BUNDLES.md) for available bundles and usage.
```

**Step 2: Edit README.md**

Add to quick-start:
```markdown
## Apply to an existing repo

    cd /path/to/myrepo
    git clone https://github.com/stharrold/stharrold-templates.git .tmp/stharrold-templates
    python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git
    rm -rf .tmp/stharrold-templates
```

**Step 3: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: add bundle system references to CLAUDE.md and README.md"
```

---

## Verification

```bash
# Tests pass
uv run pytest tests/unit/test_apply_bundle.py tests/integration/test_apply_bundle.py -v

# Lint clean
uv run ruff check scripts/apply_bundle.py

# Smoke test
mkdir /tmp/test-bundle && cd /tmp/test-bundle && git init
python /path/to/stharrold-templates/scripts/apply_bundle.py /path/to/stharrold-templates . --bundle full --dry-run
python /path/to/stharrold-templates/scripts/apply_bundle.py /path/to/stharrold-templates . --bundle git
ls .claude/skills/  # expect 3 skills
python /path/to/stharrold-templates/scripts/apply_bundle.py /path/to/stharrold-templates . --bundle secrets
ls scripts/         # expect 3 scripts
rm -rf /tmp/test-bundle

# No references to old apply_workflow.py
grep -rn "apply_workflow" --include="*.py" --include="*.md"
```
