# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""JSONL bench logger for per-document extraction results and cross-model comparison."""

import json
import logging
import os
import time
from collections import Counter
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class BenchLogger:
    """Append-only JSONL logger capturing per-document extraction metrics."""

    def __init__(self, model_name, run_id=None, output_dir="bench_logs/", batch_size=None, workers=None):
        self.model = model_name
        self.run_id = run_id or f"{model_name.replace(':', '-')}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.path = os.path.join(output_dir, f"{self.run_id}.jsonl")
        self._results = []
        self._start_time = time.perf_counter()

        # Write header line
        header = {
            "type": "header",
            "run_id": self.run_id,
            "model": self.model,
            "started_at": datetime.now(UTC).isoformat(),
            "batch_size": batch_size,
            "workers": workers,
        }
        self._append(header)
        logger.info("Bench log: %s", self.path)

    def _append(self, record):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def log_document(self, document_id, title, result, timings, chunks_attempted=1, chunks_succeeded=1, chunk_sizes_used=None):
        """Log one document's extraction result."""
        ok = result.get("ok", "error" not in result)
        entities = result.get("entities", [])
        summary = result.get("summary", "")

        type_counts = Counter(e.get("type", "Unknown") for e in entities)

        record = {
            "type": "document",
            "document_id": document_id,
            "title": (title or "")[:80],
            "model": self.model,
            "ok": bool(ok),
            "entity_count": len(entities),
            "entity_names": [e.get("name", "") for e in entities],
            "entity_types": dict(type_counts),
            "summary_length": len(summary),
            "chunks_attempted": chunks_attempted,
            "chunks_succeeded": chunks_succeeded,
            "chunk_sizes_used": chunk_sizes_used or [],
            "timings": timings,
            "error": result.get("error"),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._results.append(record)
        self._append(record)

    def log_summary(self):
        """Append a final summary line with aggregate stats."""
        ok_results = [r for r in self._results if r.get("ok")]
        failed_results = [r for r in self._results if not r.get("ok")]

        all_types = Counter()
        for r in ok_results:
            for t, c in r.get("entity_types", {}).items():
                all_types[t] += c

        decompose_times = [r["timings"].get("03_decompose", 0) for r in ok_results if "03_decompose" in r.get("timings", {})]

        summary = {
            "type": "summary",
            "run_id": self.run_id,
            "model": self.model,
            "total_documents": len(self._results),
            "succeeded": len(ok_results),
            "failed": len(failed_results),
            "avg_entities_per_doc": sum(r.get("entity_count", 0) for r in ok_results) / max(len(ok_results), 1),
            "avg_decompose_time": sum(decompose_times) / max(len(decompose_times), 1),
            "total_wall_time": time.perf_counter() - self._start_time,
            "entity_type_distribution": dict(all_types),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._append(summary)
        logger.info(
            "Bench summary: %d/%d succeeded, %.1f avg entities, %.1fs avg decompose",
            summary["succeeded"],
            summary["total_documents"],
            summary["avg_entities_per_doc"],
            summary["avg_decompose_time"],
        )
        return summary
