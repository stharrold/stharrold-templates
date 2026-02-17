# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""DuckDB maintenance: stats, vacuum, and integrity checks for document graph."""

import argparse
import logging
import os

from .core_db import CoreDB

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def show_stats(db):
    """Display row counts and file size."""
    tables = [
        "raw_documents",
        "attachments",
        "knowledge_graphs",
        "graph_nodes",
        "semantic_edges",
        "query_cache",
        "pipeline_logs",
    ]
    logger.info("=== Database Statistics ===")
    for table in tables:
        try:
            count = db.conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            logger.info("  %-20s %d rows", table, count)
        except Exception:
            logger.info("  %-20s (table not found)", table)

    db_path = db.db_path
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        logger.info("  File size: %.1f MB", size_mb)

    # Vector coverage
    try:
        total_nodes = db.conn.execute("SELECT count(*) FROM graph_nodes").fetchone()[0]
        vectorized = db.conn.execute("SELECT count(*) FROM graph_nodes WHERE embedding_bit IS NOT NULL").fetchone()[0]
        if total_nodes > 0:
            logger.info(
                "  Vector coverage: %d/%d (%.1f%%)",
                vectorized,
                total_nodes,
                100 * vectorized / total_nodes,
            )
    except Exception:
        pass


def run_vacuum(db):
    """Run CHECKPOINT + VACUUM to reclaim space."""
    logger.info("Running CHECKPOINT...")
    try:
        db.conn.execute("CHECKPOINT")
    except Exception as e:
        logger.warning("CHECKPOINT failed: %s", e)

    logger.info("Running VACUUM...")
    try:
        db.conn.execute("VACUUM")
    except Exception as e:
        logger.warning("VACUUM failed: %s", e)

    logger.info("Maintenance complete.")


def check_integrity(db):
    """Check for orphaned nodes, missing vectors, dangling edges, and unlinked documents."""
    logger.info("=== Integrity Check ===")
    issues = 0

    # 1. Nodes with name but no embedding vector
    try:
        missing_vectors = db.conn.execute("""
            SELECT count(*) FROM graph_nodes
            WHERE name IS NOT NULL AND embedding_bit IS NULL
        """).fetchone()[0]
        if missing_vectors:
            logger.warning("Nodes with name but no vector: %d", missing_vectors)
            issues += 1
        else:
            logger.info("  All named nodes have vectors.")
    except Exception as e:
        logger.warning("  Vector check failed: %s", e)

    # 2. Dangling edges (source not found)
    try:
        dangling_source = db.conn.execute("""
            SELECT count(*) FROM semantic_edges e
            LEFT JOIN graph_nodes n ON e.source_id = n.node_id
            WHERE n.node_id IS NULL
        """).fetchone()[0]
        if dangling_source:
            logger.warning("Dangling edges (source not found): %d", dangling_source)
            issues += 1
        else:
            logger.info("  No dangling source edges.")
    except Exception as e:
        logger.warning("  Source edge check failed: %s", e)

    # 3. Dangling edges (target not found)
    try:
        dangling_target = db.conn.execute("""
            SELECT count(*) FROM semantic_edges e
            LEFT JOIN graph_nodes n ON e.target_id = n.node_id
            WHERE n.node_id IS NULL
        """).fetchone()[0]
        if dangling_target:
            logger.warning("Dangling edges (target not found): %d", dangling_target)
            issues += 1
        else:
            logger.info("  No dangling target edges.")
    except Exception as e:
        logger.warning("  Target edge check failed: %s", e)

    # 4. Raw documents without knowledge graph entries
    try:
        unlinked = db.conn.execute("""
            SELECT count(*) FROM raw_documents r
            LEFT JOIN knowledge_graphs k ON r.document_id = k.document_id
            WHERE k.document_id IS NULL
        """).fetchone()[0]
        if unlinked:
            logger.warning("Raw documents without graph nodes: %d", unlinked)
            issues += 1
        else:
            logger.info("  All documents have graph entries.")
    except Exception as e:
        logger.warning("  Document linkage check failed: %s", e)

    if issues == 0:
        logger.info("All integrity checks passed.")
    else:
        logger.warning("%d issue(s) found.", issues)


def list_backups():
    """List available backups with sizes."""
    backup_base = "backups"
    if not os.path.isdir(backup_base):
        logger.info("No backups directory found at %s", backup_base)
        return
    dirs = sorted(
        [d for d in os.listdir(backup_base) if d.startswith("backup_")],
        reverse=True,
    )
    if not dirs:
        logger.info("No backups found.")
        return
    logger.info("=== Available Backups ===")
    for d in dirs:
        full_path = os.path.join(backup_base, d)
        total_size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(full_path) for f in files)
        logger.info("  %-50s %.1f MB", d, total_size / (1024 * 1024))


def main():
    parser = argparse.ArgumentParser(description="DuckDB maintenance utilities for document graph.")
    parser.add_argument("--stats", action="store_true", help="Show row counts and file size")
    parser.add_argument("--vacuum", action="store_true", help="Run CHECKPOINT + VACUUM")
    parser.add_argument("--check-integrity", action="store_true", help="Check for data issues")
    parser.add_argument("--list-backups", action="store_true", help="List available backups")
    args = parser.parse_args()

    if not any([args.stats, args.vacuum, args.check_integrity, args.list_backups]):
        parser.print_help()
        return

    db = CoreDB()

    if args.stats:
        show_stats(db)
    if args.list_backups:
        list_backups()
    if args.vacuum:
        run_vacuum(db)
    if args.check_integrity:
        check_integrity(db)

    db.close()


if __name__ == "__main__":
    main()
