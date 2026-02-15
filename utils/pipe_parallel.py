"""2-phase parallel pipeline: LLM inference with DB released, then brief DB writes.

Architecture:
  Phase 1 (Fetch):   Open DB briefly to query unprocessed documents (~1s)
  Phase 2 (Compute): LLM decompose + ONNX embed, DB connection closed (~30-35 min)
  Phase 3 (Persist): Open DB briefly to batch-write results (~30-60s)

Stages per document (in phase 2):
  03  Decompose  — LLM entity extraction with adaptive chunking
  04  Vectorize  — ONNX embed summary + entities, quantize to 1-bit
  05a Link-local — Build sender/recipient/alias nodes + edges in memory

After DB writes (in phase 3):
  06i Incremental — Approximate PageRank/HITS/community for new nodes
  06m Milestone   — Full optimization at geometric milestones (10, 30, 100, 300, ...)
"""

import json
import logging
import time
from pathlib import Path

from .core_db import CoreDB
from .core_embedder import CoreEmbedder
from .core_llm import LocalLLM
from .pipe_03_decompose import (
    KnowledgeGraphExtraction,
    _content_hash,
    extract_entities_chunked,
)
from .pipe_06_optimize import run_incremental, run_milestone_if_needed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - parallel - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

LOG_DIR = Path(__file__).parent.parent / "logs"


def _setup_file_logger():
    """Add a UTF-8 file handler to the module logger. Returns log file path."""
    LOG_DIR.mkdir(exist_ok=True)
    from datetime import UTC, datetime

    log_path = LOG_DIR / f"pipeline_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.log"
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s - parallel - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(fh)
    return log_path


# Middle documents with body content above this threshold (chars) get full LLM processing.
# Below this threshold, they are trivial replies ("Thanks", "Got it") and skip LLM.
MIDDLE_SUBSTANTIVE_THRESHOLD = 200


