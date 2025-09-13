---
title: MCP Server Configurations
version: 3.1
updated: 2025-09-12
parent: ./CLAUDE.md
related:
  - ./11_setup.md
  - ../20_credentials/CLAUDE.md
  - ./15_troubleshooting.md
---

# MCP Server Configurations

Comprehensive catalog of available MCP servers organized by tier and functionality, with installation commands and configuration examples.

## Server Selection Strategy

Choose servers based on your project needs and development phase:

- **Tier 1**: Essential core development (start here)
- **Tier 2**: High-impact productivity enhancements
- **Tier 3**: Advanced collaboration and analytics
- **Tier 4**: Specialized domain-specific tools

**Prerequisites**: Many servers require API tokens. Configure credentials first:
→ [../20_credentials/CLAUDE.md](../20_credentials/CLAUDE.md)

## Tier 1: Essential Core Development Servers

Start with these foundational servers for any development project.

### Version Control & Code Management

#### GitHub MCP Server
Repository management, PR analysis, and CI/CD workflow monitoring.

**Features:**
- Repository management and code review automation
- Issue tracking with natural language issue creation
- GitHub Actions integration and workflow monitoring

**Installation:**
```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
# Or: claude mcp add github npx @modelcontextprotocol/server-github  # Requires GITHUB_TOKEN
```

#### Git MCP Server
Core version control operations and repository analysis.

**Features:**
- Version control operations (commit, branch, merge)
- Repository history analysis and commit searching
- Branch management and conflict resolution assistance

#### Filesystem MCP Server
Secure file operations with configurable access controls.

**Features:**
- Directory structure analysis and organization
- Secure file operations with access controls

**Installation:**
```bash
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /path
```

### Development & Testing Infrastructure

#### Sequential Thinking MCP Server
Methodical problem-solving through structured thinking processes.

**Features:**
- Complex refactoring workflow guidance
- Structured problem-solving processes

**Installation:**
```bash
claude mcp add sequential-thinking npx -- -y @modelcontextprotocol/server-sequential-thinking
```

#### Playwright MCP Server
Web automation and cross-browser testing.

**Features:**
- Web automation using structured accessibility trees
- Cross-browser testing automation

**Installation:**
```bash
claude mcp add playwright npx -- @playwright/mcp@latest
```

#### Context7 MCP Server
Real-time documentation fetching from source repositories.

**Features:**
- Version-specific code examples and API documentation
- Real-time documentation from source repositories

