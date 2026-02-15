# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
import json
import logging
import re

from tqdm import tqdm

from .core_db import CoreDB
from .core_embedder import CoreEmbedder

# ---------------------------------------------------------------------------
# CUSTOMIZE: Adapt edge types and linking rules for your domain. This example
# creates sent_by, received_by, mention, and semantic_match edges for emails.
# ---------------------------------------------------------------------------

LINK_BATCH_SIZE = 2000
COMMUNITY_MIN_CANDIDATES = 50


def _normalize_name(name):
    """Normalize a name for matching: lowercase, strip, handle 'Last, First' format."""
    if not name:
        return ""
    name = name.strip().lower()
    # Remove titles
    name = re.sub(r"^(dr\.?|mr\.?|mrs\.?|ms\.?)\s+", "", name)
    # Remove trailing credentials
    name = re.sub(r",?\s*(md|phd|np|rn|do|mba|ciso)\.?$", "", name, flags=re.IGNORECASE)
    return name.strip()


def _build_name_to_email_lookup(db):
    """Build a lookup table mapping normalized names to email addresses.

    Uses from_name/from_email pairs from document headers to create mappings.
    Returns dict: normalized_name -> email_address
    """
    rows = db.query(f"""
        SELECT DISTINCT from_name, from_email
        FROM {db.table("raw_documents")}
        WHERE from_name IS NOT NULL AND from_name != ''
          AND from_email IS NOT NULL AND from_email LIKE '%@%'
    """)

    name_to_email = {}

    for from_name, from_email in rows:
        email = from_email.strip().lower()
        if not email or "@" not in email:
            continue

        # Skip Exchange distinguished names (not real emails)
        if email.startswith("/o="):
            continue

        # Skip noreply/system accounts
        if "noreply" in email or "no-reply" in email:
            continue

        # Skip workflow/automated system emails
        if "workflow.mail" in email or "oraclecloud.com" in email:
            continue

        name_norm = _normalize_name(from_name)
        if not name_norm or len(name_norm) < 3:
            continue

        # Map normalized name to email
        name_to_email[name_norm] = email

        # Also create "First Last" variant if name is "Last, First"
        if ", " in from_name:
            parts = from_name.split(", ", 1)
            if len(parts) == 2:
                last = parts[0].strip()
                first_parts = parts[1].strip().split()
                first = first_parts[0] if first_parts else ""

                if first and last:
                    # "Shah, Himanshu V" -> "himanshu shah"
                    first_last = f"{first} {last}"
                    name_to_email[_normalize_name(first_last)] = email

                    # Common nickname mappings
                    nicknames = {
                        "william": ["will", "bill", "billy"],
                        "robert": ["rob", "bob", "bobby"],
                        "richard": ["rick", "dick", "rich"],
                        "michael": ["mike", "mick"],
                        "james": ["jim", "jimmy"],
                        "melissa": ["missy", "mel"],
                        "himanshu": ["him"],
                        "samuel": ["sam"],
                        "kimberly": ["kim"],
                        "jennifer": ["jen", "jenny"],
                        "elizabeth": ["liz", "beth", "betty"],
                        "katherine": ["kate", "kathy", "katie"],
                        "patricia": ["pat", "patty"],
                        "christopher": ["chris"],
                        "nicholas": ["nick"],
                        "jonathan": ["jon", "john"],
                        "matthew": ["matt"],
                        "daniel": ["dan", "danny"],
                        "benjamin": ["ben"],
                        "alexander": ["alex"],
                        "joseph": ["joe"],
                        "anthony": ["tony"],
                        "andrew": ["andy", "drew"],
                        "thomas": ["tom", "tommy"],
                        "steven": ["steve"],
                        "leeanne": ["lee"],
                    }

                    first_lower = first.lower()
                    for full_name, nicks in nicknames.items():
                        if first_lower == full_name:
                            for nick in nicks:
                                name_to_email[_normalize_name(f"{nick} {last}")] = email
                        elif first_lower in nicks:
                            name_to_email[_normalize_name(f"{full_name} {last}")] = email

    return name_to_email


