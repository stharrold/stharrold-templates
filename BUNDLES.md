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

### `pipeline` -- Document Processing Pipeline

6-stage ETL pipeline for building knowledge graphs from documents. Uses DuckDB, ONNX embeddings (MiniLM-L6-v2), and Ollama LLM for entity extraction. Domain-agnostic core with email examples as skip-on-update customization points.

**Core infrastructure (template-owned):**
- `utils/__init__.py`
- `utils/core_db.py` -- DuckDB singleton (`raw_documents`, `knowledge_graphs`, `graph_nodes`, `semantic_edges`)
- `utils/core_embedder.py` -- ONNX MiniLM-L6-v2 (384-dim → 384-bit quantized)
- `utils/core_llm.py` -- Ollama HTTP API wrapper
- `utils/json_repair.py` -- JSON repair for LLM output
- `utils/pipe_04_vectorize.py` -- ONNX embed + 1-bit quantize
- `utils/pipe_04b_consolidate.py` -- Entity deduplication via fuzzy name matching + community clustering (token-based blocking for large groups)
- `utils/pipe_05b_cooccurrence.py` -- Co-occurrence edges (related_to/part_of) between entities mentioned in same documents
- `utils/pipe_06_optimize.py` -- PageRank, HITS, community detection, embedding clustering
- `utils/pipe_parallel.py` -- 2-phase batch pipeline (DB released during LLM inference)
- `utils/pipe_runner.py` -- Sequential pipeline orchestrator
- `utils/bench_log.py` -- Per-document JSONL bench logging
- `utils/bench_compare.py` -- Cross-model bench comparison
- `utils/tool_maintenance.py` -- DB stats and integrity checks
- `models/Modelfile.qwen3-0.6b` -- Default Ollama model definition
- `scripts/ollama_start.ps1`, `scripts/ollama_stop.ps1` -- Ollama lifecycle
- `scripts/run_pipeline.ps1` -- Orchestrated pipeline run
- `scripts/run_pipeline_incremental.py` -- Incremental import + process
- `scripts/run_entity_quality.py` -- Run all entity quality stages (strip, normalize, consolidate, co-occurrence)
- `scripts/backfill_normalize_entities.py` -- Backfill entity type normalization on existing data

**Domain-specific (user-owned, skip on update):**
- `utils/pipe_01_ingest.py` -- Document ingestion (email example)
- `utils/pipe_02_verify.py` -- Verification heuristics (email example)
- `utils/pipe_02b_strip.py` -- Content preprocessing (email example)
- `utils/pipe_02c_threads.py` -- Thread/relationship analysis (email example)
- `utils/pipe_03_decompose.py` -- Entity types and LLM prompts (email example)
- `utils/pipe_03b_normalize.py` -- Entity type normalization and blocklist (email example)
- `utils/pipe_05_link.py` -- Edge types and linking rules (email example)
- `config/pipeline_config.json` -- Model, LLM options, chunk tiers

**Merge files (user-owned):**
- `pyproject.toml` -- adds `duckdb`, `onnxruntime`, `numpy`, `httpx`, `scikit-learn`, `json-repair`
- `.gitignore` -- appends `*.duckdb`, `*.duckdb.wal`, `.claude-state/`, `.tmp/`

---

### `sql-pipeline` -- SQL Server ETL Pipeline

Python-orchestrated SQL Server ETL pipeline. Executes stored procedures in dependency order via `pipeline_config.json`, produces auditable JSONL logs with YAML frontmatter, and includes ad-hoc query runner and SQL deployer tools. Uses pyodbc, retry-on-transient-error, and atomic file writes.

