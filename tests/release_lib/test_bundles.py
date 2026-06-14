#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for release_lib.bundles -- the deterministic bundle engine
(canonical home, moved from scripts/apply_bundle.py in issue #240).

The argparse CLI and its subprocess behavior stay covered by
tests/unit/test_apply_bundle.py and tests/integration/test_apply_bundle.py;
these tests pin the engine via its canonical import path.
"""

import pytest

from release_lib.bundles import (
    BUNDLE_DEFINITIONS,
    VALID_BUNDLE_NAMES,
    resolve_bundles,
    validate_target,
)


class TestResolveBundles:
    """resolve_bundles expands composites and deduplicates."""

    def test_single_bundle_resolves_to_itself(self):
        assert resolve_bundles(["git"]) == ["git"]

    def test_graphrag_pulls_in_pipeline_dependency(self):
        """graphrag includes pipeline -- the dependency must appear."""
        resolved = resolve_bundles(["graphrag"])
        assert "pipeline" in resolved
        assert "graphrag" in resolved

    def test_deduplicates_overlapping_requests(self):
        resolved = resolve_bundles(["pipeline", "graphrag"])
        assert resolved.count("pipeline") == 1

    def test_unknown_bundle_raises_value_error(self):
        with pytest.raises(ValueError):
            resolve_bundles(["does-not-exist"])


class TestCatalog:
    """The catalog and the derived valid-name set stay in sync."""

    def test_valid_names_match_definition_keys(self):
        assert VALID_BUNDLE_NAMES == set(BUNDLE_DEFINITIONS.keys())

    def test_core_bundles_present(self):
        for name in ["git", "secrets", "ci", "full"]:
            assert name in BUNDLE_DEFINITIONS


class TestValidateTarget:
    """validate_target enforces the git-repo precondition."""

    def test_rejects_non_git_directory(self, tmp_path):
        ok, msg = validate_target(tmp_path)
        assert ok is False
        assert msg

    def test_accepts_git_worktree_file(self, tmp_path):
        # A worktree uses a `.git` FILE, not a directory; the engine must
        # accept both (see CLAUDE.md gotcha).
        (tmp_path / ".git").write_text("gitdir: /somewhere/.git/worktrees/x\n")
        ok, _ = validate_target(tmp_path)
        assert ok is True
