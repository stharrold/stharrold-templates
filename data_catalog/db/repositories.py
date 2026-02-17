# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Repository pattern for data access layer."""

from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from data_catalog.db.models import Asset, AuditLog, Lineage, Relationship


class AssetRepository:
    """Repository for asset CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, asset_id: UUID) -> Asset | None:
        return self.db.query(Asset).filter(Asset.id == asset_id).first()

    def find_by_qualified_name(self, qualified_name: str) -> Asset | None:
        return (
            self.db.query(Asset)
            .filter(Asset.qualified_name == qualified_name)
            .first()
        )

    def find_by_schema_pattern(self, pattern: str) -> list[Asset]:
        """Find assets matching schema pattern (SQL LIKE syntax)."""
        return (
            self.db.query(Asset)
            .filter(Asset.qualified_name.like(f"[{pattern}]%"))
            .order_by(Asset.qualified_name)
            .all()
        )

    def find_all(
        self,
        limit: int | None = None,
        offset: int = 0,
        asset_type: str | None = None,
    ) -> list[Asset]:
        query = self.db.query(Asset)

        if asset_type:
            query = query.filter(Asset.asset_type == asset_type)

        query = query.order_by(Asset.qualified_name)

        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def create(self, asset: Asset) -> Asset:
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def update(self, asset: Asset) -> Asset:
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete(self, asset: Asset) -> None:
        self.db.delete(asset)
        self.db.commit()

    def upsert(self, asset: Asset) -> Asset:
        """Insert or update asset by qualified_name."""
        existing = self.find_by_qualified_name(asset.qualified_name)

        if existing:
            existing.display_name = asset.display_name
            existing.description = asset.description
            existing.schema_metadata = asset.schema_metadata
            existing.statistics = asset.statistics
            existing.business_metadata = asset.business_metadata
            existing.last_discovered_at = asset.last_discovered_at
            existing.search_columns = asset.search_columns
            return self.update(existing)
        else:
            return self.create(asset)


class RelationshipRepository:
    """Repository for relationship CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def find_by_asset(self, asset_id: UUID) -> list[Relationship]:
        return (
            self.db.query(Relationship)
            .filter(
                or_(
                    Relationship.parent_asset_id == asset_id,
                    Relationship.referenced_asset_id == asset_id,
                )
            )
            .all()
        )

    def find_foreign_keys(self, parent_asset_id: UUID) -> list[Relationship]:
        return (
            self.db.query(Relationship)
            .filter(Relationship.parent_asset_id == parent_asset_id)
            .all()
        )

    def find_primary_keys(self, referenced_asset_id: UUID) -> list[Relationship]:
        return (
            self.db.query(Relationship)
            .filter(Relationship.referenced_asset_id == referenced_asset_id)
            .all()
        )

    def create(self, rel: Relationship) -> Relationship:
        self.db.add(rel)
        self.db.commit()
        self.db.refresh(rel)
        return rel

    def create_batch(self, relationships: list[Relationship]) -> list[Relationship]:
        self.db.add_all(relationships)
        self.db.commit()
        for rel in relationships:
            self.db.refresh(rel)
        return relationships

    def find_by_constraint_name(self, constraint_name: str) -> Relationship | None:
        return (
            self.db.query(Relationship)
            .filter(Relationship.constraint_name == constraint_name)
            .first()
        )


class LineageRepository:
    """Repository for lineage CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def find_upstream(self, asset_id: UUID, depth: int = 3) -> list[Lineage]:
        return (
            self.db.query(Lineage)
            .filter(Lineage.downstream_asset_id == asset_id)
            .all()
        )

    def find_downstream(self, asset_id: UUID, depth: int = 3) -> list[Lineage]:
        return (
            self.db.query(Lineage)
            .filter(Lineage.upstream_asset_id == asset_id)
            .all()
        )

    def create(self, lineage: Lineage) -> Lineage:
        self.db.add(lineage)
        self.db.commit()
        self.db.refresh(lineage)
        return lineage


class AuditLogRepository:
    """Repository for audit log operations (append-only)."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, audit_log: AuditLog) -> AuditLog:
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def find_by_user(
        self, user_email: str, limit: int = 100, offset: int = 0
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_email == user_email)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def find_by_asset(
        self, asset_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.asset_id == asset_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def find_by_action(
        self, action: str, limit: int = 100, offset: int = 0
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.action == action)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
