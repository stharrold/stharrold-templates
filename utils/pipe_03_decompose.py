# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pydantic import BaseModel
from tqdm import tqdm

from .core_db import CoreDB
from .core_llm import LocalLLM
from .json_repair import repair_and_clean

# ---------------------------------------------------------------------------
# CUSTOMIZE: Adapt entity types and LLM extraction prompts for your domain.
# This example extracts Person, Organization, Project, Topic entities from
# emails.
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# --- Pydantic Schema for Structured Output ---


class Entity(BaseModel):
    name: str
    type: str  # Person, Project, Organization, Topic, Date
    confidence: float = 0.5


class KnowledgeGraphExtraction(BaseModel):
    summary: str
    entities: list[Entity]


# --- Configuration ---
DEFAULT_BATCH_SIZE = 100
MAX_CONSECUTIVE_ERRORS = 10
MAX_WORKERS = 4
BATCH_EMAIL_LIMIT = 3  # Max documents per LLM call
BATCH_CHAR_LIMIT = 4000  # Max combined chars for batched documents
SINGLE_EMAIL_THRESHOLD = 0  # All documents go individually (CPU inference too slow for batches)

SYSTEM_PROMPT = """You extract structured entities from document text to build a knowledge graph.
Return ONLY valid JSON matching this schema, no markdown fences, no explanation:
{"summary": "string", "entities": [{"name": "string", "type": "Person|Project|Organization|Topic|Date", "confidence": 0.0-1.0}]}"""

# Few-shot prompt with explicit summary guidance (v2)
FEWSHOT_PROMPT_TEMPLATE = """Summarize this document and extract entities. Return JSON only.

Summary rules:
- 1-2 sentences describing the key information
- Include WHO is involved, WHAT happened or is requested, and any KEY DETAILS (ticket numbers, dates, systems)
- Do NOT just repeat the subject line

Entity types: Person, Organization, Project, Topic, Date

Example:
Email: "Subject: Server outage\\n\\nBody: Hi team, the PRPDW database is down. DBA team and Microsoft support are investigating. All EDW databases are affected."
Output: {{"summary": "PRPDW database is inaccessible, affecting all EDW databases. DBA team and Microsoft support are investigating.", "entities": [
{{"name": "PRPDW", "type": "Project", "confidence": 0.9}},
{{"name": "EDW", "type": "Project", "confidence": 0.85}},
{{"name": "Microsoft", "type": "Organization", "confidence": 0.9}},
{{"name": "DBA team", "type": "Organization", "confidence": 0.8}}]}}

Now extract from this document:
Email: "{email_text}"
Output:"""

# Simplified prompt: topics only (people extracted from headers)
TOPIC_PROMPT_TEMPLATE = """Summarize this document and list topics.

Example document: "Meeting about Q1 budget with finance team on Tuesday"
Example output: {{"summary": "Budget meeting scheduled", "topics": ["budget", "finance"]}}

Email: {email_text}
Output:"""

BATCH_SYSTEM_PROMPT = """You extract structured entities from multiple documents to build a knowledge graph.
Each document is delimited by [EMAIL id]...[/EMAIL id] tags.
Return ONLY valid JSON matching this schema, no markdown fences, no explanation:
{"results": {"<document_id>": {"summary": "string", "entities": [{"name": "string", "type": "Person|Project|Organization|Topic|Date", "confidence": 0.0-1.0}]}}}
Include a result entry for EVERY document id provided."""


# --- Adaptive Chunking ---

# Default tier definitions: (max_words, overlap_words, timeout_seconds)
# Overridden by config/pipeline_config.json chunking.tiers if present
_DEFAULT_CHUNK_TIERS = [
    (300, 100, 90),  # First tier: 300-word chunks, 100-word overlap
    (100, 30, 60),  # Fallback: smaller chunks if first tier fails
    (30, 10, 45),  # Last resort: very small chunks
]


