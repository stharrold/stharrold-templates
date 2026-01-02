# Workflow Guide: Planning Phases (0-3)

**Parent:** [WORKFLOW.md](../../WORKFLOW.md)
**Version:** 5.3.0

This document covers the planning and development phases of the workflow.

---

## Workflow Phases

### Phase 0: Initial Setup

**Location:** Main repository
**Branch:** `main` or create `contrib/<gh-user>`
**Skills:** tech-stack-adapter, git-workflow-manager, workflow-utilities

**Steps:**

1. **Verify prerequisites:**
   ```bash
   # Check authentication
   gh auth status

   # Extract GitHub username
   GH_USER=$(gh api user --jq '.login')
   echo "GitHub User: $GH_USER"
   ```

2. **Create skill directory structure** (if not exists):
   ```bash
   # Directory structure is already in .gemini/skills/
   ls -la .gemini/skills/
   ```

3. **Create TODO.md manifest** (if not exists):
   ```bash
   python .gemini/skills/workflow-utilities/scripts/todo_updater.py .
   ```

4. **Initialize contrib branch** (if not exists):
   ```bash
   GH_USER=$(gh api user --jq '.login')
   git checkout -b "contrib/$GH_USER"
   git push -u origin "contrib/$GH_USER"
   ```

**User prompt:** "Initialize workflow for this project" or "next step?"

**Output:**
- ✓ Skills verified
- ✓ TODO.md created with YAML frontmatter
- ✓ contrib/<gh-user> branch initialized

---

### Phase 0: Repository Initialization (Optional)

**Location:** External (source repository → target repository)
**Branch:** N/A (creates new repository)
**Skills:** initialize-repository (meta-skill)

**Purpose:** Bootstrap a new repository with the complete workflow system from an existing source repository.

**When to use:**
- Starting a new project that needs the workflow system
- Migrating existing project to workflow system
- Creating template repository with workflow standards

**Note:** This is a **one-time setup phase**, not part of the normal Phases 1-6 workflow cycle.

**Command:**
```bash
python .gemini/skills/initialize-repository/scripts/initialize_repository.py \
  <source-repo> <target-repo>
```

**Example:**
```bash
# From current repository
python .gemini/skills/initialize-repository/scripts/initialize_repository.py \
  . ../my-new-project
```

**Interactive Session Flow:**

**Phase 1: Configuration Selection (9 questions)**
```
What is the primary purpose of this repository?
  1) Web application
  2) CLI tool
  3) Library/package
  4) Data analysis
  5) Machine learning
  6) Other
> [User selects]

Brief description of the repository (one line):
> [User provides]

GitHub username [auto-detected from gh CLI]
> [User confirms or updates]

Python version (3.11 / 3.12 / 3.13) [default: 3.11]
> [User selects]

Copy workflow system? (required, always yes)
Copy domain-specific content (src/, resources/)? (yes/no)
Copy sample tests (tests/)? (yes/no)
Copy container configs? (yes/no)
```

**Phase 2: Git Setup (4-5 questions)**
```
Initialize git repository? (yes/no)
If yes: Create branch structure (main, develop, contrib)? (yes/no)
If yes: Set up remote? (yes/no)
If yes: Remote URL?
If yes and remote: Push to remote? (yes/no)
```

**What gets copied:**

**Always:**
- All 8 skills (.gemini/skills/)
- Documentation (WORKFLOW.md, CONTRIBUTING.md, UPDATE_CHECKLIST.md)
- Quality configs (pyproject.toml, .gitignore)
- Directory structure (ARCHIVED/, planning/, specs/)

**Generated/adapted:**
- README.md (customized for new repo)
- GEMINI.md (customized for new repo)
- CHANGELOG.md (initial v0.1.0)
- TODO.md (master workflow manifest)

**Optionally (based on Q&A):**
- Domain content (src/, resources/)
- Tests (tests/)
- Container configs (Containerfile, podman-compose.yml)

**Output:**
- ✓ New repository created with complete workflow system
- ✓ Documentation adapted for new context
- ✓ Git initialized with 3-branch structure (optional)
- ✓ Remote configured (optional)
- ✓ Ready to start Phase 1 (BMAD planning)

**Token Efficiency:**
- Manual setup: ~3,500 tokens
- Callable tool: ~150 tokens
- **Savings: ~3,350 tokens (96% reduction)**

**Next step after initialization:**
```bash
cd /path/to/new-repo
uv sync
python .gemini/skills/bmad-planner/scripts/create_planning.py first-feature <gh-user>
```

---

### Phase 1: Planning (BMAD)

**Location:** Main repository
**Branch:** `contrib/<gh-user>`
**Skills:** bmad-planner (callable tool), workflow-utilities

**Interactive Planning Tool:**

