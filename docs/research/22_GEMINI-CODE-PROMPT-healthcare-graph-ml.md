# Gemini Code Prompt: Air-Gapped Healthcare Graph ML Integration

## Project Context

Build a bidirectional meta-graph-database for healthcare analytics that:

1. Ingests relational healthcare data into a semantic graph (PostgreSQL + Apache AGE)
2. Trains GNNs to predict eigen-patterns across the graph
3. Feeds predictions back into the graph as enriched properties
4. Uses DSPy/GEPA/BAML for LLM-powered semantic reasoning

CRITICAL CONSTRAINT: Air-gapped deployment. Zero external network calls. All components self-hosted.

## Technology Stack

| Layer | Component | Purpose |
|-------|-----------|---------|
| Data | PostgreSQL 17 + Apache AGE | Unified relational-graph storage |
| Data | pgvector | Node/edge embeddings with HNSW |
| Data | PostgresML | In-database ML inference |
| GNN | PyTorch Geometric or DGL | Graph neural network training |
| GNN | MLflow (self-hosted) | Model registry and versioning |
| Semantic | DSPy | Modular LLM programming |
| Semantic | GEPA | Prompt optimization via reflection |
| Semantic | BAML | Type-safe structured extraction |
| Semantic | Ollama | Local LLM inference |
| Standards | CQL Engine | Clinical quality measure execution |
| Standards | FHIR JSON-LD | Semantic web integration |
| Standards | OMOP CDM v5.4 | Research analytics model |
| Methodology | BMAD | Agent-driven development |
| Methodology | Speckit | Specification management |

## Prediction Targets

The meta-graph must predict five categories:

### 1. Healthcare Entity Standardization
- Input: Raw column names, sample values, table context
- Output: FHIR resource type, OMOP domain, standard terminology codes
- Standards: SNOMED-CT, ICD-10, LOINC, RxNorm
- Validation: Local Athena vocabulary cache

### 2. Schema Inference (PK/FK/Relationships)
- Input: Table schemas, sample data, existing graph structure
- Output: Primary key candidates, foreign key relationships, edge type predictions
- Method: GNN-based schema matching + DSPy reasoning

### 3. Query Routing
- Input: Natural language question
- Output: Optimal data source (CQL engine, FHIR API, OMOP analytics, graph traversal)
- Method: DSPy classifier with GEPA optimization

### 4. Patient Outcome Opportunities
- Input: Patient graph substructure
- Output: Applicable NIH quality measures, intervention recommendations
- Standards: Clinical Quality Language (CQL), eCQM definitions
- Measures: NQF-endorsed, CMS reportable

### 5. System Efficiency Opportunities
- Input: Encounter patterns, utilization data
- Output: AHRQ Quality Indicators (PQI, IQI, PSI), resource optimization
- Standards: NIH utilization metrics

## Directory Structure

Create the following structure:

```
healthcare-graph-ml/
|-- .bmad/
|   |-- agents/
|   |   |-- architect.md
|   |   |-- data-engineer.md
|   |   |-- ml-engineer.md
|   |   |-- healthcare-analyst.md
|   |   +-- qa-engineer.md
|   |-- workflows/
|   |   |-- phase-1-data-layer.md
|   |   |-- phase-2-gnn-pipeline.md
|   |   |-- phase-3-semantic-layer.md
|   |   |-- phase-4-standards.md
|   |   +-- phase-5-integration.md
|   +-- checklists/
|       |-- hipaa-compliance.md
|       +-- air-gap-verification.md
|
|-- speckit/
|   |-- constitution.md              # Non-negotiable principles
|   |-- specs/
|   |   |-- entity-standardization.md
|   |   |-- schema-inference.md
|   |   |-- query-routing.md
|   |   |-- patient-outcomes.md
|   |   +-- system-efficiency.md
|   +-- schemas/
|       |-- fhir-graph.jsonld
|       +-- omop-graph.jsonld
|
|-- docker/
|   |-- docker-compose.yml
|   |-- docker-compose.dev.yml
|   |-- postgres/
|   |   |-- Dockerfile
|   |   |-- init-extensions.sql
|   |   +-- postgresql.conf
|   |-- gnn-training/
|   |   |-- Dockerfile
|   |   +-- requirements.txt
|   |-- ollama/
|   |   |-- Dockerfile
|   |   +-- pull-models.sh
|   +-- mlflow/
|       |-- Dockerfile
|       +-- mlflow.conf
|
|-- baml_src/
|   |-- main.baml
|   |-- generators/
|   |   +-- python.baml
|   |-- clients/
|   |   |-- ollama.baml
|   |   +-- local_embeddings.baml
|   |-- types/
|   |   |-- fhir_resources.baml
|   |   |-- omop_entities.baml
|   |   |-- schema_elements.baml
|   |   +-- quality_measures.baml
|   +-- functions/
|       |-- entity_standardization.baml
|       |-- schema_inference.baml
|       |-- query_classification.baml
|       +-- cql_generation.baml
|
|-- dspy_modules/
|   |-- __init__.py
|   |-- config.py
|   |-- modules/
|   |   |-- entity_standardizer.py
|   |   |-- schema_inferencer.py
|   |   |-- query_router.py
|   |   |-- cql_generator.py
|   |   +-- outcome_predictor.py
|   |-- optimizers/
|   |   |-- gepa_healthcare.py
|   |   +-- feedback_metrics.py
|   +-- adapters/
|       |-- baml_adapter.py
|       +-- postgres_adapter.py
|
|-- gnn_training/
|   |-- __init__.py
|   |-- data/
|   |   |-- postgres_loader.py
|   |   |-- graph_builder.py
|   |   +-- feature_encoder.py
|   |-- models/
|   |   |-- entity_classifier.py
|   |   |-- schema_matcher.py
|   |   |-- link_predictor.py
|   |   +-- outcome_predictor.py
|   |-- training/
|   |   |-- trainer.py
|   |   |-- evaluation.py
|   |   +-- hyperparameter_search.py
|   +-- export/
|       |-- model_exporter.py
|       +-- embedding_writer.py
|
|-- healthcare_standards/
|   |-- cql/
|   |   |-- engine_adapter.py
|   |   |-- measure_executor.py
|   |   +-- measures/
|   |       +-- [measure-id].cql
|   |-- fhir/
|   |   |-- jsonld_transformer.py
|   |   |-- graph_builder.py
|   |   +-- contexts/
|   |       +-- fhir-r5.jsonld
|   |-- omop/
|   |   |-- vocabulary_loader.py
|   |   |-- concept_graph.py
|   |   +-- fact_relationship.py
|   +-- quality_measures/
|       |-- nih_definitions.py
|       |-- ahrq_indicators.py
|       +-- measure_calculator.py
|
|-- postgres/
|   |-- init/
|   |   |-- 00-extensions.sql
|   |   |-- 01-schemas.sql
|   |   |-- 02-graphs.sql
|   |   +-- 03-functions.sql
|   |-- schemas/
|   |   |-- fhir_tables.sql
|   |   |-- omop_tables.sql
|   |   |-- meta_graph.sql
|   |   +-- predictions.sql
|   |-- graphs/
|   |   |-- healthcare_graph.sql
|   |   |-- schema_graph.sql
|   |   +-- prediction_graph.sql
|   +-- migrations/
|       +-- README.md
|
|-- config/
|   |-- settings.yaml
|   |-- gepa_optimization.yaml
|   |-- mlflow.yaml
|   |-- vocabulary/
|   |   +-- README.md
|   +-- models/
|       +-- README.md
|
|-- scripts/
|   |-- setup-airgap.sh
|   |-- load-vocabulary.py
|   |-- train-models.py
|   +-- run-predictions.py
|
+-- tests/
    |-- unit/
    |   |-- test_baml_functions.py
    |   |-- test_dspy_modules.py
    |   +-- test_gnn_models.py
    |-- integration/
    |   |-- test_postgres_graph.py
    |   |-- test_prediction_pipeline.py
    |   +-- test_cql_execution.py
    +-- e2e/
        |-- test_entity_standardization.py
        |-- test_schema_inference.py
        +-- test_outcome_prediction.py
```

