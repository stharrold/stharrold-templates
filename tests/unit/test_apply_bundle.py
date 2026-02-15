# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for scripts/apply_bundle.py."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from apply_bundle import BUNDLE_DEFINITIONS, resolve_bundles


def test_apply_bundle_help_exits_zero():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "apply_bundle.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "bundle" in result.stdout.lower()


def test_bundle_definitions_have_required_keys():
    """Every bundle has at least: skills, commands, copy_files, merge_pyproject_deps.
    The 'full' bundle also has 'includes'."""
    required_keys = {"skills", "commands", "copy_files", "merge_pyproject_deps"}
    for name, defn in BUNDLE_DEFINITIONS.items():
        for key in required_keys:
            assert key in defn, f"Bundle {name!r} missing required key {key!r}"
            assert isinstance(defn[key], list), f"Bundle {name!r} key {key!r} should be a list"
    # full bundle must have includes
    assert "includes" in BUNDLE_DEFINITIONS["full"]
    assert isinstance(BUNDLE_DEFINITIONS["full"]["includes"], list)


def test_full_bundle_includes_all_others():
    """The 'full' bundle's 'includes' list contains exactly ['git', 'secrets', 'ci']."""
    assert BUNDLE_DEFINITIONS["full"]["includes"] == ["git", "secrets", "ci"]


def test_all_referenced_paths_exist():
    """Every path referenced in bundle definitions actually exists in the source repo."""
    for name, defn in BUNDLE_DEFINITIONS.items():
        # Skills -> .claude/skills/{skill}/
        for skill in defn.get("skills", []):
            skill_dir = REPO_ROOT / ".claude" / "skills" / skill
            assert skill_dir.exists(), f"Bundle {name!r}: skill dir {skill_dir} does not exist"

        # Commands
        for cmd in defn.get("commands", []):
            cmd_path = REPO_ROOT / cmd
            assert cmd_path.exists(), f"Bundle {name!r}: command path {cmd_path} does not exist"

        # Copy files
        for f in defn.get("copy_files", []):
            file_path = REPO_ROOT / f
            assert file_path.exists(), f"Bundle {name!r}: copy_file {file_path} does not exist"

        # Skip on update
        for f in defn.get("skip_on_update", []):
            file_path = REPO_ROOT / f
            assert file_path.exists(), f"Bundle {name!r}: skip_on_update {file_path} does not exist"

        # Copy dirs
        for d in defn.get("copy_dirs", []):
            dir_path = REPO_ROOT / d
            assert dir_path.exists(), f"Bundle {name!r}: copy_dir {dir_path} does not exist"


def test_no_overlapping_skills_between_non_full_bundles():
    """The 'secrets' and 'ci' bundles have empty skills lists.
    No skill appears in more than one non-'full' bundle."""
    non_full = {k: v for k, v in BUNDLE_DEFINITIONS.items() if k != "full"}
    assert BUNDLE_DEFINITIONS["secrets"]["skills"] == []
    assert BUNDLE_DEFINITIONS["ci"]["skills"] == []

    seen_skills: dict[str, str] = {}
    for name, defn in non_full.items():
        for skill in defn.get("skills", []):
            assert skill not in seen_skills, f"Skill {skill!r} appears in both {seen_skills[skill]!r} and {name!r}"
            seen_skills[skill] = name


def test_dry_run_makes_no_changes(tmp_path):
    """Create a tmp git repo, run apply_bundle.py with --dry-run --bundle git,
    verify the target is unchanged (no .claude/ dir created)."""
    # Initialize a bare git repo in tmp_path
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/apply_bundle.py",
            str(REPO_ROOT),
            str(tmp_path),
            "--bundle",
            "git",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"apply_bundle.py failed: {result.stderr}"
    assert not (tmp_path / ".claude").exists(), ".claude/ dir should not be created in dry-run mode"


def test_resolve_bundles_expands_full():
    """resolve_bundles(['full']) returns ['git', 'secrets', 'ci', 'full']."""
    resolved = resolve_bundles(["full"])
    assert resolved == ["git", "secrets", "ci", "full"]


def test_resolve_bundles_deduplicates():
    """resolve_bundles(['git', 'full']) should contain 'git' only once."""
    resolved = resolve_bundles(["git", "full"])
    assert resolved.count("git") == 1
    # Should still contain all expected bundles
    assert set(resolved) == {"git", "secrets", "ci", "full"}
