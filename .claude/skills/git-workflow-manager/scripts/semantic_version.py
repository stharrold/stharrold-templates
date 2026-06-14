#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Backward-compat shim. Canonical home: release_lib.semver (issue #240).

Kept so any legacy CLI invocation (`python semantic_version.py <base>
<version>`) keeps working until issue #242 removes the old skill scripts.
New code should import from release_lib.semver directly.
"""

import subprocess  # noqa: F401  kept so legacy patch('semantic_version.subprocess...') targets resolve
import sys
from pathlib import Path

# release_lib is a top-level package; add the repo root so direct CLI
# invocation (sys.path[0] = this scripts dir) can still import it.
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from release_lib.semver import (  # noqa: E402,F401
    analyze_changes,
    bump_version,
    calculate_semantic_version,
    get_changed_files,
)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: semantic_version.py <base_branch> <current_version>")
        print("Example: semantic_version.py develop v1.0.0")
        sys.exit(1)

    print(calculate_semantic_version(sys.argv[1], sys.argv[2]))
