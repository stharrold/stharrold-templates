# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
import logging
import re

from tqdm import tqdm

from .core_db import CoreDB

# ---------------------------------------------------------------------------
# CUSTOMIZE: Adapt verification heuristics for your document domain. This
# example shows email-specific rules (marketing detection, automated digests,
# etc.).
# ---------------------------------------------------------------------------


def verify_email(subject, body, from_email="", from_name=""):
    """Heuristic verification with decision tree.

    Returns (is_valid, reason) tuple.
    """
    subject_lower = subject.lower() if subject else ""
    body_lower = body.lower() if body else ""
    from_lower = (from_email + from_name).lower()

    # 1. Basic filters
    if not body or len(body.strip()) < 10:
        return False, "body_too_short"

    if not subject:
        return False, "no_subject"

    if subject_lower.startswith("automatic reply:") or "out of office" in subject_lower:
        return False, "auto_reply"

    # 2. Marketing/Newsletter detection
    if "what's new" in subject_lower or "whats new" in subject_lower:
        return False, "marketing_newsletter"
    # NOTE: Removed "unsubscribe in body" rule - too aggressive, catches legitimate mailing lists

    # 3. Automated digest detection
    if "digest" in subject_lower:
        return False, "automated_digest"
    if "viva-noreply" in from_lower or "viva@" in from_lower:
        return False, "automated_digest"

    # 4. External survey detection (noreply + survey in subject)
    if "survey" in subject_lower and "noreply" in from_lower:
        return False, "external_survey"

    # 5. Test/debug alert detection
    if "test" in subject_lower and ("publish" in subject_lower or "alert" in subject_lower):
        return False, "automated_test_alert"

    # 6. Unmonitored mailbox notification detection
    if "this email account is not monitored" in body_lower[:200]:
        return False, "unmonitored_notification"

    # 7. Attachment-only detection (body is just "attached..." + signature)
    first_para = re.split(r"\n\s*\n", body.strip())[0] if body else ""
    if re.match(r"^attached\s+(please\s+)?find", first_para.lower()) and len(first_para) < 100:
        return False, "attachment_only"

    # 8. Expiration notifications
    if "has expired" in subject_lower or "will expire" in subject_lower:
        return False, "automated_expiration"

    # 9. Confirmation notifications
    if "successfully created" in body_lower[:200] or "successfully added" in body_lower[:200]:
        return False, "automated_confirmation"

    # 10. Feedback/survey requests
    if "your input" in subject_lower or "your feedback" in subject_lower:
        return False, "external_survey"

    # 11. Webinar marketing
    if "webinar" in subject_lower and "unsubscribe" in body_lower:
        return False, "marketing"

    # 12. External marketing with unsubscribe (targeted by @email. domain pattern)
    if "unsubscribe" in body_lower and "@email." in from_email.lower():
        return False, "marketing"

    # 13. Marketing sender detection (marketing@ or marketinggroup in from)
    from_email_lower = from_email.lower() if from_email else ""
    if "marketing@" in from_email_lower or "marketinggroup" in from_email_lower:
        return False, "marketing"

    # 14. Automated notifications from major platforms
    if from_email_lower in ["no-reply@youtube.com", "payments-noreply@google.com"]:
        return False, "automated_notification"

    # 15. MyAnalytics digest
    if "myanalytics" in from_lower:
        return False, "automated_digest"

    # 16. Confirmation notifications (expanded to full body)
    if "successfully created" in body_lower or "successfully added" in body_lower:
        return False, "automated_confirmation"

    return True, "verified"


def run(db=None):
    """Run Stage 02a: Verify documents using decision tree heuristics.

    Args:
        db: Optional CoreDB instance (creates default if None)
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - pipe_02 - %(levelname)s - %(message)s")
    own_db = db is None
    if own_db:
        db = CoreDB()

    # Get new documents (include from_email and from_name for decision tree)
    documents = db.query(f"SELECT document_id, subject, body, from_email, from_name FROM {db.table('raw_documents')} WHERE processed_status='new'")

    if not documents:
        logging.info("No new documents to verify.")
        return

    logging.info(f"Verifying {len(documents)} documents...")

    updates = []

    for mid, subject, body, from_email, from_name in tqdm(documents):
        is_valid, reason = verify_email(subject, body, from_email or "", from_name or "")
        status = "verified" if is_valid else "skipped"
        updates.append((status, mid))

    # Batch update
    logging.info("Updating database...")
    db.conn.executemany(f"UPDATE {db.table('raw_documents')} SET processed_status=? WHERE document_id=?", updates)

    verified_count = sum(1 for s, _ in updates if s == "verified")
    logging.info(f"Verification complete. {verified_count} verified, {len(documents) - verified_count} skipped.")

    if own_db:
        db.close()


def run_all(db=None):
    """Run full Stage 02: verify + strip + threads.

    This is the unified entry point for all preprocessing stages:
    - 02a: Verify (decision tree heuristics) -> status = verified/skipped
    - 02b: Strip (sanitize, remove URLs, quoted text) -> body_stripped
    - 02c: Threads (analyze positions, create reply_to edges) -> thread_position

    Args:
        db: Optional CoreDB instance (creates default if None)
    """
    from . import pipe_02b_strip, pipe_02c_threads

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - pipe_02 - %(levelname)s - %(message)s")
    own_db = db is None
    if own_db:
        db = CoreDB()

    logging.info("=== Stage 02: Full Preprocessing ===")

    # 02a: Verify
    logging.info("--- Stage 02a: Verify ---")
    run(db=db)

    # 02b: Strip
    logging.info("--- Stage 02b: Strip ---")
    pipe_02b_strip.run(db=db)

    # 02c: Threads
    logging.info("--- Stage 02c: Threads ---")
    pipe_02c_threads.run(db=db)

    logging.info("=== Stage 02: Complete ===")

    if own_db:
        db.close()


def run_preprocess(db=None):
    """Run preprocessing only: strip + threads (skip verification).

    Use this when documents are already verified (e.g., evaluation pipeline).
    - 02b: Strip (sanitize, remove URLs, quoted text) -> body_stripped
    - 02c: Threads (analyze positions, create reply_to edges) -> thread_position

    Args:
        db: Optional CoreDB instance (creates default if None)
    """
    from . import pipe_02b_strip, pipe_02c_threads

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - pipe_02 - %(levelname)s - %(message)s")
    own_db = db is None
    if own_db:
        db = CoreDB()

    logging.info("=== Stage 02: Preprocessing (strip + threads) ===")

    # 02b: Strip
    logging.info("--- Stage 02b: Strip ---")
    pipe_02b_strip.run(db=db)

    # 02c: Threads
    logging.info("--- Stage 02c: Threads ---")
    pipe_02c_threads.run(db=db)

    logging.info("=== Stage 02: Preprocessing Complete ===")

    if own_db:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stage 02: Document preprocessing")
    parser.add_argument("--all", action="store_true", help="Run all substages (verify + strip + threads)")
    args = parser.parse_args()

    if args.all:
        run_all()
    else:
        run()