## Phase 1: Core Data Layer

### Task 1.1: PostgreSQL with Extensions

Create docker/postgres/Dockerfile:

```dockerfile
FROM postgres:17-alpine

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    clang15 \
    llvm15 \
    git \
    cmake \
    readline-dev \
    zlib-dev

# SECURITY WARNING: For production, pin dependencies to specific commit SHAs
# or verified release tags with integrity verification (checksums/signatures).
# Unpinned git clones create supply-chain risk if repos are compromised.

# Install Apache AGE (pin to release tag in production)
RUN git clone --branch release/PG17/1.5.0 --depth 1 https://github.com/apache/age.git /tmp/age && \
    cd /tmp/age && \
    make install

# Install pgvector (pin to release tag in production)
RUN git clone --branch v0.8.0 --depth 1 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && make install

# Copy initialization scripts
COPY init-extensions.sql /docker-entrypoint-initdb.d/
```

Create docker/postgres/init-extensions.sql:

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS age;
CREATE EXTENSION IF NOT EXISTS vector;

-- Load AGE
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create healthcare graph
SELECT create_graph('healthcare');
SELECT create_graph('schema_meta');
SELECT create_graph('predictions');

-- Create embedding tables
CREATE TABLE node_embeddings (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    embedding vector(768),
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_node_embeddings_hnsw
ON node_embeddings USING hnsw (embedding vector_cosine_ops);

-- Prediction storage
CREATE TABLE entity_predictions (
    id SERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,
    source_column TEXT NOT NULL,
    predicted_fhir_type TEXT,
    predicted_omop_domain TEXT,
    confidence FLOAT,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE schema_predictions (
    id SERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,
    predicted_pk TEXT[],
    predicted_fk JSONB,
    predicted_relationships JSONB,
    confidence FLOAT,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Task 1.2: Docker Compose

Create docker/docker-compose.yml:

```yaml
version: '3.8'

services:
  postgres:
    build: ./postgres
    environment:
      POSTGRES_DB: healthcare_graph
      POSTGRES_USER: hgml
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d:ro
    secrets:
      - pg_password
    ports:
      - "5432:5432"
    networks:
      - hgml_network

  ollama:
    build: ./ollama
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    networks:
      - hgml_network

  mlflow:
    build: ./mlflow
    environment:
      MLFLOW_BACKEND_STORE_URI: postgresql://hgml@postgres/mlflow
      MLFLOW_ARTIFACT_ROOT: /mlflow/artifacts
    volumes:
      - mlflow_artifacts:/mlflow/artifacts
    ports:
      - "5000:5000"
    depends_on:
      - postgres
    networks:
      - hgml_network

  gnn-trainer:
    build: ./gnn-training
    volumes:
      - ./gnn_training:/app/gnn_training
      - gnn_models:/app/models
    environment:
      POSTGRES_HOST: postgres
      MLFLOW_TRACKING_URI: http://mlflow:5000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    depends_on:
      - postgres
      - mlflow
    networks:
      - hgml_network

volumes:
  postgres_data:
  ollama_models:
  mlflow_artifacts:
  gnn_models:

networks:
  hgml_network:
    driver: bridge

secrets:
  pg_password:
    file: ./secrets/pg_password.txt
```

## Phase 2: GNN Training Pipeline

### Task 2.1: PostgreSQL Data Loader

Create gnn_training/data/postgres_loader.py:

```python
"""Load healthcare graph data from PostgreSQL with Apache AGE."""

from dataclasses import dataclass
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import torch
from torch_geometric.data import HeteroData
import numpy as np


@dataclass
class GraphConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "healthcare_graph"
    user: str = "hgml"
    password: str = ""
    graph_name: str = "healthcare"


class PostgresGraphLoader:
    """Load graph data from PostgreSQL + Apache AGE into PyG HeteroData."""

    def __init__(self, config: GraphConfig):
        self.config = config
        self.conn = None

    def connect(self) -> None:
        self.conn = psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password
        )
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")

    def load_node_features(
        self,
        node_type: str,
        feature_query: Optional[str] = None
    ) -> tuple[torch.Tensor, dict[str, int]]:
        """Load node features and return tensor + ID mapping."""

        if feature_query is None:
            # Default: load from embeddings table
            feature_query = f"""
                SELECT node_id, embedding
                FROM node_embeddings
                WHERE node_type = '{node_type}'
                ORDER BY node_id
            """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(feature_query)
            rows = cur.fetchall()

        id_map = {row['node_id']: i for i, row in enumerate(rows)}
        features = torch.tensor([row['embedding'] for row in rows])

        return features, id_map

    def load_edges(
        self,
        edge_type: tuple[str, str, str],
        graph_name: Optional[str] = None
    ) -> torch.Tensor:
        """Load edges via Cypher query."""

        graph = graph_name or self.config.graph_name
        src_type, rel_type, dst_type = edge_type

        cypher = f"""
            MATCH (s:{src_type})-[r:{rel_type}]->(d:{dst_type})
            RETURN id(s) as src, id(d) as dst
        """

        query = f"""
            SELECT * FROM cypher('{graph}', $${cypher}$$)
            AS (src agtype, dst agtype)
        """

        with self.conn.cursor() as cur:
            cur.execute(query)
            edges = cur.fetchall()

        edge_index = torch.tensor(
            [[e[0] for e in edges], [e[1] for e in edges]],
            dtype=torch.long
        )

        return edge_index

    def build_hetero_data(
        self,
        node_types: list[str],
        edge_types: list[tuple[str, str, str]]
    ) -> HeteroData:
        """Build complete HeteroData object."""

        data = HeteroData()
        id_maps = {}

        # Load node features
        for node_type in node_types:
            features, id_map = self.load_node_features(node_type)
            data[node_type].x = features
            data[node_type].num_nodes = len(id_map)
            id_maps[node_type] = id_map

        # Load edges
        for edge_type in edge_types:
            edge_index = self.load_edges(edge_type)
            data[edge_type].edge_index = edge_index

        return data

    def close(self) -> None:
        if self.conn:
            self.conn.close()
```

### Task 2.2: Entity Classification GNN

Create gnn_training/models/entity_classifier.py:

```python
"""GNN model for healthcare entity classification."""

import torch
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, SAGEConv, Linear


class EntityClassifier(torch.nn.Module):
    """Classify data elements into FHIR/OMOP entity types."""

    def __init__(
        self,
        metadata: tuple,  # (node_types, edge_types)
        hidden_channels: int = 256,
        num_fhir_classes: int = 150,  # FHIR resource types
        num_omop_classes: int = 37,   # OMOP domains
        num_layers: int = 3
    ):
        super().__init__()

        self.node_types, self.edge_types = metadata
        self.num_layers = num_layers

        # Per-node-type input projections
        self.input_projections = torch.nn.ModuleDict()
        for node_type in self.node_types:
            self.input_projections[node_type] = Linear(-1, hidden_channels)

        # Heterogeneous graph convolutions
        self.convs = torch.nn.ModuleList()
        for _ in range(num_layers):
            conv_dict = {}
            for edge_type in self.edge_types:
                conv_dict[edge_type] = SAGEConv(
                    hidden_channels,
                    hidden_channels
                )
            self.convs.append(HeteroConv(conv_dict, aggr='mean'))

        # Classification heads
        self.fhir_classifier = Linear(hidden_channels, num_fhir_classes)
        self.omop_classifier = Linear(hidden_channels, num_omop_classes)

    def forward(self, x_dict, edge_index_dict):
        # Project inputs
        h_dict = {
            node_type: self.input_projections[node_type](x)
            for node_type, x in x_dict.items()
        }

        # Message passing
        for conv in self.convs:
            h_dict = conv(h_dict, edge_index_dict)
            h_dict = {
                key: F.relu(h) for key, h in h_dict.items()
            }

        # Get column node embeddings (assuming 'column' is a node type)
        column_embeddings = h_dict.get('column', h_dict.get('data_element'))

        # Classify
        fhir_logits = self.fhir_classifier(column_embeddings)
        omop_logits = self.omop_classifier(column_embeddings)

        return {
            'fhir': fhir_logits,
            'omop': omop_logits,
            'embeddings': column_embeddings
        }

    def predict(self, x_dict, edge_index_dict):
        """Return predictions with confidence scores."""

        with torch.no_grad():
            out = self.forward(x_dict, edge_index_dict)

            fhir_probs = F.softmax(out['fhir'], dim=-1)
            omop_probs = F.softmax(out['omop'], dim=-1)

            fhir_conf, fhir_pred = fhir_probs.max(dim=-1)
            omop_conf, omop_pred = omop_probs.max(dim=-1)

        return {
            'fhir_prediction': fhir_pred,
            'fhir_confidence': fhir_conf,
            'omop_prediction': omop_pred,
            'omop_confidence': omop_conf,
            'embeddings': out['embeddings']
        }
```

## Phase 3: Semantic AI Layer

### Task 3.1: BAML Client Configuration

Create baml_src/clients/ollama.baml:

```baml
// Ollama client for air-gapped deployment
client<llm> LocalLlama {
  provider "ollama"
  options {
    base_url "http://ollama:11434/v1"
    model "llama3.2"
  }
}

client<llm> LocalMistral {
  provider "ollama"
  options {
    base_url "http://ollama:11434/v1"
    model "mistral"
  }
}

client<llm> LocalQwen {
  provider "ollama"
  options {
    base_url "http://ollama:11434/v1"
    model "qwen2.5:7b"
  }
}

// Embedding client
client<embedding> LocalEmbeddings {
  provider "ollama"
  options {
    base_url "http://ollama:11434/v1"
    model "nomic-embed-text"
  }
}
```

### Task 3.2: BAML Entity Standardization

Create baml_src/functions/entity_standardization.baml:

```baml
// FHIR Resource Types
enum FHIRResourceType {
  Patient
  Condition
  Observation
  Procedure
  MedicationRequest
  Encounter
  DiagnosticReport
  Immunization
  AllergyIntolerance
  CarePlan
  CareTeam
  Claim
  Coverage
  Device
  DocumentReference
  FamilyMemberHistory
  Goal
  Location
  Medication
  MedicationAdministration
  MedicationDispense
  Organization
  Practitioner
  Provenance
  QuestionnaireResponse
  ServiceRequest
  Specimen
  Unknown
}

// OMOP Domains
enum OMOPDomain {
  Person
  ConditionOccurrence
  DrugExposure
  ProcedureOccurrence
  Measurement
  Observation
  DeviceExposure
  Visit
  VisitDetail
  Death
  Note
  Specimen
  FactRelationship
  Location
  CareSite
  Provider
  PayerPlanPeriod
  Cost
  DrugEra
  DoseEra
  ConditionEra
  Episode
  Unknown
}

// Terminology systems
enum TerminologySystem {
  SNOMED_CT
  ICD10_CM
  ICD10_PCS
  LOINC
  RxNorm
  CPT
  HCPCS
  NDC
  CVX
  UCUM
  Unknown
}

class EntityStandardization {
  fhir_type FHIRResourceType
  omop_domain OMOPDomain
  terminology_system TerminologySystem?
  standard_code string?
  display_name string?
  confidence float @description("0.0 to 1.0")
  reasoning string @description("Brief explanation of classification")
}

class ColumnContext {
  table_name string
  column_name string
  data_type string
  sample_values string[]
  related_columns string[]?
  table_description string?
}

function StandardizeEntity(context: ColumnContext) -> EntityStandardization {
  client LocalMistral
  prompt #"""
    You are a healthcare data standards expert. Analyze this database column
    and determine which FHIR resource type and OMOP domain it most likely represents.

    Table: {{ context.table_name }}
    Column: {{ context.column_name }}
    Data Type: {{ context.data_type }}
    Sample Values: {{ context.sample_values }}
    {% if context.related_columns %}Related Columns: {{ context.related_columns }}{% endif %}
    {% if context.table_description %}Description: {{ context.table_description }}{% endif %}

    Consider:
    1. Column naming conventions in healthcare databases
    2. Sample value patterns (dates, codes, identifiers, measurements)
    3. Relationships to other columns in the table
    4. Standard healthcare terminologies (SNOMED, LOINC, ICD-10, RxNorm)

    {{ ctx.output_format }}
  """#
}

function BatchStandardize(columns: ColumnContext[]) -> EntityStandardization[] {
  client LocalMistral
  prompt #"""
    You are a healthcare data standards expert. Analyze these database columns
    and determine their FHIR resource types and OMOP domains.

    {% for col in columns %}
    --- Column {{ loop.index }} ---
    Table: {{ col.table_name }}
    Column: {{ col.column_name }}
    Data Type: {{ col.data_type }}
    Samples: {{ col.sample_values[:5] }}
    {% endfor %}

    {{ ctx.output_format }}
  """#
}
```

### Task 3.3: DSPy Entity Standardizer Module

Create dspy_modules/modules/entity_standardizer.py:

```python
"""DSPy module for healthcare entity standardization with GEPA optimization."""

import dspy
from dataclasses import dataclass
from typing import Optional


@dataclass
class ColumnInfo:
    table_name: str
    column_name: str
    data_type: str
    sample_values: list[str]
    related_columns: Optional[list[str]] = None


class EntityStandardizerSignature(dspy.Signature):
    """Classify healthcare data elements into FHIR/OMOP standards."""

    column_context: str = dspy.InputField(
        desc="JSON representation of column metadata and samples"
    )
    schema_context: str = dspy.InputField(
        desc="Related schema information from the meta-graph"
    )

    fhir_resource_type: str = dspy.OutputField(
        desc="FHIR R5 resource type (e.g., Patient, Condition, Observation)"
    )
    omop_domain: str = dspy.OutputField(
        desc="OMOP CDM domain (e.g., person, condition_occurrence)"
    )
    terminology_system: str = dspy.OutputField(
        desc="Standard terminology (SNOMED-CT, LOINC, ICD-10, RxNorm, or None)"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence score 0.0-1.0"
    )
    reasoning: str = dspy.OutputField(
        desc="Brief explanation of classification decision"
    )


class EntityStandardizer(dspy.Module):
    """Multi-hop reasoning for entity standardization."""

    def __init__(self):
        super().__init__()

        # Step 1: Analyze column semantics
        self.analyze = dspy.ChainOfThought(
            "column_context -> semantic_type, value_patterns, likely_domain"
        )

        # Step 2: Match to FHIR
        self.fhir_match = dspy.Predict(
            "semantic_type, value_patterns, schema_context -> fhir_resource_type, fhir_confidence"
        )

        # Step 3: Match to OMOP
        self.omop_match = dspy.Predict(
            "semantic_type, value_patterns, schema_context -> omop_domain, omop_confidence"
        )

        # Step 4: Identify terminology
        self.terminology_match = dspy.Predict(
            "value_patterns, fhir_resource_type, omop_domain -> terminology_system"
        )

        # Step 5: Synthesize final classification
        self.synthesize = dspy.ChainOfThought(EntityStandardizerSignature)

    def forward(self, column_info: ColumnInfo, schema_context: str = ""):
        import json

        column_context = json.dumps({
            'table': column_info.table_name,
            'column': column_info.column_name,
            'type': column_info.data_type,
            'samples': column_info.sample_values[:10],
            'related': column_info.related_columns or []
        })

        # Multi-hop reasoning
        analysis = self.analyze(column_context=column_context)

        fhir_result = self.fhir_match(
            semantic_type=analysis.semantic_type,
            value_patterns=analysis.value_patterns,
            schema_context=schema_context
        )

        omop_result = self.omop_match(
            semantic_type=analysis.semantic_type,
            value_patterns=analysis.value_patterns,
            schema_context=schema_context
        )

        terminology = self.terminology_match(
            value_patterns=analysis.value_patterns,
            fhir_resource_type=fhir_result.fhir_resource_type,
            omop_domain=omop_result.omop_domain
        )

        # Final synthesis
        result = self.synthesize(
            column_context=column_context,
            schema_context=schema_context
        )

        return result


def create_fhir_conformance_metric():
    """Create GEPA-compatible metric for FHIR conformance."""

    # Load valid FHIR types (from local cache)
    valid_fhir_types = load_fhir_resource_types()
    valid_omop_domains = load_omop_domains()

    def metric(example, prediction, trace=None):
        score = 0.0
        feedback = []

        # Check FHIR validity
        if prediction.fhir_resource_type in valid_fhir_types:
            score += 0.3
        else:
            feedback.append(f"Invalid FHIR type: {prediction.fhir_resource_type}")

        # Check OMOP validity
        if prediction.omop_domain in valid_omop_domains:
            score += 0.3
        else:
            feedback.append(f"Invalid OMOP domain: {prediction.omop_domain}")

        # Check reasoning quality
        if len(prediction.reasoning) > 20:
            score += 0.2
        else:
            feedback.append("Reasoning too brief")

        # Check confidence calibration
        if hasattr(example, 'expected_fhir'):
            is_correct = prediction.fhir_resource_type == example.expected_fhir
            if is_correct and prediction.confidence > 0.7:
                score += 0.2
            elif not is_correct and prediction.confidence < 0.5:
                score += 0.1  # Well-calibrated uncertainty

        return {
            'score': score,
            'feedback': '; '.join(feedback) if feedback else 'Good classification'
        }

    return metric


def optimize_with_gepa(
    module: EntityStandardizer,
    trainset: list,
    valset: list
) -> EntityStandardizer:
    """Optimize entity standardizer using GEPA."""

    from dspy import GEPA

    metric = create_fhir_conformance_metric()

    optimizer = GEPA(
        metric=metric,
        auto="medium",
        num_generations=10,
        population_size=20
    )

    optimized = optimizer.compile(
        module,
        trainset=trainset,
        valset=valset
    )

    return optimized
```

## Phase 4: Healthcare Standards Integration

### Task 4.1: CQL Engine Adapter

Create healthcare_standards/cql/engine_adapter.py:

```python
"""Adapter for CQL execution engine integration."""

import subprocess
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class CQLMeasure:
    id: str
    name: str
    version: str
    library_path: Path
    parameters: dict


@dataclass
class MeasureResult:
    measure_id: str
    population_count: int
    numerator_count: int
    denominator_count: int
    exclusion_count: int
    score: float
    patient_list: list[str]


class CQLEngineAdapter:
    """Execute CQL measures against healthcare graph data."""

    def __init__(
        self,
        engine_path: Path,
        terminology_path: Path,
        fhir_endpoint: Optional[str] = None
    ):
        self.engine_path = engine_path
        self.terminology_path = terminology_path
        self.fhir_endpoint = fhir_endpoint or "http://localhost:8080/fhir"

    def execute_measure(
        self,
        measure: CQLMeasure,
        patient_ids: Optional[list[str]] = None,
        period_start: str = None,
        period_end: str = None
    ) -> MeasureResult:
        """Execute a CQL quality measure."""

        cmd = [
            "java", "-jar", str(self.engine_path),
            "--library", str(measure.library_path),
            "--terminology", str(self.terminology_path),
            "--fhir", self.fhir_endpoint
        ]

        if patient_ids:
            cmd.extend(["--patients", ",".join(patient_ids)])

        if period_start:
            cmd.extend(["--period-start", period_start])

        if period_end:
            cmd.extend(["--period-end", period_end])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"CQL execution failed: {result.stderr}")

        output = json.loads(result.stdout)

        return MeasureResult(
            measure_id=measure.id,
            population_count=output['initialPopulation'],
            numerator_count=output['numerator'],
            denominator_count=output['denominator'],
            exclusion_count=output.get('denominatorExclusion', 0),
            score=output['numerator'] / max(output['denominator'], 1),
            patient_list=output.get('patientList', [])
        )

    def translate_to_elm(self, cql_content: str) -> dict:
        """Translate CQL to ELM (executable representation)."""

        cmd = [
            "java", "-jar", str(self.engine_path.parent / "cql-translator.jar"),
            "--format", "json"
        ]

        result = subprocess.run(
            cmd,
            input=cql_content,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"CQL translation failed: {result.stderr}")

        return json.loads(result.stdout)


class GraphCQLProvider:
    """Provide FHIR data from Apache AGE graph for CQL execution."""

    def __init__(self, postgres_conn, graph_name: str = "healthcare"):
        self.conn = postgres_conn
        self.graph_name = graph_name

    def get_patients(self, patient_ids: list[str]) -> list[dict]:
        """Retrieve patient resources from graph."""

        cypher = f"""
            MATCH (p:Patient)
            WHERE p.id IN {patient_ids}
            RETURN p
        """

        return self._execute_cypher(cypher)

    def get_conditions(self, patient_id: str) -> list[dict]:
        """Retrieve conditions for a patient.

        SECURITY WARNING: This example uses f-string interpolation for clarity.
        In production, validate/sanitize patient_id or use parameterized queries
        to prevent Cypher injection attacks that could expose/corrupt PHI.
        """
        # Production: validate patient_id format (e.g., UUID pattern)
        # or use AGE's parameter binding if available
        cypher = f"""
            MATCH (p:Patient {{id: '{patient_id}'}})-[:HAS_CONDITION]->(c:Condition)
            RETURN c
        """

        return self._execute_cypher(cypher)

    def _execute_cypher(self, cypher: str) -> list[dict]:
        query = f"""
            SELECT * FROM cypher('{self.graph_name}', $${cypher}$$)
            AS (result agtype)
        """

        with self.conn.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]
```

### Task 4.2: NIH Quality Measure Definitions

Create healthcare_standards/quality_measures/nih_definitions.py:

```python
"""NIH Clinical Quality Measure definitions for outcome prediction."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MeasureCategory(Enum):
    PROCESS = "process"
    OUTCOME = "outcome"
    STRUCTURE = "structure"
    PATIENT_EXPERIENCE = "patient_experience"
    EFFICIENCY = "efficiency"


class ClinicalDomain(Enum):
    CARDIOVASCULAR = "cardiovascular"
    DIABETES = "diabetes"
    RESPIRATORY = "respiratory"
    MENTAL_HEALTH = "mental_health"
    PREVENTIVE_CARE = "preventive_care"
    MEDICATION_MANAGEMENT = "medication_management"
    CARE_COORDINATION = "care_coordination"
    PATIENT_SAFETY = "patient_safety"


@dataclass
class QualityMeasure:
    """NIH/CMS Clinical Quality Measure definition."""

    id: str  # e.g., CMS122v12
    nqf_id: Optional[str]  # NQF endorsement number
    title: str
    description: str
    category: MeasureCategory
    domain: ClinicalDomain

    # Population criteria
    initial_population_cql: str
    denominator_cql: str
    numerator_cql: str
    denominator_exclusion_cql: Optional[str] = None
    denominator_exception_cql: Optional[str] = None

    # Measure attributes
    measure_period_months: int = 12
    continuous_variable: bool = False
    inverse_measure: bool = False  # Lower is better

    # Value sets required
    required_valuesets: list[str] = None


# Example measures for outcome prediction
DIABETES_A1C_CONTROL = QualityMeasure(
    id="CMS122v12",
    nqf_id="0059",
    title="Diabetes: Hemoglobin A1c (HbA1c) Poor Control (>9%)",
    description="Percentage of patients 18-75 with diabetes whose HbA1c was >9%",
    category=MeasureCategory.OUTCOME,
    domain=ClinicalDomain.DIABETES,
    initial_population_cql="""
        exists ([Condition: "Diabetes"] C
            where C.clinicalStatus ~ 'active'
            and C.onset during "Measurement Period")
        and AgeInYearsAt(start of "Measurement Period") >= 18
        and AgeInYearsAt(start of "Measurement Period") <= 75
    """,
    denominator_cql="""
        "Initial Population"
    """,
    numerator_cql="""
        exists ([Observation: "HbA1c Laboratory Test"] O
            where O.effective during "Measurement Period"
            and O.value > 9 '%')
    """,
    denominator_exclusion_cql="""
        exists ([Condition: "Hospice Care"] H
            where H.onset during "Measurement Period")
    """,
    inverse_measure=True,
    required_valuesets=[
        "2.16.840.1.113883.3.464.1003.103.12.1001",  # Diabetes
        "2.16.840.1.113883.3.464.1003.198.12.1013",  # HbA1c tests
    ]
)

HYPERTENSION_CONTROL = QualityMeasure(
    id="CMS165v12",
    nqf_id="0018",
    title="Controlling High Blood Pressure",
    description="Percentage of patients with hypertension whose BP was adequately controlled",
    category=MeasureCategory.OUTCOME,
    domain=ClinicalDomain.CARDIOVASCULAR,
    initial_population_cql="""
        exists ([Condition: "Essential Hypertension"] H
            where H.onset before end of "Measurement Period")
        and AgeInYearsAt(start of "Measurement Period") >= 18
        and AgeInYearsAt(start of "Measurement Period") <= 85
    """,
    denominator_cql="""
        "Initial Population"
    """,
    numerator_cql="""
        exists ([Observation: "Blood Pressure"] BP
            where BP.effective during "Measurement Period"
            and BP.component[systolic].value < 140 'mm[Hg]'
            and BP.component[diastolic].value < 90 'mm[Hg]')
    """,
    required_valuesets=[
        "2.16.840.1.113883.3.464.1003.104.12.1011",  # Hypertension
        "2.16.840.1.113762.1.4.1032.9",  # Blood pressure
    ]
)

# Registry of all measures
MEASURE_REGISTRY = {
    "CMS122v12": DIABETES_A1C_CONTROL,
    "CMS165v12": HYPERTENSION_CONTROL,
}


def get_measures_for_patient_conditions(condition_codes: list[str]) -> list[QualityMeasure]:
    """Identify applicable quality measures based on patient conditions."""

    # Map condition codes to domains
    domain_mapping = {
        "E11": ClinicalDomain.DIABETES,  # Type 2 diabetes
        "I10": ClinicalDomain.CARDIOVASCULAR,  # Hypertension
        "J45": ClinicalDomain.RESPIRATORY,  # Asthma
    }

    patient_domains = set()
    for code in condition_codes:
        prefix = code[:3]
        if prefix in domain_mapping:
            patient_domains.add(domain_mapping[prefix])

    applicable_measures = [
        m for m in MEASURE_REGISTRY.values()
        if m.domain in patient_domains
    ]

    return applicable_measures
```

## Phase 5: Bidirectional Integration

### Task 5.1: Prediction-to-Graph Writer

Create gnn_training/export/embedding_writer.py:

```python
"""Write GNN predictions and embeddings back to PostgreSQL graph."""

import psycopg2
from psycopg2.extras import execute_values
import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class PredictionBatch:
    node_ids: list[str]
    node_type: str
    embeddings: np.ndarray
    fhir_predictions: list[str]
    fhir_confidences: list[float]
    omop_predictions: list[str]
    omop_confidences: list[float]
    model_version: str


class GraphPredictionWriter:
    """Write predictions and embeddings to PostgreSQL/AGE graph."""

    def __init__(self, conn_string: str, graph_name: str = "predictions"):
        self.conn_string = conn_string
        self.graph_name = graph_name
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(self.conn_string)
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")

    def write_embeddings(self, batch: PredictionBatch) -> int:
        """Write node embeddings to pgvector table."""

        data = [
            (
                node_id,
                batch.node_type,
                embedding.tolist(),
                batch.model_version
            )
            for node_id, embedding in zip(batch.node_ids, batch.embeddings)
        ]

        with self.conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO node_embeddings (node_id, node_type, embedding, model_version)
                VALUES %s
                ON CONFLICT (node_id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    model_version = EXCLUDED.model_version,
                    created_at = NOW()
                """,
                data,
                template="(%s, %s, %s::vector, %s)"
            )

        self.conn.commit()
        return len(data)

    def write_entity_predictions(self, batch: PredictionBatch) -> int:
        """Write entity standardization predictions to relational table."""

        data = [
            (
                node_id.split('.')[0],  # table name
                node_id.split('.')[1],  # column name
                fhir_pred,
                omop_pred,
                (fhir_conf + omop_conf) / 2,  # average confidence
                batch.model_version
            )
            for node_id, fhir_pred, fhir_conf, omop_pred, omop_conf in zip(
                batch.node_ids,
                batch.fhir_predictions,
                batch.fhir_confidences,
                batch.omop_predictions,
                batch.omop_confidences
            )
        ]

        with self.conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO entity_predictions
                    (source_table, source_column, predicted_fhir_type,
                     predicted_omop_domain, confidence, model_version)
                VALUES %s
                """,
                data
            )

        self.conn.commit()
        return len(data)

    def update_graph_properties(self, batch: PredictionBatch) -> int:
        """Update graph node properties with predictions."""

        updated = 0

        for node_id, fhir_pred, fhir_conf, omop_pred, omop_conf in zip(
            batch.node_ids,
            batch.fhir_predictions,
            batch.fhir_confidences,
            batch.omop_predictions,
            batch.omop_confidences
        ):
            cypher = f"""
                MATCH (n {{id: '{node_id}'}})
                SET n.predicted_fhir = '{fhir_pred}',
                    n.fhir_confidence = {fhir_conf},
                    n.predicted_omop = '{omop_pred}',
                    n.omop_confidence = {omop_conf},
                    n.prediction_version = '{batch.model_version}'
                RETURN n
            """

            query = f"""
                SELECT * FROM cypher('{self.graph_name}', $${cypher}$$)
                AS (n agtype)
            """

            with self.conn.cursor() as cur:
                cur.execute(query)
                if cur.fetchone():
                    updated += 1

        self.conn.commit()
        return updated

    def create_prediction_edges(
        self,
        source_ids: list[str],
        target_fhir_types: list[str],
        confidences: list[float]
    ) -> int:
        """Create edges from data elements to predicted FHIR types."""

        created = 0

        for source_id, fhir_type, conf in zip(source_ids, target_fhir_types, confidences):
            cypher = f"""
                MATCH (s {{id: '{source_id}'}})
                MERGE (t:FHIRType {{name: '{fhir_type}'}})
                MERGE (s)-[r:PREDICTED_AS {{confidence: {conf}}}]->(t)
                RETURN r
            """

            query = f"""
                SELECT * FROM cypher('{self.graph_name}', $${cypher}$$)
                AS (r agtype)
            """

            with self.conn.cursor() as cur:
                cur.execute(query)
                if cur.fetchone():
                    created += 1

        self.conn.commit()
        return created

    def close(self):
        if self.conn:
            self.conn.close()
```

### Task 5.2: Change Data Capture Pipeline

Create scripts/run-predictions.py:

```python
#!/usr/bin/env python3
"""Run prediction pipeline with CDC for real-time graph updates."""

import argparse
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json

from gnn_training.data.postgres_loader import PostgresGraphLoader, GraphConfig
from gnn_training.models.entity_classifier import EntityClassifier
from gnn_training.export.embedding_writer import GraphPredictionWriter, PredictionBatch
from dspy_modules.modules.entity_standardizer import EntityStandardizer, ColumnInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_cdc_trigger(conn_string: str):
    """Set up PostgreSQL LISTEN/NOTIFY for CDC."""

    conn = psycopg2.connect(conn_string)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    with conn.cursor() as cur:
        # Create notification function
        cur.execute("""
            CREATE OR REPLACE FUNCTION notify_schema_change()
            RETURNS TRIGGER AS $$
            BEGIN
                PERFORM pg_notify(
                    'schema_changes',
                    json_build_object(
                        'table', TG_TABLE_NAME,
                        'action', TG_OP,
                        'data', row_to_json(NEW)
                    )::text
                );
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Create trigger on information_schema changes
        cur.execute("""
            DROP TRIGGER IF EXISTS schema_change_trigger ON information_schema.columns;
        """)

    return conn


def listen_for_changes(conn, callback):
    """Listen for schema changes and trigger predictions."""

    with conn.cursor() as cur:
        cur.execute("LISTEN schema_changes;")

    logger.info("Listening for schema changes...")

    while True:
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop()
            change = json.loads(notify.payload)
            logger.info(f"Schema change detected: {change}")
            callback(change)


def run_batch_predictions(
    loader: PostgresGraphLoader,
    gnn_model: EntityClassifier,
    dspy_module: EntityStandardizer,
    writer: GraphPredictionWriter,
    model_version: str
):
    """Run predictions on all data elements."""

    # Load graph data
    data = loader.build_hetero_data(
        node_types=['table', 'column', 'value_sample'],
        edge_types=[
            ('table', 'has_column', 'column'),
            ('column', 'has_sample', 'value_sample')
        ]
    )

    logger.info(f"Loaded graph with {data.num_nodes} nodes")

    # Run GNN predictions
    gnn_output = gnn_model.predict(data.x_dict, data.edge_index_dict)

    logger.info(f"GNN predictions complete")

    # Refine with DSPy
    refined_predictions = []
    for i, (node_id, fhir_pred, conf) in enumerate(zip(
        data['column'].node_ids,
        gnn_output['fhir_prediction'],
        gnn_output['fhir_confidence']
    )):
        # Use DSPy for low-confidence predictions
        if conf < 0.8:
            column_info = ColumnInfo(
                table_name=node_id.split('.')[0],
                column_name=node_id.split('.')[1],
                data_type=data['column'].data_types[i],
                sample_values=data['column'].samples[i]
            )

            dspy_result = dspy_module(column_info)
            refined_predictions.append({
                'node_id': node_id,
                'fhir': dspy_result.fhir_resource_type,
                'fhir_conf': float(dspy_result.confidence),
                'omop': dspy_result.omop_domain,
                'omop_conf': float(dspy_result.confidence),
                'source': 'dspy'
            })
        else:
            refined_predictions.append({
                'node_id': node_id,
                'fhir': fhir_pred,
                'fhir_conf': float(conf),
                'omop': gnn_output['omop_prediction'][i],
                'omop_conf': float(gnn_output['omop_confidence'][i]),
                'source': 'gnn'
            })

    # Write predictions back to graph
    batch = PredictionBatch(
        node_ids=[p['node_id'] for p in refined_predictions],
        node_type='column',
        embeddings=gnn_output['embeddings'].numpy(),
        fhir_predictions=[p['fhir'] for p in refined_predictions],
        fhir_confidences=[p['fhir_conf'] for p in refined_predictions],
        omop_predictions=[p['omop'] for p in refined_predictions],
        omop_confidences=[p['omop_conf'] for p in refined_predictions],
        model_version=model_version
    )

    written = writer.write_embeddings(batch)
    logger.info(f"Wrote {written} embeddings")

    written = writer.write_entity_predictions(batch)
    logger.info(f"Wrote {written} entity predictions")

    updated = writer.update_graph_properties(batch)
    logger.info(f"Updated {updated} graph nodes")

    return refined_predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default='config/settings.yaml')
    parser.add_argument('--model-version', default='v1.0.0')
    parser.add_argument('--mode', choices=['batch', 'stream'], default='batch')
    args = parser.parse_args()

    # Load configuration
    import yaml
    with open(args.config) as f:
        config = yaml.safe_load(f)

    # Initialize components
    graph_config = GraphConfig(**config['postgres'])
    loader = PostgresGraphLoader(graph_config)
    loader.connect()

    # Load trained GNN model
    import torch
    gnn_model = EntityClassifier(
        metadata=(['table', 'column'], [('table', 'has_column', 'column')]),
        hidden_channels=256
    )
    gnn_model.load_state_dict(torch.load(config['models']['entity_classifier']))
    gnn_model.eval()

    # Load optimized DSPy module
    import dspy
    dspy.configure(lm=dspy.LM('ollama_chat/llama3.2', api_base='http://localhost:11434'))
    dspy_module = EntityStandardizer()
    dspy_module.load(config['models']['dspy_standardizer'])

    # Initialize writer
    writer = GraphPredictionWriter(
        conn_string=f"postgresql://{graph_config.user}:{graph_config.password}@{graph_config.host}/{graph_config.database}"
    )
    writer.connect()

    if args.mode == 'batch':
        predictions = run_batch_predictions(
            loader, gnn_model, dspy_module, writer, args.model_version
        )
        logger.info(f"Batch complete: {len(predictions)} predictions")

    elif args.mode == 'stream':
        cdc_conn = setup_cdc_trigger(writer.conn_string)

        def on_change(change):
            # Re-run predictions for affected elements
            run_batch_predictions(
                loader, gnn_model, dspy_module, writer, args.model_version
            )

        listen_for_changes(cdc_conn, on_change)

    loader.close()
    writer.close()


if __name__ == '__main__':
    main()
```

## Speckit Constitution

Create speckit/constitution.md:

```markdown
# Healthcare Graph ML Constitution

## Non-Negotiable Principles

### 1. Air-Gap Compliance
- ZERO external network calls in production
- All dependencies pre-cached and locally available
- No cloud API calls (Kumo.ai, OpenAI, etc.)
- Self-hosted LLMs via Ollama only

### 2. HIPAA Technical Safeguards
- All PHI encrypted at rest (AES-256)
- TLS 1.3 for all internal connections
- Comprehensive audit logging
- Node-level access controls in graph

### 3. Data Integrity
- ACID transactions for all writes
- Immutable audit trail
- Model versioning via MLflow
- Reproducible predictions

### 4. Healthcare Standards Compliance
- FHIR R5 resource alignment
- OMOP CDM v5.4 compatibility
- Standard terminologies (SNOMED, LOINC, ICD-10, RxNorm)
- CQL for quality measure execution

### 5. Prediction Quality
- Minimum 85% confidence for production use
- DSPy refinement for low-confidence GNN outputs
- GEPA optimization with healthcare-specific metrics
- Human-in-the-loop for critical decisions

## Architectural Constraints

- PostgreSQL 17 as single source of truth
- Apache AGE for all graph operations
- pgvector for embedding storage
- PyTorch Geometric or DGL for GNN training
- BAML for all structured LLM outputs
- DSPy for LLM orchestration
- GEPA for prompt optimization

## Quality Gates

1. Unit test coverage > 80%
2. Integration tests for all prediction paths
3. FHIR validation for entity predictions
4. OMOP vocabulary conformance checks
5. CQL measure execution validation
```

## Execution Instructions

1. Initialize project: `mkdir healthcare-graph-ml && cd healthcare-graph-ml`
2. Create directory structure as specified
3. Implement Phase 1 first (data layer must be operational)
4. Run `docker-compose up -d` to start infrastructure
5. Load vocabulary data from local Athena cache
6. Implement phases 2-5 sequentially
7. Run integration tests after each phase
8. Execute batch predictions to populate graph

## Success Criteria

- [ ] PostgreSQL + AGE + pgvector operational
- [ ] GNN training pipeline produces validated models
- [ ] DSPy modules execute with local Ollama
- [ ] GEPA optimization improves prediction quality
- [ ] BAML functions extract structured entities
- [ ] CQL measures execute against graph data
- [ ] Predictions write back to graph bidirectionally
- [ ] All tests pass in air-gapped environment
- [ ] HIPAA compliance checklist complete
