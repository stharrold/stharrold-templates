---
title: MCP (Model Context Protocol) Setup Guide
version: 3.1
updated: 2025-09-12
changelog:
  - Merged Claude Code development workflow best practices
  - Added agentic development patterns and command system optimization
  - Enhanced CLAUDE.md hierarchical organization and token efficiency
  - Added multi-instance orchestration and Plan Mode workflows
  - Updated productivity metrics with real-world deployment data
  - Added advanced context management and performance optimization
  - Added enterprise search architecture and RAG patterns from Graph RAG Kuzu report
---

# MCP (Model Context Protocol) Setup Guide

## Installation
```bash
# Download guide to home directory
curl -o ~/GUIDE-MCP.md [URL_TO_GUIDE]
# Or save manually from artifact

# Copy to all relevant locations
cp ~/GUIDE-MCP.md ~/.claude/GUIDE-MCP.md
cp ~/GUIDE-MCP.md ~/Documents/GitHub/GUIDE-MCP.md
cp ~/GUIDE-MCP.md ~/Library/Application\ Support/Claude/GUIDE-MCP.md
cp ~/GUIDE-MCP.md ~/Library/Application\ Support/Code/User/GUIDE-MCP.md
```

## Overview

MCP servers enable AI assistants to interact with external tools and data sources. This guide covers configuring MCP servers for VS Code extensions and Claude Code CLI.

**Key Benefits:**
- **Development Velocity**: 2-10x development velocity improvements reported by early adopters
- **Task Completion**: 55% faster completion rates (GitHub internal studies)
- **Documentation**: 70% reduction in manual documentation time
- **Testing**: 50% reduction in test setup and maintenance time; 85% test coverage achievement with minimal manual intervention
- **Infrastructure**: 80% reduction in infrastructure provisioning time
- **Debugging**: 40-70% reduction in debugging time (Microsoft engineering teams)
- **Code Quality**: 82% reduction in style guide violations through consistency enforcement
- **Knowledge Transfer**: 45% reduction in onboarding time for new developers
- **Context Efficiency**: 30-40% reduction in per-session token consumption with proper CLAUDE.md structuring
- **Legacy Modernization**: Excels at complex architectural changes requiring specialized expertise

**Important**: Many MCP servers require API tokens. See [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md) for secure credential setup before configuring servers, including enterprise search security considerations.

## Quick Start Workflow

1. **Setup Credentials**: Follow [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md) for your platform
2. **Add Servers**: Use `mcp-manager.py --add` for interactive setup or `claude mcp add` commands
3. **Validate Setup**: Run `mcp-manager.py --check-credentials` and `mcp-manager.py --list`
4. **Test**: Use `/mcp` in Claude Code to verify servers are working

**For detailed implementation phases, see [GUIDE-IMPLEMENTATION.md](./GUIDE-IMPLEMENTATION.md), including enterprise search and RAG implementation strategies**

## Claude Code Installation & Setup

### Installation and Authentication

Claude Code operates as a command-line interface requiring Node.js 18 or newer. The installation involves npm package management followed by authentication through either Claude Pro/Max subscription ($20-200/month) or pay-per-use API billing.

```bash
# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Initialize in your project directory
claude
```

### Authentication Options

**Subscription-Based Authentication:**
- Claude Pro ($20/month): Basic usage limits
- Claude Max ($200/month): Higher limits but still subject to 5-hour session restrictions
- Enterprise SSO and domain capture for centralized team management

**Pay-Per-Use API Billing:**
- More predictable costs for intermittent usage
- No session time limits
- Ideal for enterprise deployments with usage-based budgeting

### Project Initialization Workflow

The initial setup should prioritize three critical components: authentication configuration, permission management, and project initialization.

```bash
# Generate initial CLAUDE.md by analyzing codebase structure
claude /init

# This creates a starting template that should be immediately customized with:
# - Project-specific conventions
# - Architectural patterns  
# - Workflow requirements
# - Explicit "do not" instructions
```

## CLAUDE.md Context Management Workflow

### Technical Architecture

CLAUDE.md files serve as markdown-based "project constitutions" that AI coding assistants automatically ingest at session start, functioning as high-priority system prompts that transform generic AI tools into project-aware development partners.

