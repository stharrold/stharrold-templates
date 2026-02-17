# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""SQLAlchemy models for the metadata repository.

All 14 tables for the enterprise data catalog: assets, relationships,
lineage, cardinality history, value frequencies, column vectors,
pipeline logs, glossary, data quality, audit, search index, and
user interactions.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
    TypeDecorator,
)
from sqlalchemy.orm import declarative_base, relationship, backref

Base = declarative_base()


class DuckDBBit(TypeDecorator):
    """Custom type for DuckDB BIT type (binary-quantized vectors)."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(String)

    def compile(self, dialect=None):
        return "BIT"


class Asset(Base):
    """Core asset metadata for discovered tables/views.

    Stores both technical metadata (schema, columns, statistics) and
    business metadata (owner, domain, tags, sensitivity) in JSON
    for schema-evolution resilience.

    Key schema_metadata fields:
        columns: list[dict]       -- column definitions
        primary_key: list[str]    -- PK column names (business PK)
        pk_minimal: list[str]     -- FD-minimized architectural PK
        fd_removed: list[str]     -- columns removed by FD analysis
        grain_status: str         -- "confirmed" | "no_natural_pk" | "unknown"
        grain_source: str         -- discovery method description
        pk_discovery: dict        -- discovery metadata
    """

    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    qualified_name = Column(String(500), unique=True, nullable=False, index=True)
    source_system = Column(String(100), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False, index=True)
    table_schema = Column(String(255), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(200))
    description = Column(Text)

    # JSON for schema flexibility
    schema_metadata = Column(JSON)
    statistics = Column(JSON)
    business_metadata = Column(JSON)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_discovered_at = Column(DateTime)

    # Relationships
    parent_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.parent_asset_id",
        back_populates="parent_asset",
        cascade="all, delete-orphan",
    )
    referenced_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.referenced_asset_id",
        back_populates="referenced_asset",
    )
    upstream_lineage = relationship(
        "Lineage",
        foreign_keys="Lineage.upstream_asset_id",
        back_populates="upstream_asset",
    )
    downstream_lineage = relationship(
        "Lineage",
        foreign_keys="Lineage.downstream_asset_id",
        back_populates="downstream_asset",
    )
    glossary_terms = relationship(
        "GlossaryTerm",
        secondary="asset_glossary_terms",
        back_populates="assets",
    )
    dq_rules = relationship(
        "DataQualityRule",
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    interactions = relationship(
        "UserInteraction",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, qualified_name='{self.qualified_name}')>"


class Relationship(Base):
    """Primary key and foreign key relationships.

    Supports declared, implicit (naming conventions), and inferred
    relationships. Handles composite keys with column_mappings JSON.
    """

    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    parent_asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    referenced_asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    constraint_name = Column(String(255))
    relationship_type = Column(String(50), nullable=False, index=True)

    # JSON for composite key support
    column_mappings = Column(JSON, nullable=False)

    is_composite = Column(Boolean, nullable=False, default=False)
    cardinality = Column(String(10))  # '1:1', '1:N', 'N:M'
    on_delete = Column(String(50))
    on_update = Column(String(50))

    # For implicit/inferred relationships
    confidence_score = Column(Numeric(3, 2))
    value_overlap_pct = Column(Numeric(5, 2))
    integrity_violations = Column(Integer, default=0)
    is_validated = Column(Boolean, default=False)

    discovered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_validated_at = Column(DateTime)

    # Relationships
    parent_asset = relationship(
        "Asset",
        foreign_keys=[parent_asset_id],
        back_populates="parent_relationships",
    )
    referenced_asset = relationship(
        "Asset",
        foreign_keys=[referenced_asset_id],
        back_populates="referenced_relationships",
    )

    def __repr__(self):
        return (
            f"<Relationship(id={self.id}, type='{self.relationship_type}', "
            f"cardinality='{self.cardinality}')>"
        )


class Lineage(Base):
    """Data lineage tracking for dependency graphs."""

    __tablename__ = "lineage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    upstream_asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    downstream_asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    relationship_type = Column(String(50), nullable=False)
    transformation_logic = Column(Text)
    confidence_score = Column(Numeric(3, 2))
    discovered_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    upstream_asset = relationship(
        "Asset",
        foreign_keys=[upstream_asset_id],
        back_populates="upstream_lineage",
    )
    downstream_asset = relationship(
        "Asset",
        foreign_keys=[downstream_asset_id],
        back_populates="downstream_lineage",
    )

    def __repr__(self):
        return f"<Lineage(id={self.id}, type='{self.relationship_type}')>"


class ColumnCardinalityHistory(Base):
    """Column cardinality history from PK discovery progression.

    Stores cardinality data collected during the 7-step progressive scanning
    algorithm. Enables FK discovery by tracking how cardinality evolves
    through sampling levels.
    """

    __tablename__ = "column_cardinality_history"

    cardinality_id = Column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    table_schema = Column(String(255), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    column_name = Column(String(255), nullable=False, index=True)
    ordinal_position = Column(Integer, nullable=False)

    # Cardinality at each sample level (step 1-7)
    cardinality_at_0x1pct = Column(BigInteger)
    cardinality_at_0x3pct = Column(BigInteger)
    cardinality_at_1pct = Column(BigInteger)
    cardinality_at_3pct = Column(BigInteger)
    cardinality_at_10pct = Column(BigInteger)
    cardinality_at_30pct = Column(BigInteger)
    cardinality_at_100pct = Column(BigInteger)

    # Selectivity at each sample level
    selectivity_at_0x1pct = Column(Numeric(precision=12, scale=2))
    selectivity_at_0x3pct = Column(Numeric(precision=12, scale=2))
    selectivity_at_1pct = Column(Numeric(precision=12, scale=2))
    selectivity_at_3pct = Column(Numeric(precision=12, scale=2))
    selectivity_at_10pct = Column(Numeric(precision=12, scale=2))
    selectivity_at_30pct = Column(Numeric(precision=12, scale=2))
    selectivity_at_100pct = Column(Numeric(precision=12, scale=2))

    # Metadata
    discovered_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    discovery_method = Column(String(50), nullable=False)
    data_type = Column(String(100))
    total_rows = Column(BigInteger)
    pk_priority = Column(Integer)
    eliminated_at_step = Column(Integer, index=True)
    elimination_reason = Column(Text)

    asset = relationship("Asset", backref="cardinality_history")

    def __repr__(self):
        return (
            f"<ColumnCardinalityHistory(column='{self.column_name}', "
            f"card_100pct={self.cardinality_at_100pct})>"
        )


class ColumnValueFrequency(Base):
    """Top value frequencies for FK discovery.

    Stores top 100 values per column with their frequencies.
    Used to match FK candidates by comparing value distributions.
    """

    __tablename__ = "column_value_frequencies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    table_schema = Column(String(255), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    column_name = Column(String(255), nullable=False, index=True)

    rank = Column(Integer, nullable=False)
    value = Column(String(255))
    frequency = Column(BigInteger, nullable=False)
    relative_frequency = Column(Numeric(precision=10, scale=6))

    sample_pct = Column(Numeric(precision=5, scale=2))
    total_rows = Column(BigInteger)
    discovered_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )

    asset = relationship("Asset", backref="value_frequencies")

    __table_args__ = (
        Index(
            "ix_value_freq_lookup",
            "table_schema",
            "table_name",
            "column_name",
            "rank",
        ),
    )

    def __repr__(self):
        return (
            f"<ColumnValueFrequency(column='{self.column_name}', "
            f"rank={self.rank}, value='{self.value}')>"
        )


class AuditLog(Base):
    """Audit logging with configurable retention.

    Append-only table (no DELETE/UPDATE except automated archival).
    """

    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("assets.id"), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    additional_context = Column(JSON)

    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, user='{self.user_email}', "
            f"action='{self.action}')>"
        )


class ColumnVector(Base):
    """Vector embeddings for column value distributions.

    Enables FK discovery via vector similarity search and semantic
    retrieval. Stores 384-dim binary-quantized + float vectors.
    """

    __tablename__ = "column_vectors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    table_schema = Column(String(255), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    column_name = Column(String(255), nullable=False, index=True)

    # Binary-quantized vector (384-bit)
    vector_bits = Column(DuckDBBit, nullable=True)

    # UBIGINT decomposition for SIMD Hamming distance (6 x 64-bit chunks)
    bit_u0 = Column(BigInteger, nullable=True)
    bit_u1 = Column(BigInteger, nullable=True)
    bit_u2 = Column(BigInteger, nullable=True)
    bit_u3 = Column(BigInteger, nullable=True)
    bit_u4 = Column(BigInteger, nullable=True)
    bit_u5 = Column(BigInteger, nullable=True)
    bit_popcnt = Column(Integer, nullable=True)

    # HDBSCAN cluster assignment (-1 = noise)
    cluster_id = Column(Integer, nullable=True)

    # Float vector for cosine similarity (JSON)
    value_vector = Column(JSON, nullable=True)

    # Metadata
    vector_type = Column(String(50), nullable=False)
    num_values = Column(Integer)
    total_frequency = Column(BigInteger)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    asset = relationship("Asset", backref="column_vectors")

    __table_args__ = (
        Index(
            "ix_column_vectors_lookup",
            "table_schema",
            "table_name",
            "column_name",
            "vector_type",
            unique=True,
        ),
    )

    def __repr__(self):
        return (
            f"<ColumnVector(column='{self.column_name}', "
            f"bits_len={len(self.vector_bits) if self.vector_bits else 0})>"
        )


class PipelinePhaseLog(Base):
    """Log of individual pipeline phase executions.

    Enables per-phase commit and resume-from-failure.
    """

    __tablename__ = "pipeline_phase_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String(36), nullable=False, index=True)
    schema_pattern = Column(String(255), nullable=False)
    phase_name = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Numeric(10, 2))
    rows_affected = Column(Integer)
    items_processed = Column(Integer)
    error_detail = Column(JSON)

    def __repr__(self):
        return (
            f"<PipelinePhaseLog(run_id='{self.run_id}', "
            f"phase='{self.phase_name}', status='{self.status}')>"
        )


class AssetGlossaryTerm(Base):
    """Association table for Many-to-Many: Assets <-> GlossaryTerms."""

    __tablename__ = "asset_glossary_terms"

    asset_id = Column(String(36), ForeignKey("assets.id"), primary_key=True)
    term_id = Column(String(36), ForeignKey("glossary_terms.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GlossaryTerm(Base):
    """Business glossary term linked to technical assets."""

    __tablename__ = "glossary_terms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    term = Column(String(255), nullable=False, unique=True, index=True)
    definition = Column(Text, nullable=False)
    domain = Column(String(100), index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assets = relationship(
        "Asset", secondary="asset_glossary_terms", back_populates="glossary_terms"
    )

    def __repr__(self):
        return f"<GlossaryTerm(term='{self.term}', domain='{self.domain}')>"


class DataQualityRule(Base):
    """Data quality rule definition."""

    __tablename__ = "dq_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    column_name = Column(String(255), nullable=True)
    rule_type = Column(String(50), nullable=False)
    rule_definition = Column(JSON, nullable=False)
    severity = Column(String(20), default="warning")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    asset = relationship("Asset", back_populates="dq_rules")
    results = relationship(
        "DataQualityResult", backref="rule", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<DataQualityRule(type='{self.rule_type}', "
            f"asset_id='{self.asset_id}')>"
        )


class DataQualityResult(Base):
    """Data quality rule execution result."""

    __tablename__ = "dq_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    rule_id = Column(
        String(36), ForeignKey("dq_rules.id"), nullable=False, index=True
    )
    execution_date = Column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    status = Column(String(20), nullable=False)
    actual_value = Column(Numeric)
    expected_value = Column(Numeric)
    row_count_failed = Column(Integer)
    error_message = Column(Text)

    def __repr__(self):
        return (
            f"<DataQualityResult(rule_id='{self.rule_id}', "
            f"status='{self.status}')>"
        )


class UserInteraction(Base):
    """User collaboration and feedback."""

    __tablename__ = "user_interactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    user_id = Column(String(255), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False)
    content = Column(Text)
    rating_score = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="interactions")

    def __repr__(self):
        return (
            f"<UserInteraction(type='{self.interaction_type}', "
            f"user='{self.user_id}')>"
        )


class SearchIndexColumn(Base):
    """Flattened column data for optimized search.

    Populated from Asset.schema_metadata for fast SQL queries on columns.
    """

    __tablename__ = "search_columns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id = Column(
        String(36), ForeignKey("assets.id"), nullable=False, index=True
    )
    table_schema = Column(String(255), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    column_name = Column(String(255), nullable=False, index=True)
    data_type = Column(String(50))
    ordinal_position = Column(Integer)
    description = Column(Text)

    asset = relationship(
        "Asset",
        backref=backref("search_columns", cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return (
            f"<SearchIndexColumn(column='{self.column_name}', "
            f"asset_id='{self.asset_id}')>"
        )
