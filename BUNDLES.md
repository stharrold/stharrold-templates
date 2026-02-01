# BUNDLES.md

Bundle manifest for `stharrold-templates`. Each bundle is a named set of files that can be applied to a target repository.

## Usage

### Quick Start

```bash
cd /path/to/myrepo

# Clone the templates repo
git clone https://github.com/stharrold/stharrold-templates.git .tmp/stharrold-templates

# Apply a bundle
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git

# Apply multiple bundles
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git --bundle secrets

# Apply everything
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle full

# Cleanup
rm -rf .tmp/stharrold-templates
```

### Update (brownfield)

Re-running the same command on an existing repo is safe. Template-owned files are replaced, user-owned files are merged or skipped (see [File Ownership](#file-ownership)):

```bash
# Pull latest templates and re-apply
cd /path/to/myrepo
rm -rf .tmp/stharrold-templates
git clone https://github.com/stharrold/stharrold-templates.git .tmp/stharrold-templates
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git

# Force mode: replace ALL files regardless of ownership
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git --force

# Dry run: show what would change without modifying anything
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git --dry-run
```

---

## Bundles

### `git` -- Git Workflow and Branch Management

Skills, commands, and documentation for the `main <- develop <- contrib/* <- feature/*` branch workflow.

**Skills (template-owned):**
- `.claude/skills/git-workflow-manager/`
- `.claude/skills/workflow-orchestrator/`
- `.claude/skills/workflow-utilities/`

**Commands (template-owned):**
- `.claude/commands/workflow/v7x1_1-worktree.md`
- `.claude/commands/workflow/v7x1_2-integrate.md`
- `.claude/commands/workflow/v7x1_3-release.md`
- `.claude/commands/workflow/v7x1_4-backmerge.md`
- `.claude/commands/workflow/status.md`

**Docs (template-owned):**
- `WORKFLOW.md`
- `CONTRIBUTING.md`

**Merge files (user-owned):**
- `.gitignore` -- appends workflow-specific ignore patterns (e.g. `.worktrees/`)

---

### `secrets` -- Secrets Management

Keyring-backed secrets setup and runtime injection scripts.

**Scripts (template-owned):**
- `scripts/secrets_setup.py`
- `scripts/secrets_run.py`
- `scripts/environment_utils.py`

**Config (user-owned, skip on update):**
- `secrets.toml`

**Merge files (user-owned):**
- `pyproject.toml` -- adds `keyring` and `tomlkit` to `[dependency-groups] dev`

---

### `ci` -- CI, Containers, and Code Quality

GitHub Actions workflows, container definitions, pre-commit hooks, and linting configuration.

**Workflows (template-owned):**
- `.github/workflows/tests.yml`
- `.github/workflows/claude-code-review.yml`
- `.github/workflows/secrets-example.yml`

**Containers (template-owned):**
- `Containerfile`
- `podman-compose.yml`

**Hooks (user-owned, skip on update):**
- `.pre-commit-config.yaml`

**Merge files (user-owned):**
- `pyproject.toml` -- adds `ruff`, `pytest`, `pre-commit` to `[dependency-groups] dev`

---

### `full` -- Everything

All files from `git` + `secrets` + `ci`, plus additional skills and documentation.

**Additional skills (template-owned):**
- `.claude/skills/tech-stack-adapter/`
- `.claude/skills/agentdb-state-manager/`
- `.claude/skills/initialize-repository/`

**Additional docs (template-owned):**
- `docs/` directory structure (`archived/`, `guides/`, `plans/`, `reference/`, `research/`)
- `CLAUDE.md` template

---

## File Ownership

Ownership determines what happens when a bundle is applied to a repo that already has the file.

| Ownership | Files | First Install | Update | `--force` |
|---|---|---|---|---|
| **Template-owned** | Skills, commands, scripts, `WORKFLOW.md`, `CONTRIBUTING.md`, `Containerfile`, workflows | Copy | Replace | Replace |
| **User-owned (merge)** | `pyproject.toml`, `.gitignore` | Create from template | Merge (add missing entries only) | Replace |
| **User-owned (skip)** | `secrets.toml`, `.pre-commit-config.yaml` | Copy from template | Skip + print warning | Replace |
| **Override** | All of the above | -- | -- | Replace all files unconditionally |

### Merge behavior details

- **`.gitignore`**: Appends lines from the template that are not already present. Does not remove existing entries.
- **`pyproject.toml`**: Adds missing packages to `[dependency-groups] dev`. Does not modify existing version pins or remove packages.
- **Skip + warn**: Prints a message like `SKIP secrets.toml (already exists, use --force to overwrite)` to stderr.
- **`--force`**: Creates timestamped backups (e.g. `pyproject.toml.bak.20260131T120000`) before replacing.