def chunk_text(text, max_words=100, overlap_words=10):
    """Split text into word-based chunks with overlap. Returns [text] if already fits."""
    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunks.append(" ".join(words[start:end]))
        start = end - overlap_words
        if start >= len(words):
            break
    return chunks


def merge_entity_results(chunk_results):
    """Merge extractions across chunks. Dedup entities by (name.lower(), type), keep highest confidence."""
    seen = {}  # (name_lower, type) -> entity dict
    summary = ""

    for result in chunk_results:
        if not result or "error" in result:
            continue

        # Use first chunk's summary
        if not summary and result.get("summary"):
            summary = result["summary"]

        for ent in result.get("entities", []):
            name = ent.get("name", "")
            etype = ent.get("type", "Entity")
            key = (name.lower(), etype)
            existing = seen.get(key)
            if existing is None or ent.get("confidence", 0) > existing.get("confidence", 0):
                seen[key] = ent

    return {
        "summary": summary,
        "entities": list(seen.values()),
    }


def extract_topics_simple(llm, text, timeout=120):
    """Simple topic extraction without chunking. Fast path for small models.

    Returns (result_dict, chunk_meta) compatible with extract_entities_chunked.
    Topics are converted to entities with type='Topic'.
    """
    chunk_meta = {
        "chunks_attempted": 1,
        "chunks_succeeded": 0,
        "chunk_sizes_used": [0],
        "repairs": [],
        "raw_response": None,
    }

    # Truncate text to avoid timeout
    truncated = text[:1500]
    user_msg = TOPIC_PROMPT_TEMPLATE.format(email_text=truncated)
    if "qwen3" in llm.model.lower():
        user_msg = "/no_think " + user_msg

    t0 = time.perf_counter()
    parsed = llm.generate_json(user_msg, system_prompt="", timeout=timeout)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    chunk_meta["llm_calls"] = [{"tier": "topics", "words": len(truncated.split()), "elapsed_ms": round(elapsed_ms), "ollama": dict(llm.last_meta)}]

    # If JSON parsing failed, try repair
    if "error" in parsed and "raw" in parsed:
        raw = parsed["raw"]
        chunk_meta["raw_response"] = raw
        repaired, repairs = repair_and_clean(raw)
        if repaired:
            logger.info(f"JSON repaired: {repairs}")
            chunk_meta["repairs"] = repairs
            parsed = repaired
        else:
            # Repair failed, return original error
            return ({"entities": [], "summary": "", "error": parsed["error"]}, chunk_meta)
    elif "error" in parsed:
        return ({"entities": [], "summary": "", "error": parsed["error"]}, chunk_meta)

    # Clean any successfully parsed JSON too (remove empty nodes, nested entity fields)
    parsed = repair_and_clean(json.dumps(parsed))[0] or parsed

    # Convert topics list to entities format
    summary = parsed.get("summary", "")
    topics = parsed.get("topics", [])
    entities = [{"name": t, "type": "Topic", "confidence": 0.8} for t in topics if t]

    chunk_meta["chunks_succeeded"] = 1
    return ({"summary": summary, "entities": entities}, chunk_meta)