BMAD is now an **interactive callable Python script** that uses a three-persona approach to gather requirements and design architecture.

**Command:**
```bash
python .gemini/skills/bmad-planner/scripts/create_planning.py \
  <slug> <gh-user>
```

**Example:**
```bash
python .gemini/skills/bmad-planner/scripts/create_planning.py \
  my-feature stharrold
```

**Interactive Session Flow:**

The script conducts three-persona Q&A automatically:

#### Persona 1: 🧠 BMAD Analyst (Requirements)

Script acts as business analyst to create requirements.md:

**Interactive Q&A (5-10 questions):**
```
🧠 BMAD Analyst Persona - Requirements Gathering

What problem does this feature solve?
> [User answers]

Who are the primary users of this feature?
> [User answers]

How will we measure success?
> [User answers]

Functional requirements (FR-001, FR-002, ...):
> [User provides requirements with acceptance criteria]

Performance, security, scalability requirements?
> [User answers]
```

**Generates:** `planning/<feature>/requirements.md` (using comprehensive template)
- Business context, problem statement, success criteria
- Functional requirements (FR-001, FR-002...) with acceptance criteria
- Non-functional requirements (performance, security, scalability)
- User stories with scenarios
- Risks and mitigation

#### Persona 2: 🏗️ BMAD Architect (Architecture)

Script acts as technical architect to create architecture.md:

**Interactive Q&A (5-8 questions):**
```
🏗️ BMAD Architect Persona - Technical Architecture Design

Based on the requirements, I'll design the technical architecture.

Technology Stack:

Web framework (if applicable)?
  1) FastAPI
  2) Flask
  3) Django
  4) None
> [User selects]

Database?
  1) SQLite (dev)
  2) PostgreSQL
  3) MySQL
  4) None
> [User selects]

Container strategy, testing framework, etc.
> [User answers remaining questions]
```

**Generates:** `planning/<feature>/architecture.md` (using comprehensive template)
- System overview, component diagrams
- Technology stack with justifications
- Data models, API endpoints
- Container architecture (Containerfile, podman-compose.yml)
- Security, error handling, testing strategy
- Deployment and observability

#### Persona 3: 📋 BMAD PM (Epic Breakdown)

Script acts as project manager to create epics.md:

**Automatic Analysis (no Q&A):**
```
📋 BMAD PM Persona - Epic Breakdown

Analyzing requirements and architecture to create epic breakdown...

✓ Identified 3 epics:
  - E-001: Data Layer Foundation (Priority: P0, Medium complexity)
  - E-002: Core Business Logic (Priority: P0, High complexity)
  - E-003: Testing & Quality Assurance (Priority: P1, Medium complexity)
```

**Generates:** `planning/<feature>/epics.md` (epic breakdown)
- Epic 1, Epic 2, Epic 3... with scope and complexity
- Dependencies between epics
- Implementation priority order
- Timeline estimates

#### Automatic Commit

Script automatically commits planning documents:

```bash
git add planning/<feature>/
git commit -m "docs(planning): add BMAD planning for <feature>

BMAD planning session completed via interactive tool:
- requirements.md: Business requirements and user stories (🧠 Analyst)
- architecture.md: Technical design and technology stack (🏗️ Architect)
- epics.md: Epic breakdown and priorities (📋 PM)

Generated by: .gemini/skills/bmad-planner/scripts/create_planning.py

Refs: planning/<feature>/README.md

🤖 Generated with [Gemini Code](https://gemini.com/gemini-code)

Co-Authored-By: Gemini <noreply@anthropic.com>
"
git push origin contrib/<gh-user>
```

**User prompt:** "next step?" (from contrib branch)

**Workflow Orchestrator Call:**
```python
# In workflow orchestrator - Phase 1.1
if current_phase == 1 and current_step == '1.1':
    import subprocess

    result = subprocess.run([
        'python',
        '.gemini/skills/bmad-planner/scripts/create_planning.py',
        slug,       # my-feature
        gh_user,    # stharrold
    ], check=True)

    print(f"✓ BMAD planning created in planning/{slug}/")
    print("  Next: Create feature worktree (Phase 2)")
```

**Output:**
- ✓ planning/<feature>/requirements.md created (🧠 Analyst)
- ✓ planning/<feature>/architecture.md created (🏗️ Architect)
- ✓ planning/<feature>/epics.md created (📋 PM)
- ✓ planning/<feature>/GEMINI.md, README.md, ARCHIVED/ created
- ✓ Committed to contrib/<gh-user>
- ✓ **Token savings: ~2,300 tokens vs manual approach**

**Next:** Create feature worktree (Phase 2 will use these planning docs as context)

**Reference:** [bmad-planner skill](/.gemini/skills/bmad-planner/SKILL.md)