**Installation:**
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp
```

### Database & Data Management

#### PostgreSQL MCP Server
Natural language to SQL query translation and schema analysis.

**Features:**
- Natural language to SQL query translation
- Database schema analysis and optimization

**Installation:**
```bash
# Multiple providers available
git clone https://github.com/crystaldba/postgres-mcp
```

#### SQLite MCP Server
Lightweight database operations for development and testing.

**Installation:**
```bash
claude mcp add sqlite npx @modelcontextprotocol/server-sqlite /path/to/db
```

#### Memory MCP Server
Session context retention across coding sessions.

**Installation:**
```bash
claude mcp add memory npx @modelcontextprotocol/server-memory
```

## Tier 2: High-Impact Productivity Servers

Add these servers once core development workflow is established.

### Code Quality & Security

#### Code Quality Analysis
For code quality analysis, this repository uses a local Codacy CLI instead of an MCP server.

**Local CLI Features:**
- Code quality analysis with multiple tools (pylint, eslint, etc.)
- Security scanning with Trivy and Semgrep
- No MCP server dependency required

**Usage:**
```bash
# Local analysis (no MCP server needed)
./.codacy/cli.sh analyze --tool pylint file.py
./.codacy/cli.sh analyze --tool trivy .
```

#### Sentry MCP Server
Error tracking and performance monitoring integration.

**Features:**
- Error tracking with intelligent debugging assistance
- Performance monitoring integration
- Error pattern analysis

**Installation:**
```bash
claude mcp add --transport sse sentry https://mcp.sentry.dev/mcp
```

### CI/CD & DevOps

#### Azure DevOps MCP Server
Comprehensive project management and build pipeline integration.

**Features:**
- Project management integration
- Build pipeline management and release orchestration

**Installation:**
```bash
claude mcp add azure npx @azure-devops/mcp org-name  # Requires AZURE_DEVOPS_PAT
```

#### Buildkite MCP Server
CI/CD pipeline data exposure and build management.

**Features:**
- Build job analysis and failure investigation
- CI/CD pipeline data exposure

### Infrastructure as Code

#### Terraform MCP Server
Infrastructure automation with natural language IaC generation.

**Installation:**
```bash
# Docker deployment recommended
docker run hashicorp/terraform-mcp-server
```

#### AWS Cloud Control API MCP Server
Natural language AWS resource management.

**Features:**
- CRUD operations on AWS services
- Natural language AWS resource management

#### Kubernetes MCP Server
Container orchestration and cluster management.

**Installation:**
```bash
git clone https://github.com/Azure/mcp-kubernetes
```

## Tier 3: Advanced Collaboration & Analytics

Enterprise-focused servers for team collaboration and data insights.

### Communication & Collaboration

#### Slack MCP Server
Secure workspace integration with real Slack data access.

**Installation:**
```bash
# Via Composio platform
npx @composio/mcp@latest setup slack
```

#### Notion MCP Server
Documentation management and project requirement tracking.

**Features:**
- Task updates directly from Claude Code
- Project requirement tracking

#### Atlassian MCP Server (Jira & Confluence)
Enterprise workflow integration.

**Features:**
- Jira issue management
- Confluence documentation automation

### Analytics & Monitoring

#### PostHog MCP Server
Product analytics and user behavior insights.

**Features:**
- User behavior insights and product analytics
- Feature flag configuration and management

**Installation:**
```bash
claude mcp add --transport sse posthog https://mcp.posthog.com/sse
```

#### Memory Bank MCP Server
Session context retention and decision history tracking.

**Features:**
- Decision history tracking and rationale preservation
- Session context retention across coding sessions

### Workflow Automation

#### Zapier MCP Server
Cross-platform workflow automation.

**Features:**
- Integration across 500+ business applications
- Gmail, Trello, and productivity tool integration

#### Figma MCP Server
Design-to-code conversion and UI component generation.

**Features:**
- Design file analysis and component extraction
- UI component generation from designs

## Tier 4: Specialized Domain Servers

Specialized tools for specific use cases and domains.

### Multi-Database Support

#### MongoDB MCP Server
NoSQL database operations and document management.

**Features:**
- MongoDB Atlas, Community Edition, and Enterprise Advanced support
- NoSQL database operations

#### Astra DB MCP Server
Distributed database management and vector operations.

**Features:**
- Vector database operations for AI/ML workloads
- NoSQL collections management

### Additional Cloud Platforms

#### Azure Services MCP Servers
Microsoft cloud ecosystem integration.

**Features:**
- Azure Resource Manager operations
- Microsoft cloud service integration

#### Google Cloud MCP Servers
GCP resource management and service integration.

**Features:**
- BigQuery data analysis and machine learning operations
- GCP resource management

### Design & API Development

#### Apidog MCP Server
API specification integration with OpenAPI/Swagger support.

**Features:**
- Client code generation based on API contracts
- OpenAPI/Swagger support

#### Cal.com MCP Server
Scheduling and booking management automation.

**Features:**
- Calendar integration and availability management
- Scheduling automation

## Configuration Schema Differences

Different MCP clients use slightly different configuration schemas:

### Claude Code CLI (`~/.claude.json`)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "command",
      "args": ["arg1", "arg2"],
      "env": {
        "VAR": "${env:VAR}"
      }
    }
  }
}
```

### VS Code MCP Extension (`mcp.json`)
```json
{
  "servers": {
    "server-name": {
      "command": "command", 
      "args": ["arg1", "arg2"],
      "env": {
        "VAR": "${env:VAR}"
      }
    }
  }
}
```

