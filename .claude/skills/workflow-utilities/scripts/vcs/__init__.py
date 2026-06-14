#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Backward-compat shim. Canonical home: release_lib.vcs (issue #240).

Runtime callers still do `sys.path.insert(.../workflow-utilities/scripts)`
then `from vcs import create_pr, ...`. This shim keeps those imports
working by delegating to release_lib.vcs until issue #242 removes the old
skill scripts. New code should import from release_lib.vcs directly.
"""

import sys
from pathlib import Path

# release_lib is a top-level package; add the repo root so callers that
# only put .../workflow-utilities/scripts on sys.path can still import it.
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from release_lib.vcs import (  # noqa: E402,F401
    GITHUB_GRAPHQL_TEMPLATE,
    VCSProvider,
    check_auth,
    create_issue,
    create_pr,
    create_release,
    detect_provider,
    get_contrib_branch,
    get_username,
    query_pr_review_threads,
)

__all__ = [
    "VCSProvider",
    "check_auth",
    "create_issue",
    "create_pr",
    "create_release",
    "detect_provider",
    "get_contrib_branch",
    "get_username",
    "query_pr_review_threads",
    "GITHUB_GRAPHQL_TEMPLATE",
]
