# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""release_lib -- the deterministic core of the release pilot (Tier 2).

This package holds only logic that must NOT be left to model judgment:
version math, bundle file-ownership resolution, and the gh/az VCS
abstraction. Orchestration and "next step" judgment live in the
release-pilot skill, not here.

See ARCHIVED/20260613T210202Z_critical-assessment_*.md and issue #240.
"""

from release_lib.semver import (
    analyze_changes,
    bump_version,
    calculate_semantic_version,
    get_changed_files,
    get_last_tag,
    next_version_from_tag,
)
from release_lib.vcs import (
    VCSProvider,
    create_issue,
    create_pr,
    create_release,
    detect_provider,
    get_contrib_branch,
    get_username,
    query_pr_review_threads,
)

__all__ = [
    "analyze_changes",
    "bump_version",
    "calculate_semantic_version",
    "get_changed_files",
    "get_last_tag",
    "next_version_from_tag",
    "VCSProvider",
    "create_issue",
    "create_pr",
    "create_release",
    "detect_provider",
    "get_contrib_branch",
    "get_username",
    "query_pr_review_threads",
]