### Claude Desktop (`config.json`)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "command",
      "args": ["arg1", "arg2"],
      "env": {
        "VAR": "${env:VAR}"
      }
    }
  }
}
```

### Key Differences

| Feature | Claude Code CLI | VS Code Extension | Claude Desktop |
|---------|----------------|-------------------|----------------|
| Root key | `mcpServers` | `servers` | `mcpServers` |
| Type field | Optional | Optional | Optional |
| Env variables | `${env:VAR}` | `${env:VAR}` | `${env:VAR}` |
| Project scope | Supported | Not supported | Not supported |

### Type Field Usage

The `type` field is automatically managed:
- **stdio**: For command-line tools (default for `command` configs)
- **sse**: For Server-Sent Events URLs (default for `url` configs)

The sync script (`sync-mcp.sh`) automatically adds appropriate `type` fields when syncing between platforms.

## Unified MCP Management Workflow

### Using mcp_manager.py (Recommended)

Cross-platform management of all MCP configurations:

```bash
# List all servers across all platforms
/usr/bin/python3 mcp_manager.py --list

# Add a new server interactively
/usr/bin/python3 mcp_manager.py --add

# Validate credentials
/usr/bin/python3 mcp_manager.py --check-credentials

# Remove servers interactively
/usr/bin/python3 mcp_manager.py --remove

# Create backups
/usr/bin/python3 mcp_manager.py --backup-only
```

### Using Claude Code CLI

```bash
# Add servers to Claude Code specifically
claude mcp add github npx @modelcontextprotocol/server-github
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /path

# List Claude Code servers
claude mcp list

# Remove servers
claude mcp remove github
```

### Complete Setup Example

```bash
# 1. Setup credentials (choose your platform)
# macOS: Follow ../20_credentials/CLAUDE.md keychain setup
# Windows: Follow ../20_credentials/CLAUDE.md credential manager setup

# 2. Add GitHub server using mcp_manager.py
/usr/bin/python3 mcp_manager.py --add
# Enter: github, 1 (NPX), @modelcontextprotocol/server-github
# Add GITHUB_TOKEN env var: ${env:GITHUB_TOKEN}
# Choose: All configurations

# 3. Validate everything is working
/usr/bin/python3 mcp_manager.py --check-credentials
/usr/bin/python3 mcp_manager.py --list

# 4. Test in Claude Code
# Type: /mcp
# Should see: github server with tools available
```

## Project Template Integration

### Server Selection by Project Type

**Web Applications:**
- Tier 1: GitHub, Filesystem, Memory, PostgreSQL/SQLite
- Tier 2: Sentry, Codacy
- Tier 3: PostHog, Figma

**API Development:**
- Tier 1: GitHub, Sequential Thinking, Context7
- Tier 2: Sentry, Azure DevOps
- Tier 4: Apidog

**Data Analysis Projects:**
- Tier 1: Memory, PostgreSQL, Context7
- Tier 4: MongoDB, Google Cloud (BigQuery)

**Infrastructure Projects:**
- Tier 1: GitHub, Filesystem
- Tier 2: Terraform, AWS Cloud Control, Kubernetes
- Tier 3: Slack (team coordination)

### Environment-Specific Configurations

**Development Environment:**
```bash
# Essential development servers
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem ./
claude mcp add memory npx @modelcontextprotocol/server-memory
claude mcp add sequential-thinking npx -- -y @modelcontextprotocol/server-sequential-thinking
```

**Production Environment:**
```bash
# Production monitoring and management
claude mcp add --transport sse sentry https://mcp.sentry.dev/mcp
claude mcp add --transport sse posthog https://mcp.posthog.com/sse
```

## Next Steps

1. **Set up context management** → [13_context-management.md](./13_context-management.md)
2. **Configure enterprise search** → [14_enterprise-search.md](./14_enterprise-search.md)
3. **Troubleshoot issues** → [15_troubleshooting.md](./15_troubleshooting.md)

---

*Server configurations are synchronized across all Claude Code platforms via the auto-sync setup from [11_setup.md](./11_setup.md).*