**Hierarchical Loading System:**
- **Global settings first**: `~/.claude.json` (user-level preferences)
- **Project-specific**: `.claude.json` or `CLAUDE.md` in project root
- **Subdirectory-level**: Feature-specific configurations

**Context Window Management:**
- Typical limit: 200,000 tokens for Claude Code (equivalent to ~500-page technical specifications)
- Optimal CLAUDE.md size: Under 30,000 tokens for best performance
- Performance degradation occurs at 50,000+ tokens (2-3x slower responses)
- Advanced practitioners report 40-60% reduction in context provision during sessions with well-structured CLAUDE.md files
- Token efficiency achieved through hierarchical organization and modular structure

### Workflow Modes

**Plan Mode** - Read-only analysis and strategy formulation
- Use `/init` command to regenerate context files
- AI scans project structure and establishes session parameters
- Safe for exploration without system modifications

**Edit Mode** - Active code modifications
- Context-aware development with preserved project knowledge
- Maintains coding standards and architectural decisions across sessions
- Use `/clear` to reset conversation while preserving CLAUDE.md configuration

### Context Management Best Practices

**"Lean and Intentional" Principle:**
- Include only information AI needs to work effectively
- Use short, declarative bullet points rather than narrative paragraphs
- Structure hierarchically: global → project → feature-level overrides

**Automated Validation:**
- Implement pre-commit hooks to verify context file syntax
- Establish review processes for context file changes (similar to code reviews)
- Monitor for outdated information and automatically flag stale context
- Create alerts for context files exceeding optimal size thresholds

**Version Control Integration:**
- Version control context files alongside code
- Use `.gitignore` for personal preference files
- Treat context file changes as requiring peer review

**Advanced CLAUDE.md Patterns:**
- **Hierarchical Organization**: Parent directories provide broad context while child directories contain specific implementation details
- **Dynamic Context Loading**: Runtime file references and modular organization to prevent instruction bleeding
- **Team-Wide Standards**: Consistent formatting and structure across team members
- **Token Optimization**: Balance comprehensive coverage with token efficiency, typically maintaining core context under 50,000 tokens while referencing extended documentation for on-demand loading

## Enterprise Search Architecture with MCP

### Data Quality Foundations

Enterprise search effectiveness depends fundamentally on data quality, not just AI model sophistication. Unlike public web content with clear URLs and ownership, enterprise information lacks governance and structure, creating critical challenges:

**The Foundational Problem:**
- **Version Ambiguity**: Multiple versions of documents (draft in shared drive, outdated wiki page, final PDF in email)
- **Shadow Documents**: Employees create duplicates when they can't find originals
- **Staleness**: Information becomes outdated without clear update cycles
- **Ownership Gaps**: No clear data stewards or maintenance responsibility

**Solution: Data Census Approach**
```bash
# Use MCP servers to inventory critical knowledge sources
claude mcp add data-census "python -m data_census" \
  --env DATA_SOURCES="confluence,sharepoint,wikis,gdrive"

# Regular data quality audits
claude mcp add data-audit "python -m audit_knowledge_base" \
  --schedule weekly
```

### Hybrid Retrieval Architecture

Enterprise environments lack web search signals (PageRank, click-through rates, backlinks), requiring sophisticated multi-faceted retrieval:

**Three-Layer Retrieval System:**
1. **BM25 for Exact Phrase Matching** - Essential for finding specific contract clauses, policy numbers
2. **Dense Embeddings for Conceptual Similarity** - When users don't know exact terminology
3. **Knowledge Graph Traversal** - Authority-based discovery through trusted authors, recent approvals

**MCP Implementation:**
```bash
# Configure hybrid retrieval MCP server
claude mcp add enterprise-search "uvx enterprise-search-server" \
  --env SEARCH_METHODS="bm25,embeddings,graph" \
  --env RERANK_MODEL="cross-encoder/ms-marco-MiniLM-L-12-v2"

# Knowledge graph server for entity relationships
claude mcp add knowledge-graph "python -m knowledge_graph_server" \
  --env GRAPH_DB="neo4j://localhost:7687" \
  --env SCHEMA_PATH="./enterprise_ontology.json"
```

### RAG 2.0 Architecture Patterns

Traditional RAG fails when wrong documents are retrieved initially. Enterprise RAG requires robust architecture:

