# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""JSONL logging with batch and time-based progress tracking."""

import threading
import time
from datetime import UTC, datetime
from typing import Any


class QueryLogger:
    """Logger for query execution with batch and time-based tracking."""

    def __init__(self, start_time: float | None = None):
        """Initialize logger."""
        self.log_entries: list[dict[str, Any]] = []
        self.timer_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.start_time = start_time or time.time()
        self.current_batch = 0
        self.expected_batches = 0
        self.rows_per_second = 0.0

    def log_event(self, event_type: str, **kwargs: Any) -> None:
        """Log an event to memory buffer."""
        entry: dict[str, Any] = {
            "type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            **kwargs,
        }
        self.log_entries.append(entry)

    def log_start(self, expected_rows: int, expected_batches: int) -> None:
        """Log query start event."""
        self.expected_batches = expected_batches
        self.log_event("start", expected_rows=expected_rows, expected_batches=expected_batches)

    def log_batch(
        self,
        batch: int,
        rows_processed: int,
        progress_pct: float,
        mb_batch: float,
        mb_total: float,
        last_processed_value: dict[str, Any],
        resumption_template: str | None = None,
    ) -> None:
        """Log batch completion event."""
        self.current_batch = batch
        elapsed_sec = time.time() - self.start_time

        if elapsed_sec > 0:
            self.rows_per_second = rows_processed / elapsed_sec

        log_data: dict[str, Any] = {
            "batch": batch,
            "rows_processed": rows_processed,
            "progress_pct": round(progress_pct, 2),
            "mb_batch": round(mb_batch, 3),
            "mb_total": round(mb_total, 3),
            "elapsed_sec": round(elapsed_sec, 2),
        }

        if last_processed_value:
            log_data["last_processed_value"] = last_processed_value

        if resumption_template:
            log_data["resumption_template"] = resumption_template

        self.log_event("batch", **log_data)

    def log_time_milestone(self) -> None:
        """Log time-based progress update (called every 60 seconds)."""
        elapsed_sec = time.time() - self.start_time

        eta_sec = 0
        if self.current_batch > 0 and self.expected_batches > 0:
            batches_remaining = self.expected_batches - self.current_batch
            if batches_remaining > 0 and self.current_batch > 0:
                time_per_batch = elapsed_sec / self.current_batch
                eta_sec = int(batches_remaining * time_per_batch)

        self.log_event(
            "time",
            elapsed_sec=round(elapsed_sec, 2),
            current_batch=self.current_batch,
            expected_batches=self.expected_batches,
            eta_sec=eta_sec,
            rows_per_second=round(self.rows_per_second, 2),
        )

    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log warning event."""
        self.log_event("warning", message=message, **kwargs)

    def log_error(self, error: Exception) -> None:
        """Log error event with traceback."""
        import traceback

        self.log_event(
            "error",
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
        )

    def log_end(self, exit_status: str) -> None:
        """Log query end event."""
        runtime_seconds = time.time() - self.start_time
        self.log_event("end", runtime_seconds=round(runtime_seconds, 2), exit_status=exit_status)

    def start_timer_thread(self) -> None:
        """Start background timer thread (logs every 60 seconds)."""
        self.stop_event.clear()

        def timer_worker() -> None:
            while not self.stop_event.wait(timeout=60):
                self.log_time_milestone()

        self.timer_thread = threading.Thread(target=timer_worker, daemon=True)
        self.timer_thread.start()

    def stop_timer_thread(self) -> None:
        """Stop background timer thread."""
        self.stop_event.set()
        if self.timer_thread:
            self.timer_thread.join(timeout=5)

    def get_log_entries(self) -> list[dict[str, Any]]:
        """Get all logged events."""
        return self.log_entries
