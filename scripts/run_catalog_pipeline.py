#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Config-driven 11-phase catalog pipeline runner.

This is a skip-on-update file -- customize for your source database.

CUSTOMIZE: Update connection logic, schema patterns, and phase
configuration for your environment.

Phases:
  1. seed          - Create Asset stubs in catalog DB
  2. enrich        - Query source DB for column metadata, row counts
  3. pipeline      - PK discovery + cardinality + value frequencies
  4. vectors       - Semantic value vectors from frequency data
  5. fk            - FK discovery + validation per-asset
  6. col_populate  - Sync columns to search index
  7. col_prepare   - Build prompt files for LLM descriptions
  8. col_describe  - Generate runbook (list assets needing descriptions)
  9. col_import    - Import description JSON into search index
 10. col_embed     - Embed descriptions as semantic_description vectors
 11. graph_analyze - Graph analysis for entity discovery (no source DB)

Usage:
    python scripts/run_catalog_pipeline.py
    python scripts/run_catalog_pipeline.py --batch my_schema
    python scripts/run_catalog_pipeline.py --phase seed,enrich
    python scripts/run_catalog_pipeline.py --resume
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# CUSTOMIZE: Adjust the Python path for your project layout.
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from data_catalog.db.connection import SessionLocal
from data_catalog.db.models import Asset

# CUSTOMIZE: Paths to config and checkpoint files.
DEFAULT_CONFIG = Path("config/catalog_config.json")
CHECKPOINT_PATH = Path("data/output/pipeline_state.json")

ALL_PHASES = [
    "seed", "enrich", "pipeline", "vectors", "fk",
    "col_populate", "col_prepare", "col_describe",
    "col_import", "col_embed", "graph_analyze",
]


def get_source_connection():
    """Get source database connection.

    CUSTOMIZE: Replace with your database connection logic.
    This example shows a generic pyodbc pattern.

    Returns:
        (connection, cursor) tuple.
    """
    raise NotImplementedError(
        "CUSTOMIZE: Implement get_source_connection() for your database. "
        "See the SQL Server example in the docstring."
    )
    # Example for SQL Server:
    # import pyodbc
    # conn_str = (
    #     "Driver={ODBC Driver 18 for SQL Server};"
    #     "Server=your-server.database.windows.net;"
    #     "Database=YourDB;"
    #     "UID=your_user;"
    #     "PWD=your_password;"
    #     "Encrypt=yes;"
    # )
    # conn = pyodbc.connect(conn_str)
    # return conn, conn.cursor()


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    """Load pipeline configuration."""
    if not path.exists():
        logger.warning(f"Config not found: {path}, using defaults")
        return {"batches": {}}
    with open(path) as f:
        return json.load(f)