def extract_entities_chunked(llm, text, use_fewshot=True, topics_only=False, chunk_tiers=None):
    """Adaptive chunking extraction with automatic retry at smaller chunk sizes.

    Args:
        llm: LocalLLM instance
        text: Document text to extract from
        use_fewshot: If True, use few-shot prompt (better for small models like 0.5b)
        topics_only: If True, use fast topic-only extraction (people from headers)
        chunk_tiers: List of (max_words, overlap_words, timeout_seconds) tuples.
                     Falls back to _DEFAULT_CHUNK_TIERS if None.

    Returns (result_dict, chunk_meta) where chunk_meta has:
        chunks_attempted, chunks_succeeded, chunk_sizes_used, repairs
    """
    # Fast path: topic-only extraction
    if topics_only:
        return extract_topics_simple(llm, text)

    tiers = chunk_tiers if chunk_tiers is not None else _DEFAULT_CHUNK_TIERS

    chunk_meta = {
        "chunks_attempted": 0,
        "chunks_succeeded": 0,
        "chunk_sizes_used": [],
        "repairs": [],
        "llm_calls": [],
    }

    all_chunk_results = []
    pending_texts = [text]

    for max_words, overlap, timeout in tiers:
        if not pending_texts:
            break

        next_pending = []
        for t in pending_texts:
            chunks = chunk_text(t, max_words=max_words, overlap_words=overlap)
            for chunk in chunks:
                chunk_meta["chunks_attempted"] += 1
                chunk_meta["chunk_sizes_used"].append(max_words)

                chunk_words = len(chunk.split())
                t0 = time.perf_counter()

                if use_fewshot:
                    # Few-shot prompt in user message, no system prompt
                    user_msg = FEWSHOT_PROMPT_TEMPLATE.format(email_text=chunk[:2000])
                    # Disable thinking for Qwen3 models
                    if "qwen3" in llm.model.lower():
                        user_msg = "/no_think " + user_msg
                    parsed = llm.generate_json(user_msg, system_prompt="", timeout=timeout)
                else:
                    user_msg = f"Document Text:\n{chunk}"
                    parsed = llm.generate_json(user_msg, system_prompt=SYSTEM_PROMPT, timeout=timeout)

                elapsed_ms = (time.perf_counter() - t0) * 1000
                call_info = {
                    "tier": max_words,
                    "words": chunk_words,
                    "elapsed_ms": round(elapsed_ms),
                    "ollama": dict(llm.last_meta),
                }

                # Try JSON repair if parsing failed
                if "error" in parsed and "raw" in parsed:
                    repaired, repairs = repair_and_clean(parsed["raw"])
                    if repaired:
                        logger.info(f"JSON repaired: {repairs}")
                        chunk_meta["repairs"].extend(repairs)
                        parsed = repaired

                if "error" in parsed:
                    logger.debug("Chunk failed at tier %d words: %s", max_words, parsed["error"])
                    call_info["status"] = "fail"
                    call_info["error"] = parsed["error"][:80]
                    next_pending.append(chunk)
                else:
                    # Clean the parsed result (remove empty nodes, nested entity fields)
                    cleaned, clean_repairs = repair_and_clean(json.dumps(parsed))
                    if cleaned:
                        parsed = cleaned
                        if clean_repairs:
                            chunk_meta["repairs"].extend(clean_repairs)

                    try:
                        KnowledgeGraphExtraction(**parsed)
                        all_chunk_results.append(parsed)
                        chunk_meta["chunks_succeeded"] += 1
                        call_info["status"] = "ok"
                    except Exception:
                        call_info["status"] = "validation_fail"
                        next_pending.append(chunk)

                chunk_meta["llm_calls"].append(call_info)

        pending_texts = next_pending

    if not all_chunk_results:
        return (
            {"entities": [], "error": "all chunks failed"},
            chunk_meta,
        )

    merged = merge_entity_results(all_chunk_results)
    return merged, chunk_meta


def _content_hash(subject, body):
    """SHA-256 hash of subject + body for deduplication."""
    text = f"{subject or ''}\n{body or ''}"
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _call_llm(llm, user_msg, system_prompt, timeout=300):
    """Call local LLM via Ollama and return parsed JSON or error dict."""
    return llm.generate_json(user_msg, system_prompt=system_prompt, timeout=timeout)


def extract_entities(llm, text):
    """Extract Knowledge Graph entities for a single document."""
    user_msg = f"Document Text:\n{text[:8000]}"
    parsed = _call_llm(llm, user_msg, SYSTEM_PROMPT)

    if "error" in parsed:
        return {"entities": [], "error": parsed["error"]}

    try:
        KnowledgeGraphExtraction(**parsed)
    except Exception as e:
        return {"entities": [], "error": f"Validation: {e}"}

    return parsed


