# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Pipeline stage 05b: Entity co-occurrence edges.

Creates related_to/part_of edges between Topic/Project/Organization entities
that frequently co-occur in the same documents.
"""

import logging
from collections import Counter, defaultdict

from .core_db import CoreDB

logger = logging.getLogger(__name__)

MIN_COOCCURRENCE = 3
ASYMMETRY_RATIO = 5.0


def compute_cooccurrences(mentions: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
    """Compute entity pair co-occurrence counts from (doc_id, entity_id) pairs."""
    doc_entities = defaultdict(set)
    for doc_id, entity_id in mentions:
        doc_entities[doc_id].add(entity_id)

    pair_counts = Counter()
    for _doc_id, entities in doc_entities.items():
        entities_list = sorted(entities)
        for i in range(len(entities_list)):
            for j in range(i + 1, len(entities_list)):
                pair_counts[(entities_list[i], entities_list[j])] += 1

    return dict(pair_counts)


def classify_edge(count_ab: int, total_a: int, total_b: int) -> str | None:
    """Classify a co-occurrence as related_to, part_of, or None.

    Args:
        count_ab: Number of documents where both entities co-occur.
        total_a: Total documents mentioning entity A.
        total_b: Total documents mentioning entity B.

    Returns:
        "related_to" for symmetric co-occurrence, "part_of" when entity B
        appears far more broadly than entity A, or None if below threshold.
    """
    if count_ab < MIN_COOCCURRENCE:
        return None

    if total_b > total_a * ASYMMETRY_RATIO:
        return "part_of"

    return "related_to"


def run(db: CoreDB = None):
    """Create co-occurrence edges between Topic/Project/Organization entities."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - pipe_05b - %(levelname)s - %(message)s",
    )

    own_db = db is None
    if own_db:
        db = CoreDB()

    rows = db.query(f"""
        SELECT e.source_id, e.target_id
        FROM {db.table("semantic_edges")} e
        JOIN {db.table("graph_nodes")} g ON e.target_id = g.node_id
        WHERE e.edge_type = 'mention'
          AND g.node_type IN ('Topic', 'Project', 'Organization')
    """)

    logger.info("Loaded %d mention edges.", len(rows))

    if not rows:
        logger.info("No mention edges found. Skipping.")
        if own_db:
            db.close()
        return

    mentions = [(source_id, target_id) for source_id, target_id in rows]

    pair_counts = compute_cooccurrences(mentions)
    logger.info("Computed %d entity pairs.", len(pair_counts))

    entity_totals = Counter()
    doc_entities = defaultdict(set)
    for doc_id, entity_id in mentions:
        doc_entities[doc_id].add(entity_id)
    for _doc_id, entities in doc_entities.items():
        for ent in entities:
            entity_totals[ent] += 1

    edges = []
    for (entity_a, entity_b), count in pair_counts.items():
        total_a = entity_totals[entity_a]
        total_b = entity_totals[entity_b]

        edge_type = classify_edge(count, total_a, total_b)
        if edge_type is None:
            continue

        weight = min(count / 10.0, 1.0)
        edges.append((entity_a, entity_b, edge_type, weight))

    logger.info(
        "Creating %d co-occurrence edges (threshold >= %d).",
        len(edges),
        MIN_COOCCURRENCE,
    )

    if edges:
        db.conn.executemany(
            f"INSERT OR IGNORE INTO {db.table('semantic_edges')}"
            " (source_id, target_id, edge_type, weight) VALUES (?, ?, ?, ?)",
            edges,
        )

    logger.info("Co-occurrence edge creation complete.")

    if own_db:
        db.close()

    return {"pairs_computed": len(pair_counts), "edges_created": len(edges)}


if __name__ == "__main__":
    run()
