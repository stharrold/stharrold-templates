import logging

from .core_db import CoreDB

# ---------------------------------------------------------------------------
# CUSTOMIZE: Implement document ingestion for your source (files, APIs,
# databases). This example shows Outlook email extraction.
# ---------------------------------------------------------------------------


def run():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - pipe_01 - %(levelname)s - %(message)s")
    db = CoreDB()

    # 1. Migrate Legacy Data
    logging.info("Checking for legacy SQLite data...")
    db.migrate_from_sqlite()

    # 2. (Future) Live Ingest from Outlook
    # This is where we would integrate the logic from scripts/export_outlook_to_sqlite.py
    # For now, we assume the primary data source for the prototype is the migration.

    # Check count
    count = db.query("SELECT count(*) FROM raw_documents WHERE processed_status='new'")[0][0]
    logging.info(f"Extraction complete. {count} new documents ready for processing.")

    db.close()


if __name__ == "__main__":
    run()
