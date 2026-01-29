# Project Inventory

Current status of Standard Workflow v1.15.1 deployment across D:\Projects\ repositories.

**Last Updated:** 2025-11-24
**Workflow Version:** v1.15.1 (based on German Workflow v5.3.0)
**Source:** D:\Projects\stharrold-templates

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Workflow installed, 9 skills present |
| 🔄 | Partial installation or update needed |
| ⚠️ | Special case (see notes) |
| ❌ | No workflow installed |
| N/A | Not applicable (not a git repo, excluded) |

---

## Production Projects (5)

These are actively used in production environments.

| Project | Type | Workflow Status | Skill Count | Last Applied | Notes |
|---------|------|-----------------|-------------|--------------|-------|
| **sql/** | Production | ✅ | 9 | 2025-11-19 | HIPAA-compliant SQL tool, 89% coverage |
| **catalog/** | Production | ✅ | 9 | 2025-11-19 | EDW data catalog, 144 views |
| **OracleERP/** | Production | ❌ | 0 | Never | SSIS project (Visual Studio 2019) |
| **azure-devops/** | Tool | ✅ | 9 | 2025-11-19 | Work item CLI, SQLite cache |
| **azure-pr-reviewer/** | Tool | ✅ | 9 | 2025-11-19 | PR review automation |

**Notes:**
- **OracleERP/** - SSIS project, may not benefit from Python workflow. Consider if workflow applicable.
- **sql/** - Currently used as source for apply-workflow-batch.sh (should switch to stharrold-templates)

---

## Development Projects (10)

Active development repositories.

| Project | Type | Workflow Status | Skill Count | Last Applied | Notes |
|---------|------|-----------------|-------------|--------------|-------|
| **app_geocode/** | Development | ✅ | 9 | 2025-11-19 | Geocoding utilities |
| **CBIA/** | Development | ✅ | 9 | 2025-11-19 | CBIA-specific tools |
| **Demand/** | Development | ✅ | 9 | 2025-11-19 | Demand analysis |
| **GeocodedAddresses/** | Development | ✅ | 9 | 2025-11-19 | Address processing |
| **Huddles/** | Development | ✅ | 9 | 2025-11-19 | Huddles data |
| **NRC/** | Development | ✅ | 9 | 2025-11-19 | NRC utilities |
| **PerformanceGoals/** | Development | ✅ | 9 | 2025-11-19 | Goals tracking |
| **Rooms/** | Development | ✅ | 9 | 2025-11-19 | Room data |
| **SysIntg/** | Development | ✅ | 9 | 2025-11-19 | System integration |
| **emails/** | Tool | ✅ | 9 | 2025-11-19 | Outlook export, FTS5 search |

---

## Reference Projects (1)

| Project | Type | Workflow Status | Skill Count | Last Applied | Notes |
|---------|------|-----------------|-------------|--------------|-------|
| **CPSC/** | Reference | ✅ | 9 | 2025-11-19 | SSIS patterns (formerly Tempcpsc_reference) |

---

## Infrastructure & Workspace Directories (7)

Not git repositories or special-purpose directories.

| Directory | Type | Workflow Status | Reason |
|-----------|------|-----------------|--------|
| **Azure/** | Infrastructure | N/A | Not a git repository (ARM, Bicep, Functions) |
| **Gemini_Sessions/** | Workspace | N/A | Container for temporary Claude Code workspaces |
| **Databases/** | Tools | N/A | DBeaver workspaces, exports |
| **Notebooks/** | Analysis | N/A | marimo notebooks (not git) |
| **onboarding-guide/** | Documentation | N/A | Not a git repository |
| **templates/** | Templates | N/A | Contains workflow-template (separate) |
| **ARCHIVED/** | Archive | N/A | Archived versions |

---

## Special Cases

### stharrold-templates

**Status:** Source repository (not a target)
**Location:** D:\Projects\stharrold-templates
**Purpose:** Development version of workflow system
**Notes:**
- This is the authoritative source for applying workflow to other repos
- On branch: contrib/sharrold (not yet merged to main)
- Will eventually merge into templates/workflow-template

### templates/workflow-template

**Status:** Deployed template (not a target)
**Location:** D:\Projects\templates\workflow-template
**Purpose:** Production template for new projects
**Notes:**
- Currently based on Standard Workflow v7x1.0 (older than stharrold-templates)
- Used by initialize-repository script
- Should be updated from stharrold-templates after merge

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Total git repositories** | 16 |
| **With workflow (9 skills)** | 14 |
| **Without workflow** | 1 (OracleERP) |
| **Unknown status** | 1 (OracleERP - needs verification) |
| **Non-git directories** | 7 |
| **Coverage** | 93% (14/15 applicable repos) |

---

## Batch Script Coverage

### Currently in apply-workflow-batch.sh (10 projects)

```bash
PROJECTS=(
    "app_geocode"
    "CBIA"
    "Demand"
    "emails"
    "GeocodedAddresses"
    "Huddles"
    "NRC"
    "PerformanceGoals"
    "Rooms"
    "SysIntg"
)
```

### Missing from Batch Script (5 projects)

Projects that should be added to batch script:

1. **azure-devops** - Tool (has workflow)
2. **azure-pr-reviewer** - Tool (has workflow)
3. **catalog** - Production (has workflow)
4. **CPSC** - Reference (has workflow)
5. **OracleERP** - Production (needs evaluation)

---

## Planned Actions

### Phase 1: Update Source (Completed)
- [x] Analyze structure difference between stharrold-templates and sql/
- [x] Create deployment documentation
- [x] Document version numbering scheme

### Phase 2: Update Scripts (In Progress)
- [ ] Update apply-workflow-batch.sh to use stharrold-templates as source
- [ ] Add missing projects to PROJECTS array
- [ ] Enhance verify-workflow.sh with skill validation

### Phase 3: Re-apply Workflow (Pending)
- [ ] Dry run on single project
- [ ] Run updated batch script on all projects
- [ ] Verify with verify-workflow.sh

### Phase 4: Verification (Pending)
- [ ] Confirm all projects have 9 skills
- [ ] Test quality gates in each project
- [ ] Update this inventory with results

---

## Project Details

### Production Projects

#### sql/ (HIPAA-compliant SQL Query Tool)
- **Status:** ✅ Complete (9 skills)
- **Tech Stack:** Python 3.11, uv, pyodbc, polars
- **Coverage:** 89%
- **Tests:** 83 passing
- **Features:**
  - Azure AD authentication
  - Windows Credential Manager encryption
  - 4-file output (SQL, JSONL, log, config)
  - YAML frontmatter
- **Workflow Applied:** 2025-11-19
- **Source Used:** sql/.gemini (self)

#### catalog/ (EDW Data Catalog)
- **Status:** ✅ Complete (9 skills)
- **Tech Stack:** Python 3.11, FastAPI, PostgreSQL, polars
- **Coverage:** ≥80%
- **Features:**
  - 144 views cataloged
  - PK/FK detection
  - PyODBC-based discovery
- **Workflow Applied:** 2025-11-19

#### OracleERP/ (SSIS Package)
- **Status:** ❌ No workflow
- **Tech Stack:** Visual Studio 2019, SSIS, SQL Server Synapse
- **Features:**
  - Creates stored procedures, base tables, views
  - OracleERP_* data integration
  - Comprehensive data dictionary (1839 lines)
- **Decision Needed:** Is Python workflow applicable to SSIS project?

#### azure-devops/ (Work Item CLI)
- **Status:** ✅ Complete (9 skills)
- **Tech Stack:** Python 3.11, Azure DevOps CLI, SQLite
- **Features:**
  - Work item management
  - SQLite cache
  - IUH-DSA/CBIA/ organization
- **Workflow Applied:** 2025-11-19

#### azure-pr-reviewer/ (PR Review Automation)
- **Status:** ✅ Complete (9 skills)
- **Tech Stack:** Python 3.11
- **Features:** PR review automation
- **Workflow Applied:** 2025-11-19

### Development Projects

All development projects (app_geocode, CBIA, Demand, GeocodedAddresses, Huddles, NRC, PerformanceGoals, Rooms, SysIntg) have:
- ✅ Workflow installed (9 skills)
- Applied: 2025-11-19
- Source: sql/.gemini

### Reference Projects

#### CPSC/ (SSIS Patterns)
- **Status:** ✅ Complete (9 skills)
- **Type:** Reference implementation
- **Features:**
  - SSIS patterns and SQL transformations
  - Children's Pediatric Specialty Clinic data
- **History:** Moved from catalog/ to Projects root (2025-11-19)
- **Workflow Applied:** 2025-11-19

---

## Next Update Schedule

This inventory should be updated:
- ✅ Before batch workflow application
- ✅ After batch workflow application
- ✅ When new projects are added
- ✅ After workflow version upgrades
- ✅ Monthly (first Monday of month)

**Next Update Due:** 2025-12-02

---

## Verification Commands

To regenerate this inventory:

```bash
# Count projects with workflow
cd D:\Projects
bash verify-workflow.sh

# Check specific project
cd D:\Projects\<project>
ls .claude/skills/ | wc -l  # Should be 9
```

To verify quality gates:

```bash
cd D:\Projects\<project>
python .claude/skills/quality-enforcer/scripts/run_quality_gates.py
```

---

## Related Documentation

- [Application Guide](application-guide.md) - How to apply workflow
- [Decision Matrix](decision-matrix.md) - Method selection
- [Version Mapping](version-mapping.md) - Version numbering
- [D:\Projects\CLAUDE.md](../../../CLAUDE.md) - Meta-repository overview
