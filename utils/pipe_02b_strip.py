"""Pipeline stage 02b: Strip quoted content and sanitize document text.

Preserves original body in raw_documents.body, writes stripped version to body_stripped.
Decomposition stage uses body_stripped if available, else falls back to body.

Operations:
1. Sanitize: Remove problematic Unicode (control chars, combining marks, zero-width)
2. Strip: Remove quoted content (From/Sent blocks, separators, reply chains)
"""

import logging
import re
import unicodedata

from tqdm import tqdm

from .core_db import CoreDB

# ---------------------------------------------------------------------------
# CUSTOMIZE: Adapt content preprocessing patterns for your domain. This
# example strips email reply quotes, URLs, and normalizes encoding.
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# Patterns that indicate start of reply-quoted content (truncate from match point)
REPLY_PATTERNS = [
    # Outlook: "From: Name <email>\nSent: Date"
    re.compile(r"^From:\s+.+\n\s*Sent:\s+", re.MULTILINE | re.IGNORECASE),
    # Outlook separator line (20+ underscores or dashes)
    re.compile(r"^[_\-]{20,}\s*$", re.MULTILINE),
    # Gmail/generic: "On Oct 2, 2020, at 8:57 AM, Name wrote:"
    re.compile(r"^On\s+.+wrote:\s*$", re.MULTILINE | re.IGNORECASE),
]

