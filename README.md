# stharrold-templates

Templates and utilities for MCP (Model Context Protocol) server configuration and agentic development workflows.

## Features

- **Multi-platform MCP manager** (`mcp_manager.py`) - Configure Claude Code CLI, VS Code, and Claude Desktop
- **Containerized development** - Podman + uv + Python 3.11 for consistent environments
- **Workflow automation** - Git helpers, archive management, semantic versioning
- **AI-optimized documentation** - Modular guides (≤30KB per file) for context efficiency
- **Cross-tool AI compatibility** - Configuration syncs to `.agents/` ([OpenAI agents.md spec](https://github.com/openai/agents.md)) and `.github/copilot-instructions.md` for Cursor, Windsurf, GitHub Copilot, and other AI assistants

## Prerequisites

```bash
podman --version          # 4.0+
podman-compose --version
git --version

# VCS Provider CLI (one of):
gh --version              # GitHub CLI (for GitHub repos)
# OR
az --version              # Azure CLI (for Azure DevOps repos)
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

# Check MCP status
podman-compose run --rm dev python mcp_manager.py --status
```

## Usage

All commands run through the container:

```bash
podman-compose run --rm dev <command>
```

Common operations:

| Command | Description |
|---------|-------------|
| `pytest` | Run tests |
| `ruff check .` | Lint code |
| `python mcp_manager.py --status` | Check MCP configuration |

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
uv run scripts/run.py <command> [args...]

# Examples
uv run scripts/run.py uv run pytest
uv run scripts/run.py python main.py
```

### How It Works

1. **Environment variable set** -> uses it (allows external injection)
2. **CI detected** -> requires env vars (GitHub Actions, Azure DevOps, etc.)
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

**Azure DevOps** - Use variable groups or pipeline variables:
```yaml
env:
  DB_PASSWORD: $(DB_PASSWORD)
  API_KEY: $(API_KEY)
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
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Project Structure

```
├── mcp_manager.py          # Main MCP configuration tool
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
