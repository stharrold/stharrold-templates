# GCP Native Pipeline Implementation with Cloud Workflows

## Architecture Overview

```yaml
Orchestration: Cloud Workflows (lower latency than Pub/Sub)
Cache: Memorystore Redis (composite keys)
Storage: Cloud Storage (hierarchical blob naming)
Hierarchy: BigQuery (recursive CTEs, 15 levels)
Embeddings: Vertex AI text-embedding-005 (256d native)
NLP: Natural Language API (stored as-is)
```

## Blob Naming Convention

```
{document-guid}.00-original.{ext}
{document-guid}.10-processed.json
{document-guid}.20-nlp.json
{document-guid}.40-embed.json
{document-guid}.60-search.json
{document-guid}.70-result.json
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
    
    # Continue for all stages...
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

@dataclass
class Pub:
    """Pub/Sub-like object for pipeline state"""
    document_guid: str
    message: str
    stages: Dict[str, PubStage] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def update(self, *args):
        """Update pub with results from multiple stages"""
        for stage_result in args:
            if stage_result:
                self.stages.update(stage_result)
        return self
    
    def get_blob_guid(self, stage: str) -> Optional[str]:
        return self.stages.get(stage, {}).get('after', {}).get('blob_guid')
```

### Stage 00: Orchestrator

```python
import functions_framework
from google.cloud import storage, redis
import json

redis_client = redis.Client(host='10.0.0.1', port=6379)
storage_client = storage.Client()
bucket_name = 'corpus-bucket'

@functions_framework.http
def gcp_run_query_00_orchestrator(request):
    """Initialize pub object with stages"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    # Initialize stages
    pub.stages = {
        "10-original": PubStage(stage_name="10-original"),
        "20-extract": PubStage(stage_name="20-extract"),
        "30-nlp": PubStage(stage_name="30-nlp"),
        "40-embed": PubStage(stage_name="40-embed"),
        "60-search": PubStage(stage_name="60-search"),
        "70-result": PubStage(stage_name="70-result")
    }
    
    # Set initial content
    pub.stages["10-original"].before["content_bytes"] = pub.message.encode()
    pub.stages["10-original"].before["extension"] = "md"
    
    return pub.__dict__
```

### Stage 01: Cache Original Lookup

```python
@functions_framework.http
def gcp_run_query_01_cache_original_lookup(request):
    """Check Redis for existing original document"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["10-original"]
    cache_key = f"original:{stage.get_hash()}"
    
    cached_guid = redis_client.get(cache_key)
    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True
    
    return pub.__dict__
```

### Stage 10: Process Original

```python
@functions_framework.http
def gcp_run_query_10_original(request):
    """Store original document in GCS"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["10-original"]
    if stage.cache_hit:
        return pub.__dict__
    
    # Create blob name with timestamp
    blob_name = f"{pub.document_guid}.00-original.{stage.before['extension']}"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    
    # Set metadata with ISO 8601 timestamp
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(stage.before['content_bytes'])
    
    # Update cache
    cache_key = f"original:{stage.get_hash()}"
    redis_client.setex(cache_key, 86400*30, blob_name)  # 30-day TTL
    
    stage.after["blob_guid"] = blob_name
    return pub.__dict__
```

### Stage 20: Extract Text with Document AI

```python
from google.cloud import documentai_v1

@functions_framework.http
def gcp_run_query_20_extract(request):
    """Extract text using Document AI with hierarchical chunking"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["20-extract"]
    original_blob = pub.get_blob_guid("10-original")
    
    # Check cache
    cache_key = f"extract:{original_blob}"
    cached_guid = redis_client.get(cache_key)
    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True
        return pub.__dict__
    
    # Process with Document AI
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
    
    # Store as .10-processed.json
    blob_name = f"{pub.document_guid}.10-processed.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(hierarchical_chunks))
    
    # Update cache
    redis_client.setex(cache_key, 86400*30, blob_name)
    stage.after["blob_guid"] = blob_name
    stage.after["chunk_count"] = len(hierarchical_chunks)
    
    return pub.__dict__
```

### Stage 30: NLP Processing

```python
from google.cloud import language_v1

@functions_framework.http
def gcp_run_query_30_nlp(request):
    """Process each hierarchical level with NLP API"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["30-nlp"]
    extract_blob = pub.get_blob_guid("20-extract")
    
    # Load processed chunks
    blob = storage_client.bucket(bucket_name).blob(extract_blob)
    chunks = json.loads(blob.download_as_text())
    
    language_client = language_v1.LanguageServiceClient()
    nlp_results = {}
    
    for chunk in chunks:
        cache_key = f"nlp:{chunk['id']}"
        cached_nlp = redis_client.get(cache_key)
        
        if cached_nlp:
            nlp_results[chunk['id']] = json.loads(cached_nlp)
        else:
            # Full NLP analysis - store as-is per requirement
            document = language_v1.Document(
                content=chunk['content'],
                type_=language_v1.Document.Type.PLAIN_TEXT,
            )
            
            features = {
                "extract_entities": True,
                "extract_document_sentiment": True,
                "extract_entity_sentiment": True,
                "extract_syntax": True,
                "classify_text": len(chunk['content']) > 20  # Min length for classification
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
    
    # Store as .20-nlp.json
    blob_name = f"{pub.document_guid}.20-nlp.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(nlp_results))
    
    stage.after["blob_guid"] = blob_name
    return pub.__dict__
```

