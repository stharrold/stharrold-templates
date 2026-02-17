#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Generate LLM business descriptions for columns, embed as vectors.

This is a skip-on-update file -- customize for your LLM integration.

CUSTOMIZE: Update prompts, LLM model choice, and domain mappings.

Orchestrates 4 phases:
  populate  - Sync columns from Asset.schema_metadata into search index
  prepare   - Build per-asset prompt files for LLM agents
  import    - Import agent-generated descriptions into search index
  embed     - Embed descriptions via ONNX, store in column_vectors

Usage:
    python scripts/generate_column_descriptions.py --phase populate
    python scripts/generate_column_descriptions.py --phase prepare
    python scripts/generate_column_descriptions.py --phase import
    python scripts/generate_column_descriptions.py --phase embed [--batch-size 64]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from data_catalog.db.connection import SessionLocal
from data_catalog.services.column_descriptions import (
    phase_embed,
    phase_import_descriptions,
    phase_populate,
    phase_prepare,
)

# CUSTOMIZE: Map your schema names to business domains.
SCHEMA_DOMAINS = {
    "dbo": "Core",
    "staging": "Staging",
    "reporting": "Reporting",
}


def main():
    parser = argparse.ArgumentParser(
        description="Column Description Pipeline"
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["populate", "prepare", "import", "embed"],
        help="Pipeline phase to execute",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for embedding phase",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.phase == "populate":
            count = phase_populate(db)
            logger.info(f"Populated {count} columns")

        elif args.phase == "prepare":
            count = phase_prepare(db)
            logger.info(f"Generated {count} prompt files")

        elif args.phase == "import":
            count = phase_import_descriptions(db)
            logger.info(f"Imported {count} descriptions")

        elif args.phase == "embed":
            count = phase_embed(db, batch_size=args.batch_size)
            logger.info(f"Embedded {count} descriptions")

    finally:
        db.close()


if __name__ == "__main__":
    main()