# Patterns that indicate forwarded content (preserve body after marker)
FORWARD_PATTERNS = [
    re.compile(r"^-{3,}\s*Original Message\s*-{3,}", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^-{3,}\s*Forwarded message\s*-{3,}", re.MULTILINE | re.IGNORECASE),
]

# Mechanical header block inside a forward (From/Sent/To/Cc/Subject lines)
FORWARD_HEADER_RE = re.compile(
    r"^\s*(?:From:\s+.+\n)(?:\s*Sent:\s+.+\n)?(?:\s*To:\s+.+\n)?(?:\s*Cc:\s+.+\n)?(?:\s*Subject:\s+.+\n)?",
    re.MULTILINE | re.IGNORECASE,
)

# Signature patterns (to strip trailing signatures before quoted content)
SIGNATURE_PATTERNS = [
    # Common signature starters
    re.compile(r"^(Best|Regards|Thanks|Cheers|Sincerely),?\s*$", re.MULTILINE | re.IGNORECASE),
    # Name + title block (Name\nTitle\nCompany)
    re.compile(r"\n[A-Z][a-z]+\s+[A-Z][a-z]+\n[A-Z].{5,50}\n", re.MULTILINE),
]


def normalize_backslash_paths(text: str) -> str:
    r"""Replace backslash in domain\user and file\path patterns with forward slash.

    LLMs interpret \X as Unicode escapes in JSON output (e.g. \i -> \uXXXX),
    which can produce invalid surrogates that DuckDB rejects on INSERT.
    """
    if not text or "\\" not in text:
        return text
    # domain\user patterns: word\word (e.g. MHG\iuhpsvc, CORP\jsmith)
    text = re.sub(r"(\w)\\(\w)", r"\1/\2", text)
    return text


def strip_urls(text: str) -> str:
    """Remove URLs from text to avoid LLM confusion.

    Removes:
    - http:// and https:// URLs
    - SafeLinks wrapped URLs
    - Mailto links
    """
    if not text:
        return text

    # Remove URLs (greedy, captures long SafeLinks)
    text = re.sub(r"https?://[^\s<>\"\')]+", "[URL]", text)
    text = re.sub(r"mailto:[^\s<>\"\')]+", "[EMAIL]", text)

    # Clean up multiple [URL] placeholders
    text = re.sub(r"(\[URL\]\s*)+", "[URL] ", text)

    return text


def sanitize_text(text: str, ascii_only: bool = True) -> str:
    """Remove problematic characters that can cause HTTP/encoding errors.

    Args:
        text: Input text to sanitize
        ascii_only: If True, keep only ASCII printable chars (32-126) plus whitespace.
                   If False, use Unicode category filtering (less aggressive).

    With ascii_only=True (default), removes ALL non-ASCII including:
    - Unicode letters, symbols, emojis
    - Non-breaking spaces (U+00A0)
    - Smart quotes, dashes, etc.

    Always keeps: newline, tab, carriage return, ASCII printable (32-126)
    """
    if not text:
        return text

    result = []
    for char in text:
        code = ord(char)

        # Always keep common whitespace
        if char in "\n\r\t":
            result.append(char)
        # ASCII printable range (space through tilde)
        elif 32 <= code <= 126:
            result.append(char)
        # Non-ASCII handling
        elif not ascii_only:
            # Keep letters/numbers/punctuation, remove control/format/combining
            category = unicodedata.category(char)
            if category not in {"Cc", "Cf", "Mn", "Mc", "Me", "Cs", "Co"}:
                result.append(char)
        # ascii_only=True: skip all non-ASCII

    return "".join(result)


def strip_quoted_content(body: str) -> tuple[str, dict]:
    """Strip quoted content from document body.

    Returns:
        (stripped_body, metadata) where metadata contains:
        - original_length: int
        - stripped_length: int
        - pattern_matched: str or None
        - reduction_pct: float
    """
    if not body:
        return body, {"original_length": 0, "stripped_length": 0, "pattern_matched": None, "reduction_pct": 0, "sanitized": False, "urls_stripped": False}

    original_length = len(body)

    # Step 1: Sanitize - remove problematic Unicode (ASCII only)
    sanitized = sanitize_text(body)
    was_sanitized = len(sanitized) != len(body)

    # Step 2: Normalize backslash paths (domain\user -> domain/user)
    sanitized = normalize_backslash_paths(sanitized)

    # Step 3: Strip URLs to avoid LLM confusion
    url_stripped = strip_urls(sanitized)
    urls_removed = len(sanitized) != len(url_stripped)

    stripped = url_stripped
    pattern_matched = None

    # Check for forwarded content first (preserve forwarded body)
    forward_match = None
    for pattern in FORWARD_PATTERNS:
        m = pattern.search(body)
        if m and (forward_match is None or m.start() < forward_match.start()):
            forward_match = m

    if forward_match:
        preamble = sanitize_text(body[: forward_match.start()].rstrip())
        preamble = normalize_backslash_paths(preamble)
        preamble = strip_urls(preamble)

        forwarded_raw = body[forward_match.end() :]
        # Strip the mechanical header block (From/Sent/To/Cc/Subject)
        forwarded_raw = FORWARD_HEADER_RE.sub("", forwarded_raw, count=1)
        forwarded = sanitize_text(forwarded_raw.strip())
        forwarded = normalize_backslash_paths(forwarded)
        forwarded = strip_urls(forwarded)

        # Apply reply-pattern stripping within the forwarded content
        # (the forward itself may contain a reply chain)
        earliest_reply = len(forwarded)
        for rp in REPLY_PATTERNS:
            rm = rp.search(forwarded)
            if rm and rm.start() < earliest_reply:
                earliest_reply = rm.start()
        if earliest_reply < len(forwarded):
            forwarded = forwarded[:earliest_reply].rstrip()

        # Combine preamble + forwarded body
        if preamble.strip():
            stripped = preamble.strip() + "\n\n" + forwarded
        else:
            stripped = forwarded

        pattern_matched = "forward:" + forward_match.re.pattern[:40]
    else:
        # No forward -- apply reply-pattern stripping (truncate at earliest match)
        earliest_pos = len(body)
        for pattern in REPLY_PATTERNS:
            match = pattern.search(body)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()
                pattern_matched = pattern.pattern[:50]

        if earliest_pos < len(body):
            stripped = body[:earliest_pos].rstrip()
            # Re-apply sanitize/normalize/URL-strip to the truncated portion
            stripped = sanitize_text(stripped)
            stripped = normalize_backslash_paths(stripped)
            stripped = strip_urls(stripped)

    # Clean up: remove trailing signature-like content if body is now very short
    # (don't strip signatures if that's all we have)
    if len(stripped) > 100:
        for sig_pattern in SIGNATURE_PATTERNS:
            match = sig_pattern.search(stripped)
            if match and match.start() > len(stripped) * 0.5:  # Only if in latter half
                # Don't strip if it would leave less than 50 chars
                if match.start() > 50:
                    stripped = stripped[: match.start()].rstrip()
                    break

    stripped_length = len(stripped)
    reduction_pct = round((1 - stripped_length / original_length) * 100, 1) if original_length > 0 else 0

    return stripped, {
        "original_length": original_length,
        "stripped_length": stripped_length,
        "pattern_matched": pattern_matched,
        "reduction_pct": reduction_pct,
        "sanitized": was_sanitized,
        "urls_stripped": urls_removed,
    }


def ensure_column_exists(db: CoreDB):
    """Add body_stripped column if it doesn't exist."""
    try:
        db.query(f"SELECT body_stripped FROM {db.table('raw_documents')} LIMIT 1")
    except Exception:
        logger.info(f"Adding body_stripped column to {db.table('raw_documents')}...")
        db.conn.execute(f"ALTER TABLE {db.table('raw_documents')} ADD COLUMN body_stripped TEXT")
        logger.info("Column added.")


def run(batch_size: int = 1000, force: bool = False, db: CoreDB = None):
    """Strip quoted content from verified documents.

    Args:
        batch_size: Number of documents to process per batch
        force: If True, reprocess documents that already have body_stripped
        db: Optional CoreDB instance (creates default if None)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - pipe_02b - %(levelname)s - %(message)s",
    )

    if db is None:
        db = CoreDB()
    ensure_column_exists(db)

    # Find documents to process
    if force:
        where_clause = "processed_status IN ('verified', 'decomposed', 'vectorized', 'linked')"
    else:
        where_clause = "processed_status IN ('verified', 'decomposed', 'vectorized', 'linked') AND body_stripped IS NULL"

    count_result = db.query(f"SELECT COUNT(*) FROM {db.table('raw_documents')} WHERE {where_clause}")
    total = count_result[0][0] if count_result else 0

    if total == 0:
        logger.info("No documents to process.")
        return

    logger.info(f"Processing {total} documents...")

    processed = 0
    total_reduction = 0
    patterns_matched = 0

    # Process in batches
    offset = 0
    with tqdm(total=total, desc="Stripping quoted content") as pbar:
        while offset < total:
            rows = db.query(f"""
                SELECT document_id, body
                FROM {db.table("raw_documents")}
                WHERE {where_clause}
                ORDER BY document_id
                LIMIT {batch_size} OFFSET {offset}
            """)

            if not rows:
                break

            updates = []
            for document_id, body in rows:
                stripped, meta = strip_quoted_content(body or "")
                updates.append((stripped, document_id))

                total_reduction += meta["reduction_pct"]
                if meta["pattern_matched"]:
                    patterns_matched += 1
                processed += 1

            # Batch update
            db.conn.executemany(f"UPDATE {db.table('raw_documents')} SET body_stripped = ? WHERE document_id = ?", updates)

            pbar.update(len(rows))
            offset += batch_size

    avg_reduction = total_reduction / processed if processed > 0 else 0
    logger.info(f"Processed {processed} documents. Avg reduction: {avg_reduction:.1f}%. Patterns matched: {patterns_matched} ({patterns_matched / processed * 100:.1f}%)")


def run_single(db: CoreDB, document_id: str, body: str) -> str:
    """Strip quoted content for a single document. Used by parallel pipeline.

    Returns the stripped body (does not write to DB).
    """
    stripped, _ = strip_quoted_content(body)
    return stripped


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Strip quoted content from documents")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size")
    parser.add_argument("--force", action="store_true", help="Reprocess all documents")
    args = parser.parse_args()

    run(batch_size=args.batch_size, force=args.force)
