# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Incremental pipeline: import new documents, verify, and process.

Designed to run periodically via Task Scheduler after an external export
writes new documents into the source database.

Three phases, all idempotent:
  1. Import  --Source DB -> DuckDB (skip existing document_ids)
  2. Verify  --pipe_02.run_all() on status='new' documents
  3. Process --pipe_parallel.run_batches(batch_size=25) on verified documents
"""

import datetime
import logging
import sys
import time
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import pipe_02_verify
from utils.core_db import CoreDB
from utils.pipe_parallel import run_batches


def main():
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"incremental_{timestamp}.log"

    # DEBUG to file, INFO to stdout
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[stream_handler, file_handler],
    )
    logger = logging.getLogger("incremental")
    run_start = time.perf_counter()
    logger.info("=== Incremental Pipeline Start ===")
    logger.debug("Log file: %s", log_path)

    # --- Phase 1: Import from source database ---
    logger.info("--- Phase 1: Import (source DB -> DuckDB) ---")
    t0 = time.perf_counter()
    with CoreDB() as db:
        before = db.query("SELECT count(*) FROM raw_documents")[0][0]
        logger.debug("raw_documents before import: %d", before)
        # TODO: implement import method for your source database
        # db.migrate_from_source()
        after = db.query("SELECT count(*) FROM raw_documents")[0][0]
    new_imported = after - before
    logger.info("Imported %d new documents (%d -> %d total) [%.1fs]", new_imported, before, after, time.perf_counter() - t0)

    # --- Phase 2: Verify + Strip + Threads ---
    logger.info("--- Phase 2: Verify + Strip + Threads ---")
    t0 = time.perf_counter()
    with CoreDB() as db:
        new_count = db.query("SELECT count(*) FROM raw_documents WHERE processed_status = 'new'")[0][0]
    if new_count == 0:
        logger.info("No new documents to verify. Skipping Phase 2.")
    else:
        logger.info("Verifying %d new documents...", new_count)
        pipe_02_verify.run_all()
        logger.info("Phase 2 complete [%.1fs]", time.perf_counter() - t0)

    # --- Phase 3: Process (LLM decompose + vectorize + link + optimize) ---
    logger.info("--- Phase 3: Process (parallel pipeline) ---")
    t0 = time.perf_counter()
    with CoreDB() as db:
        remaining = db.query("""
            SELECT count(*) FROM raw_documents r
            LEFT JOIN knowledge_graphs k ON r.document_id = k.document_id
            WHERE r.processed_status = 'verified' AND k.document_id IS NULL
        """)[0][0]
    if remaining == 0:
        logger.info("No verified documents to process. Done.")
        logger.info("=== Incremental Pipeline Complete (nothing to do) [%.1fs] ===", time.perf_counter() - run_start)
        return

    logger.info("%d verified documents to process...", remaining)
    run_batches(batch_size=25)
    logger.info("Phase 3 complete [%.1fs]", time.perf_counter() - t0)

    logger.info("=== Incremental Pipeline Complete [%.1fs total] ===", time.perf_counter() - run_start)


if __name__ == "__main__":
    main()