### Stage 40: Generate Embeddings

```python
from google.cloud import aiplatform

@functions_framework.http
def gcp_run_query_40_embed(request):
    """Generate embeddings using Vertex AI native dimensions"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["40-embed"]
    nlp_blob = pub.get_blob_guid("30-nlp")
    
    # Initialize Vertex AI
    aiplatform.init(project="PROJECT", location="us-central1")
    model = aiplatform.TextEmbeddingModel.from_pretrained("text-embedding-005")
    
    # Load NLP results
    blob = storage_client.bucket(bucket_name).blob(nlp_blob)
    nlp_data = json.loads(blob.download_as_text())
    
    embeddings = {}
    for chunk_id, nlp_result in nlp_data.items():
        cache_key = f"embed:{chunk_id}"
        cached_embed = redis_client.get(cache_key)
        
        if cached_embed:
            embeddings[chunk_id] = json.loads(cached_embed)
        else:
            # Get chunk content from processed data
            extract_blob = pub.get_blob_guid("20-extract")
            blob = storage_client.bucket(bucket_name).blob(extract_blob)
            chunks = json.loads(blob.download_as_text())
            
            chunk_content = next((c['content'] for c in chunks if c['id'] == chunk_id), "")
            
            # Generate embedding with smallest native dimension (256)
            embedding = model.get_embeddings(
                [chunk_content],
                output_dimensionality=256  # Smallest native dimension
            )[0].values
            
            embeddings[chunk_id] = embedding
            redis_client.setex(cache_key, 86400*30, json.dumps(embedding))
    
    # Store as .40-embed.json
    blob_name = f"{pub.document_guid}.40-embed.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(embeddings))
    
    stage.after["blob_guid"] = blob_name
    return pub.__dict__
```

### Stage 60: Vector Search

```python
from google.cloud import aiplatform_v1

@functions_framework.http
def gcp_run_query_60_search(request):
    """Search using Vertex AI Vector Search with native types"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["60-search"]
    embed_blob = pub.get_blob_guid("40-embed")
    nearest_n = stage.before.get("nearest_n", 10)
    
    # Load embeddings
    blob = storage_client.bucket(bucket_name).blob(embed_blob)
    embeddings = json.loads(blob.download_as_text())
    
    # Check cache for search results
    cache_key = f"search:{embed_blob}:{nearest_n}"
    cached_search = redis_client.get(cache_key)
    
    if cached_search and len(json.loads(cached_search)) >= nearest_n:
        stage.after["blob_guid"] = cached_search.decode()
        stage.cache_hit = True
        return pub.__dict__
    
    # Use Vertex AI Vector Search
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint("INDEX_ENDPOINT_ID")
    
    search_results = []
    for chunk_id, embedding in embeddings.items():
        # Find nearest neighbors
        response = index_endpoint.find_neighbors(
            deployed_index_id="DEPLOYED_INDEX_ID",
            queries=[embedding],
            num_neighbors=nearest_n
        )
        
        for neighbor in response[0]:
            search_results.append({
                "source_id": chunk_id,
                "neighbor_id": neighbor.id,
                "distance": neighbor.distance,
                "metric": "COSINE"  # Native metric
            })
    
    # Store as .60-search.json
    blob_name = f"{pub.document_guid}.60-search.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(search_results))
    
    # Update cache
    redis_client.setex(cache_key, 86400*30, blob_name)
    stage.after["blob_guid"] = blob_name
    
    return pub.__dict__
```

### Stage 70: Aggregate Results

```python
@functions_framework.http
def gcp_run_query_70_result(request):
    """Aggregate search results and return text"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["70-result"]
    search_blob = pub.get_blob_guid("60-search")
    nearest_n = stage.before.get("nearest_n", 10)
    
    # Load search results
    blob = storage_client.bucket(bucket_name).blob(search_blob)
    search_results = json.loads(blob.download_as_text())
    
    # Get unique neighbor IDs (top N by distance)
    neighbors = sorted(search_results, key=lambda x: x['distance'])[:nearest_n]
    neighbor_ids = list(set(n['neighbor_id'] for n in neighbors))
    
    # Retrieve neighbor texts
    result_texts = []
    for neighbor_id in neighbor_ids:
        # Parse neighbor_id to get document_guid
        parts = neighbor_id.split('.')
        neighbor_doc_guid = parts[0]
        
        # Load neighbor's processed text
        neighbor_blob = f"{neighbor_doc_guid}.10-processed.json"
        blob = storage_client.bucket(bucket_name).blob(neighbor_blob)
        
        if blob.exists():
            chunks = json.loads(blob.download_as_text())
            # Find specific chunk
            chunk = next((c for c in chunks if c['id'] == neighbor_id), None)
            if chunk:
                result_texts.append({
                    "id": neighbor_id,
                    "content": chunk['content'],
                    "hierarchy_path": chunk.get('hierarchy_path', [])
                })
    
    # Store as .70-result.json
    blob_name = f"{pub.document_guid}.70-result.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps(result_texts))
    
    stage.after["blob_guid"] = blob_name
    stage.after["content_result_text"] = result_texts
    
    return pub.__dict__
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
    
    -- NLP results (stored as-is)
    nlp_entities JSON,
    nlp_sentiment FLOAT64,
    nlp_categories JSON,
    
    -- Native embeddings (256d)
    embedding ARRAY<FLOAT64>,
    
    -- Blob references
    original_blob STRING,
    processed_blob STRING,
    nlp_blob STRING,
    embed_blob STRING,
    search_blob STRING,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY document_guid, level;

-- Query hierarchical relationships (up to 15 levels)
WITH RECURSIVE hierarchy AS (
    SELECT * FROM `project.dataset.document_hierarchy`
    WHERE parent_id IS NULL
    
    UNION ALL
    
    SELECT child.*
    FROM `project.dataset.document_hierarchy` child
    JOIN hierarchy parent ON child.parent_id = parent.chunk_id
    WHERE ARRAY_LENGTH(child.hierarchy_path) <= 15
)
SELECT * FROM hierarchy
WHERE document_guid = 'specific-doc-guid';
```