**RAG 2.0 Pipeline Components:**
1. **Document Intelligence**: Layout-aware parsing, section hierarchy, provenance tracking
2. **Mixture of Retrievers**: Multiple retrieval methods to maximize recall
3. **Strong Reranker**: Business logic enforcement and relevance scoring
4. **Grounded Generation**: Source citation requirements and trained "I don't know" responses
5. **Curated FAQ Bank**: Common queries bypass brittle retrieval entirely

**Implementation Pattern:**
```bash
# Document processing pipeline
claude mcp add doc-intelligence "python -m document_processor" \
  --env PARSE_LAYOUT="true" \
  --env EXTRACT_METADATA="true" \
  --env TRACK_PROVENANCE="true"

# Instructable reranker with business rules
claude mcp add reranker "python -m business_reranker" \
  --config rerank_rules.yaml
```

### Knowledge Graph Integration

Graphs provide the reliable signals missing from unstructured text by identifying entities and mapping relationships:

**Graph-Based Signals:**
- **Authority Relationships**: "Engineer A owns Jira Ticket B"
- **Recency Tracking**: "Document C was approved by Legal on Date D"
- **Expertise Networks**: "Person E is the SME for Technology F"

**MCP Graph Server Configuration:**
```bash
# Knowledge graph with entity extraction
claude mcp add kuzu-graph "python -m kuzu_graph_server" \
  --env GRAPH_PATH="./enterprise_knowledge.db" \
  --env ENTITY_TYPES="person,project,document,policy"

# Automated relationship extraction
claude mcp add relation-extractor "python -m extract_relations" \
  --env SOURCE_TYPES="email,slack,confluence,jira"
```

### Instructable Reranking Systems

Transform ranking from opaque algorithms into configurable business tools:

**Business Logic Examples:**
- **Pharmaceutical**: Always prioritize FDA-approved documents over internal research
- **Legal**: Boost documents by authoring partner seniority
- **Engineering**: Prefer recently updated technical specifications

**Configuration Pattern:**
```yaml
# rerank_rules.yaml
rules:
  - condition: "document_type == 'FDA_APPROVED'"
    boost: 2.0
    priority: 1
  - condition: "author_role == 'senior_partner'"
    boost: 1.5
  - condition: "last_updated > 30_days_ago"
    boost: 1.2
```

### Enterprise-Specific Answer Engines

Instead of monolithic enterprise search, build multiple curated "answer engines" for specific domains:

**Domain-Specific Approach:**
- **HR Engine**: Vetted policy documents only, cite-required responses
- **IT Support**: Technical documentation with step-by-step procedures
- **Legal Compliance**: Regulatory documents with audit trails
- **Engineering**: Code repositories with architectural decision records

This approach treats search as building trustworthy, predictable systems where understood failure modes are more valuable than unpredictable brilliance.

