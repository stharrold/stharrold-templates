# stharrold-templates

Templates and utilities for MCP (Model Context Protocol) server configuration and agentic development workflows.

## Features

- **v7x1 Workflow** - Streamlined 4-step autonomous development process
- **Claude Code Review** - Automated PR analysis via GitHub Actions
- **AgentDB Tracking** - Persistent state and metrics using DuckDB
- **Containerized development** - Podman + uv + Python 3.11 for consistency
- **AI-optimized documentation** - Modular guides (≤30KB per file) for context efficiency
- **Gemini-first design** - Optimized for Claude Code and MCP (Model Context Protocol)

## Prerequisites

```bash
podman --version          # 4.0+
podman-compose --version
git --version

# GitHub CLI:
gh --version              # GitHub CLI (for PR operations)
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/stharrold/stharrold-templates.git
cd stharrold-templates

# Build the container
podman-compose build

# Run tests
podman-compose run --rm dev pytest
```

## Usage

Workflow commands use `uv run` directly for speed and simplicity:

```bash
uv run <command>
```

For containerized execution (e.g., in CI or strictly isolated environments):

```bash
podman-compose run --rm dev uv run <command>
```

Common operations:

| Command | Description |
|---------|-------------|
| `pytest` | Run tests |
| `ruff check .` | Lint code |

## Apply to an Existing Repo

```bash
cd /path/to/myrepo
git clone https://github.com/stharrold/stharrold-templates.git .tmp/stharrold-templates

# Apply specific bundles (git, secrets, ci, or full)
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle git
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle secrets

# Or apply everything
python .tmp/stharrold-templates/scripts/apply_bundle.py .tmp/stharrold-templates . --bundle full

rm -rf .tmp/stharrold-templates
```

See [BUNDLES.md](BUNDLES.md) for bundle contents and update behavior.

## Secrets Management

Cross-platform secrets management using environment variables with keyring fallback.

### Setup (Local Development)

```bash
# Configure secrets in OS keyring (one-time)
uv run scripts/secrets_setup.py

# Verify secrets are configured
uv run scripts/secrets_setup.py --check
```

### Usage

```bash
# Run any command with secrets injected
uv run scripts/secrets_run.py <command> [args...]

# Examples
uv run scripts/secrets_run.py uv run pytest
uv run scripts/secrets_run.py python main.py
```

### How It Works

1. **Environment variable set** -> uses it (allows external injection)
2. **CI detected** -> requires env vars (GitHub Actions, etc.)
3. **Container detected** -> requires env vars (Docker, Podman)
4. **Local development** -> fetches from OS keyring

### Platform Notes

| Platform | Keyring Backend |
|----------|-----------------|
| macOS | Keychain (automatic) |
| Windows | Credential Manager (automatic) |
| Linux | libsecret/KWallet (may require: `apt install libsecret-1-0`) |

### CI/CD Configuration

**GitHub Actions** - Set secrets in repository settings, map to env vars:
```yaml
env:
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
  API_KEY: ${{ secrets.API_KEY }}
```

**Containers** - Inject at runtime:
```bash
podman run --secret db_pass,type=env,target=DB_PASSWORD ...
docker run -e DB_PASSWORD="$DB_PASSWORD" ...
```

See `secrets.toml` for secret definitions.

## Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | AI agent instructions |
| [WORKFLOW.md](WORKFLOW.md) | Complete workflow guide |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Project Structure

```
├── tests/                  # pytest test suite
├── docs/                   # Documentation
│   ├── guides/             # Production guides
│   ├── research/           # Exploratory documents
│   └── reference/          # Reference materials
├── .claude/skills/         # AI workflow skills (6 active)
├── scripts/                # Utility scripts (secrets, run helpers)
└── ARCHIVED/               # Archived specs, planning docs, deprecated code
```

## License

See repository for license information.