## Daily Scheduled Incremental Ingestion

### Cloud Scheduler Configuration

```yaml
# terraform/scheduler.tf
resource "google_cloud_scheduler_job" "daily_ingestion" {
  name        = "rag-daily-incremental-ingestion"
  description = "Daily incremental document ingestion"
  schedule    = "0 2 * * *"  # 2 AM UTC daily
  time_zone   = "UTC"
  
  http_target {
    uri         = "https://us-central1-${var.project_id}.cloudfunctions.net/gcp-run-incremental-ingestion"
    http_method = "POST"
    body        = base64encode(jsonencode({
      source_bucket = "corpus-source"
      target_bucket = "corpus-bucket"
      batch_size    = 50
    }))
    headers = {
      "Content-Type" = "application/json"
    }
  }
}
```

### Incremental Ingestion Function

```python
import functions_framework
from google.cloud import storage, workflows
from datetime import datetime, timezone, timedelta
import json
import hashlib

@functions_framework.http
def gcp_run_incremental_ingestion(request):
    """
    Daily incremental ingestion - only process if:
    file-source-datestamp-utc > file-blob-datestamp-utc
    """
    config = request.get_json()
    source_bucket = config.get('source_bucket', 'corpus-source')
    target_bucket = config.get('target_bucket', 'corpus-bucket')
    batch_size = config.get('batch_size', 50)
    
    storage_client = storage.Client()
    redis_client = redis.Client(host='10.0.0.1', port=6379)
    
    # Get all source files
    source_files = storage_client.bucket(source_bucket).list_blobs()
    
    documents_to_ingest = []
    skipped_count = 0
    
    for source_blob in source_files:
        # Skip if not a document file
        if not any(source_blob.name.endswith(ext) for ext in ['.md', '.pdf', '.txt', '.html']):
            continue
        
        # Get source file timestamp
        source_timestamp = source_blob.updated
        
        # Generate document GUID from content hash
        source_content = source_blob.download_as_bytes()
        content_hash = hashlib.sha256(source_content).hexdigest()[:16]
        document_guid = f"doc-{content_hash}-{source_blob.name.replace('/', '-')}"
        
        # Check if already processed
        cache_key = f"ingest:status:{document_guid}"
        cached_status = redis_client.get(cache_key)
        
        if cached_status:
            status = json.loads(cached_status)
            blob_timestamp = datetime.fromisoformat(status['blob_timestamp'])
            
            # Compare timestamps
            if source_timestamp <= blob_timestamp:
                skipped_count += 1
                continue
        
        # Check blob storage for existing processed files
        target_blobs = storage_client.bucket(target_bucket).list_blobs(
            prefix=f"{document_guid}.00-original"
        )
        
        newest_blob_timestamp = None
        for target_blob in target_blobs:
            if target_blob.metadata and 'timestamp' in target_blob.metadata:
                blob_dt = datetime.fromisoformat(target_blob.metadata['timestamp'])
                if not newest_blob_timestamp or blob_dt > newest_blob_timestamp:
                    newest_blob_timestamp = blob_dt
        
        # Determine if needs ingestion
        needs_ingestion = False
        if not newest_blob_timestamp:
            # Never processed
            needs_ingestion = True
        elif source_timestamp > newest_blob_timestamp:
            # Source is newer
            needs_ingestion = True
        
        if needs_ingestion:
            documents_to_ingest.append({
                "guid": document_guid,
                "content": source_content.decode('utf-8', errors='ignore'),
                "source_name": source_blob.name,
                "source_timestamp": source_timestamp.isoformat(),
                "extension": source_blob.name.split('.')[-1],
                "mime_type": source_blob.content_type or 'text/plain'
            })
        else:
            skipped_count += 1
    
    # Process in batches
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_scanned": skipped_count + len(documents_to_ingest),
        "to_ingest": len(documents_to_ingest),
        "skipped": skipped_count,
        "batches": []
    }
    
    for i in range(0, len(documents_to_ingest), batch_size):
        batch = documents_to_ingest[i:i+batch_size]
        
        # Trigger workflow for batch
        workflow_result = trigger_ingestion_workflow(batch)
        results["batches"].append(workflow_result)
        
        # Update cache with ingestion status
        for doc in batch:
            cache_key = f"ingest:status:{doc['guid']}"
            redis_client.setex(cache_key, 86400*30, json.dumps({
                "blob_timestamp": datetime.now(timezone.utc).isoformat(),
                "source_timestamp": doc['source_timestamp'],
                "workflow_id": workflow_result['execution_id']
            }))
    
    # Store ingestion report
    report_blob = storage_client.bucket(target_bucket).blob(
        f"ingestion-reports/{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    )
    report_blob.upload_from_string(json.dumps(results))
    
    return results

def trigger_ingestion_workflow(documents):
    """Trigger Cloud Workflow for document batch"""
    workflows_client = workflows.WorkflowsClient()
    parent = workflows_client.workflow_path(
        "PROJECT", "us-central1", "rag-ingest-pipeline"
    )
    
    execution = workflows_client.create_execution(
        parent=parent,
        execution={
            "argument": json.dumps({
                "documents": documents,
                "batch_size": len(documents)
            })
        }
    )
    
    return {
        "execution_id": execution.name,
        "document_count": len(documents),
        "document_guids": [doc['guid'] for doc in documents]
    }

@functions_framework.http
def gcp_run_incremental_check(request):
    """
    Check individual file for incremental update need
    Returns: needs_update (bool), reason (str)
    """
    data = request.get_json()
    source_path = data['source_path']
    document_guid = data.get('document_guid')
    
    storage_client = storage.Client()
    redis_client = redis.Client(host='10.0.0.1', port=6379)
    
    # Get source file
    source_bucket, source_name = source_path.replace('gs://', '').split('/', 1)
    source_blob = storage_client.bucket(source_bucket).blob(source_name)
    
    if not source_blob.exists():
        return {"needs_update": False, "reason": "source_not_found"}
    
    source_timestamp = source_blob.updated
    
    # Generate document GUID if not provided
    if not document_guid:
        content = source_blob.download_as_bytes()
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        document_guid = f"doc-{content_hash}-{source_name.replace('/', '-')}"
    
    # Check cache
    cache_key = f"ingest:status:{document_guid}"
    cached_status = redis_client.get(cache_key)
    
    if cached_status:
        status = json.loads(cached_status)
        blob_timestamp = datetime.fromisoformat(status['blob_timestamp'])
        
        if source_timestamp > blob_timestamp:
            return {
                "needs_update": True,
                "reason": "source_newer",
                "source_timestamp": source_timestamp.isoformat(),
                "blob_timestamp": blob_timestamp.isoformat()
            }
        else:
            return {
                "needs_update": False,
                "reason": "up_to_date",
                "source_timestamp": source_timestamp.isoformat(),
                "blob_timestamp": blob_timestamp.isoformat()
            }
    
    # Check blob storage
    target_bucket = storage_client.bucket('corpus-bucket')
    blobs = target_bucket.list_blobs(prefix=f"{document_guid}.00-original")
    
    newest_blob = None
    for blob in blobs:
        if not newest_blob or blob.updated > newest_blob.updated:
            newest_blob = blob
    
    if newest_blob:
        blob_timestamp = newest_blob.updated
        
        if source_timestamp > blob_timestamp:
            return {
                "needs_update": True,
                "reason": "source_newer",
                "source_timestamp": source_timestamp.isoformat(),
                "blob_timestamp": blob_timestamp.isoformat()
            }
        else:
            # Update cache
            redis_client.setex(cache_key, 86400*30, json.dumps({
                "blob_timestamp": blob_timestamp.isoformat(),
                "source_timestamp": source_timestamp.isoformat()
            }))
            
            return {
                "needs_update": False,
                "reason": "up_to_date",
                "source_timestamp": source_timestamp.isoformat(),
                "blob_timestamp": blob_timestamp.isoformat()
            }
    
    # Never processed
    return {
        "needs_update": True,
        "reason": "never_processed",
        "source_timestamp": source_timestamp.isoformat()
    }

@functions_framework.http
def gcp_run_ingestion_monitor(request):
    """Monitor ingestion status and retry failures"""
    storage_client = storage.Client()
    redis_client = redis.Client(host='10.0.0.1', port=6379)
    
    # Get recent ingestion reports
    reports_bucket = storage_client.bucket('corpus-bucket')
    reports = reports_bucket.list_blobs(
        prefix='ingestion-reports/',
        max_results=10
    )
    
    summary = {
        "last_24h": {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "pending": 0
        },
        "failed_documents": [],
        "pending_retries": []
    }
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    for report_blob in reports:
        if report_blob.updated < cutoff:
            continue
        
        report = json.loads(report_blob.download_as_text())
        summary["last_24h"]["total_processed"] += report["to_ingest"]
        
        # Check workflow statuses
        for batch in report.get("batches", []):
            execution_status = check_workflow_status(batch["execution_id"])
            
            if execution_status == "SUCCEEDED":
                summary["last_24h"]["successful"] += batch["document_count"]
            elif execution_status == "FAILED":
                summary["last_24h"]["failed"] += batch["document_count"]
                summary["failed_documents"].extend(batch["document_guids"])
            else:
                summary["last_24h"]["pending"] += batch["document_count"]
    
    # Retry failed documents
    if summary["failed_documents"]:
        retry_documents = []
        for doc_guid in summary["failed_documents"]:
            # Clear cache to force reprocessing
            cache_key = f"ingest:status:{doc_guid}"
            redis_client.delete(cache_key)
            retry_documents.append(doc_guid)
        
        summary["pending_retries"] = retry_documents
    
    return summary

def check_workflow_status(execution_id):
    """Check Cloud Workflow execution status"""
    workflows_client = workflows.WorkflowsClient()
    
    try:
        execution = workflows_client.get_execution(name=execution_id)
        return execution.state.name  # SUCCEEDED, FAILED, RUNNING, etc.
    except Exception as e:
        return "UNKNOWN"
```