def extract_entities_batch(llm, items):
    """Extract entities for multiple documents in a single LLM call.

    Args:
        llm: LocalLLM instance.
        items: List of (document_id, subject, body) tuples.

    Returns:
        dict mapping document_id -> extraction result (or error dict).
    """
    # Build batched prompt
    parts = []
    for mid, subject, body in items:
        content = f"Subject: {subject}\n\nBody: {body}"[:4000]
        parts.append(f"[EMAIL {mid}]\n{content}\n[/EMAIL {mid}]")

    user_msg = "\n\n".join(parts)
    parsed = _call_llm(llm, user_msg, BATCH_SYSTEM_PROMPT, timeout=300)

    if "error" in parsed:
        return {mid: {"entities": [], "error": parsed["error"]} for mid, _, _ in items}

    # Extract per-document results
    results_map = parsed.get("results", {})
    output = {}
    for mid, _, _ in items:
        if mid in results_map:
            try:
                KnowledgeGraphExtraction(**results_map[mid])
                output[mid] = results_map[mid]
            except Exception as e:
                output[mid] = {"entities": [], "error": f"Validation: {e}"}
        else:
            output[mid] = {"entities": [], "error": "Missing from batch response"}

    return output


def _process_one(llm, mid, subject, body, chunk_tiers=None):
    """Worker: extract entities for a single document. Returns (mid, result, profile)."""
    content = f"Subject: {subject}\n\nBody: {body}"
    word_count = len(content.split())

    t0 = time.perf_counter()
    result, chunk_meta = extract_entities_chunked(llm, content, chunk_tiers=chunk_tiers)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Fallback for very short documents: if all chunks failed and body is short,
    # produce a valid empty extraction rather than an error. Short one-liner
    # replies ("Agree", "Thanks") have no meaningful entities to extract.
    if "error" in result and len((body or "").split()) < 50:
        logger.info(
            "Short document fallback mid=%s words=%d (body too short for reliable LLM extraction)",
            mid[:16],
            word_count,
        )
        result = {"summary": (body or "")[:200].strip(), "entities": []}

    entity_count = len(result.get("entities", []))
    status = "ok" if "error" not in result else result["error"][:40]

    # Aggregate Ollama token stats across all LLM calls
    total_prompt_tokens = sum(c.get("ollama", {}).get("prompt_eval_count", 0) for c in chunk_meta.get("llm_calls", []))
    total_eval_tokens = sum(c.get("ollama", {}).get("eval_count", 0) for c in chunk_meta.get("llm_calls", []))
    total_ollama_ms = sum(c.get("ollama", {}).get("total_duration_ms", 0) for c in chunk_meta.get("llm_calls", []))
    tokens_per_sec = total_eval_tokens / (total_ollama_ms / 1000) if total_ollama_ms > 0 else 0

    profile = {
        "document_id": mid[:20],
        "words": word_count,
        "elapsed_ms": round(elapsed_ms),
        "status": status,
        "entities": entity_count,
        "chunks_attempted": chunk_meta.get("chunks_attempted", 0),
        "chunks_succeeded": chunk_meta.get("chunks_succeeded", 0),
        "prompt_tokens": total_prompt_tokens,
        "eval_tokens": total_eval_tokens,
        "ollama_ms": round(total_ollama_ms),
        "tokens_per_sec": round(tokens_per_sec, 1),
        "llm_calls": chunk_meta.get("llm_calls", []),
    }

    logger.info(
        "PROFILE mid=%s words=%d elapsed=%dms chunks=%d/%d entities=%d prompt_tok=%d eval_tok=%d ollama=%dms tok/s=%.1f status=%s",
        mid[:16],
        word_count,
        round(elapsed_ms),
        chunk_meta.get("chunks_succeeded", 0),
        chunk_meta.get("chunks_attempted", 0),
        entity_count,
        total_prompt_tokens,
        total_eval_tokens,
        round(total_ollama_ms),
        tokens_per_sec,
        status,
    )

    return mid, result, profile