**For comprehensive enterprise search implementation phases and detailed KPIs, see the [Enterprise Search & RAG Implementation section in GUIDE-IMPLEMENTATION.md](./GUIDE-IMPLEMENTATION.md#enterprise-search--rag-implementation).**

## Command System & Workflow Optimization

Claude Code's command system extends beyond simple text generation to provide sophisticated project management capabilities. Understanding and mastering these commands is essential for optimal performance.

### Critical Commands for Performance

**Context Management Commands:**
- `/clear` - Most critical command for maintaining performance; resets conversation history between unrelated tasks
- `/compact` - Natural breakpoints in related work to compress context without full reset
- `/context` - Debug token usage issues and monitor context window utilization
- `/cost` - Real-time token usage monitoring for proactive management

**Development Commands:**
- `/init` - Generate initial CLAUDE.md by analyzing project structure
- `/mcp` - View and interact with configured MCP servers
- `/model` - Dynamic model switching for optimal performance-cost balance

### Optimal Workflow Patterns

**Explore-Plan-Code-Commit Methodology:**
1. **Explore**: Thoroughly understand requirements before implementation
2. **Plan**: Use Plan Mode (Shift+Tab twice) for complex architectural decisions
3. **Code**: Execute implementation with full context
4. **Commit**: Generate intelligent commit messages with Git operations

**Plan Mode (Advanced):**
- Activated through Shift+Tab twice
- Separates research from execution phases
- Restricts Claude to read-only operations during analysis
- Provides predictable responses with detailed analysis before code modifications
- Teams report 65% reduction in error rates when enforcing Plan Mode for significant changes

**Test-Driven Development Patterns:**
- Generate comprehensive test suites before implementation
- Leverage Claude's ability to create edge case coverage
- Iterate on tests and implementation together

**Visual Iteration Workflows:**
- Provide screenshots for UI refinement
- Capitalize on Claude's multimodal capabilities for pixel-perfect implementations
- Enable design-to-code conversion workflows

### Multi-Instance Orchestration

Advanced teams implement parallel Claude Code sessions for complex projects using Git worktrees:

```bash
# Create parallel development streams
git worktree add ../project-feature-auth feature/auth
git worktree add ../project-feature-ui feature/ui
git worktree add ../project-security-review security/review

# Run independent Claude sessions in each worktree
# - One instance implements new functionality
# - Another performs security reviews  
# - Third generates comprehensive tests
```

This orchestration approach mirrors how human development teams operate, with specialized roles contributing to the final product while preventing context conflicts.

### Context Priming Strategy

Before requesting implementation, provide comprehensive background through:
- Well-structured CLAUDE.md files with project conventions
- Visual mockups and design specifications
- Explicit architectural constraints and requirements
- Extended thinking triggers like "think harder" or "ultrathink" for complex problems

This front-loaded context investment reduces iteration cycles and improves first-attempt success rates significantly.

**For comprehensive implementation strategy and agentic development patterns, see [GUIDE-IMPLEMENTATION.md](./GUIDE-IMPLEMENTATION.md).**

## Directory Structure

### macOS
```
~/
├── .claude.json                                    # Claude Code CLI configuration
├── bin/
│   └── sync-mcp.sh                                # Auto-sync script
└── Library/Application Support/
    ├── Code/User/
    │   └── mcp.json                               # VS Code MCP extension config
    └── Claude/
        └── config.json                             # Claude Desktop app config
```

### Windows
```
~/
├── .claude.json                                    # Claude Code CLI configuration
├── bin/
│   └── sync-mcp.sh                                # Auto-sync script
└── AppData/Roaming/
    ├── Code/User/
    │   └── mcp.json                               # VS Code MCP extension config
    └── Claude/
        └── config.json                             # Claude Desktop app config
```

### Linux
```
~/
├── .claude.json                                    # Claude Code CLI configuration
├── bin/
│   └── sync-mcp.sh                                # Auto-sync script
└── .config/
    ├── Code/User/
    │   └── mcp.json                               # VS Code MCP extension config
    └── claude/
        └── config.json                             # Claude Desktop app config
```

## Claude Code CLI Configuration

### 1. Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Add MCP Servers
```bash
# Add servers via CLI
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /Users/stharrold
claude mcp add github npx @modelcontextprotocol/server-github
claude mcp add memory npx @modelcontextprotocol/server-memory

# List configured servers
claude mcp list
```

### 3. Config Locations
Claude Code uses different scopes:
- **User scope**: `~/.claude.json` (global, all projects)
- **Project scope**: `.mcp.json` in project root (shared via git)
- **Local scope**: `~/.claude.json` with project-specific section

### 4. Test in VS Code
- Open Claude Code: Command Palette → "Run Claude Code"
- Type `/mcp` to see configured servers
- Test: "List files in /Users/stharrold"

## VS Code MCP Extension

### 1. Install Extension
Search "MCP" in VS Code marketplace.

### 2. Configure
Edit VS Code MCP configuration file:
- **macOS**: `~/Library/Application Support/Code/User/mcp.json`
- **Windows**: `~/AppData/Roaming/Code/User/mcp.json`  
- **Linux**: `~/.config/Code/User/mcp.json`
```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path"]
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

## Claude Desktop App

Configuration file location:
- **macOS**: `~/Library/Application Support/Claude/config.json`
- **Windows**: `~/AppData/Roaming/Claude/config.json`
- **Linux**: `~/.config/claude/config.json`
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path"]
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

## Auto-Sync Configuration

### Step 1: Create Sync Script
```bash
mkdir -p ~/bin
cat > ~/bin/sync-mcp.sh << 'EOF'
#!/bin/bash

# Detect platform and set paths
case "$(uname -s)" in
    Darwin)
        VS_CODE_MCP="$HOME/Library/Application Support/Code/User/mcp.json"
        CLAUDE_DESKTOP="$HOME/Library/Application Support/Claude/config.json"
        ;;
    MINGW*|CYGWIN*|MSYS*)
        VS_CODE_MCP="$HOME/AppData/Roaming/Code/User/mcp.json"
        CLAUDE_DESKTOP="$HOME/AppData/Roaming/Claude/config.json"
        ;;
    *)
        VS_CODE_MCP="$HOME/.config/Code/User/mcp.json"
        CLAUDE_DESKTOP="$HOME/.config/claude/config.json"
        ;;
