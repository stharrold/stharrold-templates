import json
import logging

from tqdm import tqdm

from .core_db import CoreDB
from .core_embedder import CoreEmbedder


def run(db=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - pipe_04 - %(levelname)s - %(message)s")
    own_db = db is None
    if own_db:
        db = CoreDB()
    embedder = CoreEmbedder()

    # 1. Vectorize Documents (Content)
    # Get verified documents that are in knowledge_graphs but not in graph_nodes
    logging.info("Vectorizing Documents...")
    docs = db.query(f"""
        SELECT r.document_id, r.title, k.json_ld
        FROM {db.table("raw_documents")} r
        JOIN {db.table("knowledge_graphs")} k ON r.document_id = k.document_id
        LEFT JOIN {db.table("graph_nodes")} n ON n.node_id = r.document_id
        WHERE r.processed_status IN ('verified', 'decomposed') AND n.node_id IS NULL
    """)

    nodes_to_insert = []

    for did, title, json_str in tqdm(docs, desc="Documents"):
        data = json.loads(json_str)
        summary = data.get("summary", title)

        # Embed
        vec = embedder.embed(summary)
        bits = embedder.quantize_1bit(vec)
        ubigints, popcnt = embedder.quantize_ubigint(vec)

        nodes_to_insert.append((did, "Document", "Document: " + title[:50], bits, *ubigints, popcnt))

        # 2. Vectorize Entities (Extracted)
        entities = data.get("entities", [])
        for ent in entities:
            name = ent.get("name")
            etype = ent.get("type", "Entity")

            if not name:
                continue

            node_id = f"{etype}:{name.lower().replace(' ', '_')}"

            # Check if we already processed this node in this batch to avoid dupes
            # (In production we'd check DB, but INSERT OR IGNORE handles it)

            # Embed Entity Name (Context-free embedding)
            ent_vec = embedder.embed(name)
            ent_bits = embedder.quantize_1bit(ent_vec)
            ent_ubigints, ent_popcnt = embedder.quantize_ubigint(ent_vec)

            nodes_to_insert.append((node_id, etype, name, ent_bits, *ent_ubigints, ent_popcnt))

    if nodes_to_insert:
        logging.info(f"Inserting {len(nodes_to_insert)} nodes...")
        # Use INSERT OR IGNORE for Entities to handle duplicates
        db.conn.executemany(
            f"""
            INSERT OR IGNORE INTO {db.table("graph_nodes")}
                (node_id, node_type, name, embedding_bit,
                 bit_u0, bit_u1, bit_u2, bit_u3, bit_u4, bit_u5, bit_popcnt)
            VALUES (?, ?, ?, cast(? as BIT), ?, ?, ?, ?, ?, ?, ?)
        """,
            nodes_to_insert,
        )

        # Update raw_documents status
        db.conn.execute(
            f"UPDATE {db.table('raw_documents')} SET processed_status='vectorized' WHERE document_id IN ({','.join(['?'] * len(docs))})", [e[0] for e in docs]
        )

    logging.info("Vectorization complete.")
    if own_db:
        db.close()


if __name__ == "__main__":
    run()