def _resolve_person_to_email(name, name_to_email):
    """Try to resolve a person name to their email address.

    Returns email if found, None otherwise.
    """
    if not name:
        return None

    name_norm = _normalize_name(name)
    if not name_norm:
        return None

    # Direct lookup
    if name_norm in name_to_email:
        return name_to_email[name_norm]

    # Try without middle initial: "John A Smith" -> "John Smith"
    words = name_norm.split()
    if len(words) >= 2:
        # Remove single-letter middle initials (but keep first and last)
        first = words[0]
        last = words[-1]
        simplified = f"{first} {last}"
        if simplified in name_to_email:
            return name_to_email[simplified]

        # Try removing periods: "j." -> ""
        words_no_periods = [w.rstrip(".") for w in words if len(w.rstrip(".")) > 1]
        if len(words_no_periods) >= 2:
            simplified2 = " ".join(words_no_periods)
            if simplified2 in name_to_email:
                return name_to_email[simplified2]

    return None


def _get_community_candidates(db, source_node_ids, min_candidates=COMMUNITY_MIN_CANDIDATES):
    """Get Email node_ids in the same or adjacent communities as source nodes.

    Returns a list of candidate node_ids, or None if too few candidates
    (caller should fall back to full cross-join).
    """
    if not source_node_ids:
        return None

    placeholders = ",".join(["?" for _ in source_node_ids])

    # Get communities of source nodes
    rows = db.query(
        f"SELECT DISTINCT community_id FROM {db.table('graph_nodes')} WHERE node_id IN ({placeholders}) AND community_id IS NOT NULL AND community_id != -1",
        list(source_node_ids),
    )
    if not rows:
        return None

    community_ids = [r[0] for r in rows]
    comm_placeholders = ",".join(["?" for _ in community_ids])

    # Find adjacent communities via edges
    adjacent = db.query(
        f"""
        SELECT DISTINCT g2.community_id
        FROM {db.table("semantic_edges")} e
        JOIN {db.table("graph_nodes")} g1 ON e.source_id = g1.node_id
        JOIN {db.table("graph_nodes")} g2 ON e.target_id = g2.node_id
        WHERE g1.community_id IN ({comm_placeholders})
          AND g2.community_id IS NOT NULL AND g2.community_id != -1
    """,
        community_ids,
    )

    all_communities = set(community_ids)
    for r in adjacent:
        all_communities.add(r[0])

    all_comm_placeholders = ",".join(["?" for _ in all_communities])

    # Get all Email nodes in those communities
    candidates = db.query(
        f"SELECT node_id FROM {db.table('graph_nodes')} WHERE node_type = 'Email' AND community_id IN ({all_comm_placeholders})",
        list(all_communities),
    )

    candidate_ids = [r[0] for r in candidates]
    if len(candidate_ids) < min_candidates:
        return None

    return candidate_ids


