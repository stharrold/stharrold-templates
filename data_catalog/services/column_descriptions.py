# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Column description pipeline for LLM-generated business descriptions.

Provides 4-phase workflow for generating and embedding column descriptions:
  1. populate  - Sync columns from asset metadata into search index
  2. prepare   - Build per-asset prompt files for LLM agents
  3. import_descriptions - Import generated descriptions into search index
  4. embed     - Embed descriptions as semantic_description vectors

Each phase is idempotent and checkpoint-resumable. The LLM generation
step (between prepare and import) is intentionally external -- users
configure their own LLM integration.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from data_catalog.db.models import (
    Asset,
    ColumnValueFrequency,
    ColumnVector,
    SearchIndexColumn,
)

logger = logging.getLogger(__name__)

# CUSTOMIZE: Adjust paths for your project layout.
DEFAULT_PROMPTS_DIR = Path("data/output/column_prompts")
DEFAULT_DESCRIPTIONS_DIR = Path("data/output/column_descriptions")
DEFAULT_CHECKPOINT_PATH = Path("data/output/col_description_checkpoint.json")


def load_checkpoint(path: Path = DEFAULT_CHECKPOINT_PATH) -> dict:
    """Load or initialize the description checkpoint."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"populated": [], "described": [], "embedded": []}


def save_checkpoint(
    checkpoint: dict, path: Path = DEFAULT_CHECKPOINT_PATH
) -> None:
    """Persist checkpoint to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)


def phase_populate(db: Session) -> int:
    """Phase 1: Sync columns from Asset.schema_metadata into SearchIndexColumn.

    Creates one SearchIndexColumn row per column per asset, preserving
    existing entries (upsert by table_schema + table_name + column_name).

    Returns:
        Number of columns synced.
    """
    assets = db.query(Asset).all()
    synced = 0

    for asset in assets:
        columns = (asset.schema_metadata or {}).get("columns", [])
        if not columns:
            continue

        for col in columns:
            existing = (
                db.query(SearchIndexColumn)
                .filter(
                    SearchIndexColumn.table_schema == asset.table_schema,
                    SearchIndexColumn.table_name == asset.table_name,
                    SearchIndexColumn.column_name == col["name"],
                )
                .first()
            )
            if existing:
                continue

            entry = SearchIndexColumn(
                id=str(uuid4()),
                table_schema=asset.table_schema,
                table_name=asset.table_name,
                column_name=col["name"],
                data_type=col.get("data_type", col.get("type", "unknown")),
                ordinal_position=col.get("ordinal_position", 0),
            )
            db.add(entry)
            synced += 1

    db.commit()
    logger.info(f"Populated {synced} search index columns")
    return synced


def phase_prepare(
    db: Session,
    prompts_dir: Path = DEFAULT_PROMPTS_DIR,
    checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH,
) -> int:
    """Phase 2: Build per-asset prompt files for LLM description.

    Each prompt file contains the asset name, column list, sample values
    (from value frequencies), and instructions for generating business
    descriptions.

    Returns:
        Number of prompt files generated.
    """
    checkpoint = load_checkpoint(checkpoint_path)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    assets = db.query(Asset).all()
    generated = 0

    for asset in assets:
        # Build filename stem
        stem = f"{asset.table_schema}_{asset.table_name}"
        if stem in checkpoint.get("described", []):
            continue

        columns = (asset.schema_metadata or {}).get("columns", [])
        if not columns:
            continue

        # Build prompt content
        lines = [
            f"# Column Descriptions for {asset.qualified_name}",
            "",
            "Generate a concise business description for each column.",
            "Return JSON: {\"column_name\": \"description\", ...}",
            "",
            "## Columns",
            "",
        ]

        for col in columns:
            col_name = col["name"]
            data_type = col.get("data_type", col.get("type", "unknown"))
            lines.append(f"### {col_name} ({data_type})")

            # Add sample values from frequencies
            freqs = (
                db.query(ColumnValueFrequency)
                .filter(
                    ColumnValueFrequency.table_schema == asset.table_schema,
                    ColumnValueFrequency.table_name == asset.table_name,
                    ColumnValueFrequency.column_name == col_name,
                )
                .order_by(ColumnValueFrequency.rank)
                .limit(5)
                .all()
            )
            if freqs:
                samples = [f.value for f in freqs if f.value is not None]
                if samples:
                    lines.append(f"Sample values: {', '.join(samples[:5])}")
            lines.append("")

        prompt_path = prompts_dir / f"{stem}.md"
        prompt_path.write_text("\n".join(lines))
        generated += 1

    logger.info(f"Generated {generated} prompt files in {prompts_dir}")
    return generated


