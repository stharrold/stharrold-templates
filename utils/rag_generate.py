"""RAG Generation: query → embed → search → rerank → format → generate → answer with citations."""

import argparse
import hashlib
import logging

from .core_db import CoreDB
from .core_embedder import CoreEmbedder
from .core_formatter import format_search_results_as_context
from .core_llm import LocalLLM
from .core_reranker import rerank
from .rag_directives import build_prompt, list_directives

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def normalize_query(query):
    """Normalize query for cache key generation."""
    return " ".join(query.lower().strip().split())


def make_cache_key(query, directive="qa", hops=1):
    """SHA256 hash of the normalized query + directive + hops."""
    normalized = f"{normalize_query(query)}|d={directive}|h={hops}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def rag_query(query, top_k=10, use_rerank=True, use_cache=True, hops=1, directive="qa"):
    """Execute a full RAG pipeline: retrieve, rerank, generate.

    Args:
        query: User's natural language question.
        top_k: Number of results to use for context.
        use_rerank: Whether to apply cosine reranking.
        use_cache: Whether to check/store cache.
        hops: Number of graph expansion hops (1-3).
        directive: Analysis mode (qa, compare, timeline, summarize, connections).

    Returns:
        dict with 'answer', 'sources', 'cached', and 'directive' fields.
    """
    hops = max(1, min(3, hops))
    db = CoreDB()

    # 1. Check cache
    cache_key = make_cache_key(query, directive, hops)
    if use_cache:
        cached = db.cache_get(cache_key)
        if cached:
            logger.info("Cache hit for query: %s", query[:50])
            cached["cached"] = True
            return cached

    # 2. Embed query
    logger.info("Embedding query: %s", query[:80])
    embedder = CoreEmbedder()
    query_float = embedder.embed(query)
    query_ubigints, query_popcnt = embedder.quantize_ubigint(query_float)

    # 3. Retrieve candidates with document metadata (fetch more if reranking)
    retrieve_k = top_k * 5 if use_rerank else top_k
    full_candidates = db.search_nodes_with_citations(query_ubigints, query_popcnt, limit=retrieve_k)
    logger.info("Retrieved %d candidates.", len(full_candidates))

    # Extract base 4-tuple for reranker: (node_id, name, node_type, distance)
    candidates = [(r[0], r[1], r[2], r[3]) for r in full_candidates]

    # Build citation lookup: node_id -> document metadata
    citation_lookup = {
        r[0]: {
            "document_id": r[4],
            "from_email": r[5],
            "subject": r[6],
            "sent_on_utc": r[7],
            "folder_path": r[8],
        }
        for r in full_candidates
    }

    if not candidates:
        return {
            "answer": "No relevant content found in the document knowledge base.",
            "sources": [],
            "cached": False,
            "directive": directive,
        }

    # 4. Rerank (optional)
    if use_rerank and len(candidates) > top_k:
        logger.info("Reranking %d candidates to top-%d...", len(candidates), top_k)
        reranked = rerank(query, candidates, embedder, top_k=top_k)
        # Convert cosine score back to pseudo-distance for formatter
        final_results = [(r[0], r[1], r[2], int((1 - r[3]) * 384)) for r in reranked]
    else:
        final_results = candidates[:top_k]

    # 5. Expand context with N-hop graph neighbors
    direct_node_ids = [r[0] for r in final_results]
    expanded = db.expand_nodes_nhop(direct_node_ids, hops=hops, max_neighbors=3)
    logger.info("Graph expansion: %d neighbor nodes (%d hops).", len(expanded), hops)

    # Add expanded nodes to citation lookup
    for r in expanded:
        if r[0] not in citation_lookup:
            citation_lookup[r[0]] = {
                "document_id": r[4],
                "from_email": r[5],
                "subject": r[6],
                "sent_on_utc": r[7],
                "folder_path": r[8],
            }

    # 6. Format context with citation info
    context = format_search_results_as_context(final_results, citation_lookup=citation_lookup)
    if expanded:
        expanded_parts = []
        for i, (_node_id, content, node_type, weight, *_rest) in enumerate(expanded):
            expanded_parts.append(f"[R{i + 1}] (graph neighbor, edge weight: {weight:.2f}, type: {node_type}) {content}")
        context += "\n\n--- Related context (graph neighbors) ---\n\n" + "\n\n".join(expanded_parts)

    # 7. Generate answer with local LLM using directive template
    prompt = build_prompt(directive, query, context)

    llm = LocalLLM()
    logger.info("Generating answer with Ollama (directive=%s)...", directive)
    answer = llm.generate_text(prompt, timeout=120)

    # 8. Build source list with document metadata
    sources = []
    for node_id, content, node_type, dist in final_results:
        similarity = (1 - dist / 384.0) * 100
        source_entry = {
            "node_id": node_id,
            "content": content[:200] if content else "",
            "type": node_type,
            "similarity": round(similarity, 1),
        }
        cite_meta = citation_lookup.get(node_id)
        if cite_meta:
            if cite_meta.get("subject"):
                source_entry["subject"] = cite_meta["subject"]
            if cite_meta.get("from_email"):
                source_entry["from_email"] = cite_meta["from_email"]
            if cite_meta.get("sent_on_utc"):
                source_entry["sent_on_utc"] = str(cite_meta["sent_on_utc"])
            if cite_meta.get("folder_path"):
                source_entry["folder_path"] = cite_meta["folder_path"]
        sources.append(source_entry)

    result = {"answer": answer, "sources": sources, "cached": False, "directive": directive}

    # 9. Cache result
    if use_cache:
        db.cache_set(cache_key, query, result)
        logger.info("Cached result for query: %s", query[:50])

    db.close()
    return result


