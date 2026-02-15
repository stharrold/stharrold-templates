"""Format graph nodes and search results for display and LLM context (document domain)."""

import logging

# ---------------------------------------------------------------------------
# CUSTOMIZE: Adapt citation formatting for your document domain. This example
# formats email citations with sender, subject, date, and folder.
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


def format_node_as_text(node):
    """Format a graph node for display.

    Args:
        node: A tuple/row from graph_nodes -- at minimum (node_id, name, node_type, ...).

    Returns:
        Formatted string representation.
    """
    if not node:
        return ""
    # node could be a string (content) or a tuple
    if isinstance(node, str):
        return node
    # Assume tuple: (node_id, name, node_type, ...)
    name = node[1] if len(node) > 1 else str(node[0])
    node_type = node[2] if len(node) > 2 else ""
    if node_type:
        return f"{name} [{node_type}]"
    return name


def format_search_results_as_context(results, citation_lookup=None):
    """Format search results into a context block for LLM prompts.

    Args:
        results: List of (node_id, name, node_type, distance) tuples from search_nodes.
        citation_lookup: Optional dict mapping node_id -> document metadata dict with keys:
            document_id, from_email, subject, sent_on_utc, folder_path.

    Returns:
        Formatted context string.
    """
    if not results:
        return "No relevant content found."

    context_parts = []
    for i, (node_id, content, node_type, distance) in enumerate(results):
        similarity = (1 - distance / 384.0) * 100
        header = f"[{i + 1}] ({similarity:.0f}% match, type: {node_type})"

        # Add document source info if available
        if citation_lookup and node_id in citation_lookup:
            meta = citation_lookup[node_id]
            label = _extract_document_label(meta)
            if label:
                header += f" — {label}"

        context_parts.append(f"{header}\n{content}")

    return "\n\n".join(context_parts)


def _extract_document_label(meta):
    """Build a short document label from citation metadata."""
    if not meta or not isinstance(meta, dict):
        return None

    parts = []
    subject = meta.get("subject")
    if subject:
        parts.append(subject)
    from_email = meta.get("from_email")
    if from_email:
        parts.append(f"from {from_email}")
    sent_on = meta.get("sent_on_utc")
    if sent_on:
        parts.append(str(sent_on))
    folder = meta.get("folder_path")
    if folder:
        parts.append(folder)

    return " — ".join(parts) if parts else None