### Modified Cloud Workflows for Incremental Support

```yaml
# workflows/rag-incremental-ingest.yaml
main:
  params: [input]
  steps:
    - init:
        assign:
          - documents: ${input.documents}
          - results: []
          - skipped: []
    
    - process_documents:
        for:
          value: doc
          in: ${documents}
          steps:
            # Check if needs processing
            - check_update:
                call: http.post
                args:
                  url: https://us-central1-PROJECT.cloudfunctions.net/gcp-run-incremental-check
                  body:
                    source_path: ${doc.source_path}
                    document_guid: ${doc.guid}
                result: check_result
            
            - process_if_needed:
                switch:
                  - condition: ${check_result.needs_update == true}
                    steps:
                      - ingest_document:
                          call: sub_workflow_ingest
                          args:
                            document: ${doc}
                          result: ingest_result
                      - append_result:
                          assign:
                            - results: ${list.concat(results, ingest_result)}
                  - condition: ${check_result.needs_update == false}
                    steps:
                      - append_skipped:
                          assign:
                            - skipped: ${list.concat(skipped, doc.guid)}
    
    - return_summary:
        return:
          processed: ${len(results)}
          skipped: ${len(skipped)}
          results: ${results}
          skipped_ids: ${skipped}
```

## Document Ingestion Pipeline (gcp-run-ingest-*)