esac

CLAUDE_CODE_CONFIG="$HOME/.claude.json"

# Create backups
for file in "$VS_CODE_MCP" "$CLAUDE_CODE_CONFIG" "$CLAUDE_DESKTOP"; do
    if [ -f "$file" ]; then
        cp "$file" "$file.backup"
    fi
done

# Initialize empty servers if files don't exist
[ ! -f "$VS_CODE_MCP" ] && echo '{"servers":{}}' > "$VS_CODE_MCP"
[ ! -f "$CLAUDE_CODE_CONFIG" ] && echo '{"mcpServers":{}}' > "$CLAUDE_CODE_CONFIG"
[ ! -f "$CLAUDE_DESKTOP" ] && echo '{"mcpServers":{}}' > "$CLAUDE_DESKTOP"

# Merge all MCP servers from all sources and add type fields
jq -s '
    # Extract servers from each source
    (.[0].servers // {}) as $vscode |
    (.[1].mcpServers // {}) as $claude_code |
    (.[2].mcpServers // {}) as $claude_desktop |
    
    # Merge all servers (later sources override earlier)
    ($vscode + $claude_code + $claude_desktop) as $merged |
    
    # Add type fields where missing
    ($merged | with_entries(
        .value |= (
            if .url then 
                .type = "sse"
            elif .command then 
                .type = "stdio"
            else . end
        )
    )) as $typed |
    
    # Return all three configs
    [
        {servers: $typed},
        (.[1] | .mcpServers = $typed),
        (.[2] | .mcpServers = $typed)
    ]
' "$VS_CODE_MCP" "$CLAUDE_CODE_CONFIG" "$CLAUDE_DESKTOP" > /tmp/mcp-merge.json

# Write back to all locations
jq '.[0]' /tmp/mcp-merge.json > /tmp/vscode.json && mv /tmp/vscode.json "$VS_CODE_MCP"
jq '.[1]' /tmp/mcp-merge.json > /tmp/claude-code.json && mv /tmp/claude-code.json "$CLAUDE_CODE_CONFIG"
jq '.[2]' /tmp/mcp-merge.json > /tmp/claude-desktop.json && mv /tmp/claude-desktop.json "$CLAUDE_DESKTOP"

# Clean up
rm -f /tmp/mcp-merge.json

echo "MCP configs synced across all locations at $(date)"
EOF

chmod +x ~/bin/sync-mcp.sh
```

### Step 2: Create Launch Agent (macOS only)
```bash
cat > ~/Library/LaunchAgents/com.user.sync-mcp.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.sync-mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/bin/sync-mcp.sh</string>
    </array>
    <key>WatchPaths</key>
    <array>
        <string>$HOME/Library/Application Support/Code/User/mcp.json</string>
        <string>$HOME/.claude.json</string>
        <string>$HOME/Library/Application Support/Claude/config.json</string>
    </array>
    <key>StandardOutPath</key>
    <string>/tmp/sync-mcp.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/sync-mcp.error.log</string>
</dict>
</plist>
EOF
```

**Note**: Launch Agents are macOS-specific. For Windows/Linux, use the application startup triggers instead.

### Step 3: Add Application Startup Triggers

#### VS Code - Auto-sync on startup
```bash
# Create tasks.json via script
mkdir -p .vscode
cat > .vscode/tasks.json << 'EOF'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Sync MCP on startup",
      "type": "shell",
      "command": "~/bin/sync-mcp.sh",
      "runOptions": {
        "runOn": "folderOpen"
      },
      "presentation": {
        "reveal": "silent",
        "panel": "new"
      }
    }
  ]
}
EOF
```

#### Claude CLI - Auto-sync on every command
Add to shell config:
```bash
# For bash (~/.bashrc)
alias claude='~/bin/sync-mcp.sh 2>/dev/null && command claude'