def _decompose_document(llm, embedder, did, subject, body, from_name, from_email, to_emails, cc_emails):
    """Run stages 03 → 04 → 05a for a single document. No DB access.

    Returns a result dict with all data needed for _persist_results().
    """
    timings = {}

    # --- Stage 03: Decompose (topic extraction, people from headers) ---
    t0 = time.perf_counter()
    subject = subject or ""
    body = body or ""
    content = f"Subject: {subject}\n\nBody: {body}"
    parsed, chunk_meta = extract_entities_chunked(llm, content, topics_only=True)

    # Fallback: if extraction failed, use subject-as-summary with empty entities.
    # Covers short documents, error-echo documents (LLM interprets document error content
    # as its own error), timeouts, and other non-deterministic LLM failures.
    if "error" in parsed:
        fallback_summary = subject[:200].strip() if subject.strip() else body[:200].strip()
        logger.info("Decompose fallback did=%s err=%s", did[:16], str(parsed["error"])[:40])
        parsed = {"summary": fallback_summary or "(no content)", "entities": []}

    if "error" in parsed:
        timings["03_decompose"] = time.perf_counter() - t0
        return {
            "ok": False,
            "document_id": did,
            "error": f"03: {parsed['error']}",
            "timings": timings,
            "entities": [],
            "chunk_meta": chunk_meta,
        }

    try:
        KnowledgeGraphExtraction(**parsed)
    except Exception as e:
        timings["03_decompose"] = time.perf_counter() - t0
        return {
            "ok": False,
            "document_id": did,
            "error": f"03 validation: {e}",
            "timings": timings,
            "entities": [],
            "chunk_meta": chunk_meta,
        }

    json_str = json.dumps(parsed)
    body_hash = _content_hash(subject, body)
    timings["03_decompose"] = time.perf_counter() - t0

    # --- Stage 04: Vectorize ---
    t0 = time.perf_counter()
    summary = parsed.get("summary", "") or subject or "(no content)"
    vec = embedder.embed(summary)
    bits = embedder.quantize_1bit(vec)
    ubigints, popcnt = embedder.quantize_ubigint(vec)
    doc_node = (did, "Email", f"Email: {(subject or '')[:50]}", bits, *ubigints, popcnt)

    entity_nodes = []
    for ent in parsed.get("entities", []):
        name = ent.get("name")
        etype = ent.get("type", "Entity")
        if not name:
            continue
        node_id = f"{etype}:{name.lower().replace(' ', '_')}"
        ent_vec = embedder.embed(name)
        ent_bits = embedder.quantize_1bit(ent_vec)
        ent_ubigints, ent_popcnt = embedder.quantize_ubigint(ent_vec)
        entity_nodes.append((node_id, etype, name, ent_bits, *ent_ubigints, ent_popcnt))
    timings["04_vectorize"] = time.perf_counter() - t0

    # --- Stage 05a: Link-local (identity anchors + mention edges) ---
    t0 = time.perf_counter()
    extra_nodes = []
    edges = []

    # Sender person node
    if from_email:
        clean_from = from_email.strip().lower()
        hub_id = f"Person:{clean_from}"
        person_vec = embedder.embed(clean_from)
        person_bits = embedder.quantize_1bit(person_vec)
        person_ubigints, person_popcnt = embedder.quantize_ubigint(person_vec)
        extra_nodes.append((hub_id, "Person", clean_from, person_bits, *person_ubigints, person_popcnt))
        edges.append((did, hub_id, "sent_by", 1.0))

        # Alias
        display_name = (from_name or "").strip()
        if display_name and display_name.lower() != clean_from:
            alias_id = f"Alias:{display_name.lower()}"
            alias_vec = embedder.embed(display_name)
            alias_bits = embedder.quantize_1bit(alias_vec)
            alias_ubigints, alias_popcnt = embedder.quantize_ubigint(alias_vec)
            extra_nodes.append((alias_id, "Alias", display_name, alias_bits, *alias_ubigints, alias_popcnt))
            edges.append((hub_id, alias_id, "has_alias", 1.0))

    # Recipient nodes
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
        rec_vec = embedder.embed(clean_rec)
        rec_bits = embedder.quantize_1bit(rec_vec)
        rec_ubigints, rec_popcnt = embedder.quantize_ubigint(rec_vec)
        extra_nodes.append((rec_hub_id, "Person", clean_rec, rec_bits, *rec_ubigints, rec_popcnt))
        edges.append((did, rec_hub_id, "received_by", 0.8))

    # Mention edges (document -> entity)
    for ent in parsed.get("entities", []):
        name = ent.get("name")
        etype = ent.get("type", "Entity")
        if not name:
            continue
        target_id = f"{etype}:{name.lower().replace(' ', '_')}"
        edges.append((did, target_id, "mention", 1.0))

    timings["05a_link_local"] = time.perf_counter() - t0

    all_nodes = [doc_node] + entity_nodes + extra_nodes
    return {
        "ok": True,
        "document_id": did,
        "json_str": json_str,
        "body_hash": body_hash,
        "nodes": all_nodes,
        "edges": edges,
        "timings": timings,
        "entities": parsed.get("entities", []),
        "summary": parsed.get("summary", ""),
        "chunk_meta": chunk_meta,
    }


def _process_middle_document(embedder, did, subject, from_name, from_email, to_emails, cc_emails):
    """Lightweight processing for middle-of-thread documents (no LLM, no DB).

    Returns a result dict ready for _persist_middle_results().
    """
    t0 = time.perf_counter()

    summary = subject or "(no subject)"
    json_str = json.dumps({"summary": summary, "entities": [], "skipped": "middle_of_thread"})

    # Embed just the subject for the Email node
    doc_node_id = f"email:{did}"
    vec = embedder.embed(summary)
    bit_str = embedder.quantize_1bit(vec)
    ubigints, popcnt = embedder.quantize_ubigint(vec)

    all_nodes = [(doc_node_id, "Email", summary[:200], bit_str, *ubigints, popcnt)]

    edges = []

    def add_person(name, email_addr, edge_type):
        if not email_addr:
            return
        person_id = f"person:{email_addr.lower()}"
        all_nodes.append((person_id, "Person", name or email_addr, None, None, None, None, None, None, None, None))
        if edge_type == "sent_by":
            edges.append((doc_node_id, person_id, edge_type, 1.0))
        else:
            edges.append((person_id, doc_node_id, edge_type, 1.0))

    add_person(from_name, from_email, "sent_by")

    for addr in (to_emails or "").split(";"):
        addr = addr.strip()
        if addr:
            add_person(None, addr, "received_by")

    for addr in (cc_emails or "").split(";"):
        addr = addr.strip()
        if addr:
            add_person(None, addr, "cc_to")

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "skipped": True,
        "document_id": did,
        "subject": (subject or "")[:50],
        "json_str": json_str,
        "nodes": all_nodes,
        "edges": edges,
        "timings": {"middle_process": elapsed},
    }


