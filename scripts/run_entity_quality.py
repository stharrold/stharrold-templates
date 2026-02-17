# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Run all entity quality improvements on existing data.

Usage: uv run python scripts/run_entity_quality.py

Stages (in order):
1. Re-strip: applies enhanced content stripping to all documents
2. Backfill normalize: fixes entity types in existing knowledge_graphs
3. Consolidation: merges duplicate entities, creates has_alias edges
4. Co-occurrence: creates related_to/part_of edges between co-occurring entities

Each stage is idempotent — safe to re-run.
"""

import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - entity_quality - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    total_start = time.perf_counter()

    # Stage 1: Re-strip documents with enhanced content detection
    logger.info("=" * 60)
    logger.info("Stage 1: Re-strip documents (enhanced content detection)")
    logger.info("=" * 60)
    from utils.pipe_02b_strip import run as run_strip

    t0 = time.perf_counter()
    run_strip(force=True)
    logger.info("Strip complete in %.1fs", time.perf_counter() - t0)

    # Stage 2: Normalize entity types in existing knowledge_graphs
    logger.info("=" * 60)
    logger.info("Stage 2: Backfill entity type normalization")
    logger.info("=" * 60)
    import scripts.backfill_normalize_entities as backfill

    t0 = time.perf_counter()
    backfill.run()
    logger.info("Backfill complete in %.1fs", time.perf_counter() - t0)

    # Stage 3: Entity consolidation
    logger.info("=" * 60)
    logger.info("Stage 3: Entity consolidation")
    logger.info("=" * 60)
    from utils.pipe_04b_consolidate import run as run_consolidate

    t0 = time.perf_counter()
    result = run_consolidate()
    logger.info("Consolidation complete in %.1fs: %s", time.perf_counter() - t0, result)

    # Stage 4: Co-occurrence edges
    logger.info("=" * 60)
    logger.info("Stage 4: Co-occurrence edges")
    logger.info("=" * 60)
    from utils.pipe_05b_cooccurrence import run as run_cooccurrence

    t0 = time.perf_counter()
    result = run_cooccurrence()
    logger.info("Co-occurrence complete in %.1fs: %s", time.perf_counter() - t0, result)

    total_elapsed = time.perf_counter() - total_start
    logger.info("=" * 60)
    logger.info("All entity quality improvements complete in %.1fs", total_elapsed)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