# For zsh (~/.zshrc) 
alias claude='~/bin/sync-mcp.sh 2>/dev/null && command claude'
```

#### Claude Desktop - Auto-sync on launch
```bash
# Create launcher script
cat > /Applications/Claude-Synced.command << 'EOF'
#!/bin/bash
~/bin/sync-mcp.sh
open -a "Claude"
exit
EOF
chmod +x /Applications/Claude-Synced.command

# Drag Claude-Synced.command to dock instead of Claude.app
```

### Step 4: Load File Watch Service
```bash
# Always unload first to avoid "Input/output error"
launchctl unload ~/Library/LaunchAgents/com.user.sync-mcp.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.user.sync-mcp.plist
```

Service persists across restarts. Disable: `launchctl unload -w ~/Library/LaunchAgents/com.user.sync-mcp.plist`

## Available MCP Servers

### Tier 1: Essential Core Development Servers

#### Version Control & Code Management

**GitHub MCP Server**
- Repository management, PR analysis, and code review automation
- Issue tracking with natural language issue creation
- CI/CD workflow monitoring and GitHub Actions integration
```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
# Or: claude mcp add github npx @modelcontextprotocol/server-github  # Requires GITHUB_TOKEN
```

**Git MCP Server**
- Core version control operations (commit, branch, merge)
- Repository history analysis and commit searching
- Branch management and conflict resolution assistance

**Filesystem MCP Server**
- Secure file operations with configurable access controls
- Directory structure analysis and organization
```bash
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /path
```

#### Development & Testing Infrastructure

**Sequential Thinking MCP Server**
- Methodical problem-solving through structured thinking processes
- Complex refactoring workflow guidance
```bash
claude mcp add sequential-thinking npx -- -y @modelcontextprotocol/server-sequential-thinking
```

**Playwright MCP Server**
- Web automation and testing using structured accessibility trees
- Cross-browser testing automation
```bash
claude mcp add playwright npx -- @playwright/mcp@latest
```

**Context7 MCP Server**
- Real-time documentation fetching from source repositories
- Version-specific code examples and API documentation
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp
```

#### Database & Data Management

**PostgreSQL MCP Server**
- Natural language to SQL query translation
- Database schema analysis and optimization
```bash
# Multiple providers available
git clone https://github.com/crystaldba/postgres-mcp
```

**SQLite MCP Server**
- Lightweight database operations for development and testing
```bash
claude mcp add sqlite npx @modelcontextprotocol/server-sqlite /path/to/db
```

**Memory MCP Server**
- Session context retention across coding sessions
```bash
claude mcp add memory npx @modelcontextprotocol/server-memory
```

### Tier 2: High-Impact Productivity Servers

#### Code Quality & Security

**Codacy MCP Server**
- Integrated code quality analysis with SAST, secrets detection
- Required by repository guidelines for all file edits
```bash
claude mcp add codacy npx @codacy/codacy-mcp
```

**Sentry MCP Server**
- Error tracking and performance monitoring integration
- Intelligent debugging assistance with error pattern analysis
```bash
claude mcp add --transport sse sentry https://mcp.sentry.dev/mcp
```

#### CI/CD & DevOps

**Azure DevOps MCP Server**
- Comprehensive project management integration
- Build pipeline management and release orchestration
```bash
claude mcp add azure npx @azure-devops/mcp org-name  # Requires AZURE_DEVOPS_PAT
```

**Buildkite MCP Server**
- CI/CD pipeline data exposure and build management
- Build job analysis and failure investigation

#### Infrastructure as Code

**Terraform MCP Server**
- Infrastructure automation with natural language IaC generation
```bash
# Docker deployment recommended
docker run hashicorp/terraform-mcp-server
```

**AWS Cloud Control API MCP Server**
- Natural language AWS resource management
- CRUD operations on AWS services

**Kubernetes MCP Server**
- Container orchestration and cluster management
```bash
git clone https://github.com/Azure/mcp-kubernetes
```

### Tier 3: Advanced Collaboration & Analytics

#### Communication & Collaboration

**Slack MCP Server**
- Secure workspace integration with real Slack data access
```bash
# Via Composio platform
npx @composio/mcp@latest setup slack
```