def phase_import_descriptions(
    db: Session,
    descriptions_dir: Path = DEFAULT_DESCRIPTIONS_DIR,
    checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH,
) -> int:
    """Phase 3: Import LLM-generated descriptions into SearchIndexColumn.

    Reads JSON files from descriptions_dir, updates SearchIndexColumn.description.

    Returns:
        Number of columns updated.
    """
    if not descriptions_dir.exists():
        logger.warning(f"Descriptions directory not found: {descriptions_dir}")
        return 0

    checkpoint = load_checkpoint(checkpoint_path)
    updated = 0

    for desc_file in sorted(descriptions_dir.glob("*.json")):
        stem = desc_file.stem
        if stem in checkpoint.get("described", []):
            continue

        with open(desc_file) as f:
            descriptions = json.load(f)

        # Parse schema and table from filename (Schema_Table format)
        parts = stem.rsplit("_", 1)
        if len(parts) != 2:
            logger.warning(f"Cannot parse filename: {desc_file.name}")
            continue

        table_schema, table_name = parts

        for col_name, description in descriptions.items():
            entry = (
                db.query(SearchIndexColumn)
                .filter(
                    SearchIndexColumn.table_schema == table_schema,
                    SearchIndexColumn.table_name == table_name,
                    SearchIndexColumn.column_name == col_name,
                )
                .first()
            )
            if entry:
                entry.description = description
                updated += 1

        checkpoint.setdefault("described", []).append(stem)
        save_checkpoint(checkpoint, checkpoint_path)

    db.commit()
    logger.info(f"Imported {updated} column descriptions")
    return updated


def phase_embed(
    db: Session,
    batch_size: int = 64,
    checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH,
) -> int:
    """Phase 4: Embed descriptions as semantic_description vectors.

    Uses the EmbeddingService to embed each column's description text,
    storing results in ColumnVector with vector_type='semantic_description'.

    Returns:
        Number of columns embedded.
    """
    from data_catalog.services.embedding import EmbeddingService

    checkpoint = load_checkpoint(checkpoint_path)
    embedding_svc = EmbeddingService()

    # Find columns with descriptions but no semantic_description vector
    columns = (
        db.query(SearchIndexColumn)
        .filter(SearchIndexColumn.description.isnot(None))
        .all()
    )

    embedded = 0
    batch_texts = []
    batch_cols = []

    for col in columns:
        qualified = f"[{col.table_schema}].[{col.table_name}]"
        if qualified in checkpoint.get("embedded", []):
            continue

        # Check if vector already exists
        existing = (
            db.query(ColumnVector)
            .filter(
                ColumnVector.table_schema == col.table_schema,
                ColumnVector.table_name == col.table_name,
                ColumnVector.column_name == col.column_name,
                ColumnVector.vector_type == "semantic_description",
            )
            .first()
        )
        if existing:
            continue

        batch_texts.append(col.description)
        batch_cols.append(col)

        if len(batch_texts) >= batch_size:
            embedded += _embed_batch(db, embedding_svc, batch_texts, batch_cols)
            batch_texts, batch_cols = [], []

    # Final batch
    if batch_texts:
        embedded += _embed_batch(db, embedding_svc, batch_texts, batch_cols)

    db.commit()
    logger.info(f"Embedded {embedded} column descriptions")
    return embedded


def _embed_batch(
    db: Session,
    embedding_svc,
    texts: list[str],
    columns: list,
) -> int:
    """Embed a batch of description texts and store vectors."""
    vectors = embedding_svc.embed(texts)
    binary = embedding_svc.binarize(vectors)

    stored = 0
    for i, col in enumerate(columns):
        vector = ColumnVector(
            id=str(uuid4()),
            table_schema=col.table_schema,
            table_name=col.table_name,
            column_name=col.column_name,
            vector_type="semantic_description",
            value_vector=vectors[i].tolist(),
            binary_vector=binary[i],
        )
        db.add(vector)
        stored += 1

    return stored