**Core infrastructure (template-owned):**
- `src/__init__.py` -- Package init with version
- `src/config_validator.py` -- Lightweight JSON schema validator (no jsonschema dependency)
- `src/deployer.py` -- SQL file deployment with GO-batch splitting
- `src/environment_utils.py` -- CI/WSL environment detection
- `src/execute_pipeline.py` -- Pipeline orchestrator (load_config, get_connection_string, PipelineRunner)
- `src/file_writer.py` -- YAML frontmatter + atomic writes (4-file output)
- `src/logger.py` -- JSONL logging with batch and time-based progress tracking
- `src/query_runner.py` -- Paginated query execution with 4-file output
- `src/query_types.py` -- TypedDict, dataclass, and Literal type definitions
- `src/resumption.py` -- Row-level (WHERE clause) and step-level pipeline resumption
- `src/retry.py` -- Retry decorator for transient pyodbc errors
- `src/slug_generator.py` -- Filename slug generation from SQL or description
- `src/sql_utils.py` -- GO-batch splitter
- `docs/sharepoint/build.py` -- Assemble source .md files into single SharePoint page

**Project-specific (user-owned, skip on update):**
- `config/config.schema.json` -- JSON schema for config.{env}.json
- `config/config.dev.json` -- Dev environment connection config
- `pipeline_config.json` -- Pipeline step definitions and smoke tests
- `.sqlfluff` -- SQLFluff linter config (tsql dialect)
- `azure-pipelines.yml` -- Azure Pipelines CI/CD template
- `sql/v1/example_view.sql` -- Example SP + EXEC + VIEW pattern
- `docs/sharepoint/src/10_overview.md` -- Documentation overview page

**Merge files (user-owned):**
- `pyproject.toml` -- adds `pyodbc`, `polars`, `pyyaml`, `sqlfluff`, `mypy`
- `.gitignore` -- appends `outputs/`, `*.log.jsonl`, `.claude-state/`, `.tmp/`

---

### `graphrag` -- Graph RAG Retrieval

Graph-based retrieval-augmented generation. Embeds queries, searches the knowledge graph via Hamming distance, reranks with cosine similarity, expands context via N-hop graph walks, then generates answers with source citations. Requires `pipeline` bundle (auto-included).

**Retrieval infrastructure (template-owned):**
- `utils/core_reranker.py` -- Cosine reranking of Hamming-retrieved candidates
- `utils/rag_generate.py` -- Full RAG pipeline: embed → search → rerank → expand → generate

**Domain-specific (user-owned, skip on update):**
- `utils/core_formatter.py` -- Citation formatting (email example)
- `utils/rag_directives.py` -- RAG prompt templates (email example)

**Includes:** `pipeline` (all pipeline files + deps are auto-included)

---

### `full` -- Everything

All files from `git` + `secrets` + `ci` + `graphrag` (which includes `pipeline`) + `sql-pipeline`, plus additional skills and documentation.

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
| **Template-owned** | Skills, commands, scripts, core `utils/`, core `src/`, `WORKFLOW.md`, `CONTRIBUTING.md`, `Containerfile`, workflows, `docs/sharepoint/build.py` | Copy | Replace | Replace |
| **User-owned (merge)** | `pyproject.toml`, `.gitignore` | Create from template | Merge (add missing entries only) | Merge |
| **User-owned (skip)** | `secrets.toml`, `.pre-commit-config.yaml`, `config/pipeline_config.json`, `config/config.*.json`, `pipe_01_ingest.py`..`pipe_05_link.py`, `core_formatter.py`, `rag_directives.py`, `.sqlfluff`, `azure-pipelines.yml`, `sql/v1/example_view.sql`, `docs/sharepoint/src/*.md` | Copy from template | Skip + print warning | Replace |
| **Override** | Template-owned + skip-on-update | -- | -- | Replace (merge files still merge) |

### Merge behavior details

- **`.gitignore`**: Appends lines from the template that are not already present. Does not remove existing entries.
- **`pyproject.toml`**: Adds missing packages to `[dependency-groups] dev`. Does not modify existing version pins or remove packages.
- **Skip + warn**: Prints a message like `SKIP secrets.toml (already exists, use --force to overwrite)` to stdout.
- **`--force`**: Overwrites skip-on-update files. Merge-type files (`pyproject.toml`, `.gitignore`) keep their merge behavior.