def run(db=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - pipe_05 - %(levelname)s - %(message)s")
    own_db = db is None
    if own_db:
        db = CoreDB()
    embedder = CoreEmbedder()

    # 0. Identity Anchor: Create Nodes & Edges from Metadata (Sender)
    logging.info("Creating Identity Anchors (Sender Metadata)...")

    # Fetch headers from raw_documents
    senders = db.query(f"""
        SELECT document_id, from_name, from_email, subject, to_emails, cc_emails
        FROM {db.table("raw_documents")}
        WHERE processed_status IN ('verified', 'vectorized', 'decomposed')
    """)

    batch_size = 1000

    # Track which nodes already exist to avoid re-embedding
    existing_node_ids = set(row[0] for row in db.query(f"SELECT node_id FROM {db.table('graph_nodes')}"))

    # --- Pass 1: Collect unique (node_id -> text) pairs that need embedding ---
    logging.info("Pass 1: Collecting unique nodes to embed...")
    unique_texts = {}  # node_id -> (node_type, name, embed_text)

    for mid, name, email, subject, to_emails, cc_emails in senders:
        if not email:
            continue

        # Email node
        if mid not in existing_node_ids and mid not in unique_texts:
            subj_text = subject if subject else "No Subject"
            unique_texts[mid] = ("Email", f"Email: {subj_text[:50]}", subj_text)

        # Sender Person node
        clean_from = email.strip().lower()
        hub_id = f"Person:{clean_from}"
        if hub_id not in existing_node_ids and hub_id not in unique_texts:
            unique_texts[hub_id] = ("Person", clean_from, clean_from)

        # Sender Alias node
        display_name = name.strip() if name else ""
        if display_name and display_name.lower() != clean_from:
            alias_id = f"Alias:{display_name.lower()}"
            if alias_id not in existing_node_ids and alias_id not in unique_texts:
                unique_texts[alias_id] = ("Alias", display_name, display_name)

        # Recipient Person nodes
        recipients = []
        if to_emails:
            recipients.extend(to_emails.split(";"))
        if cc_emails:
            recipients.extend(cc_emails.split(";"))

        for rec in recipients:
            clean_rec = rec.strip().lower()
            if not clean_rec or "@" not in clean_rec:
                continue
            rec_hub_id = f"Person:{clean_rec}"
            if rec_hub_id not in existing_node_ids and rec_hub_id not in unique_texts:
                unique_texts[rec_hub_id] = ("Person", clean_rec, clean_rec)

    # --- Pass 2: Batch embed all unique texts ---
    logging.info(f"Pass 2: Batch embedding {len(unique_texts)} unique nodes...")
    node_ids_list = list(unique_texts.keys())
    texts_to_embed = [unique_texts[nid][2] for nid in node_ids_list]

    all_vecs = embedder.embed_batch(texts_to_embed)
    all_bits = embedder.quantize_1bit_batch(all_vecs)
    all_ubigints = embedder.quantize_ubigint_batch(all_vecs)

    # Build lookup: node_id -> (bit_string, ubigints, popcnt)
    bits_lookup = {}
    for nid, bit_str, (ubigs, popcnt) in zip(node_ids_list, all_bits, all_ubigints, strict=True):
        bits_lookup[nid] = (bit_str, ubigs, popcnt)

    # --- Pass 3: Build node rows and edge rows ---
    logging.info("Pass 3: Building nodes and edges...")
    sender_nodes = []
    sender_edges = []

    def _make_node(nid, info, lookup_entry):
        """Build an 11-element node tuple from lookup entry (bit_str, ubigints, popcnt)."""
        bit_str, ubigs, popcnt = lookup_entry
        return (nid, info[0], info[1], bit_str, *ubigs, popcnt)

    for mid, name, email, _subject, to_emails, cc_emails in tqdm(senders, desc="Graph Linking"):
        if not email:
            continue

        # Email node
        if mid in bits_lookup:
            info = unique_texts[mid]
            sender_nodes.append(_make_node(mid, info, bits_lookup.pop(mid)))

        # Sender Person
        clean_from = email.strip().lower()
        hub_id = f"Person:{clean_from}"
        if hub_id in bits_lookup:
            info = unique_texts[hub_id]
            sender_nodes.append(_make_node(hub_id, info, bits_lookup.pop(hub_id)))
        sender_edges.append((mid, hub_id, "sent_by", 1.0))

        # Sender Alias
        display_name = name.strip() if name else ""
        if display_name and display_name.lower() != clean_from:
            alias_id = f"Alias:{display_name.lower()}"
            if alias_id in bits_lookup:
                info = unique_texts[alias_id]
                sender_nodes.append(_make_node(alias_id, info, bits_lookup.pop(alias_id)))
            sender_edges.append((hub_id, alias_id, "has_alias", 1.0))

        # Recipients
        recipients = []
        if to_emails:
            recipients.extend(to_emails.split(";"))
        if cc_emails:
            recipients.extend(cc_emails.split(";"))

        for rec in recipients:
            clean_rec = rec.strip().lower()
            if not clean_rec or "@" not in clean_rec:
                continue
            rec_hub_id = f"Person:{clean_rec}"
            if rec_hub_id in bits_lookup:
                info = unique_texts[rec_hub_id]
                sender_nodes.append(_make_node(rec_hub_id, info, bits_lookup.pop(rec_hub_id)))
            sender_edges.append((mid, rec_hub_id, "received_by", 0.8))

        # Batch Insert
        if len(sender_nodes) >= batch_size:
            db.conn.executemany(
                f"INSERT OR IGNORE INTO {db.table('graph_nodes')} (node_id, node_type, name, embedding_bit,"
                f" bit_u0, bit_u1, bit_u2, bit_u3, bit_u4, bit_u5, bit_popcnt)"
                f" VALUES (?, ?, ?, cast(? as BIT), ?, ?, ?, ?, ?, ?, ?)",
                sender_nodes,
            )
            db.conn.executemany(f"INSERT OR IGNORE INTO {db.table('semantic_edges')} (source_id, target_id, edge_type, weight) VALUES (?, ?, ?, ?)", sender_edges)
            sender_nodes, sender_edges = [], []

    # Final Batch
    if sender_nodes:
        db.conn.executemany(
            f"""
            INSERT OR IGNORE INTO {db.table("graph_nodes")}
                (node_id, node_type, name, embedding_bit,
                 bit_u0, bit_u1, bit_u2, bit_u3, bit_u4, bit_u5, bit_popcnt)
            VALUES (?, ?, ?, cast(? as BIT), ?, ?, ?, ?, ?, ?, ?)
        """,
            sender_nodes,
        )

    if sender_edges:
        db.conn.executemany(
            f"""
            INSERT OR IGNORE INTO {db.table("semantic_edges")} (source_id, target_id, edge_type, weight)
            VALUES (?, ?, ?, ?)
        """,
            sender_edges,
        )

    # 1. Create Hard Links (Email -> Entity Mentions) with Name Resolution
    logging.info("Building name-to-email lookup for Person resolution...")
    name_to_email = _build_name_to_email_lookup(db)
    logging.info(f"Built lookup with {len(name_to_email)} name->email mappings")

    logging.info("Creating Hard Links (Email mentions Entity)...")

    records = db.query(f"SELECT document_id, json_ld FROM {db.table('knowledge_graphs')}")

    edges = []
    alias_edges = []  # Person:email -> Alias:name edges
    resolved_count = 0
    unresolved_count = 0

    for mid, json_str in tqdm(records, desc="Mention Links"):
        try:
            data = json.loads(json_str)
            entities = data.get("entities", [])

            for ent in entities:
                name = ent.get("name")
                etype = ent.get("type", "Entity")
                if not name:
                    continue

                # For Person entities, try to resolve name to email
                if etype == "Person":
                    resolved_email = _resolve_person_to_email(name, name_to_email)
                    if resolved_email:
                        # Use Person:{email} as canonical node
                        target_id = f"Person:{resolved_email}"
                        edges.append((mid, target_id, "mention", 1.0))

                        # Create has_alias edge from Person:email to Alias:name
                        alias_id = f"Alias:{name.lower().replace(' ', '_')}"
                        alias_edges.append((target_id, alias_id, "has_alias", 1.0))
                        resolved_count += 1
                    else:
                        # Keep original Person:name format if no email found
                        target_id = f"Person:{name.lower().replace(' ', '_')}"
                        edges.append((mid, target_id, "mention", 1.0))
                        unresolved_count += 1
                else:
                    # Non-Person entities: use original format
                    target_id = f"{etype}:{name.lower().replace(' ', '_')}"
                    edges.append((mid, target_id, "mention", 1.0))
        except json.JSONDecodeError:
            continue

    logging.info(f"Person name resolution: {resolved_count} resolved to email, {unresolved_count} unresolved")

    if edges:
        db.conn.executemany(
            f"""
            INSERT OR IGNORE INTO {db.table("semantic_edges")} (source_id, target_id, edge_type, weight)
            VALUES (?, ?, ?, ?)
        """,
            edges,
        )

    if alias_edges:
        db.conn.executemany(
            f"""
            INSERT OR IGNORE INTO {db.table("semantic_edges")} (source_id, target_id, edge_type, weight)
            VALUES (?, ?, ?, ?)
        """,
            alias_edges,
        )

    # 2. Create Semantic Links (Email <-> Email) -- UBIGINT Hamming with popcount pre-filter
    logging.info("Creating Semantic Links (UBIGINT Hamming, batched)...")

    threshold = 30  # 384 bits, < 30 = very similar for MiniLM-L6

    # Get all email node IDs that have UBIGINT columns populated
    email_node_ids = [row[0] for row in db.query(f"SELECT node_id FROM {db.table('graph_nodes')} WHERE node_type = 'Email' AND bit_u0 IS NOT NULL ORDER BY node_id")]
    total_emails = len(email_node_ids)

    # Try community pre-filtering to reduce cross-join size
    community_candidates = _get_community_candidates(db, email_node_ids)
    if community_candidates is not None:
        logging.info(f"Community pre-filter: {len(community_candidates)} candidates (vs {total_emails} total). Using filtered set.")
        target_node_ids = community_candidates
    else:
        logging.info(f"Community pre-filter: not enough candidates, using full set of {total_emails} documents.")
        target_node_ids = email_node_ids

    logging.info(f"Processing {total_emails} document nodes in chunks of {LINK_BATCH_SIZE}...")

    # Process in chunks to limit memory and compute
    for chunk_start in range(0, total_emails, LINK_BATCH_SIZE):
        chunk_end = min(chunk_start + LINK_BATCH_SIZE, total_emails)
        chunk_ids = email_node_ids[chunk_start:chunk_end]

        if not chunk_ids:
            continue

        # Build parameterized IN clause for this chunk
        placeholders = ",".join(["?" for _ in chunk_ids])

        if community_candidates is not None:
            # Compare chunk against community-filtered targets only
            target_placeholders = ",".join(["?" for _ in target_node_ids])
            db.conn.execute(
                f"""
                INSERT OR IGNORE INTO {db.table("semantic_edges")} (source_id, target_id, edge_type, weight)
                SELECT
                    a.node_id,
                    b.node_id,
                    'semantic_match',
                    1.0 - (hamming_u6(a.bit_u0, a.bit_u1, a.bit_u2, a.bit_u3, a.bit_u4, a.bit_u5,
                                      b.bit_u0, b.bit_u1, b.bit_u2, b.bit_u3, b.bit_u4, b.bit_u5) / 384.0) AS weight
                FROM {db.table("graph_nodes")} a, {db.table("graph_nodes")} b
                WHERE a.node_id IN ({placeholders})
                  AND b.node_id IN ({target_placeholders})
                  AND b.node_type = 'Email'
                  AND b.bit_u0 IS NOT NULL
                  AND a.node_id < b.node_id
                  AND abs(a.bit_popcnt::INTEGER - b.bit_popcnt::INTEGER) <= {threshold}
                  AND hamming_u6(a.bit_u0, a.bit_u1, a.bit_u2, a.bit_u3, a.bit_u4, a.bit_u5,
                                 b.bit_u0, b.bit_u1, b.bit_u2, b.bit_u3, b.bit_u4, b.bit_u5) < {threshold}
            """,
                chunk_ids + target_node_ids,
            )
        else:
            # Full cross-join fallback with popcount pre-filter
            db.conn.execute(
                f"""
                INSERT OR IGNORE INTO {db.table("semantic_edges")} (source_id, target_id, edge_type, weight)
                SELECT
                    a.node_id,
                    b.node_id,
                    'semantic_match',
                    1.0 - (hamming_u6(a.bit_u0, a.bit_u1, a.bit_u2, a.bit_u3, a.bit_u4, a.bit_u5,
                                      b.bit_u0, b.bit_u1, b.bit_u2, b.bit_u3, b.bit_u4, b.bit_u5) / 384.0) AS weight
                FROM {db.table("graph_nodes")} a, {db.table("graph_nodes")} b
                WHERE a.node_id IN ({placeholders})
                  AND b.node_type = 'Email'
                  AND b.bit_u0 IS NOT NULL
                  AND a.node_id < b.node_id
                  AND abs(a.bit_popcnt::INTEGER - b.bit_popcnt::INTEGER) <= {threshold}
                  AND hamming_u6(a.bit_u0, a.bit_u1, a.bit_u2, a.bit_u3, a.bit_u4, a.bit_u5,
                                 b.bit_u0, b.bit_u1, b.bit_u2, b.bit_u3, b.bit_u4, b.bit_u5) < {threshold}
            """,
                chunk_ids,
            )

        logging.info(f"  Processed chunk {chunk_start}-{chunk_end} of {total_emails}")

    count = db.query(f"SELECT count(*) FROM {db.table('semantic_edges')} WHERE edge_type='semantic_match'")[0][0]
    logging.info(f"Linking complete. Total semantic edges: {count}")

    if own_db:
        db.close()


if __name__ == "__main__":
    run()
