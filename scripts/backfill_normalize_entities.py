# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Backfill: normalize entity types in existing knowledge_graphs rows."""

import json
import logging

from utils.core_db import CoreDB
from utils.pipe_03b_normalize import normalize_entities

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


def run():
    db = CoreDB()
    total = db.query("SELECT COUNT(*) FROM knowledge_graphs")[0][0]
    logger.info("Normalizing entities in %d knowledge_graph rows...", total)

    updated = 0
    offset = 0

    while offset < total:
        rows = db.query(
            "SELECT message_id, json_ld FROM knowledge_graphs ORDER BY message_id LIMIT ? OFFSET ?",
            [BATCH_SIZE, offset],
        )
        if not rows:
            break

        updates = []
        for mid, json_str in rows:
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                continue

            old_entities = data.get("entities", [])
            new_entities = normalize_entities(old_entities)

            if len(old_entities) != len(new_entities) or any(
                o.get("type") != n.get("type")
                for o, n in zip(old_entities, new_entities)
            ):
                data["entities"] = new_entities
                updates.append((json.dumps(data), mid))

        if updates:
            db.conn.executemany(
                "UPDATE knowledge_graphs SET json_ld = ? WHERE message_id = ?",
                updates,
            )
            updated += len(updates)

        offset += BATCH_SIZE
        if offset % 10000 == 0:
            logger.info("  Progress: %d/%d (%d updated)", offset, total, updated)

    logger.info("Done. Updated %d/%d rows.", updated, total)
    db.close()


if __name__ == "__main__":
    run()
