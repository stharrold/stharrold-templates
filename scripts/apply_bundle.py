#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Apply named bundles of files from stharrold-templates to a target repo.

Usage:
    python scripts/apply_bundle.py <source-repo> <target-repo> --bundle <name> [--bundle <name>] [--force] [--dry-run]

Bundles: git, secrets, ci, pipeline, graphrag, sql-pipeline, data-catalog, full
"""

from __future__ import annotations

import argparse
import shutil
import sys
import textwrap
import tomllib
from pathlib import Path

# ---------------------------------------------------------------------------
# Bundle definitions (source of truth)
# ---------------------------------------------------------------------------

BUNDLE_DEFINITIONS: dict[str, dict] = {
    "git": {
        "skills": ["git-workflow-manager", "workflow-orchestrator", "workflow-utilities"],
        "commands": [".claude/commands/workflow/"],
        "copy_files": ["WORKFLOW.md", "CONTRIBUTING.md"],
        "merge_gitignore": True,
        "merge_pyproject_deps": [],
    },
    "secrets": {
        "skills": [],
        "commands": [],
        "copy_files": ["scripts/secrets_setup.py", "scripts/secrets_run.py", "scripts/environment_utils.py"],
        "skip_on_update": ["secrets.toml"],
        "merge_gitignore": False,
        "merge_pyproject_deps": ["keyring>=24.0.0", "tomlkit>=0.13.3"],
    },
    "ci": {
        "skills": [],
        "commands": [],
        "copy_files": [
            ".github/workflows/tests.yml",
            ".github/workflows/claude-code-review.yml",
            ".github/workflows/secrets-example.yml",
            "Containerfile",
            "podman-compose.yml",
        ],
        "skip_on_update": [".pre-commit-config.yaml"],
        "merge_gitignore": False,
        "merge_pyproject_deps": ["ruff>=0.14.1", "pytest>=8.4.2", "pytest-cov>=7.0.0", "pre-commit>=4.5.0"],
    },
    "pipeline": {
        "skills": [],
        "commands": [],
        "copy_files": [
            # Core infrastructure (template-owned, always replaced)
            "utils/__init__.py",
            "utils/core_db.py",
            "utils/core_embedder.py",
            "utils/core_llm.py",
            "utils/json_repair.py",
            "utils/pipe_04_vectorize.py",
            "utils/pipe_04b_consolidate.py",
            "utils/pipe_05b_cooccurrence.py",
            "utils/pipe_06_optimize.py",
            "utils/pipe_parallel.py",
            "utils/pipe_runner.py",
            "utils/bench_log.py",
            "utils/bench_compare.py",
            "utils/tool_maintenance.py",
            "models/Modelfile.qwen3-0.6b",
            "scripts/ollama_start.ps1",
            "scripts/ollama_stop.ps1",
            "scripts/run_pipeline.ps1",
            "scripts/run_pipeline_incremental.py",
            "scripts/run_entity_quality.py",
            "scripts/backfill_normalize_entities.py",
        ],
        "skip_on_update": [
            # Domain-specific (email examples, user customizes)
            "utils/pipe_01_ingest.py",
            "utils/pipe_02_verify.py",
            "utils/pipe_02b_strip.py",
            "utils/pipe_02c_threads.py",
            "utils/pipe_03_decompose.py",
            "utils/pipe_03b_normalize.py",
            "utils/pipe_05_link.py",
            "config/pipeline_config.json",
        ],
        "merge_gitignore": True,
        "merge_pyproject_deps": [
            "duckdb>=1.2.0",
            "onnxruntime>=1.21.0",
            "numpy>=2.2.0",
            "httpx>=0.28.0",
            "scikit-learn>=1.6.0",
            "json-repair>=0.39.0",
        ],
    },
    "sql-pipeline": {
        "skills": [],
        "commands": [],
        "copy_files": [
            # Core infrastructure (template-owned, always replaced)
            "src/__init__.py",
            "src/config_validator.py",
            "src/deployer.py",
            "src/environment_utils.py",
            "src/execute_pipeline.py",
            "src/file_writer.py",
            "src/logger.py",
            "src/query_runner.py",
            "src/query_types.py",
            "src/resumption.py",
            "src/retry.py",
            "src/slug_generator.py",
            "src/sql_utils.py",
            "docs/sharepoint/build.py",
        ],
        "skip_on_update": [
            # Project-specific (user customizes)
            "config/config.schema.json",
            "config/config.dev.json",
            "pipeline_config.json",
            ".sqlfluff",
            "azure-pipelines.yml",
            "sql/v1/example_view.sql",
            "docs/sharepoint/src/10_overview.md",
        ],
        "merge_gitignore": True,
        "merge_pyproject_deps": [
            "pyodbc>=5.1.0",
            "polars>=1.0.0",
            "pyyaml>=6.0.0",
            "sqlfluff>=3.0.0",
            "mypy>=1.10.0",
        ],
    },
    "data-catalog": {
        "skills": [],
        "commands": [],
        "copy_files": [
            "data_catalog/__init__.py",
            "data_catalog/exceptions.py",
            "data_catalog/db/__init__.py",
            "data_catalog/db/models.py",
            "data_catalog/db/connection.py",
            "data_catalog/db/repositories.py",
            "data_catalog/models/__init__.py",
            "data_catalog/models/data_model.py",
            "data_catalog/utils/__init__.py",
            "data_catalog/utils/sql_safety.py",
            "data_catalog/services/__init__.py",
            "data_catalog/services/sql_dialect.py",
            "data_catalog/services/embedding.py",
            "data_catalog/services/vector_similarity.py",
            "data_catalog/services/graph_metrics.py",
            "data_catalog/services/rag_search.py",
            "data_catalog/services/grain_discovery.py",
            "data_catalog/services/pk_discovery/__init__.py",
            "data_catalog/services/pk_discovery/models.py",
            "data_catalog/services/pk_discovery/scanner.py",
            "data_catalog/services/pk_discovery/decision.py",
            "data_catalog/services/fk_discovery.py",
            "data_catalog/services/fk_validator.py",
            "data_catalog/services/sample_pool.py",
            "data_catalog/services/cardinality_scanner.py",
            "data_catalog/services/pipeline_orchestrator.py",
            "data_catalog/services/column_descriptions.py",
            "data_catalog/cli.py",
            "tests/__init__.py",
            "tests/conftest.py",
            "tests/test_models.py",
            "tests/test_grain_discovery.py",
            "tests/test_fk_discovery.py",
            "tests/test_graph_metrics.py",
            "tests/test_rag_search.py",
            "tests/test_pipeline_orchestrator.py",
            "tests/test_repositories.py",
        ],
        "skip_on_update": [
            "data_catalog/services/dialects/__init__.py",
            "data_catalog/services/dialects/sqlserver.py",
            "data_catalog/services/fk_patterns.py",
            "config/catalog_config.json",
            "config/primary_keys_config.json",
            "config/foreign_keys_config.json",
            "scripts/run_catalog_pipeline.py",
            "scripts/generate_column_descriptions.py",
        ],
        "merge_gitignore": True,
        "merge_pyproject_deps": [
            "duckdb>=1.2.0",
            "duckdb-engine>=0.15.0",
            "sqlalchemy>=2.0.0",
            "onnxruntime>=1.21.0",
            "numpy>=2.2.0",
            "scikit-learn>=1.6.0",
            "click>=8.1.0",
            "rich>=13.0.0",
            "networkx>=3.0",
            "tokenizers>=0.21.0",
        ],
    },
    "graphrag": {
        "includes": ["pipeline"],
        "skills": [],
        "commands": [],
        "copy_files": [
            # Retrieval infrastructure (template-owned)
            "utils/core_reranker.py",
            "utils/rag_generate.py",
        ],
        "skip_on_update": [
            # Domain-specific formatting and prompts
            "utils/core_formatter.py",
            "utils/rag_directives.py",
        ],
        "merge_gitignore": False,
        "merge_pyproject_deps": [],
    },
    "full": {
        "includes": ["git", "secrets", "ci", "graphrag", "sql-pipeline", "data-catalog"],
        "skills": ["tech-stack-adapter", "agentdb-state-manager", "initialize-repository"],
        "commands": [],
        "copy_files": [],
        "copy_dirs": ["docs/"],
        "merge_gitignore": False,
        "merge_pyproject_deps": [],
    },
}

VALID_BUNDLE_NAMES = set(BUNDLE_DEFINITIONS.keys())

# Patterns always added when merge_gitignore is True
GITIGNORE_WORKFLOW_PATTERNS = [
    ".claude-state/",
    ".tmp/",
    "*.duckdb",
    "*.duckdb.wal",
]

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_source(source: Path) -> tuple[bool, str]:
    """Check *source* has `.claude/skills/` with >= 3 skills."""
    skills_dir = source / ".claude" / "skills"
    if not skills_dir.is_dir():
        return False, f"Source missing .claude/skills/ directory: {skills_dir}"
    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(skill_dirs) < 3:
        return False, f"Source has only {len(skill_dirs)} skills in .claude/skills/ (need >= 3)"
    return True, "ok"


def validate_target(target: Path) -> tuple[bool, str]:
    """Check *target* has `.git/` (directory) or `.git` (worktree file)."""
    git_path = target / ".git"
    if not git_path.exists():
        return False, f"Target is not a git repo (no .git): {target}"
    return True, "ok"


# ---------------------------------------------------------------------------
# Bundle resolution
# ---------------------------------------------------------------------------


def resolve_bundles(names: list[str]) -> list[str]:
    """Expand composite bundles (e.g. ``full``) into constituents.

    Recursively expands ``includes`` so nested composites (e.g.
    ``full`` -> ``graphrag`` -> ``pipeline``) are fully flattened.
    Returns a flat, deduplicated list preserving first-seen order.
    """
    seen: set[str] = set()
    result: list[str] = []

    def _expand(name: str) -> None:
        if name not in VALID_BUNDLE_NAMES:
            raise ValueError(f"Unknown bundle: {name!r} (valid: {sorted(VALID_BUNDLE_NAMES)})")
        if name in seen:
            return
        defn = BUNDLE_DEFINITIONS[name]
        # Recursively expand includes first
        if "includes" in defn:
            for sub in defn["includes"]:
                _expand(sub)
        # Then add the bundle itself
        if name not in seen:
            seen.add(name)
            result.append(name)

    for name in names:
        _expand(name)

    return result


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


def copy_tree(source: Path, target: Path, rel_dir: str, *, dry_run: bool) -> int:
    """Copy an entire directory from *source* to *target*.

    Returns the number of items reported.
    """
    src = source / rel_dir
    dst = target / rel_dir
    if not src.is_dir():
        print(f"  WARN {rel_dir} not found in source, skipping")
        return 0

    action = "COPY" if not dst.exists() else "REPLACE"
    print(f"  {action} {rel_dir}")
    if not dry_run:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, dirs_exist_ok=True)
    return 1


def copy_files(source: Path, target: Path, rel_paths: list[str], *, dry_run: bool) -> int:
    """Copy individual files, creating parent dirs as needed.

    Returns the count of items reported.
    """
    count = 0
    for rel in rel_paths:
        src = source / rel
        dst = target / rel
        if not src.exists():
            print(f"  WARN {rel} not found in source, skipping")
            continue
        action = "COPY" if not dst.exists() else "REPLACE"
        print(f"  {action} {rel}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        count += 1
    return count


def copy_skip_on_update(source: Path, target: Path, rel_paths: list[str], *, force: bool, dry_run: bool) -> int:
    """Copy if not exists; skip+warn if exists (unless *force*)."""
    count = 0
    for rel in rel_paths:
        src = source / rel
        dst = target / rel
        if not src.exists():
            print(f"  WARN {rel} not found in source, skipping")
            continue
        if dst.exists() and not force:
            print(f"  SKIP {rel} (exists, use --force to overwrite)")
            count += 1
            continue
        action = "COPY" if not dst.exists() else "REPLACE"
        print(f"  {action} {rel}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Merge helpers
# ---------------------------------------------------------------------------


def _extract_dep_name(spec: str) -> str:
    """Return the bare package name from a PEP 508 specifier string."""
    for ch in (">=", "<=", "==", "!=", "~=", ">", "<", "["):
        idx = spec.find(ch)
        if idx != -1:
            return spec[:idx].strip().lower()
    return spec.strip().lower()


def merge_pyproject_deps(target: Path, deps: list[str], *, dry_run: bool) -> int:
    """Append missing *deps* to the target ``pyproject.toml``.

    Uses string manipulation to avoid a tomlkit dependency.
    Returns 1 if any action was taken, else 0.
    """
    if not deps:
        return 0

    pyproject_path = target / "pyproject.toml"

    if not pyproject_path.exists():
        # Create a minimal pyproject.toml with the deps
        deps_str = ",\n".join(f'    "{d}"' for d in sorted(deps))
        project_name = target.name or "project"
        content = textwrap.dedent(f"""\
            [project]
            name = "{project_name}"
            version = "0.0.0"
            requires-python = ">=3.11"

            [dependency-groups]
            dev = [
            {deps_str},
            ]
        """)
        print(f"  CREATE pyproject.toml ({len(deps)} deps)")
        if not dry_run:
            pyproject_path.write_text(content)
        return 1

    text = pyproject_path.read_text()

    # Parse existing TOML to find current deps
    try:
        data = tomllib.loads(text)
    except Exception:
        print("  WARN could not parse pyproject.toml, skipping dep merge")
        return 0

    # Determine which section to use
    existing_deps: list[str] = []
    section_key: str | None = None

    dg_dev = data.get("dependency-groups", {}).get("dev")
    uv_dev = data.get("tool", {}).get("uv", {}).get("dev-dependencies")

    if dg_dev is not None:
        existing_deps = list(dg_dev)
        section_key = "dependency-groups"
    elif uv_dev is not None:
        existing_deps = list(uv_dev)
        section_key = "tool.uv"
    else:
        section_key = None  # will create [dependency-groups].dev

    existing_names = {_extract_dep_name(d) for d in existing_deps}
    missing = [d for d in deps if _extract_dep_name(d) not in existing_names]

    if not missing:
        print("  MERGE pyproject.toml (0 deps added)")
        return 0

    print(f"  MERGE pyproject.toml ({len(missing)} dep{'s' if len(missing) != 1 else ''} added)")

    if dry_run:
        return 1

    lines = text.splitlines(keepends=True)

    if section_key == "dependency-groups":
        # Find the closing ] for [dependency-groups] dev = [...]
        _insert_deps_into_array(lines, "[dependency-groups]", "dev", missing)
    elif section_key == "tool.uv":
        _insert_deps_into_array(lines, "[tool.uv]", "dev-dependencies", missing)
    else:
        # Append a new section at the end
        deps_str = "\n".join(f'    "{d}",' for d in sorted(missing))
        lines.append("\n[dependency-groups]\n")
        lines.append(f"dev = [\n{deps_str}\n]\n")

    pyproject_path.write_text("".join(lines))
    return 1


def _insert_deps_into_array(lines: list[str], section_header: str, key: str, deps: list[str]) -> None:
    """Insert *deps* into a TOML array-of-strings in *lines* in-place.

    Locates *section_header* (e.g. ``[tool.uv]``), then the *key* = ``[`` line,
    then finds the closing ``]`` and inserts new entries just before it.
    """
    in_section = False
    found_key = False
    insert_idx: int | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Track section headers
        if stripped.startswith("[") and not stripped.startswith("[["):
            in_section = stripped == section_header or stripped.startswith(section_header.rstrip("]") + ".")
            # Also match exact header
            if stripped == section_header:
                in_section = True

        if in_section and not found_key:
            if stripped.startswith(f"{key}") and "=" in stripped:
                found_key = True

        if found_key:
            if stripped == "]":
                insert_idx = i
                break

    if insert_idx is not None:
        new_lines = [f'    "{d}",\n' for d in sorted(deps)]
        for j, nl in enumerate(new_lines):
            lines.insert(insert_idx + j, nl)


def merge_gitignore(target: Path, source: Path, *, dry_run: bool) -> int:
    """Append missing lines from source .gitignore and workflow patterns.

    Returns 1 if any action was taken, else 0.
    """
    target_gi = target / ".gitignore"
    source_gi = source / ".gitignore"

    # Collect existing target lines
    if target_gi.exists():
        existing_lines = set(target_gi.read_text().splitlines())
    else:
        existing_lines = set()

    # Collect candidate lines: workflow patterns + source .gitignore
    candidates: list[str] = list(GITIGNORE_WORKFLOW_PATTERNS)
    if source_gi.exists():
        for line in source_gi.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                candidates.append(stripped)

    missing = [c for c in dict.fromkeys(candidates) if c not in existing_lines]

    if not missing:
        print("  MERGE .gitignore (0 patterns added)")
        return 0

    print(f"  MERGE .gitignore ({len(missing)} pattern{'s' if len(missing) != 1 else ''} added)")

    if dry_run:
        return 1

    with open(target_gi, "a") as f:
        if existing_lines:
            if not target_gi.read_text().endswith("\n"):
                f.write("\n")
            f.write("\n# Added by apply_bundle\n")
        else:
            f.write("# Added by apply_bundle\n")
        for pat in missing:
            f.write(f"{pat}\n")

    return 1


# ---------------------------------------------------------------------------
# Bundle application
# ---------------------------------------------------------------------------


def apply_bundle(source: Path, target: Path, bundle_name: str, *, force: bool, dry_run: bool) -> None:
    """Apply a single bundle from *source* to *target*."""
    defn = BUNDLE_DEFINITIONS[bundle_name]
    item_count = 0
    print(f"Applying bundle: {bundle_name}")

    # Skills
    for skill in defn.get("skills", []):
        rel = f".claude/skills/{skill}/"
        item_count += copy_tree(source, target, rel, dry_run=dry_run)

    # Commands (directories)
    for cmd_dir in defn.get("commands", []):
        item_count += copy_tree(source, target, cmd_dir, dry_run=dry_run)

    # Copy files (template-owned, always replace)
    rel_paths = defn.get("copy_files", [])
    if rel_paths:
        item_count += copy_files(source, target, rel_paths, dry_run=dry_run)

    # Copy dirs (template-owned, always replace)
    for d in defn.get("copy_dirs", []):
        item_count += copy_tree(source, target, d, dry_run=dry_run)

    # Skip-on-update files
    skip_paths = defn.get("skip_on_update", [])
    if skip_paths:
        item_count += copy_skip_on_update(source, target, skip_paths, force=force, dry_run=dry_run)

    # Merge pyproject deps
    merge_deps = defn.get("merge_pyproject_deps", [])
    if merge_deps:
        item_count += merge_pyproject_deps(target, merge_deps, dry_run=dry_run)

    # Merge .gitignore
    if defn.get("merge_gitignore"):
        item_count += merge_gitignore(target, source, dry_run=dry_run)

    print(f"\nApplied: {bundle_name} ({item_count} item{'s' if item_count != 1 else ''})\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Apply named bundles of files from stharrold-templates to a target repo.",
        epilog="Example: python scripts/apply_bundle.py . ../my-project --bundle git --bundle secrets",
    )
    parser.add_argument("source_repo", type=Path, help="Path to cloned stharrold-templates")
    parser.add_argument("target_repo", type=Path, help="Path to target repo (must be a git repo)")
    parser.add_argument(
        "--bundle",
        dest="bundles",
        action="append",
        required=True,
        choices=sorted(VALID_BUNDLE_NAMES),
        help="Bundle to apply (repeatable)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite files that would normally be skipped (e.g. skip_on_update entries)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would change, make no modifications")

    args = parser.parse_args()

    source = args.source_repo.resolve()
    target = args.target_repo.resolve()

    # Validate
    ok, msg = validate_source(source)
    if not ok:
        print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    ok, msg = validate_target(target)
    if not ok:
        print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    # Resolve bundles (expand composites, deduplicate)
    try:
        resolved = resolve_bundles(args.bundles)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("=== DRY RUN ===\n")

    # Apply each bundle
    for name in resolved:
        apply_bundle(source, target, name, force=args.force, dry_run=args.dry_run)

    summary = ", ".join(resolved)
    print(f"Done. Bundles applied: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