def _process_batch(llm, items):
    """Worker: extract entities for a batch of documents. Returns list of (mid, result)."""
    results = extract_entities_batch(llm, items)
    return [(mid, results.get(mid, {"entities": [], "error": "batch miss"})) for mid, _, _ in items]


def _group_for_batching(documents):
    """Group documents into batches for efficient LLM calls.

    Short documents are grouped together (up to BATCH_EMAIL_LIMIT or BATCH_CHAR_LIMIT).
    Long documents go individually.

    Returns:
        List of work items, each either:
        - ("single", (mid, subject, body))
        - ("batch", [(mid, subject, body), ...])
    """
    work = []
    current_batch = []
    current_chars = 0

    for mid, subject, body in documents:
        content_len = len(subject or "") + len(body or "")

        # Long documents go individually
        if content_len > SINGLE_EMAIL_THRESHOLD:
            if current_batch:
                work.append(("batch", list(current_batch)))
                current_batch = []
                current_chars = 0
            work.append(("single", (mid, subject, body)))
            continue

        # Would this exceed batch limits?
        if current_batch and (len(current_batch) >= BATCH_EMAIL_LIMIT or current_chars + content_len > BATCH_CHAR_LIMIT):
            work.append(("batch", list(current_batch)))
            current_batch = []
            current_chars = 0

        current_batch.append((mid, subject, body))
        current_chars += content_len

    if current_batch:
        work.append(("batch", list(current_batch)))

    return work


def _load_config():
    """Load full pipeline config dict, or empty dict if not found."""
    config_path = Path(__file__).parent.parent / "config" / "pipeline_config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _parse_chunk_tiers(config):
    """Parse chunking.tiers from config into list of (max_words, overlap, timeout) tuples."""
    tiers_cfg = config.get("chunking", {}).get("tiers", [])
    if not tiers_cfg:
        return None
    try:
        return [(t["max_words"], t["overlap_words"], t["timeout_seconds"]) for t in tiers_cfg]
    except (KeyError, TypeError):
        logger.warning("Invalid chunking.tiers in config, using defaults")
        return None


