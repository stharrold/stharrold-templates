#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
# conftest.py - Shared pytest fixtures for stharrold-templates
"""Shared pytest fixtures and configuration."""

from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(repo_root: Path) -> Path:
    """Return the test data directory."""
    data_dir = repo_root / "tests" / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir
