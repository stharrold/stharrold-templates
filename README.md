# stharrold-templates

Templates and utilities for MCP (Model Context Protocol) server configuration and agentic development workflows.

## Features

- **Multi-platform MCP manager** (`mcp_manager.py`) - Configure Claude Code CLI, VS Code, and Claude Desktop
- **Containerized development** - Podman + uv + Python 3.11 for consistent environments
- **Workflow automation** - Git helpers, archive management, semantic versioning
- **AI-optimized documentation** - Modular guides (≤30KB per file) for context efficiency

## Prerequisites

```bash
podman --version          # 4.0+
podman-compose --version
git --version
gh --version              # GitHub CLI
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
├── .claude/skills/         # AI workflow skills
├── specs/                  # Feature specifications
└── tools/                  # Utility scripts
```

## License

See repository for license information.