**Notion MCP Server**
- Documentation management and project requirement tracking
- Task updates directly from Claude Code

**Atlassian MCP Server (Jira & Confluence)**
- Enterprise workflow integration with Jira issue management
- Confluence documentation automation

#### Analytics & Monitoring

**PostHog MCP Server**
- Product analytics and user behavior insights
- Feature flag configuration and management
```bash
claude mcp add --transport sse posthog https://mcp.posthog.com/sse
```

**Memory Bank MCP Server**
- Session context retention across coding sessions
- Decision history tracking and rationale preservation

#### Workflow Automation

**Zapier MCP Server**
- Cross-platform workflow automation across 500+ business applications
- Integration with Gmail, Trello, and productivity tools

**Figma MCP Server**
- Design-to-code conversion and UI component generation
- Design file analysis and component extraction

### Tier 4: Specialized Domain Servers

#### Multi-Database Support

**MongoDB MCP Server**
- NoSQL database operations and document management
- MongoDB Atlas, Community Edition, and Enterprise Advanced support

**Astra DB MCP Server**
- NoSQL collections and distributed database management
- Vector database operations for AI/ML workloads

#### Additional Cloud Platforms

**Azure Services MCP Servers**
- Microsoft cloud ecosystem integration
- Azure Resource Manager operations

**Google Cloud MCP Servers**
- GCP resource management and service integration
- BigQuery data analysis and machine learning operations

#### Design & API Development

**Apidog MCP Server**
- API specification integration with OpenAPI/Swagger support
- Client code generation based on API contracts

**Cal.com MCP Server**
- Scheduling and booking management automation
- Calendar integration and availability management

**Note**: Servers marked with credential requirements need tokens configured. See [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md) for detailed setup instructions.

## Configuration Schema Differences

Different MCP clients use slightly different configuration schemas. Understanding these differences helps when manually editing configs or troubleshooting:

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

### Using mcp-manager.py (Recommended)

The `mcp-manager.py` tool provides cross-platform management of all MCP configurations:

```bash
# List all servers across all platforms
/usr/bin/python3 mcp-manager.py --list

# Add a new server interactively  
/usr/bin/python3 mcp-manager.py --add

# Validate credentials
/usr/bin/python3 mcp-manager.py --check-credentials

# Remove servers interactively
/usr/bin/python3 mcp-manager.py --remove

# Create backups
/usr/bin/python3 mcp-manager.py --backup-only
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
# macOS: Follow GUIDE-CREDENTIALS.md keychain setup
# Windows: Follow GUIDE-CREDENTIALS.md credential manager setup

# 2. Add GitHub server using mcp-manager.py
/usr/bin/python3 mcp-manager.py --add
# Enter: github, 1 (NPX), @modelcontextprotocol/server-github
# Add GITHUB_TOKEN env var: ${env:GITHUB_TOKEN}
# Choose: All configurations

# 3. Validate everything is working
/usr/bin/python3 mcp-manager.py --check-credentials
/usr/bin/python3 mcp-manager.py --list

# 4. Test in Claude Code
# Type: /mcp
# Should see: github server with tools available
```

## Troubleshooting

### MCP Not Found in Claude Code
```bash
# List all configurations to see what's available
/usr/bin/python3 mcp-manager.py --list

# Check specific config file
cat ~/.claude.json | jq .mcpServers

# Add server using unified tool
/usr/bin/python3 mcp-manager.py --add

# Or add using Claude CLI directly
claude mcp add test npx @modelcontextprotocol/server-filesystem /tmp
```

### Server Connection Failed
```bash
# Validate credentials first
/usr/bin/python3 mcp-manager.py --check-credentials

# Test server manually
npx @modelcontextprotocol/server-filesystem /path

# Check logs
tail -f /tmp/sync-mcp.error.log
```

Common causes:
- Missing API tokens (see [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md))
- Incorrect server paths or commands
- Network connectivity issues

### View MCP Tools
In Claude Code:
1. Type `/mcp`
2. Press Enter on server name
3. See available tools

### Sync Issues
```bash
# Check service
launchctl list | grep sync-mcp

# Reload (unload first to avoid errors)
launchctl unload ~/Library/LaunchAgents/com.user.sync-mcp.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.user.sync-mcp.plist

# Verify plist syntax
plutil -lint ~/Library/LaunchAgents/com.user.sync-mcp.plist

# Run manually
~/bin/sync-mcp.sh
```

