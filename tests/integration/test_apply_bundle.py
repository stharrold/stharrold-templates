# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Integration tests for scripts/apply_bundle.py."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path("/Users/stharrold/Documents/GitHub/stharrold-templates")
SCRIPT = REPO_ROOT / "scripts" / "apply_bundle.py"


@pytest.fixture()
def target_repo(tmp_path):
    """Create a temporary git repository."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    return tmp_path


def run_apply(target: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """Run apply_bundle.py with REPO_ROOT as source."""
    return subprocess.run(
        ["python", str(SCRIPT), str(REPO_ROOT), str(target), *extra_args],
        capture_output=True,
        text=True,
    )


@pytest.mark.integration
def test_apply_git_bundle_to_empty_repo(target_repo):
    """Applying the git bundle copies skills, commands, docs, and .gitignore."""
    result = run_apply(target_repo, "--bundle", "git")
    assert result.returncode == 0, result.stderr

    assert (target_repo / ".claude" / "skills" / "git-workflow-manager").is_dir()
    assert (target_repo / ".claude" / "skills" / "workflow-orchestrator").is_dir()
    assert (target_repo / ".claude" / "skills" / "workflow-utilities").is_dir()
    assert (target_repo / ".claude" / "commands" / "workflow").is_dir()
    assert (target_repo / "WORKFLOW.md").exists()
    assert (target_repo / "CONTRIBUTING.md").exists()

    gitignore = target_repo / ".gitignore"
    assert gitignore.exists()
    assert ".claude-state/" in gitignore.read_text()


@pytest.mark.integration
def test_apply_secrets_bundle_copies_scripts(target_repo):
    """Applying the secrets bundle copies script files and secrets.toml."""
    result = run_apply(target_repo, "--bundle", "secrets")
    assert result.returncode == 0, result.stderr

    assert (target_repo / "scripts" / "secrets_setup.py").exists()
    assert (target_repo / "scripts" / "secrets_run.py").exists()
    assert (target_repo / "scripts" / "environment_utils.py").exists()
    assert (target_repo / "secrets.toml").exists()


@pytest.mark.integration
def test_apply_multiple_bundles(target_repo):
    """Applying multiple bundles in one invocation installs items from each."""
    result = run_apply(target_repo, "--bundle", "git", "--bundle", "secrets")
    assert result.returncode == 0, result.stderr

    # From git bundle
    assert (target_repo / ".claude" / "skills" / "git-workflow-manager").is_dir()
    # From secrets bundle
    assert (target_repo / "scripts" / "secrets_setup.py").exists()


@pytest.mark.integration
def test_update_replaces_template_owned_files(target_repo):
    """Re-applying a bundle replaces template-owned directories entirely."""
    result1 = run_apply(target_repo, "--bundle", "git")
    assert result1.returncode == 0, result1.stderr

    # Plant a marker file inside a template-owned skill directory
    marker = target_repo / ".claude" / "skills" / "git-workflow-manager" / "MARKER.txt"
    marker.write_text("I should be removed on re-apply")

    result2 = run_apply(target_repo, "--bundle", "git")
    assert result2.returncode == 0, result2.stderr

    # The marker should be gone because the directory was replaced
    assert not marker.exists()


@pytest.mark.integration
def test_update_preserves_user_owned_pyproject(target_repo):
    """Applying secrets merges deps into an existing pyproject.toml without removing user content."""
    pyproject = target_repo / "pyproject.toml"
    pyproject.write_text('[project]\nname = "my-project"\nversion = "1.0.0"\nrequires-python = ">=3.11"\n\n[dependency-groups]\ndev = [\n    "my-custom-dep>=1.0",\n]\n')

    result = run_apply(target_repo, "--bundle", "secrets")
    assert result.returncode == 0, result.stderr

    content = pyproject.read_text()
    assert "my-custom-dep" in content
    assert "keyring" in content


@pytest.mark.integration
def test_secrets_toml_skipped_on_update(target_repo):
    """On second apply, secrets.toml is skipped (not overwritten) without --force."""
    result1 = run_apply(target_repo, "--bundle", "secrets")
    assert result1.returncode == 0, result1.stderr

    secrets_toml = target_repo / "secrets.toml"
    secrets_toml.write_text("# custom\n")

    result2 = run_apply(target_repo, "--bundle", "secrets")
    assert result2.returncode == 0, result2.stderr

    assert "# custom" in secrets_toml.read_text()
    assert "SKIP" in result2.stdout


@pytest.mark.integration
def test_force_overwrites_user_owned_files(target_repo):
    """With --force, skip-on-update files are replaced."""
    result1 = run_apply(target_repo, "--bundle", "secrets")
    assert result1.returncode == 0, result1.stderr

    secrets_toml = target_repo / "secrets.toml"
    secrets_toml.write_text("# custom\n")

    result2 = run_apply(target_repo, "--bundle", "secrets", "--force")
    assert result2.returncode == 0, result2.stderr

    assert "# custom" not in secrets_toml.read_text()
