#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""VCS provider enumeration.

This module provides the VCS provider enum. GitHub is the only supported provider.
"""

from enum import Enum


class VCSProvider(Enum):
    """Supported VCS providers."""

    GITHUB = "github"