def _persist_results(db, results):
    """Batch-write decomposition results to DB. Returns (succeeded, failed_ids)."""
    succeeded = 0
    failed_ids = []
    all_node_ids = []

    for r in results:
        if not r.get("ok"):
            failed_ids.append(r["document_id"])
            continue

        did = r["document_id"]
        try:
            db.conn.execute(
                "INSERT OR IGNORE INTO knowledge_graphs (document_id, json_ld, body_hash) VALUES (?, ?, ?)",
                (did, r["json_str"], r.get("body_hash")),
            )
            if r["nodes"]:
                db.conn.executemany(
                    "INSERT OR IGNORE INTO graph_nodes (node_id, node_type, name, embedding_bit,"
                    " bit_u0, bit_u1, bit_u2, bit_u3, bit_u4, bit_u5, bit_popcnt)"
                    " VALUES (?, ?, ?, cast(? as BIT), ?, ?, ?, ?, ?, ?, ?)",
                    r["nodes"],
                )
                all_node_ids.extend(n[0] for n in r["nodes"])
            if r["edges"]:
                db.conn.executemany(
                    "INSERT OR IGNORE INTO semantic_edges (source_id, target_id, edge_type, weight) VALUES (?, ?, ?, ?)",
                    r["edges"],
                )
            db.conn.execute(
                "UPDATE raw_documents SET processed_status = 'vectorized' WHERE document_id = ?",
                (did,),
            )
            succeeded += 1
        except Exception as e:
            logger.error("DB write failed for %s: %s", did[:20], e)
            failed_ids.append(did)

    # Incremental optimization for all new nodes in the batch
    if all_node_ids:
        run_incremental(db, all_node_ids)
        run_milestone_if_needed(db)

    return succeeded, failed_ids


def _load_config():
    """Load full pipeline config dict, or empty dict if not found."""
    from pathlib import Path

    config_path = Path(__file__).parent.parent / "config" / "pipeline_config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _fetch_query(threshold):
    """Return the SQL for fetching full-processing documents."""
    return f"""
        SELECT r.document_id, r.subject, COALESCE(r.body_stripped, r.body) AS body, r.from_name, r.from_email, r.to_emails, r.cc_emails
        FROM raw_documents r
        LEFT JOIN knowledge_graphs k ON r.document_id = k.document_id
        WHERE r.processed_status = 'verified'
          AND k.document_id IS NULL
          AND (r.thread_position IS NULL OR r.thread_position != 'middle'
               OR (r.thread_position = 'middle'
                   AND LENGTH(COALESCE(r.body_stripped, r.body, '')) > {threshold}))
        ORDER BY
          (EXISTS (SELECT 1 FROM semantic_edges e WHERE e.target_id = r.document_id AND e.edge_type = 'reply_to')) DESC,
          (LOWER(r.from_email) = 'sharrold@iuhealth.org') DESC,
          (LOWER(r.to_emails) LIKE '%sharrold@iuhealth.org%') DESC,
          (LOWER(r.cc_emails) LIKE '%sharrold@iuhealth.org%') DESC,
          r.received_time_utc DESC NULLS LAST
        LIMIT ?
    """


