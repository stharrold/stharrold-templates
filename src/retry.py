# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Retry logic for transient database errors.

Provides a decorator for retrying operations that fail due to transient
SQL Server / Azure Synapse errors (connection drops, timeouts, etc.).
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

import pyodbc

logger = logging.getLogger(__name__)

# SQLSTATE prefixes indicating transient errors:
#   08xxx = connection exceptions
#   HYTxx = timeout expired
RETRYABLE_SQLSTATE_PREFIXES = ("08", "HYT")


def is_retryable_error(error: Exception) -> bool:
    """Check if a pyodbc error is transient and retryable.

    Args:
        error: The exception to check.

    Returns:
        True if the error is likely transient and worth retrying.
    """
    if not isinstance(error, pyodbc.Error):
        return False

    # pyodbc errors have args like ('SQLSTATE', 'message')
    if error.args and len(error.args) >= 1:
        sqlstate = str(error.args[0])
        for prefix in RETRYABLE_SQLSTATE_PREFIXES:
            if sqlstate.startswith(prefix):
                return True

    # Azure Synapse auto-pause error (error 40892)
    error_msg = str(error)
    if "40892" in error_msg:
        return True

    return False


def retry_on_transient_error(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 5.0,
) -> Callable[..., Any]:
    """Decorator that retries a function on transient database errors.

    Uses exponential backoff: delay = base_delay * (backoff_factor ** attempt).

    Args:
        max_retries: Maximum number of retry attempts (default 3).
        base_delay: Initial delay in seconds before first retry (default 1.0).
        backoff_factor: Multiplier for each subsequent delay (default 5.0).

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if attempt >= max_retries or not is_retryable_error(e):
                        raise

                    delay = base_delay * (backoff_factor**attempt)
                    func_name = getattr(func, "__name__", repr(func))
                    logger.warning(
                        "Transient error on attempt %d/%d for %s: %s. Retrying in %.1fs...",
                        attempt + 1,
                        max_retries + 1,
                        func_name,
                        e,
                        delay,
                    )
                    time.sleep(delay)

            # Should not reach here, but satisfy type checker
            if last_error is not None:
                raise last_error

        return wrapper

    return decorator
