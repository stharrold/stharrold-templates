# GCP Native Pipeline Implementation with Cloud Workflows

## Architecture Overview

```yaml
Orchestration: Cloud Workflows (lower latency than Pub/Sub)
Cache: Memorystore Redis (composite keys)
Storage: Cloud Storage (hierarchical blob naming)
Hierarchy: BigQuery (recursive CTEs, 15 levels)
Embeddings: Vertex AI text-embedding-005 (256d native)
Quantization: BigQuery ML PCA (256d → 32d)
NLP: Natural Language API (stored as-is)
```

## Blob Naming Convention

```
{document-guid}.00-original.v{version}.{ext}
{document-guid}.10-processed.v{version}.json
{document-guid}.20-nlp.v{version}.json
{document-guid}.40-embed.v{version}.json
{document-guid}.50-encode.v{version}.json
{document-guid}.60-search.v{version}.json
{document-guid}.70-result.v{version}.json
```

Each blob includes ISO 8601 UTC timestamp in metadata.

## Cloud Workflows Definition

```yaml
# workflows/rag-pipeline.yaml
main:
  params: [input]
  steps:
    - init:
        assign:
          - pub:
              message: ${input.message}
              document_guid: ${input.document_guid}
              stages: {}

    # Stage 00: Orchestrator initialization
    - orchestrator_init:
        call: http.post
        args:
          url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-00-orchestrator
          body:
            pub: ${pub}
        result: pub

    # Stage 01: Cache lookup for original
    - cache_original_lookup:
        call: http.post
        args:
          url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-01-cache-original-lookup
          body:
            pub: ${pub}
        result: pub

    # Stage 10: Process original if not cached
    - process_original:
        switch:
          - condition: ${pub.stages["10-original"].cache_hit == false}
            call: http.post
            args:
              url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-10-original
              body:
                pub: ${pub}
            result: pub

    # Stage 02: Cache lookup for extract
    - cache_extract_lookup:
        call: http.post
        args:
          url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-02-cache-extract-lookup
          body:
            pub: ${pub}
        result: pub

    # Stage 20: Extract text if not cached
    - process_extract:
        switch:
          - condition: ${pub.stages["20-extract"].cache_hit == false}
            call: http.post
            args:
              url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-20-extract
              body:
                pub: ${pub}
            result: pub

    # Stage 03: Cache lookup for NLP
    - cache_nlp_lookup:
        call: http.post
        args:
          url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-03-cache-nlp-lookup
          body:
            pub: ${pub}
        result: pub

    # Stage 30: Process NLP if not cached
    - process_nlp:
        switch:
          - condition: ${pub.stages["30-nlp"].cache_hit == false}
            call: http.post
            args:
              url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-30-nlp
              body:
                pub: ${pub}
            result: pub

    # Stage 04: Cache lookup for embeddings
    - cache_embed_lookup:
        call: http.post
        args:
          url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-04-cache-embed-lookup
          body:
            pub: ${pub}
        result: pub

    # Stage 40: Generate embeddings if not cached
    - process_embed:
        switch:
          - condition: ${pub.stages["40-embed"].cache_hit == false}
            call: http.post
            args:
              url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-40-embed
              body:
                pub: ${pub}
            result: pub

    # Stage 05: Cache lookup for quantization
    - cache_encode_lookup:
        call: http.post
        args:
          url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-05-cache-encode-lookup
          body:
            pub: ${pub}
        result: pub

    # Stage 50: Reduce dimensions if not cached
    - process_encode:
        switch:
          - condition: ${pub.stages["50-encode"].cache_hit == false}
            call: http.post
            args:
              url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-50-encode
              body:
                pub: ${pub}
            result: pub

    # Stage 06: Cache lookup for search
    - cache_search_lookup:
        call: http.post
        args:
          url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-06-cache-search-lookup
          body:
            pub: ${pub}
        result: pub

    # Stage 60: Search if not cached
    - process_search:
        switch:
          - condition: ${pub.stages["60-search"].cache_hit == false}
            call: http.post
            args:
              url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-60-search
              body:
                pub: ${pub}
            result: pub

    # Stage 70: Aggregate results
    - process_result:
        call: http.post
        args:
          url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-query-70-result
          body:
            pub: ${pub}
        result: pub

    - return_result:
        return: ${pub}
```