### Cloud Workflows for Ingestion

```yaml
# workflows/rag-ingest-pipeline.yaml
main:
  params: [input]
  steps:
    - init:
        assign:
          - documents: ${input.documents}
          - batch_size: ${default(input.batch_size, 10)}
          - results: []
    
    # Process documents in batches
    - process_batch:
        for:
          value: doc
          in: ${documents}
          steps:
            - create_pub:
                assign:
                  - pub:
                      document_guid: ${doc.guid}
                      message: ${doc.content}
                      extension: ${default(doc.extension, "md")}
                      mime_type: ${default(doc.mime_type, "text/plain")}
                      stages: {}
            
            # Stage 00: Initialize
            - init_stages:
                call: http.post
                args:
                  url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-ingest-00-orchestrator
                  body:
                    pub: ${pub}
                result: pub
            
            # Stage 01-10: Original document
            - cache_original:
                call: http.post
                args:
                  url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-ingest-01-cache-original-lookup
                  body:
                    pub: ${pub}
                result: pub
            
            - process_original:
                switch:
                  - condition: ${pub.stages["10-original"].cache_hit == false}
                    call: http.post
                    args:
                      url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-ingest-10-original
                      body:
                        pub: ${pub}
                    result: pub
            
            # Stage 02-20: Extract text
            - cache_extract:
                call: http.post
                args:
                  url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-ingest-02-cache-extract-lookup
                  body:
                    pub: ${pub}
                result: pub
            
            - process_extract:
                switch:
                  - condition: ${pub.stages["20-extract"].cache_hit == false}
                    call: http.post
                    args:
                      url: https://us-central1-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}.cloudfunctions.net/gcp-run-ingest-20-extract
                      body:
                        pub: ${pub}
                    result: pub
            
            # Continue for all stages...
            - append_result:
                assign:
                  - results: ${list.concat(results, pub)}
    
    - return_results:
        return:
          total: ${len(results)}
          documents: ${results}
```

### Ingestion Functions Implementation