def run(batch_size=DEFAULT_BATCH_SIZE, workers=MAX_WORKERS, model=None, db=None, num_thread=0):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - pipe_03 - %(levelname)s - %(message)s")

    # Load settings from config if not explicitly passed
    config = _load_config()
    ollama_cfg = config.get("ollama", {})
    llm_cfg = config.get("llm", {})
    if model is None:
        model = ollama_cfg.get("model", "qwen3:0.6b-q4_K_S")
    if num_thread == 0:
        num_thread = ollama_cfg.get("num_thread", 0)

    # Build LLM options from config (temperature, top_p, top_k, etc.)
    llm_options = {}
    for key in ("num_ctx", "num_predict", "temperature", "top_p", "top_k", "min_p", "repeat_penalty"):
        if key in llm_cfg:
            llm_options[key] = llm_cfg[key]

    chunk_tiers = _parse_chunk_tiers(config)
    if chunk_tiers:
        tier_desc = [(t[0], t[1], t[2]) for t in chunk_tiers]
        logging.info(f"Chunk tiers from config: {tier_desc}")

    llm = LocalLLM(model=model, num_thread=num_thread, llm_options=llm_options)
    if num_thread > 0:
        logging.info(f"Using num_thread={num_thread}")
    if not llm.is_available():
        logging.error(f"Ollama model '{model}' not available. Run: ollama pull {model}")
        return
    own_db = db is None
    if own_db:
        db = CoreDB()

    documents = db.query(
        f"""
        SELECT r.document_id, r.subject, COALESCE(r.body_stripped, r.body) AS body
        FROM {db.table("raw_documents")} r
        LEFT JOIN {db.table("knowledge_graphs")} k ON r.document_id = k.document_id
        WHERE r.processed_status = 'verified'
          AND k.document_id IS NULL
          AND (r.thread_position IS NULL OR r.thread_position != 'middle')
        LIMIT ?
    """,
        [batch_size],
    )

    if not documents:
        logging.info("No verified documents pending decomposition.")
        if own_db:
            db.close()
        return

    logging.info(f"Decomposing {len(documents)} documents ({workers} workers)...")

    # --- Phase 1: Content-hash deduplication ---
    existing_hashes = {}
    hash_rows = db.query(f"SELECT body_hash, json_ld FROM {db.table('knowledge_graphs')} WHERE body_hash IS NOT NULL")
    for h, jld in hash_rows:
        if h and jld:
            existing_hashes[h] = jld

    dedup_count = 0
    to_process = []

    for mid, subject, body in documents:
        h = _content_hash(subject, body)

        if h in existing_hashes:
            # Reuse existing extraction
            db.conn.execute(
                f"INSERT OR IGNORE INTO {db.table('knowledge_graphs')} (document_id, json_ld, body_hash) VALUES (?, ?, ?)",
                (mid, existing_hashes[h] if isinstance(existing_hashes[h], str) else json.dumps(existing_hashes[h]), h),
            )
            db.conn.execute(f"UPDATE {db.table('raw_documents')} SET processed_status = 'decomposed' WHERE document_id = ?", (mid,))
            dedup_count += 1
        else:
            to_process.append((mid, subject, body, h))

    if dedup_count:
        logging.info(f"Dedup: {dedup_count} documents reused from existing extractions.")

    if not to_process:
        logging.info("All documents resolved via dedup. No LLM calls needed.")
        if own_db:
            db.close()
        return

    # --- Phase 2: Group into work items (singles + batches) ---
    documents_for_llm = [(mid, subject, body) for mid, subject, body, _ in to_process]
    hash_lookup = {mid: h for mid, _, _, h in to_process}

    work_items = _group_for_batching(documents_for_llm)
    total_items = sum(1 if w[0] == "single" else len(w[1]) for w in work_items)
    batch_count = sum(1 for w in work_items if w[0] == "batch")
    single_count = sum(1 for w in work_items if w[0] == "single")
    logging.info(f"Work plan: {single_count} individual + {batch_count} batches ({total_items} documents total)")

    # --- Phase 3: Parallel execution ---
    success = 0
    errors = 0
    consecutive_errors = 0
    all_profiles = []
    phase3_start = time.perf_counter()

    def _store_result(mid, json_result):
        nonlocal success, errors, consecutive_errors, existing_hashes
        if "error" not in json_result:
            h = hash_lookup.get(mid, "")
            json_str = json.dumps(json_result)
            db.conn.execute(
                f"INSERT OR IGNORE INTO {db.table('knowledge_graphs')} (document_id, json_ld, body_hash) VALUES (?, ?, ?)",
                (mid, json_str, h),
            )
            db.conn.execute(f"UPDATE {db.table('raw_documents')} SET processed_status = 'decomposed' WHERE document_id = ?", (mid,))
            # Cache hash for future dedup within this run
            if h:
                existing_hashes[h] = json_str
            success += 1
            consecutive_errors = 0
        else:
            logging.warning(f"Failed {mid}: {json_result['error']}")
            errors += 1
            consecutive_errors += 1

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}

        for work_type, payload in work_items:
            if work_type == "single":
                mid, subject, body = payload
                f = pool.submit(_process_one, llm, mid, subject, body, chunk_tiers=chunk_tiers)
                futures[f] = ("single", mid)
            else:
                f = pool.submit(_process_batch, llm, payload)
                futures[f] = ("batch", [mid for mid, _, _ in payload])

        for future in tqdm(as_completed(futures), total=len(futures), desc="Decomposing"):
            work_type, meta = futures[future]

            try:
                if work_type == "single":
                    _, json_result, profile = future.result()
                    _store_result(meta, json_result)
                    all_profiles.append(profile)
                else:
                    batch_results = future.result()
                    for mid, json_result in batch_results:
                        _store_result(mid, json_result)
                        # If batch item failed, try individually as fallback
                        if "error" in json_result and "batch" in json_result.get("error", "").lower():
                            logging.info(f"Retrying {mid} individually after batch failure...")
                            _, retry_result, _ = _process_one(llm, mid, "", "", chunk_tiers=chunk_tiers)

            except Exception as e:
                if work_type == "single":
                    logging.error(f"Worker exception for {meta}: {e}")
                else:
                    logging.error(f"Batch worker exception for {meta}: {e}")
                errors += 1
                consecutive_errors += 1

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logging.error(f"Aborting: {MAX_CONSECUTIVE_ERRORS} consecutive errors.")
                pool.shutdown(wait=False, cancel_futures=True)
                break

    phase3_ms = (time.perf_counter() - phase3_start) * 1000

    # --- Profile Summary ---
    if all_profiles:
        ok_profiles = [p for p in all_profiles if p["status"] == "ok"]
        elapsed_vals = [p["elapsed_ms"] for p in all_profiles]
        tok_vals = [p["tokens_per_sec"] for p in ok_profiles if p["tokens_per_sec"] > 0]
        logging.info(
            "PROFILE_SUMMARY documents=%d ok=%d fail=%d wall=%dms per_doc_ms=[min=%d avg=%d max=%d] tok/s=[min=%.1f avg=%.1f max=%.1f]",
            len(all_profiles),
            len(ok_profiles),
            len(all_profiles) - len(ok_profiles),
            round(phase3_ms),
            min(elapsed_vals) if elapsed_vals else 0,
            sum(elapsed_vals) // len(elapsed_vals) if elapsed_vals else 0,
            max(elapsed_vals) if elapsed_vals else 0,
            min(tok_vals) if tok_vals else 0,
            sum(tok_vals) / len(tok_vals) if tok_vals else 0,
            max(tok_vals) if tok_vals else 0,
        )

    logging.info(f"Decomposition complete. {success} succeeded, {errors} failed, {dedup_count} deduped.")
    if own_db:
        db.close()


