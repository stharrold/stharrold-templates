# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Reranking layer: refine Hamming-based retrieval with cosine similarity."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def cosine_similarity(a, b):
    """Compute cosine similarity between two float vectors."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def rerank(query_text, candidate_results, embedder, top_k=10):
    """Rerank Hamming-retrieved candidates using cosine similarity on float embeddings.

    Args:
        query_text: Original query string.
        candidate_results: List of (node_id, content, node_type, hamming_distance) from DB search.
        embedder: CoreEmbedder instance with embed(text).
        top_k: Number of results to return after reranking.

    Returns:
        Reranked list of (node_id, content, node_type, cosine_score) tuples.
    """
    if not candidate_results:
        return []

    # 1. Batch embed query + all candidate contents in one call
    all_texts = [query_text] + [content for _, content, _, _ in candidate_results]
    all_embeddings = embedder.embed_batch(all_texts)
    query_embedding = all_embeddings[0]

    # 2. Compute cosine similarity for each candidate
    scored = []
    for idx, (node_id, content, node_type, _hamming_dist) in enumerate(candidate_results):
        score = cosine_similarity(query_embedding, all_embeddings[idx + 1])
        scored.append((node_id, content, node_type, score))

    # 3. Sort by cosine similarity (descending)
    scored.sort(key=lambda x: x[3], reverse=True)

    return scored[:top_k]