```python
import functions_framework
from google.cloud import storage, redis, bigquery, documentai_v1, language_v1, aiplatform
from datetime import datetime, timezone
import hashlib
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Initialize clients
redis_client = redis.Client(host='10.0.0.1', port=6379)
storage_client = storage.Client()
bigquery_client = bigquery.Client()
bucket_name = 'corpus-bucket'
dataset_id = 'rag_dataset'
table_id = 'document_hierarchy'

@functions_framework.http
def gcp_run_ingest_00_orchestrator(request):
    """Initialize ingestion pipeline"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    # Initialize stages for ingestion
    pub.stages = {
        "10-original": PubStage(stage_name="10-original"),
        "20-extract": PubStage(stage_name="20-extract"),
        "30-nlp": PubStage(stage_name="30-nlp"),
        "40-embed": PubStage(stage_name="40-embed"),
        "50-bigquery": PubStage(stage_name="50-bigquery"),
        "60-index": PubStage(stage_name="60-index")
    }
    
    # Set initial content
    pub.stages["10-original"].before["content_bytes"] = pub.message.encode()
    pub.stages["10-original"].before["extension"] = getattr(pub, 'extension', 'md')
    pub.stages["10-original"].before["mime_type"] = getattr(pub, 'mime_type', 'text/plain')
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_01_cache_original_lookup(request):
    """Check if document already ingested"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["10-original"]
    cache_key = f"ingest:original:{stage.get_hash()}"
    
    cached_guid = redis_client.get(cache_key)
    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True
        
        # Check if document needs re-processing (daily update pattern)
        blob = storage_client.bucket(bucket_name).blob(cached_guid.decode())
        if blob.exists():
            metadata = blob.metadata or {}
            cached_timestamp = metadata.get('timestamp', '')
            
            # Re-process if older than 24 hours
            if cached_timestamp:
                cached_dt = datetime.fromisoformat(cached_timestamp)
                current_dt = datetime.now(timezone.utc)
                if (current_dt - cached_dt).total_seconds() > 86400:
                    stage.cache_hit = False
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_10_original(request):
    """Store original document"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["10-original"]
    if stage.cache_hit:
        return pub.__dict__
    
    # Store with versioning
    timestamp = datetime.now(timezone.utc)
    version = timestamp.strftime("%Y%m%d%H%M%S")
    blob_name = f"{pub.document_guid}.00-original.v{version}.{stage.before['extension']}"
    
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {
        'timestamp': timestamp.isoformat(),
        'version': version,
        'document_guid': pub.document_guid
    }
    blob.upload_from_string(stage.before['content_bytes'])
    
    # Update cache
    cache_key = f"ingest:original:{stage.get_hash()}"
    redis_client.setex(cache_key, 86400*30, blob_name)
    
    stage.after["blob_guid"] = blob_name
    stage.after["version"] = version
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_02_cache_extract_lookup(request):
    """Check cache for extracted text"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["20-extract"]
    original_blob = pub.get_blob_guid("10-original")
    
    cache_key = f"ingest:extract:{original_blob}"
    cached_guid = redis_client.get(cache_key)
    
    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_20_extract(request):
    """Extract and chunk document with hierarchy"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["20-extract"]
    if stage.cache_hit:
        return pub.__dict__
    
    original_blob = pub.get_blob_guid("10-original")
    
    # Document AI batch processing for efficiency
    doc_ai = documentai_v1.DocumentProcessorServiceClient()
    
    # For batch ingestion, use batch processing
    batch_request = {
        "name": "projects/PROJECT/locations/us/processors/PROCESSOR_ID",
        "input_configs": [{
            "gcs_source": {
                "uri": f"gs://{bucket_name}/{original_blob}"
            },
            "mime_type": pub.stages["10-original"].before["mime_type"]
        }],
        "output_config": {
            "gcs_destination": {
                "uri": f"gs://{bucket_name}/temp-extract/"
            }
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
    
    operation = doc_ai.batch_process_documents(batch_request)
    result = operation.result(timeout=300)
    
    # Parse hierarchical structure
    hierarchical_chunks = []
    chunk_index = 0
    
    for batch_output in result.output_configs:
        # Read processed output
        output_blob = storage_client.bucket(bucket_name).blob(
            batch_output.gcs_destination.uri.replace(f"gs://{bucket_name}/", "")
        )
        document = json.loads(output_blob.download_as_text())
        
        # Build hierarchy (up to 15 levels)
        for page_idx, page in enumerate(document.get('pages', [])):
            page_id = f"{pub.document_guid}.L01-{page_idx:04d}"
            
            for section_idx, section in enumerate(page.get('sections', [])):
                section_id = f"{page_id}.L02-{section_idx:04d}"
                
                for block_idx, block in enumerate(section.get('blocks', [])):
                    block_id = f"{section_id}.L03-{block_idx:04d}"
                    
                    hierarchical_chunks.append({
                        "id": block_id,
                        "content": block.get('text', ''),
                        "parent_id": section_id,
                        "level": 3,
                        "hierarchy_path": [
                            pub.document_guid,
                            f"L01-{page_idx:04d}",
                            f"L02-{section_idx:04d}",
                            f"L03-{block_idx:04d}"
                        ],
                        "chunk_index": chunk_index,
                        "metadata": {
                            "page": page_idx,
                            "section": section_idx,
                            "block": block_idx
                        }
                    })
                    chunk_index += 1
    
    # Store processed chunks
    version = pub.stages["10-original"].after.get("version", "")
    blob_name = f"{pub.document_guid}.10-processed.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp, 'chunk_count': len(hierarchical_chunks)}
    blob.upload_from_string(json.dumps(hierarchical_chunks))
    
    # Update cache
    cache_key = f"ingest:extract:{original_blob}"
    redis_client.setex(cache_key, 86400*30, blob_name)
    
    stage.after["blob_guid"] = blob_name
    stage.after["chunk_count"] = len(hierarchical_chunks)
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_03_cache_nlp_lookup(request):
    """Check NLP cache for all chunks"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["30-nlp"]
    extract_blob = pub.get_blob_guid("20-extract")
    
    cache_key = f"ingest:nlp:{extract_blob}"
    cached_guid = redis_client.get(cache_key)
    
    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_30_nlp(request):
    """Batch NLP processing for all chunks"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["30-nlp"]
    if stage.cache_hit:
        return pub.__dict__
    
    extract_blob = pub.get_blob_guid("20-extract")
    
    # Load chunks
    blob = storage_client.bucket(bucket_name).blob(extract_blob)
    chunks = json.loads(blob.download_as_text())
    
    language_client = language_v1.LanguageServiceClient()
    nlp_results = {}
    
    # Batch process with thread pool for efficiency
    def process_chunk(chunk):
        chunk_id = chunk['id']
        cache_key = f"nlp:chunk:{chunk_id}"
        
        # Check individual chunk cache
        cached = redis_client.get(cache_key)
        if cached:
            return chunk_id, json.loads(cached)
        
        # Process with NLP API
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
        
        try:
            response = language_client.annotate_text(
                request={"document": document, "features": features}
            )
            
            # Store complete response
            nlp_json = {
                "entities": [
                    {
                        "name": e.name,
                        "type": e.type_.name,
                        "salience": e.salience,
                        "mentions": [{"text": m.text.content, "type": m.type_.name} for m in e.mentions]
                    }
                    for e in response.entities
                ],
                "sentiment": {
                    "score": response.document_sentiment.score,
                    "magnitude": response.document_sentiment.magnitude
                },
                "categories": [
                    {"name": c.name, "confidence": c.confidence}
                    for c in response.categories
                ] if response.categories else [],
                "syntax": {
                    "tokens": len(response.tokens),
                    "sentences": len(response.sentences)
                },
                "language": response.language,
                "chunk_metadata": chunk.get('metadata', {})
            }
            
            # Cache individual result
            redis_client.setex(cache_key, 86400*30, json.dumps(nlp_json))
            
            return chunk_id, nlp_json
            
        except Exception as e:
            print(f"NLP error for chunk {chunk_id}: {e}")
            return chunk_id, {"error": str(e)}
    
    # Process in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        for future in futures:
            chunk_id, nlp_result = future.result()
            nlp_results[chunk_id] = nlp_result
    
    # Store aggregated results
    version = pub.stages["10-original"].after.get("version", "")
    blob_name = f"{pub.document_guid}.20-nlp.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp, 'processed_chunks': len(nlp_results)}
    blob.upload_from_string(json.dumps(nlp_results))
    
    # Update cache
    cache_key = f"ingest:nlp:{extract_blob}"
    redis_client.setex(cache_key, 86400*30, blob_name)
    
    stage.after["blob_guid"] = blob_name
    stage.after["processed_count"] = len(nlp_results)
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_04_cache_embed_lookup(request):
    """Check embedding cache"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["40-embed"]
    nlp_blob = pub.get_blob_guid("30-nlp")
    
    cache_key = f"ingest:embed:{nlp_blob}"
    cached_guid = redis_client.get(cache_key)
    
    if cached_guid:
        stage.after["blob_guid"] = cached_guid.decode()
        stage.cache_hit = True
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_40_embed(request):
    """Generate embeddings for all chunks"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["40-embed"]
    if stage.cache_hit:
        return pub.__dict__
    
    # Initialize Vertex AI
    aiplatform.init(project="PROJECT", location="us-central1")
    model = aiplatform.TextEmbeddingModel.from_pretrained("text-embedding-005")
    
    # Load chunks and NLP results
    extract_blob = pub.get_blob_guid("20-extract")
    blob = storage_client.bucket(bucket_name).blob(extract_blob)
    chunks = json.loads(blob.download_as_text())
    
    # Batch embedding generation
    embeddings = {}
    batch_size = 100  # Vertex AI batch limit
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [chunk['content'] for chunk in batch]
        
        # Generate embeddings with smallest native dimension
        batch_embeddings = model.get_embeddings(
            texts,
            output_dimensionality=256  # Smallest native
        )
        
        for chunk, embedding in zip(batch, batch_embeddings):
            embeddings[chunk['id']] = {
                "values": embedding.values,
                "metadata": {
                    "level": chunk['level'],
                    "parent_id": chunk.get('parent_id'),
                    "chunk_index": chunk.get('chunk_index', 0)
                }
            }
    
    # Store embeddings
    version = pub.stages["10-original"].after.get("version", "")
    blob_name = f"{pub.document_guid}.40-embed.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp, 'embedding_count': len(embeddings)}
    blob.upload_from_string(json.dumps(embeddings))
    
    # Update cache
    cache_key = f"ingest:embed:{pub.get_blob_guid('30-nlp')}"
    redis_client.setex(cache_key, 86400*30, blob_name)
    
    stage.after["blob_guid"] = blob_name
    stage.after["embedding_count"] = len(embeddings)
    
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_50_bigquery(request):
    """Store hierarchical data in BigQuery"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["50-bigquery"]
    
    # Load all processed data
    extract_blob = pub.get_blob_guid("20-extract")
    nlp_blob = pub.get_blob_guid("30-nlp")
    embed_blob = pub.get_blob_guid("40-embed")
    
    chunks = json.loads(storage_client.bucket(bucket_name).blob(extract_blob).download_as_text())
    nlp_results = json.loads(storage_client.bucket(bucket_name).blob(nlp_blob).download_as_text())
    embeddings = json.loads(storage_client.bucket(bucket_name).blob(embed_blob).download_as_text())
    
    # Prepare rows for BigQuery
    rows = []
    for chunk in chunks:
        chunk_id = chunk['id']
        nlp = nlp_results.get(chunk_id, {})
        embed = embeddings.get(chunk_id, {})
        
        row = {
            "chunk_id": chunk_id,
            "document_guid": pub.document_guid,
            "level": chunk['level'],
            "parent_id": chunk.get('parent_id'),
            "hierarchy_path": chunk['hierarchy_path'],
            "content": chunk['content'],
            
            # NLP results
            "nlp_entities": json.dumps(nlp.get('entities', [])),
            "nlp_sentiment": nlp.get('sentiment', {}).get('score'),
            "nlp_categories": json.dumps(nlp.get('categories', [])),
            
            # Embeddings
            "embedding": embed.get('values', []),
            
            # Blob references
            "original_blob": pub.get_blob_guid("10-original"),
            "processed_blob": extract_blob,
            "nlp_blob": nlp_blob,
            "embed_blob": embed_blob,
            
            # Metadata
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "version": pub.stages["10-original"].after.get("version", "")
        }
        rows.append(row)
    
    # Insert into BigQuery
    table_ref = bigquery_client.dataset(dataset_id).table(table_id)
    errors = bigquery_client.insert_rows_json(table_ref, rows)
    
    if errors:
        print(f"BigQuery insert errors: {errors}")
        stage.after["errors"] = errors
    else:
        stage.after["inserted_rows"] = len(rows)
    
    stage.after["completed"] = True
    return pub.__dict__

@functions_framework.http
def gcp_run_ingest_60_index(request):
    """Add embeddings to Vertex AI Vector Search index"""
    pub_data = request.get_json()['pub']
    pub = Pub(**pub_data)
    
    stage = pub.stages["60-index"]
    embed_blob = pub.get_blob_guid("40-embed")
    
    # Load embeddings
    blob = storage_client.bucket(bucket_name).blob(embed_blob)
    embeddings = json.loads(blob.download_as_text())
    
    # Initialize Vertex AI Vector Search
    aiplatform.init(project="PROJECT", location="us-central1")
    
    # Get or create index
    index_id = "rag-corpus-index"
    try:
        index = aiplatform.MatchingEngineIndex(index_id)
    except:
        # Create index if doesn't exist
        index = aiplatform.MatchingEngineIndex.create(
            display_name="RAG Corpus Index",
            dimensions=256,
            approximate_neighbors_count=100,
            distance_measure_type="COSINE_DISTANCE",
            index_update_method="STREAM_UPDATE"
        )
    
    # Prepare datapoints
    datapoints = []
    for chunk_id, embedding_data in embeddings.items():
        datapoints.append({
            "datapoint_id": chunk_id,
            "feature_vector": embedding_data['values'],
            "restricts": [
                {"namespace": "document_guid", "allow_list": [pub.document_guid]},
                {"namespace": "level", "allow_list": [str(embedding_data['metadata']['level'])]}
            ]
        })
    
    # Batch upsert (more efficient for ingestion)
    batch_size = 1000
    for i in range(0, len(datapoints), batch_size):
        batch = datapoints[i:i+batch_size]
        index.upsert_datapoints(batch)
    
    # Store indexing metadata
    version = pub.stages["10-original"].after.get("version", "")
    blob_name = f"{pub.document_guid}.60-index.v{version}.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.metadata = {'timestamp': pub.timestamp}
    blob.upload_from_string(json.dumps({
        "indexed_count": len(datapoints),
        "index_id": index_id,
        "version": version
    }))
    
    stage.after["blob_guid"] = blob_name
    stage.after["indexed_count"] = len(datapoints)
    
    return pub.__dict__

# Batch ingestion orchestrator for multiple documents
@functions_framework.http
def gcp_run_ingest_batch(request):
    """Handle batch document ingestion"""
    documents = request.get_json().get('documents', [])
    batch_id = request.get_json().get('batch_id', datetime.now().strftime("%Y%m%d%H%M%S"))
    
    results = {
        "batch_id": batch_id,
        "total": len(documents),
        "successful": 0,
        "failed": 0,
        "documents": []
    }
    
    # Process documents in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        
        for doc in documents:
            # Create workflow execution for each document
            workflow_client = workflows.WorkflowsClient()
            parent = workflow_client.workflow_path("PROJECT", "us-central1", "rag-ingest-pipeline")
            
            execution = workflow_client.create_execution(
                parent=parent,
                execution={
                    "argument": json.dumps({
                        "documents": [doc],
                        "batch_size": 1
                    })
                }
            )
            futures.append(executor.submit(wait_for_execution, execution))
        
        # Collect results
        for future in futures:
            try:
                result = future.result(timeout=600)
                results["successful"] += 1
                results["documents"].append(result)
            except Exception as e:
                results["failed"] += 1
                results["documents"].append({"error": str(e)})
    
    # Store batch results
    blob_name = f"batch-{batch_id}.result.json"
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.upload_from_string(json.dumps(results))
    
    return results
```