---

### Phase 2: Feature Development

**Location:** Feature worktree
**Branch:** `feature/<timestamp>_<slug>`
**Skills:** git-workflow-manager, speckit-author, quality-enforcer, workflow-utilities

#### Step 2.1: Create Feature Worktree

**Command:**
```bash
python .gemini/skills/git-workflow-manager/scripts/create_worktree.py \
  feature <slug> contrib/<gh-user>
```

**Example:**
```bash
python .gemini/skills/git-workflow-manager/scripts/create_worktree.py \
  feature certificate-a1 contrib/stharrold
```

**Output:**
```
✓ Worktree created: /Users/user/Documents/GitHub/standard_feature_certificate-a1
✓ Branch: feature/20251023T104248Z_certificate-a1
✓ TODO file: TODO_feature_20251023T104248Z_certificate-a1.md
```

**Side effects:**
- Creates worktree directory: `<repo>_feature_<slug>/`
- Creates branch: `feature/<timestamp>_<slug>`
- Creates TODO_*.md in **main repo** (not worktree)
- Updates TODO.md manifest with new workflow reference
- Runs `uv sync` in worktree

**User prompt:** "next step?" (after planning)

#### Step 2.2: Switch to Worktree

```bash
cd /Users/user/Documents/GitHub/standard_feature_certificate-a1
```

#### Step 2.3: Create SpecKit Specifications

**Files created in worktree:**
- `spec.md` - Detailed specification (API contracts, data models, behaviors)
- `plan.md` - Implementation task breakdown (impl_001, impl_002, test_001, etc.)

**BMAD Context Integration:**

If planning documents exist in `../planning/<feature>/`:
```
I found BMAD planning documents from Phase 1.

Using as context:
- requirements.md: 15 functional requirements, 5 user stories
- architecture.md: Python/FastAPI stack, PostgreSQL database
- epics.md: 3 epics (data layer, API, tests)

Generating SpecKit specifications that align with BMAD planning...
```

If no planning documents:
```
No BMAD planning found. Creating specifications from scratch.

What is the main purpose of this feature?
```

**SpecKit uses planning context to generate:**
- spec.md sections align with requirements.md functional requirements
- plan.md tasks organized by epics.md epic breakdown
- Technology choices match architecture.md stack

**User prompt:** "next step?" (from worktree)

**Output:**
- ✓ spec.md created (~400-600 lines, informed by BMAD if available)
- ✓ plan.md created (~300-400 lines, organized by epics if available)
- ✓ Committed and pushed to feature branch

#### Step 2.4: Implementation Tasks

**Process:**
1. Parse `plan.md` for next pending task
2. Implement code following spec.md
3. Write tests (target ≥80% coverage)
4. **Check for deprecated files** - If implementation replaces existing files, use [file deprecation](#file-deprecation) process
5. Commit with semantic message
6. Update TODO_*.md task status
7. Repeat for all tasks

**User prompt:** "next step?" (iteratively)

**Commit format:**
```
<type>(<scope>): <subject>

<body>

Implements: impl_003
Spec: spec.md
Tests: tests/test_validator.py
Coverage: 85%

Refs: TODO_feature_20251023T104248Z_certificate-a1.md

🤖 Generated with [Gemini Code](https://gemini.com/gemini-code)

Co-Authored-By: Gemini <noreply@anthropic.com>
```

---

### Phase 3: Quality Assurance

**Location:** Feature worktree
**Branch:** `feature/<timestamp>_<slug>`
**Skills:** quality-enforcer, workflow-utilities

**Quality Gates (all must pass):**

1. **Test Coverage ≥ 80%:**
   ```bash
   uv run pytest --cov=src --cov-report=term --cov-fail-under=80
   ```

2. **All Tests Passing:**
   ```bash
   uv run pytest
   ```

3. **Linting Clean:**
   ```bash
   uv run ruff check src/ tests/
   ```

4. **Type Checking Clean:**
   ```bash
   uv run mypy src/
   ```

5. **Build Successful:**
   ```bash
   uv build
   ```

6. **Container Healthy** (if applicable):
   ```bash
   podman build -t standard:test .
   podman run --rm standard:test pytest
   ```

**User prompt:** "next step?" (after all implementation)

**Command:**
```bash
python .gemini/skills/quality-enforcer/scripts/run_quality_gates.py
```

**Output:**
```
Running Quality Gates...

COVERAGE: ✓ 87% (≥80% required)
TESTS: ✓ 45/45 passing
LINTING: ✓ 0 issues
TYPES: ✓ 0 errors
BUILD: ✓ Success

✓ ALL GATES PASSED

Next: Semantic version calculation
```

---


---

**Next:** [Integration Phases (4-5)](workflow-integration.md)