def _middle_query(threshold):
    """Return the SQL for fetching trivial middle-of-thread documents."""
    return f"""
        SELECT r.document_id, r.subject, r.from_name, r.from_email, r.to_emails, r.cc_emails
        FROM raw_documents r
        LEFT JOIN knowledge_graphs k ON r.document_id = k.document_id
        WHERE r.processed_status = 'verified'
          AND k.document_id IS NULL
          AND r.thread_position = 'middle'
          AND LENGTH(COALESCE(r.body_stripped, r.body, '')) <= {threshold}
        ORDER BY
          (EXISTS (SELECT 1 FROM semantic_edges e WHERE e.target_id = r.document_id AND e.edge_type = 'reply_to')) DESC,
          (LOWER(r.from_email) = 'sharrold@iuhealth.org') DESC,
          (LOWER(r.to_emails) LIKE '%sharrold@iuhealth.org%') DESC,
          (LOWER(r.cc_emails) LIKE '%sharrold@iuhealth.org%') DESC,
          r.received_time_utc DESC NULLS LAST
        LIMIT ?
    """


def run(batch_size=10, workers=1, model=None, bench=False):
    """Process a single batch of documents through the 2-phase pipeline."""
    config = _load_config()
    ollama_cfg = config.get("ollama", {})
    llm_cfg = config.get("llm", {})
    if model is None:
        model = ollama_cfg.get("model", "qwen3:0.6b-q4_K_S")
    num_thread = ollama_cfg.get("num_thread", 0)
    llm_options = {}
    for key in ("num_ctx", "num_predict", "temperature", "top_p", "top_k", "min_p", "repeat_penalty"):
        if key in llm_cfg:
            llm_options[key] = llm_cfg[key]
    llm = LocalLLM(model=model, num_thread=num_thread, llm_options=llm_options)
    if not llm.is_available():
        logger.error("Ollama model '%s' not available.", model)
        return

    embedder = CoreEmbedder()

    # Optional bench logger
    bench_logger = None
    if bench:
        from .bench_log import BenchLogger

        bench_logger = BenchLogger(model_name=model, batch_size=batch_size, workers=workers)

    # Phase 1: Fetch (brief DB open)
    with CoreDB() as db:
        docs = db.query(_fetch_query(MIDDLE_SUBSTANTIVE_THRESHOLD), [batch_size])
        middle_docs = db.query(_middle_query(MIDDLE_SUBSTANTIVE_THRESHOLD), [batch_size])

    if not docs and not middle_docs:
        logger.info("No verified documents pending.")
        return

    # Phase 2: Compute (no DB)
    middle_results = []
    if middle_docs:
        logger.info("Processing %d middle-of-thread documents (no LLM)...", len(middle_docs))
        for did, subject, from_name, from_email, to_emails, cc_emails in middle_docs:
            result = _process_middle_document(embedder, did, subject, from_name, from_email, to_emails, cc_emails)
            middle_results.append(result)

    results = []
    wall_start = time.perf_counter()

    if docs:
        logger.info("Processing %d documents (LLM decompose, DB released)...", len(docs))
        for did, subject, body, from_name, from_email, to_emails, cc_emails in docs:
            result = _decompose_document(llm, embedder, did, subject, body, from_name, from_email, to_emails, cc_emails)
            result["subject"] = (subject or "")[:50]
            results.append(result)

            # Bench logging
            if bench_logger and result.get("ok"):
                chunk_meta = result.get("chunk_meta", {})
                bench_logger.log_document(
                    document_id=did,
                    title=subject,
                    result=result,
                    timings=result.get("timings", {}),
                    chunks_attempted=chunk_meta.get("chunks_attempted", 1),
                    chunks_succeeded=chunk_meta.get("chunks_succeeded", 1),
                    chunk_sizes_used=chunk_meta.get("chunk_sizes_used", []),
                )

    wall_elapsed = time.perf_counter() - wall_start

    # Phase 3: Persist (brief DB open)
    with CoreDB() as db:
        if middle_results:
            _persist_results(db, middle_results)
        if results:
            _persist_results(db, results)

    # --- Report ---
    print(f"\n{'=' * 90}")
    print(f"PARALLEL PIPELINE RESULTS — {len(docs)} documents, wall time: {wall_elapsed:.1f}s")
    print(f"{'=' * 90}")

    print(f"\n{'#':>2}  {'OK':>3}  {'03_decomp':>10}  {'04_vector':>10}  {'05a_link':>10}  Subject")
    print("-" * 80)
    for i, r in enumerate(results, 1):
        t = r.get("timings", {})
        ok = "Y" if r.get("ok") else "N"
        d03 = f"{t.get('03_decompose', 0):.1f}s" if "03_decompose" in t else "—"
        d04 = f"{t.get('04_vectorize', 0):.3f}s" if "04_vectorize" in t else "—"
        d05 = f"{t.get('05a_link_local', 0):.3f}s" if "05a_link_local" in t else "—"
        subj = r.get("subject", "")
        if not r.get("ok"):
            subj = f"[ERR: {r.get('error', '?')[:40]}]"
        print(f"{i:2}  {ok:>3}  {d03:>10}  {d04:>10}  {d05:>10}  {subj}")

    ok_results = [r for r in results if r.get("ok")]
    if ok_results:
        stages = ["03_decompose", "04_vectorize", "05a_link_local"]
        print(f"\n{'STAGE':<20} {'MIN':>8} {'AVG':>8} {'MAX':>8} {'TOTAL':>8}")
        print("-" * 56)
        for stage in stages:
            vals = [r["timings"].get(stage, 0) for r in ok_results]
            print(f"{stage:<20} {min(vals):>7.2f}s {sum(vals) / len(vals):>7.2f}s {max(vals):>7.2f}s {sum(vals):>7.1f}s")

        total_per_doc = [sum(r["timings"].get(s, 0) for s in stages) for r in ok_results]
        print(f"\n{'per-document total':<20} {min(total_per_doc):>7.2f}s {sum(total_per_doc) / len(total_per_doc):>7.2f}s {max(total_per_doc):>7.2f}s")
        total_nodes = sum(r.get("nodes", 0) if isinstance(r.get("nodes"), int) else len(r.get("nodes", [])) for r in ok_results)
        total_edges = sum(r.get("edges", 0) if isinstance(r.get("edges"), int) else len(r.get("edges", [])) for r in ok_results)
        print(f"\nCreated {total_nodes} nodes, {total_edges} edges")

    print(f"\nSuccess: {len(ok_results)}/{len(results)}")
    failed = [r for r in results if not r.get("ok")]
    for r in failed:
        print(f"  FAILED: {r.get('error', '?')}")

    if middle_results:
        middle_ok = [r for r in middle_results if r.get("ok")]
        middle_nodes = sum(len(r.get("nodes", [])) for r in middle_ok)
        middle_edges = sum(len(r.get("edges", [])) for r in middle_ok)
        print(f"\nMiddle documents (skipped LLM): {len(middle_ok)}/{len(middle_results)}")
        print(f"  Created {middle_nodes} nodes, {middle_edges} edges")

    if bench_logger:
        bench_logger.log_summary()
        print(f"\nBench log: {bench_logger.path}")


