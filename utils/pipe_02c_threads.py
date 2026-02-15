# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Pipeline stage 02c: Thread analysis and position tagging.

Identifies document threads using conversation_id and marks each document's position:
- 'first': Thread starter (always process)
- 'last': Most recent in thread (always process)
- 'middle': Between first and last (skip LLM, link only)
- 'standalone': Not part of a thread (always process)

Also creates thread edges in semantic_edges for graph connectivity.
"""

import logging

from .core_db import CoreDB

# ---------------------------------------------------------------------------
# CUSTOMIZE: Adapt thread/relationship analysis for your domain. This example
# detects email conversation threads and reply chains.
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


def ensure_columns_exist(db: CoreDB):
    """Add thread-related columns if they don't exist."""
    # thread_position: first, middle, last, standalone
    try:
        db.query(f"SELECT thread_position FROM {db.table('raw_documents')} LIMIT 1")
    except Exception:
        logger.info(f"Adding thread_position column to {db.table('raw_documents')}...")
        db.conn.execute(f"ALTER TABLE {db.table('raw_documents')} ADD COLUMN thread_position VARCHAR")

    # thread_size: number of documents in this thread
    try:
        db.query(f"SELECT thread_size FROM {db.table('raw_documents')} LIMIT 1")
    except Exception:
        logger.info(f"Adding thread_size column to {db.table('raw_documents')}...")
        db.conn.execute(f"ALTER TABLE {db.table('raw_documents')} ADD COLUMN thread_size INTEGER")


def analyze_threads(db: CoreDB) -> dict:
    """Analyze all threads and return position mappings.

    Returns:
        dict mapping document_id -> {position, thread_size, prev_document_id}
    """
    # Get all documents grouped by conversation, ordered by time
    rows = db.query(f"""
        SELECT conversation_id, document_id, received_time_utc
        FROM {db.table("raw_documents")}
        WHERE conversation_id IS NOT NULL
        ORDER BY conversation_id, received_time_utc
    """)

    if not rows:
        return {}

    # Group by conversation
    threads = {}
    for conv_id, doc_id, recv_time in rows:
        if conv_id not in threads:
            threads[conv_id] = []
        threads[conv_id].append((doc_id, recv_time))

    # Determine positions
    positions = {}
    for _conv_id, documents in threads.items():
        thread_size = len(documents)

        if thread_size == 1:
            # Single document thread = standalone
            doc_id = documents[0][0]
            positions[doc_id] = {
                "position": "standalone",
                "thread_size": 1,
                "prev_document_id": None,
            }
        else:
            # Multi-document thread
            for i, (doc_id, _) in enumerate(documents):
                if i == 0:
                    position = "first"
                    prev_id = None
                elif i == thread_size - 1:
                    position = "last"
                    prev_id = documents[i - 1][0]
                else:
                    position = "middle"
                    prev_id = documents[i - 1][0]

                positions[doc_id] = {
                    "position": position,
                    "thread_size": thread_size,
                    "prev_document_id": prev_id,
                }

    return positions


def update_thread_positions(db: CoreDB, positions: dict, batch_size: int = 5000):
    """Update raw_documents with thread position info."""
    updates = [(p["position"], p["thread_size"], mid) for mid, p in positions.items()]

    # Batch update
    for start in range(0, len(updates), batch_size):
        batch = updates[start : start + batch_size]
        db.conn.executemany(f"UPDATE {db.table('raw_documents')} SET thread_position = ?, thread_size = ? WHERE document_id = ?", batch)

    logger.info(f"Updated thread positions for {len(updates)} documents")


def create_thread_edges(db: CoreDB, positions: dict, batch_size: int = 5000):
    """Create reply_to edges between documents in threads.

    Edge: child_document --reply_to--> parent_document
    """
    edges = []
    for doc_id, info in positions.items():
        prev_id = info.get("prev_document_id")
        if prev_id:
            # Edge from this document to the one it replies to
            edges.append((doc_id, prev_id, "reply_to", 1.0))

    if not edges:
        logger.info("No thread edges to create")
        return 0

    # Insert edges (skip duplicates)
    inserted = 0
    for start in range(0, len(edges), batch_size):
        batch = edges[start : start + batch_size]
        for source_id, target_id, edge_type, weight in batch:
            try:
                db.conn.execute(
                    f"""
                    INSERT INTO {db.table("semantic_edges")} (source_id, target_id, edge_type, weight)
                    SELECT ?, ?, ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM {db.table("semantic_edges")}
                        WHERE source_id = ? AND target_id = ? AND edge_type = ?
                    )
                """,
                    (source_id, target_id, edge_type, weight, source_id, target_id, edge_type),
                )
                inserted += 1
            except Exception:
                pass  # Skip duplicates

    logger.info(f"Created {inserted} reply_to edges")
    return inserted


def get_skippable_documents(db: CoreDB) -> set:
    """Get document_ids of documents that should skip LLM processing.

    Middle documents in threads are skipped - their content is captured
    in the quoted text of later documents (which we strip anyway).
    """
    rows = db.query(f"""
        SELECT document_id FROM {db.table("raw_documents")}
        WHERE thread_position = 'middle'
    """)
    return {r[0] for r in rows} if rows else set()


def get_thread_stats(db: CoreDB) -> dict:
    """Get statistics about thread processing."""
    stats = db.query(f"""
        SELECT
            thread_position,
            COUNT(*) as cnt
        FROM {db.table("raw_documents")}
        WHERE thread_position IS NOT NULL
        GROUP BY thread_position
    """)

    return {r[0]: r[1] for r in stats} if stats else {}


def run(force: bool = False, db: CoreDB = None):
    """Analyze threads and update positions.

    Args:
        force: If True, reanalyze all documents even if already tagged
        db: Optional CoreDB instance (creates default if None)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - pipe_02c - %(levelname)s - %(message)s",
    )

    if db is None:
        db = CoreDB()
    ensure_columns_exist(db)

    # Check if already processed
    if not force:
        existing = db.query(f"SELECT COUNT(*) FROM {db.table('raw_documents')} WHERE thread_position IS NOT NULL")
        if existing and existing[0][0] > 0:
            logger.info(f"Thread positions already set for {existing[0][0]} documents. Use --force to reprocess.")
            stats = get_thread_stats(db)
            for pos, cnt in stats.items():
                logger.info(f"  {pos}: {cnt}")
            return

    logger.info("Analyzing document threads...")
    positions = analyze_threads(db)

    if not positions:
        logger.info("No threaded documents found.")
        return

    logger.info(f"Found {len(positions)} documents in threads")

    # Count positions
    pos_counts = {}
    for info in positions.values():
        pos = info["position"]
        pos_counts[pos] = pos_counts.get(pos, 0) + 1

    for pos, cnt in sorted(pos_counts.items()):
        logger.info(f"  {pos}: {cnt}")

    logger.info("Updating thread positions...")
    update_thread_positions(db, positions)

    logger.info("Creating thread edges...")
    create_thread_edges(db, positions)

    # Summary
    skippable = pos_counts.get("middle", 0)
    total = len(positions)
    logger.info(f"Thread analysis complete. {skippable}/{total} documents ({skippable / total * 100:.1f}%) can skip LLM.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze document threads")
    parser.add_argument("--force", action="store_true", help="Reanalyze all documents")
    args = parser.parse_args()

    run(force=args.force)