### Import from Claude Desktop
```bash
# If desktop config exists at standard location
claude mcp add-from-claude-desktop

# Manual import if needed (adjust path for your platform)
# macOS
jq '.mcpServers' "$HOME/Library/Application Support/Claude/config.json" | \
  jq -r 'to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"'

# Windows  
jq '.mcpServers' "$HOME/AppData/Roaming/Claude/config.json" | \
  jq -r 'to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"'

# Linux
jq '.mcpServers' "$HOME/.config/claude/config.json" | \
  jq -r 'to_entries[] | "claude mcp add \(.key) \(.value.command) \(.value.args | join(" "))"'
```

## Cross-System Compatibility

For shared configs:
- Windows paths fail silently on macOS
- Use environment variables for system-specific paths
- Sync script removes `type` fields automatically

## File Locations Summary

### Universal (All Platforms)
```bash
~/.claude.json                        # Claude Code CLI user config
./.mcp.json                          # Claude Code CLI project config
~/bin/sync-mcp.sh                    # Sync script
```

### Platform-Specific Configurations

#### macOS
```bash
~/Library/Application Support/Code/User/mcp.json           # VS Code MCP
~/Library/Application Support/Claude/config.json           # Claude Desktop
~/Library/LaunchAgents/com.user.sync-mcp.plist            # Auto-run service
```

#### Windows
```bash
~/AppData/Roaming/Code/User/mcp.json                       # VS Code MCP
~/AppData/Roaming/Claude/config.json                       # Claude Desktop
```

#### Linux
```bash
~/.config/Code/User/mcp.json                               # VS Code MCP
~/.config/claude/config.json                               # Claude Desktop
```

### Logs (All Platforms)
```bash
/tmp/sync-mcp.log                                          # Sync output
/tmp/sync-mcp.error.log                                    # Errors
```

## Security Considerations

### Recent Vulnerabilities

**CVE-2025-52882 (Claude Code Extension)**
- **Severity**: High (CVSS 8.8)
- **Impact**: WebSocket authentication bypass allowing unauthorized MCP server access
- **Status**: Fully resolved in versions 1.0.24+
- **Mitigation**: Ensure Claude Code extensions are updated to latest versions

**PostgreSQL MCP Server SQL Injection**
- **Impact**: Bypassing read-only restrictions and arbitrary SQL execution
- **Mitigation**: Use Postgres MCP Pro with proper access controls

### Security Best Practices

- Use OS-native credential stores (Keychain on macOS, Credential Manager on Windows)
- Configure MCP servers with principle of least privilege
- Regular credential rotation and access auditing
- Integration with Sentry for error tracking and security incident detection
- Codacy integration for continuous security scanning

For detailed credential security setup, see [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md).

## Monitoring & Maintenance

### Health Monitoring
- Regular MCP server availability and performance checks
- Token expiration monitoring and automated renewal
- Security vulnerability scanning and patch management
- Usage analytics and optimization recommendations

### Update Management
- Automated MCP server version monitoring
- Staged rollout of server updates
- Rollback procedures for problematic updates
- Change impact assessment for server modifications

### Performance Optimization
- Regular review of server usage patterns
- Optimization of token limits and rate limiting
- Performance tuning based on development workflow metrics
- Removal of unused or underutilized servers

## Best Practices

1. **Secure Credentials**: Follow [GUIDE-CREDENTIALS.md](./GUIDE-CREDENTIALS.md) for secure token storage using OS credential stores
2. **Permissions**: Limit filesystem access to specific directories
3. **Testing**: Use `/mcp` in Claude Code to verify servers
4. **Backups**: Sync script creates timestamped backups
5. **Validation**: Use `mcp-manager.py --check-credentials` to verify credential setup
6. **Implementation Strategy**: Follow [GUIDE-IMPLEMENTATION.md](./GUIDE-IMPLEMENTATION.md) for phased rollout

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [MCP Community Servers](https://github.com/modelcontextprotocol/servers)
- [Implementation Strategy Guide](./GUIDE-IMPLEMENTATION.md)
- [Credential Security Guide](./GUIDE-CREDENTIALS.md)