def run_batches(total_docs=0, batch_size=10, workers=1, model=None):
    """Run multiple batches with 2-phase architecture (LLM with DB released, then brief DB writes).

    Args:
        total_docs: Max documents to process. 0 = auto-detect remaining from DB.

    Logs to pipeline_logs table with task='parallel_batch' for each batch.
    Failed documents can be queried and reprocessed later.
    """
    import datetime

    log_path = _setup_file_logger()

    config = _load_config()
    ollama_cfg = config.get("ollama", {})
    llm_cfg = config.get("llm", {})
    if model is None:
        model = ollama_cfg.get("model", "qwen3:0.6b-q4_K_S")
    num_thread = ollama_cfg.get("num_thread", 0)
    llm_options = {}
    for key in ("num_ctx", "num_predict", "temperature", "top_p", "top_k", "min_p", "repeat_penalty"):
        if key in llm_cfg:
            llm_options[key] = llm_cfg[key]

    # Auto-detect remaining documents if total not specified
    if total_docs <= 0:
        with CoreDB() as db:
            remaining = db.query("""
                SELECT count(*) FROM raw_documents r
                LEFT JOIN knowledge_graphs k ON r.document_id = k.document_id
                WHERE r.processed_status = 'verified' AND k.document_id IS NULL
            """)[0][0]
        total_docs = remaining
        if total_docs == 0:
            logger.info("No unprocessed documents found.")
            return

    num_batches = (total_docs + batch_size - 1) // batch_size
    logger.info("Starting %d batches of %d documents (%d remaining)", num_batches, batch_size, total_docs)
    logger.info("Log file: %s", log_path)

    llm = LocalLLM(model=model, num_thread=num_thread, llm_options=llm_options)
    if not llm.is_available():
        logger.error("Ollama model '%s' not available.", model)
        return

    embedder = CoreEmbedder()

    total_processed = 0
    total_succeeded = 0
    total_failed = 0
    failed_document_ids = []
    start_time = datetime.datetime.now(datetime.UTC)

    for batch_num in range(1, num_batches + 1):
        try:
            batch_start = time.perf_counter()
            logger.info("\n%s", "=" * 70)
            logger.info("BATCH %d/%d", batch_num, num_batches)
            logger.info("=" * 70)

            # === Phase 1: Fetch documents (brief DB open) ===
            with CoreDB() as db:
                # Log batch start
                db.conn.execute(
                    "INSERT OR IGNORE INTO pipeline_logs (document_id, task, status, details) VALUES (?, ?, ?, ?)",
                    (
                        f"batch_{batch_num}",
                        "parallel_batch",
                        "started",
                        json.dumps(
                            {
                                "batch_num": batch_num,
                                "total_batches": num_batches,
                                "batch_size": batch_size,
                                "model": model,
                                "started_at": datetime.datetime.now(datetime.UTC).isoformat(),
                            }
                        ),
                    ),
                )

                docs = db.query(_fetch_query(MIDDLE_SUBSTANTIVE_THRESHOLD), [batch_size])
                middle_docs = db.query(_middle_query(MIDDLE_SUBSTANTIVE_THRESHOLD), [batch_size])

            if not docs and not middle_docs:
                logger.info("No more documents to process. Done.")
                with CoreDB() as db:
                    db.conn.execute(
                        "UPDATE pipeline_logs SET status = ?, details = ? WHERE document_id = ? AND task = ? AND status = 'started'",
                        ("completed", json.dumps({"reason": "no_more_documents"}), f"batch_{batch_num}", "parallel_batch"),
                    )
                break

            # === Phase 2: Compute (no DB connection held) ===

            # Process trivial middle documents (fast, no LLM, no DB)
            middle_results = []
            if middle_docs:
                logger.info("Processing %d middle-of-thread documents (no LLM)...", len(middle_docs))
                for did, subject, from_name, from_email, to_emails, cc_emails in middle_docs:
                    result = _process_middle_document(embedder, did, subject, from_name, from_email, to_emails, cc_emails)
                    middle_results.append(result)

            # Process full documents (LLM decompose, no DB)
            batch_results = []
            if docs:
                logger.info("Processing %d documents (LLM decompose, DB released)...", len(docs))
                for did, subject, body, from_name, from_email, to_emails, cc_emails in docs:
                    try:
                        result = _decompose_document(llm, embedder, did, subject, body, from_name, from_email, to_emails, cc_emails)
                        result["subject"] = (subject or "")[:50]
                    except Exception as e:
                        logger.error("Uncaught error processing %s: %s", did[:20], e, exc_info=True)
                        result = {
                            "ok": False,
                            "document_id": did,
                            "subject": (subject or "")[:50],
                            "error": f"uncaught: {e}",
                            "timings": {},
                            "entities": [],
                            "chunk_meta": {},
                        }
                    batch_results.append(result)

                    # Log progress
                    status_str = "OK" if result.get("ok") else f"ERR: {result.get('error', '?')[:30]}"
                    t03 = result.get("timings", {}).get("03_decompose", 0)
                    logger.info("  %s - %.1fs - %s", result["subject"][:35], t03, status_str)

            # === Phase 3: Persist to DB (brief DB open) ===
            with CoreDB() as db:
                middle_count = 0
                if middle_results:
                    mid_ok, _ = _persist_results(db, middle_results)
                    middle_count = mid_ok

                batch_succeeded = 0
                batch_failed = []
                if batch_results:
                    batch_succeeded, batch_failed = _persist_results(db, batch_results)

                    # Log each document result
                    for r in batch_results:
                        did = r["document_id"]
                        status = "succeeded" if r.get("ok") else "failed"
                        db.conn.execute(
                            "INSERT OR IGNORE INTO pipeline_logs (document_id, task, status, details) VALUES (?, ?, ?, ?)",
                            (
                                did,
                                "parallel_document",
                                status,
                                json.dumps(
                                    {
                                        "batch_num": batch_num,
                                        "subject": r.get("subject", "")[:80],
                                        "error": r.get("error"),
                                        "timings": r.get("timings", {}),
                                        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                                    }
                                ),
                            ),
                        )

                batch_elapsed = time.perf_counter() - batch_start

                # Update batch log
                db.conn.execute(
                    "UPDATE pipeline_logs SET status = ?, details = ? WHERE document_id = ? AND task = ? AND status = 'started'",
                    (
                        "completed",
                        json.dumps(
                            {
                                "batch_num": batch_num,
                                "docs_processed": len(batch_results),
                                "succeeded": batch_succeeded,
                                "failed": len(batch_failed),
                                "middle_processed": middle_count,
                                "elapsed_seconds": round(batch_elapsed, 2),
                                "failed_document_ids": batch_failed[:10],
                                "completed_at": datetime.datetime.now(datetime.UTC).isoformat(),
                            }
                        ),
                        f"batch_{batch_num}",
                        "parallel_batch",
                    ),
                )

            total_processed += len(batch_results) + middle_count
            total_succeeded += batch_succeeded + middle_count
            total_failed += len(batch_failed)
            failed_document_ids.extend(batch_failed)

            logger.info("Batch %d: %d/%d succeeded, %d middle, %.1fs", batch_num, batch_succeeded, len(batch_results), middle_count, batch_elapsed)
            logger.info("Running total: %d/%d succeeded, %d failed", total_succeeded, total_processed, total_failed)

            if total_processed >= total_docs:
                logger.info("Reached target of %d documents.", total_docs)
                break

        except Exception as e:
            logger.error("BATCH %d FAILED with uncaught error: %s", batch_num, e, exc_info=True)
            logger.info("Continuing to next batch...")
            continue

    # Final summary
    end_time = datetime.datetime.now(datetime.UTC)
    duration = (end_time - start_time).total_seconds()

    logger.info("\n%s", "=" * 70)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 70)
    logger.info("Total processed: %d", total_processed)
    logger.info("Succeeded: %d", total_succeeded)
    logger.info("Failed: %d", total_failed)
    logger.info("Duration: %.1fs (%.1f min)", duration, duration / 60)
    if duration > 0:
        logger.info("Rate: %.1f documents/min", total_processed / duration * 60)

    if failed_document_ids:
        logger.info("\nFailed document_ids logged to pipeline_logs (task='parallel_document', status='failed')")
        logger.info("Query: SELECT document_id, details FROM pipeline_logs WHERE task='parallel_document' AND status='failed'")

    return {
        "total_processed": total_processed,
        "succeeded": total_succeeded,
        "failed": total_failed,
        "duration_seconds": duration,
        "failed_document_ids": failed_document_ids,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="2-phase parallel pipeline (LLM with DB released).")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--model", default=None, help="LLM model (default: from config)")
    parser.add_argument("--bench", action="store_true", help="Enable JSONL bench logging for model comparison")
    parser.add_argument("--total", type=int, default=0, help="Total documents to process (0=auto-detect remaining)")
    parser.add_argument("--single-batch", action="store_true", help="Run a single batch only (for testing)")
    args = parser.parse_args()

    if args.single_batch:
        run(batch_size=args.batch_size, workers=args.workers, model=args.model, bench=args.bench)
    else:
        run_batches(total_docs=args.total, batch_size=args.batch_size, workers=args.workers, model=args.model)