## Redis Cache Key Structure

```python
# Composite keys for efficient lookups
cache_keys = {
    "original": "original:{content_hash}",
    "extract": "extract:{original_blob_guid}",
    "nlp": "nlp:{chunk_id}",
    "embed": "embed:{chunk_id}",
    "search": "search:{embed_blob_guid}:{n}",
    "index": "index:{document_guid}"
}

# TTL: 30 days for all cache entries
TTL_SECONDS = 86400 * 30
```

## Cost Optimization

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| Cloud Workflows | 10K executions | $5 |
| Cloud Functions | 50K invocations | $20 |
| Memorystore Redis | 1GB Basic | $35 |
| Cloud Storage | 100GB Standard | $2 |
| BigQuery | 10GB storage, 1TB queries | $50 |
| Document AI | 1000 pages | Free tier |
| Natural Language API | 5000 units | $5 |
| Vertex AI Embeddings | 1M tokens (256d) | $10 |
| Vertex AI Vector Search | 2 nodes | $400 |
| **Total** | | **~$527/month** |

## Key Benefits

1. **Native GCP types only** - No custom quantization needed
2. **Explainable** - Every stage preserved with timestamps
3. **Hierarchical** - Up to 15 levels in BigQuery
4. **Cached** - Efficient composite key lookups
5. **Low latency** - Cloud Workflows orchestration
6. **Scalable** - Handles incremental daily updates
7. **Separation of concerns** - Each stage independent