def load_checkpoint() -> dict:
    """Load or initialize pipeline checkpoint."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {"assets": {}, "phases": {}}


def save_checkpoint(state: dict) -> None:
    """Persist checkpoint to disk."""
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ------------------------------------------------------------------
# Phase implementations
# ------------------------------------------------------------------


def phase_seed(batch_config: dict, db_session) -> dict:
    """Phase 1: Create Asset stubs in catalog database.

    CUSTOMIZE: Adjust asset creation for your schema structure.
    """
    schema = batch_config.get("schema", "dbo")
    tables = batch_config.get("tables", [])
    created = 0

    for table_name in tables:
        qualified = f"[{schema}].[{table_name}]"
        existing = db_session.query(Asset).filter(
            Asset.qualified_name == qualified
        ).first()

        if existing:
            continue

        asset = Asset(
            id=str(uuid4()),
            qualified_name=qualified,
            table_schema=schema,
            table_name=table_name,
            asset_type="table",
            source_system="source_db",
            schema_metadata={},
            statistics={},
            business_metadata={},
        )
        db_session.add(asset)
        created += 1

    db_session.commit()
    logger.info(f"  Seeded {created} assets for schema {schema}")
    return {"created": created}


def phase_enrich(batch_config: dict, db_session, cursor) -> dict:
    """Phase 2: Enrich assets with column metadata from source DB.

    CUSTOMIZE: Adjust column metadata queries for your database.
    """
    from data_catalog.services.dialects import SQLServerDialect

    dialect = SQLServerDialect()
    schema = batch_config.get("schema", "dbo")

    assets = db_session.query(Asset).filter(
        Asset.table_schema == schema
    ).all()

    enriched = 0
    for asset in assets:
        try:
            sql = dialect.column_metadata_query(schema, asset.table_name)
            cursor.execute(sql)
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "name": row[0],
                    "data_type": row[1],
                    "ordinal_position": row[2],
                })

            if columns:
                asset.schema_metadata = asset.schema_metadata or {}
                asset.schema_metadata["columns"] = columns
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(asset, "schema_metadata")
                enriched += 1

        except Exception as e:
            logger.warning(f"  Enrich failed for {asset.qualified_name}: {e}")

    db_session.commit()
    logger.info(f"  Enriched {enriched}/{len(assets)} assets")
    return {"enriched": enriched}


def run_pipeline(args: argparse.Namespace) -> None:
    """Main pipeline entry point."""
    config = load_config(args.config if hasattr(args, "config") else DEFAULT_CONFIG)
    state = load_checkpoint() if args.resume else {"assets": {}, "phases": {}}

    # Determine phases to run
    if args.phase:
        phases = [p.strip() for p in args.phase.split(",")]
    else:
        phases = ALL_PHASES

    # Determine batches
    batches = config.get("batches", {})
    if args.batch:
        if args.batch not in batches:
            logger.error(f"Batch '{args.batch}' not found in config")
            return
        batches = {args.batch: batches[args.batch]}

    if not batches:
        logger.error("No batches defined in config")
        return

    logger.info(f"Running phases: {phases}")
    logger.info(f"Batches: {list(batches.keys())}")

    db = SessionLocal()
    cursor = None

    # CUSTOMIZE: Connect to source DB for phases that need it.
    needs_source = {"enrich", "pipeline", "fk"}
    if needs_source & set(phases):
        try:
            _, cursor = get_source_connection()
        except NotImplementedError:
            logger.warning(
                "Source DB connection not configured. "
                "Skipping phases that require it."
            )
            phases = [p for p in phases if p not in needs_source]

    try:
        for batch_name, batch_config in batches.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Batch: {batch_name}")
            logger.info(f"{'='*60}")

            for phase_name in phases:
                if phase_name in state.get("phases", {}).get(batch_name, []):
                    logger.info(f"  Phase {phase_name}: already complete (skipping)")
                    continue

                logger.info(f"  Phase {phase_name}: starting...")
                t0 = time.time()

                try:
                    if phase_name == "seed":
                        phase_seed(batch_config, db)
                    elif phase_name == "enrich" and cursor:
                        phase_enrich(batch_config, db, cursor)
                    # CUSTOMIZE: Add phase implementations as needed.
                    # elif phase_name == "pipeline" and cursor:
                    #     phase_pipeline(batch_config, db, cursor)
                    else:
                        logger.info(f"  Phase {phase_name}: not implemented (skipping)")
                        continue

                    elapsed = time.time() - t0
                    logger.info(f"  Phase {phase_name}: done in {elapsed:.1f}s")

                    # Update checkpoint
                    state.setdefault("phases", {}).setdefault(batch_name, []).append(
                        phase_name
                    )
                    save_checkpoint(state)

                except Exception as e:
                    elapsed = time.time() - t0
                    logger.error(f"  Phase {phase_name} failed after {elapsed:.1f}s: {e}")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Data Catalog Pipeline Runner")
    parser.add_argument("--batch", help="Run specific batch only")
    parser.add_argument("--phase", help="Comma-separated phases to run")
    parser.add_argument("--asset", help="Run for specific asset only")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--force-restart", action="store_true", help="Clear checkpoint")
    parser.add_argument("--skip-source", action="store_true",
                        help="Skip phases requiring source DB")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help="Path to config file")
    args = parser.parse_args()

    if args.force_restart and CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")

    run_pipeline(args)


if __name__ == "__main__":
    main()
