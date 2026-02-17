# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""FK pattern matching for relationship discovery.

This is a skip-on-update file -- customize patterns for your domain.

Each pattern implements the FKPattern interface:
    match(col_name, target_name, pk_cols, source_name) -> list[FKCandidate]

Built-in patterns:
    SameNamePattern     -- FK column name matches PK column name exactly
    EntityNamePattern   -- FK column = EntityName + "_ID" (e.g. Patient_ID)
    PrefixPattern       -- FK column has table prefix (e.g. ord_ProductID)
    SuffixPattern       -- FK column has standard suffix (_id, _key, _sk)
    CompositePattern    -- Multi-column FK where all columns match PK
    DomainSpecificPattern -- CUSTOMIZE: your domain-specific mappings
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod

from data_catalog.services.fk_discovery import FKCandidate

logger = logging.getLogger(__name__)


def _normalize_col(name: str) -> str:
    """Normalize column name: spaces -> underscores, uppercase."""
    return name.replace(" ", "_").upper()


class FKPattern(ABC):
    """Abstract base class for FK matching patterns."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def match(
        self,
        col_name: str,
        target_name: str,
        pk_cols: list[str],
        source_name: str,
    ) -> list[FKCandidate]:
        """Test if col_name in source matches a PK in target.

        Args:
            col_name: Column name in the source (FK) table.
            target_name: Qualified name of the target (PK) table.
            pk_cols: PK column names of the target table.
            source_name: Qualified name of the source (FK) table.

        Returns:
            List of FKCandidate matches (empty if no match).
        """
        ...


class SameNamePattern(FKPattern):
    """FK column name matches PK column name exactly (or normalized)."""

    @property
    def name(self) -> str:
        return "same_name"

    def match(self, col_name, target_name, pk_cols, source_name):
        matches = []
        norm_col = _normalize_col(col_name)
        for pk_col in pk_cols:
            if col_name == pk_col:
                matches.append(
                    FKCandidate(
                        parent_view=source_name,
                        parent_columns=[col_name],
                        referenced_view=target_name,
                        referenced_columns=[pk_col],
                        pattern_name=self.name,
                        priority=1,
                        confidence=0.9,
                        evidence={"match_type": "exact_name"},
                    )
                )
            elif _normalize_col(pk_col) == norm_col:
                matches.append(
                    FKCandidate(
                        parent_view=source_name,
                        parent_columns=[col_name],
                        referenced_view=target_name,
                        referenced_columns=[pk_col],
                        pattern_name=self.name,
                        priority=2,
                        confidence=0.7,
                        evidence={"match_type": "normalized_name"},
                    )
                )
        return matches


class EntityNamePattern(FKPattern):
    """FK column = EntityName + suffix (e.g. Patient_ID -> Patient.PatientID).
    """

    _SUFFIXES = ["_ID", "_KEY", "_SK", "_SID", "ID", "Key"]

    @property
    def name(self) -> str:
        return "entity_name"

    def match(self, col_name, target_name, pk_cols, source_name):
        matches = []
        norm_col = _normalize_col(col_name)
        # Extract entity name from target (last part after '.')
        entity = (
            target_name.split(".")[-1].replace("[", "").replace("]", "")
        )
        norm_entity = _normalize_col(entity)

        for suffix in self._SUFFIXES:
            expected = norm_entity + suffix.upper()
            if norm_col == expected:
                # Match FK column to first PK column
                if pk_cols:
                    matches.append(
                        FKCandidate(
                            parent_view=source_name,
                            parent_columns=[col_name],
                            referenced_view=target_name,
                            referenced_columns=[pk_cols[0]],
                            pattern_name=self.name,
                            priority=2,
                            confidence=0.8,
                            evidence={
                                "entity": entity,
                                "suffix": suffix,
                            },
                        )
                    )
                break
        return matches


class PrefixPattern(FKPattern):
    """FK column has table prefix (e.g. ord_ProductID, customer_name)."""

    @property
    def name(self) -> str:
        return "prefix"

    def match(self, col_name, target_name, pk_cols, source_name):
        matches = []
        norm_col = _normalize_col(col_name)
        for pk_col in pk_cols:
            norm_pk = _normalize_col(pk_col)
            if norm_col.endswith("_" + norm_pk) or norm_col.endswith(
                norm_pk
            ):
                if norm_col != norm_pk:  # Avoid SameNamePattern overlap
                    matches.append(
                        FKCandidate(
                            parent_view=source_name,
                            parent_columns=[col_name],
                            referenced_view=target_name,
                            referenced_columns=[pk_col],
                            pattern_name=self.name,
                            priority=3,
                            confidence=0.6,
                            evidence={"prefix_match": True},
                        )
                    )
        return matches


class SuffixPattern(FKPattern):
    """FK column has standard suffix matching PK naming convention."""

    _ID_RE = re.compile(r"^(.+?)_?(ID|KEY|SK|SID)$", re.IGNORECASE)

    @property
    def name(self) -> str:
        return "suffix"

    def match(self, col_name, target_name, pk_cols, source_name):
        matches = []
        m = self._ID_RE.match(col_name)
        if not m:
            return matches

        stem = _normalize_col(m.group(1))
        entity = (
            target_name.split(".")[-1].replace("[", "").replace("]", "")
        )
        norm_entity = _normalize_col(entity)

        if stem == norm_entity or norm_entity.startswith(stem):
            if pk_cols:
                matches.append(
                    FKCandidate(
                        parent_view=source_name,
                        parent_columns=[col_name],
                        referenced_view=target_name,
                        referenced_columns=[pk_cols[0]],
                        pattern_name=self.name,
                        priority=3,
                        confidence=0.5,
                        evidence={"stem": stem, "entity": entity},
                    )
                )
        return matches


class CompositePattern(FKPattern):
    """Multi-column FK where all PK columns appear in source."""

    @property
    def name(self) -> str:
        return "composite"

    def match(self, col_name, target_name, pk_cols, source_name):
        # Composite patterns are checked at the asset level, not per-column
        return []

    def match_composite(
        self,
        source_columns: list[str],
        target_name: str,
        pk_cols: list[str],
        source_name: str,
    ) -> list[FKCandidate]:
        """Match when ALL PK columns of target exist in source."""
        if len(pk_cols) < 2:
            return []

        norm_source = {_normalize_col(c): c for c in source_columns}
        mappings = []
        for pk_col in pk_cols:
            norm_pk = _normalize_col(pk_col)
            if norm_pk in norm_source:
                mappings.append((norm_source[norm_pk], pk_col))

        if len(mappings) == len(pk_cols):
            return [
                FKCandidate(
                    parent_view=source_name,
                    parent_columns=[m[0] for m in mappings],
                    referenced_view=target_name,
                    referenced_columns=[m[1] for m in mappings],
                    pattern_name=self.name,
                    priority=1,
                    confidence=0.85,
                    evidence={
                        "composite_match": True,
                        "key_width": len(pk_cols),
                    },
                )
            ]
        return []


# CUSTOMIZE: Replace this with your domain-specific FK mappings.
# This example shows e-commerce patterns (Customer, Order, Product, etc.).
class DomainSpecificPattern(FKPattern):
    """Domain-specific FK pattern matching.

    CUSTOMIZE: Map column names to known reference tables for your domain.
    This example uses e-commerce patterns:
        customer_id -> Customers table
        order_id    -> Orders table
        product_id  -> Products table
    """

    # CUSTOMIZE: Add your domain-specific column -> table mappings
    DOMAIN_MAPPINGS: dict[str, str] = {
        "CUSTOMER_ID": "Customers",
        "ORDER_ID": "Orders",
        "PRODUCT_ID": "Products",
        "CATEGORY_ID": "Categories",
        "SUPPLIER_ID": "Suppliers",
    }

    @property
    def name(self) -> str:
        return "domain_specific"

    def match(self, col_name, target_name, pk_cols, source_name):
        matches = []
        norm_col = _normalize_col(col_name)
        entity = (
            target_name.split(".")[-1].replace("[", "").replace("]", "")
        )

        expected_table = self.DOMAIN_MAPPINGS.get(norm_col)
        if expected_table and _normalize_col(entity) == _normalize_col(
            expected_table
        ):
            if pk_cols:
                matches.append(
                    FKCandidate(
                        parent_view=source_name,
                        parent_columns=[col_name],
                        referenced_view=target_name,
                        referenced_columns=[pk_cols[0]],
                        pattern_name=self.name,
                        priority=1,
                        confidence=0.95,
                        evidence={"domain_mapping": expected_table},
                    )
                )
        return matches


class FKPatternRegistry:
    """Registry for FK matching patterns.

    IMPORTANT: Constructor does NOT auto-register patterns.
    Call ``register_defaults()`` explicitly after creation.
    """

    def __init__(self) -> None:
        self._patterns: list[FKPattern] = []

    def register(self, pattern: FKPattern) -> None:
        self._patterns.append(pattern)

    def register_defaults(self) -> None:
        """Register the built-in patterns."""
        self._patterns = [
            SameNamePattern(),
            EntityNamePattern(),
            PrefixPattern(),
            SuffixPattern(),
            CompositePattern(),
            DomainSpecificPattern(),
        ]

    def get_patterns(self) -> list[FKPattern]:
        return self._patterns