def run_continuous(batch_size=1000, workers=MAX_WORKERS, model=None, db=None, num_thread=0):
    """Run decomposition in a loop until no verified documents remain."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - pipe_03 - %(levelname)s - %(message)s")
    round_num = 0
    while True:
        round_num += 1
        logging.info(f"=== Continuous round {round_num} (batch_size={batch_size}) ===")

        check_db = db if db is not None else CoreDB()
        remaining = check_db.query(
            f"SELECT COUNT(*) FROM {check_db.table('raw_documents')} r"
            f" LEFT JOIN {check_db.table('knowledge_graphs')} k ON r.document_id = k.document_id"
            " WHERE r.processed_status = 'verified' AND k.document_id IS NULL"
        )
        count = remaining[0][0] if remaining else 0
        if db is None:
            check_db.close()

        if count == 0:
            logging.info("No verified documents remaining. Done.")
            break

        logging.info(f"{count} documents remaining.")
        run(batch_size=batch_size, workers=workers, model=model, db=db, num_thread=num_thread)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Decompose verified documents into knowledge graphs.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--model", default=None, help="LLM model (default: from config)")
    parser.add_argument("--num-thread", type=int, default=0, help="Ollama num_thread (0=auto from config)")
    parser.add_argument("--continuous", action="store_true", help="Loop until all verified documents are processed.")
    args = parser.parse_args()

    if args.continuous:
        run_continuous(batch_size=args.batch_size, workers=args.workers, model=args.model, num_thread=args.num_thread)
    else:
        run(batch_size=args.batch_size, workers=args.workers, model=args.model, num_thread=args.num_thread)