## Python Implementation

### Base Pub Object

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import hashlib
import json

@dataclass
class PubStage:
    """Stage-specific data with before/after states"""
    stage_name: str
    before: Dict[str, Any] = field(default_factory=dict)
    after: Dict[str, Any] = field(default_factory=dict)
    cache_hit: bool = False

    def get_hash(self) -> str:
        content = json.dumps(self.before, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def get_alphanum(self) -> str:
        """For NLP stage - uses alphanumeric content only"""
        text = self.before.get('content_text', '')
        alphanum = ''.join(c for c in text if c.isalnum())
        return hashlib.sha256(alphanum.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "before": self.before,
            "after": self.after,
            "cache_hit": self.cache_hit
        }

@dataclass
class Pub:
    """Pub/Sub-like object for pipeline state"""
    document_guid: str
    message: str
    stages: Dict[str, PubStage] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: Optional[str] = None

    def update(self, *args):
        """Update pub with results from multiple stages"""
        for stage_result in args:
            if stage_result:
                self.stages.update(stage_result)
        return self

    def get_blob_guid(self, stage: str) -> Optional[str]:
        return self.stages.get(stage, {}).get('after', {}).get('blob_guid')

    def to_dict(self) -> Dict[str, Any]:
        """Proper serialization for Cloud Functions"""
        return {
            "document_guid": self.document_guid,
            "message": self.message,
            "timestamp": self.timestamp,
            "version": self.version,
            "stages": {k: v.to_dict() for k, v in self.stages.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Deserialize from dict"""
        pub = cls(
            document_guid=data["document_guid"],
            message=data["message"],
            timestamp=data.get("timestamp"),
            version=data.get("version")
        )
        pub.stages = {
            k: PubStage(**v) for k, v in data.get("stages", {}).items()
        }
        return pub
```

### Stage 00: Orchestrator

```python
import functions_framework
from google.cloud import storage, redis, bigquery
import json

redis_client = redis.Client(host='10.0.0.1', port=6379)
storage_client = storage.Client()
bigquery_client = bigquery.Client()
bucket_name = 'corpus-bucket'

@functions_framework.http
def gcp_run_query_00_orchestrator(request):
    """Initialize pub object with stages"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    # Initialize all stages
    pub.stages = {
        "10-original": PubStage(stage_name="10-original"),
        "20-extract": PubStage(stage_name="20-extract"),
        "30-nlp": PubStage(stage_name="30-nlp"),
        "40-embed": PubStage(stage_name="40-embed"),
        "50-encode": PubStage(stage_name="50-encode"),  # 256d → 32d
        "60-search": PubStage(stage_name="60-search"),
        "70-result": PubStage(stage_name="70-result")
    }

    # Set initial content
    pub.stages["10-original"].before["content_bytes"] = pub.message.encode()
    pub.stages["10-original"].before["extension"] = "md"

    # Set version preference (latest by default)
    pub.version = request.get_json().get('version', 'latest')

    return pub.to_dict()
```

### Stage 01-10: Original Document

```python
@functions_framework.http
def gcp_run_query_01_cache_original_lookup(request):
    """Check Redis for existing original document"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["10-original"]
    cache_key = f"doc:original:{stage.get_hash()}"

    cached_guid = redis_client.get(cache_key)
    if cached_guid:
        if pub.version and pub.version != 'latest':
            version_blob = f"{pub.document_guid}.00-original.v{pub.version}.{stage.before.get('extension', 'md')}"
            blob = storage_client.bucket(bucket_name).blob(version_blob)
            if blob.exists():
                stage.after["blob_guid"] = version_blob
                stage.cache_hit = True
        else:
            stage.after["blob_guid"] = cached_guid.decode()
            stage.cache_hit = True

    return pub.to_dict()

@functions_framework.http
def gcp_run_query_10_original(request):
    """Store original document in GCS with version support"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["10-original"]
    if stage.cache_hit:
        return pub.to_dict()

    # Create versioned blob name
    if pub.version and pub.version != 'latest':
        blob_name = f"{pub.document_guid}.00-original.v{pub.version}.{stage.before['extension']}"
    else:
        existing_blobs = storage_client.bucket(bucket_name).list_blobs(
            prefix=f"{pub.document_guid}.00-original.v"
        )
        latest_version = "00000000000000"
        for existing in existing_blobs:
            parts = existing.name.split('.v')
            if len(parts) > 1:
                version = parts[1].split('.')[0]
                if version > latest_version:
                    latest_version = version

        version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        blob_name = f"{pub.document_guid}.00-original.v{version}.{stage.before['extension']}"
        pub.version = version

    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {
        'timestamp': pub.timestamp,
        'version': pub.version
    }
    blob.upload_from_string(stage.before['content_bytes'])

    cache_key = f"doc:original:{stage.get_hash()}"
    redis_client.setex(cache_key, 86400*30, blob_name)

    version_key = f"doc:version:{pub.document_guid}"
    redis_client.setex(version_key, 86400*30, pub.version)

    stage.after["blob_guid"] = blob_name
    return pub.to_dict()
```

### Stage 02-20: Document AI Processing

```python
from google.cloud import documentai_v1

@functions_framework.http
def gcp_run_query_02_cache_extract_lookup(request):
    """Check cache for extracted text"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["20-extract"]
    original_blob = pub.get_blob_guid("10-original")

    cache_key = f"doc:extract:{original_blob}"
    cached_guid = redis_client.get(cache_key)

    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True

    return pub.to_dict()

@functions_framework.http
def gcp_run_query_20_extract(request):
    """Extract text using Document AI with hierarchical chunking"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["20-extract"]
    if stage.cache_hit:
        return pub.to_dict()

    original_blob = pub.get_blob_guid("10-original")

    doc_ai = documentai_v1.DocumentProcessorServiceClient()
    request = {
        "name": "projects/PROJECT/locations/us/processors/PROCESSOR_ID",
        "gcs_document": {
            "gcs_uri": f"gs://{bucket_name}/{original_blob}",
            "mime_type": "text/plain"
        },
        "process_options": {
            "layout_config": {
                "chunking_config": {
                    "chunk_size": 500,
                    "include_ancestor_headings": True,
                    "chunking_strategy": "LAYOUT_BASED"
                }
            }
        }
    }

    result = doc_ai.process_document(request)

    # Build hierarchical structure (up to 15 levels)
    hierarchical_chunks = []
    for page_idx, page in enumerate(result.pages):
        for block_idx, block in enumerate(page.blocks):
            for para_idx, para in enumerate(block.paragraphs):
                chunk_id = f"{pub.document_guid}.{page_idx:03d}.{block_idx:03d}.{para_idx:03d}"
                hierarchical_chunks.append({
                    "id": chunk_id,
                    "content": para.layout.text_anchor.content,
                    "parent_id": f"{pub.document_guid}.{page_idx:03d}.{block_idx:03d}",
                    "level": 3,
                    "hierarchy_path": [pub.document_guid, f"{page_idx:03d}", f"{block_idx:03d}", f"{para_idx:03d}"]
                })

    version = pub.version or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    blob_name = f"{pub.document_guid}.10-processed.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(hierarchical_chunks))

    cache_key = f"doc:extract:{original_blob}"
    redis_client.setex(cache_key, 86400*30, blob_name)

    stage.after["blob_guid"] = blob_name
    stage.after["chunk_count"] = len(hierarchical_chunks)

    return pub.to_dict()
```

### Stage 03-30: NLP Processing

```python
from google.cloud import language_v1

@functions_framework.http
def gcp_run_query_03_cache_nlp_lookup(request):
    """Check NLP cache"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["30-nlp"]
    extract_blob = pub.get_blob_guid("20-extract")

    cache_key = f"doc:nlp:{extract_blob}"
    cached_guid = redis_client.get(cache_key)

    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True

    return pub.to_dict()

@functions_framework.http
def gcp_run_query_30_nlp(request):
    """Process each hierarchical level with NLP API"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["30-nlp"]
    if stage.cache_hit:
        return pub.to_dict()

    extract_blob = pub.get_blob_guid("20-extract")

    blob = storage_client.bucket(bucket_name).blob(extract_blob)
    chunks = json.loads(blob.download_as_text())

    language_client = language_v1.LanguageServiceClient()
    nlp_results = {}

    for chunk in chunks:
        cache_key = f"doc:nlp:{chunk['id']}"
        cached_nlp = redis_client.get(cache_key)

        if cached_nlp:
            nlp_results[chunk['id']] = json.loads(cached_nlp)
        else:
            document = language_v1.Document(
                content=chunk['content'],
                type_=language_v1.Document.Type.PLAIN_TEXT,
            )

            features = {
                "extract_entities": True,
                "extract_document_sentiment": True,
                "extract_entity_sentiment": True,
                "extract_syntax": True,
                "classify_text": len(chunk['content']) > 20
            }

            response = language_client.annotate_text(
                request={"document": document, "features": features}
            )

            # Store complete NLP response as-is
            nlp_json = {
                "entities": [{"name": e.name, "type": e.type_.name, "salience": e.salience}
                           for e in response.entities],
                "sentiment": {
                    "score": response.document_sentiment.score,
                    "magnitude": response.document_sentiment.magnitude
                },
                "categories": [{"name": c.name, "confidence": c.confidence}
                             for c in response.categories] if response.categories else [],
                "syntax": {"tokens": len(response.tokens)},
                "language": response.language
            }

            nlp_results[chunk['id']] = nlp_json
            redis_client.setex(cache_key, 86400*30, json.dumps(nlp_json))

    version = pub.version or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    blob_name = f"{pub.document_guid}.20-nlp.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(nlp_results))

    cache_key = f"doc:nlp:{extract_blob}"
    redis_client.setex(cache_key, 86400*30, blob_name)

    stage.after["blob_guid"] = blob_name
    return pub.to_dict()
```

### Stage 04-40: Generate Embeddings

```python
from google.cloud import aiplatform

@functions_framework.http
def gcp_run_query_04_cache_embed_lookup(request):
    """Check embedding cache"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["40-embed"]
    nlp_blob = pub.get_blob_guid("30-nlp")

    cache_key = f"doc:embed:{nlp_blob}"
    cached_guid = redis_client.get(cache_key)

    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True

    return pub.to_dict()

@functions_framework.http
def gcp_run_query_40_embed(request):
    """Generate embeddings using Vertex AI native dimensions"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["40-embed"]
    if stage.cache_hit:
        return pub.to_dict()

    nlp_blob = pub.get_blob_guid("30-nlp")
    extract_blob = pub.get_blob_guid("20-extract")

    aiplatform.init(project="PROJECT", location="us-central1")
    model = aiplatform.TextEmbeddingModel.from_pretrained("text-embedding-005")

    blob = storage_client.bucket(bucket_name).blob(extract_blob)
    chunks = json.loads(blob.download_as_text())

    embeddings = {}
    for chunk in chunks:
        cache_key = f"doc:embed:{chunk['id']}"
        cached_embed = redis_client.get(cache_key)

        if cached_embed:
            embeddings[chunk['id']] = json.loads(cached_embed)
        else:
            embedding = model.get_embeddings(
                [chunk['content']],
                output_dimensionality=256  # Smallest native dimension
            )[0].values

            embeddings[chunk['id']] = embedding
            redis_client.setex(cache_key, 86400*30, json.dumps(embedding))

    version = pub.version or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    blob_name = f"{pub.document_guid}.40-embed.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(embeddings))

    cache_key = f"doc:embed:{nlp_blob}"
    redis_client.setex(cache_key, 86400*30, blob_name)

    stage.after["blob_guid"] = blob_name
    return pub.to_dict()
```

### Stage 05-50: Dimensionality Reduction (256d → 32d)

```python
@functions_framework.http
def gcp_run_query_05_cache_encode_lookup(request):
    """Check cache for reduced embeddings"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["50-encode"]
    embed_blob = pub.get_blob_guid("40-embed")

    cache_key = f"doc:encode:{embed_blob}"
    cached_guid = redis_client.get(cache_key)

    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True

    return pub.to_dict()

@functions_framework.http
def gcp_run_query_50_encode(request):
    """Reduce dimensions from 256d to 32d using BigQuery ML PCA"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["50-encode"]
    if stage.cache_hit:
        return pub.to_dict()

    embed_blob = pub.get_blob_guid("40-embed")

    blob = storage_client.bucket(bucket_name).blob(embed_blob)
    embeddings = json.loads(blob.download_as_text())

    # Create temp table for PCA
    dataset_id = "rag_dataset"
    temp_table = f"{dataset_id}.temp_pca_{pub.document_guid.replace('-', '_')}"

    # Insert embeddings into BigQuery
    rows = []
    for chunk_id, embedding in embeddings.items():
        for i, val in enumerate(embedding):
            rows.append({
                "chunk_id": chunk_id,
                "feature_index": i,
                "feature_value": val
            })

    # Create table
    schema = [
        bigquery.SchemaField("chunk_id", "STRING"),
        bigquery.SchemaField("feature_index", "INT64"),
        bigquery.SchemaField("feature_value", "FLOAT64")
    ]

    table = bigquery.Table(f"{bigquery_client.project}.{temp_table}", schema=schema)
    table = bigquery_client.create_table(table, exists_ok=True)
    bigquery_client.insert_rows_json(table, rows)

    # Create PCA model
    pca_model = f"{dataset_id}.pca_model_{pub.document_guid.replace('-', '_')}"

    pca_query = f"""
    CREATE OR REPLACE MODEL `{pca_model}`
    OPTIONS(
        model_type='PCA',
        num_principal_components=32,
        scale_features=TRUE
    ) AS
    SELECT
        chunk_id,
        ARRAY_AGG(feature_value ORDER BY feature_index) AS features
    FROM `{temp_table}`
    GROUP BY chunk_id
    """

    bigquery_client.query(pca_query).result()

    # Apply PCA transformation
    transform_query = f"""
    SELECT
        chunk_id,
        ARRAY(
            SELECT value
            FROM UNNEST(ML.PREDICT(
                MODEL `{pca_model}`,
                (SELECT chunk_id, ARRAY_AGG(feature_value ORDER BY feature_index) AS features
                 FROM `{temp_table}`
                 WHERE chunk_id = outer.chunk_id
                 GROUP BY chunk_id)
            ).principal_component_values) AS value
        ) AS reduced_embedding
    FROM (SELECT DISTINCT chunk_id FROM `{temp_table}`) outer
    """

    results = bigquery_client.query(transform_query).result()

    # Collect reduced embeddings
    reduced_embeddings = {}
    for row in results:
        reduced_embeddings[row.chunk_id] = {
            "values": list(row.reduced_embedding),  # 32 dimensions
            "reduction_method": "bigquery_pca",
            "original_dim": 256,
            "reduced_dim": 32
        }

    # Clean up
    bigquery_client.delete_table(temp_table, not_found_ok=True)
    bigquery_client.delete_model(pca_model, not_found_ok=True)

    # Store reduced embeddings
    version = pub.version or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    blob_name = f"{pub.document_guid}.50-encode.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {
        'timestamp': pub.timestamp,
        'reduction': 'pca_256_to_32'
    }
    blob.upload_from_string(json.dumps(reduced_embeddings))

    cache_key = f"doc:encode:{embed_blob}"
    redis_client.setex(cache_key, 86400*30, blob_name)

    stage.after["blob_guid"] = blob_name
    stage.after["reduction_method"] = "pca_256_to_32"
    return pub.to_dict()
```

### Stage 06-60: Vector Search

```python
@functions_framework.http
def gcp_run_query_06_cache_search_lookup(request):
    """Check cache for search results"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["60-search"]
    encode_blob = pub.get_blob_guid("50-encode")
    nearest_n = stage.before.get("nearest_n", 10)

    cache_key = f"doc:search:{encode_blob}:{nearest_n}"
    cached_search = redis_client.get(cache_key)

    if cached_search:
        stage.after["blob_guid"] = cached_search
        stage.cache_hit = True

    return pub.to_dict()

@functions_framework.http
def gcp_run_query_60_search(request):
    """Search using 32d reduced embeddings with BigQuery"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["60-search"]
    if stage.cache_hit:
        return pub.to_dict()

    encode_blob = pub.get_blob_guid("50-encode")
    nearest_n = stage.before.get("nearest_n", 10)

    blob = storage_client.bucket(bucket_name).blob(encode_blob)
    reduced_embeddings = json.loads(blob.download_as_text())

    # Use first chunk as query
    query_chunk_id = list(reduced_embeddings.keys())[0]
    query_embed = reduced_embeddings[query_chunk_id]['values']

    # Store corpus in BigQuery temporarily
    dataset_id = "rag_dataset"
    corpus_table = f"{dataset_id}.corpus_32d"

    # Create/update corpus table
    rows = []
    for chunk_id, embed_data in reduced_embeddings.items():
        rows.append({
            "chunk_id": chunk_id,
            "document_guid": pub.document_guid,
            "embedding": embed_data['values']
        })

    schema = [
        bigquery.SchemaField("chunk_id", "STRING"),
        bigquery.SchemaField("document_guid", "STRING"),
        bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED")
    ]

    table = bigquery.Table(f"{bigquery_client.project}.{corpus_table}", schema=schema)
    table = bigquery_client.create_table(table, exists_ok=True)
    bigquery_client.insert_rows_json(table, rows)

    # Calculate L2 distance
    search_query = f"""
    WITH query AS (
        SELECT {query_embed} as query_embedding
    )
    SELECT
        chunk_id,
        SQRT(
            (SELECT SUM(POW(corpus_val - query_val, 2))
             FROM UNNEST(embedding) corpus_val WITH OFFSET pos
             JOIN UNNEST((SELECT query_embedding FROM query)) query_val WITH OFFSET qpos
             ON pos = qpos)
        ) AS distance
    FROM `{corpus_table}`
    WHERE document_guid != '{pub.document_guid}'
    ORDER BY distance ASC
    LIMIT {nearest_n}
    """

    results = bigquery_client.query(search_query).result()

    search_results = []
    for row in results:
        search_results.append({
            "source_id": query_chunk_id,
            "neighbor_id": row.chunk_id,
            "distance": row.distance,
            "metric": "L2_32d"
        })

    # Store search results
    version = pub.version or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    blob_name = f"{pub.document_guid}.60-search.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(search_results))

    cache_key = f"doc:search:{encode_blob}:{nearest_n}"
    redis_client.setex(cache_key, 86400*30, blob_name)

    stage.after["blob_guid"] = blob_name
    return pub.to_dict()
```

### Stage 70: Aggregate Results

```python
@functions_framework.http
def gcp_run_query_70_result(request):
    """Aggregate search results and return text"""
    pub_data = request.get_json()['pub']
    pub = Pub.from_dict(pub_data)

    stage = pub.stages["70-result"]
    search_blob = pub.get_blob_guid("60-search")
    nearest_n = stage.before.get("nearest_n", 10)

    blob = storage_client.bucket(bucket_name).blob(search_blob)
    search_results = json.loads(blob.download_as_text())

    neighbors = sorted(search_results, key=lambda x: x['distance'])[:nearest_n]
    neighbor_ids = list(set(n['neighbor_id'] for n in neighbors))

    result_texts = []
    for neighbor_id in neighbor_ids:
        parts = neighbor_id.split('.')
        neighbor_doc_guid = parts[0]

        neighbor_blob = f"{neighbor_doc_guid}.10-processed.v*.json"
        blobs = storage_client.bucket(bucket_name).list_blobs(prefix=neighbor_blob[:-6])

        latest_blob = None
        for b in blobs:
            if not latest_blob or b.updated > latest_blob.updated:
                latest_blob = b

        if latest_blob:
            chunks = json.loads(latest_blob.download_as_text())
            chunk = next((c for c in chunks if c['id'] == neighbor_id), None)
            if chunk:
                result_texts.append({
                    "id": neighbor_id,
                    "content": chunk['content'],
                    "hierarchy_path": chunk.get('hierarchy_path', [])
                })

    version = pub.version or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    blob_name = f"{pub.document_guid}.70-result.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(result_texts))

    stage.after["blob_guid"] = blob_name
    stage.after["content_result_text"] = result_texts

    return pub.to_dict()
```

## BigQuery Schema for Hierarchical Storage

```sql
CREATE TABLE `project.dataset.document_hierarchy` (
    chunk_id STRING NOT NULL,
    document_guid STRING NOT NULL,
    level INT64,
    parent_id STRING,
    hierarchy_path ARRAY<STRING>,
    content TEXT,

    -- NLP results (