def main():
    parser = argparse.ArgumentParser(description="RAG query against the document knowledge graph.")
    parser.add_argument("query", help="Natural language question")
    parser.add_argument("--top-k", type=int, default=10, help="Number of context passages")
    parser.add_argument("--no-rerank", action="store_true", help="Disable cosine reranking")
    parser.add_argument("--no-cache", action="store_true", help="Disable query caching")
    parser.add_argument("--hops", type=int, default=1, help="Graph expansion hops (1-3)")
    parser.add_argument(
        "--directive",
        default="qa",
        choices=[d[0] for d in list_directives()],
        help="Analysis mode: " + ", ".join(f"{d[0]} ({d[1]})" for d in list_directives()),
    )
    parser.add_argument("--list-directives", action="store_true", help="List available directives and exit")
    args = parser.parse_args()

    if args.list_directives:
        print("Available directives:")
        for did, name, desc in list_directives():
            print(f"  {did:15s} {name:25s} {desc}")
        return

    result = rag_query(
        args.query,
        top_k=args.top_k,
        use_rerank=not args.no_rerank,
        use_cache=not args.no_cache,
        hops=args.hops,
        directive=args.directive,
    )

    print(f"\n{'=' * 60}")
    print(f"ANSWER {'(cached)' if result.get('cached') else ''} [directive: {result.get('directive', 'qa')}]")
    print(f"{'=' * 60}")
    print(result["answer"])
    print(f"\n{'=' * 60}")
    print(f"SOURCES ({len(result['sources'])} references)")
    print(f"{'=' * 60}")
    for i, src in enumerate(result["sources"]):
        print(f"[{i + 1}] ({src['similarity']}%) {src['content'][:120]}...")
        subject = src.get("subject")
        from_email = src.get("from_email")
        sent = src.get("sent_on_utc")
        if subject or from_email:
            parts = []
            if subject:
                parts.append(f"Subject: {subject}")
            if from_email:
                parts.append(f"From: {from_email}")
            if sent:
                parts.append(f"Date: {sent}")
            print(f"     {' | '.join(parts)}")
        folder = src.get("folder_path")
        if folder:
            print(f"     Folder: {folder}")


if __name__ == "__main__":
    main()
