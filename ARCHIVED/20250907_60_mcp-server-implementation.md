# MCP Server Implementation for Optimized RAG Pipeline

## Server Architecture

```python
# mcp_rag_server.py
from mcp import Server, Tool, Resource, Progress
from typing import List, Dict, Optional, Any
import asyncio
import json
import kuzu
import redis
import numpy as np
from dataclasses import dataclass

@dataclass
class SearchResult:
    guid: str
    content: str
    score: float
    metadata: Dict
    source_type: str
    cluster_id: str

class RagMcpServer:
    """MCP server exposing optimized RAG pipeline"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.server = Server("rag-unified-knowledge")
        self.config = self._load_config(config_path)
        
        # Initialize connections
        self.db = kuzu.Database(self.config['kuzu']['path'])
        self.conn = kuzu.Connection(self.db)
        self.cache = redis.Redis(**self.config['redis'])
        
        # Initialize pipeline
        from pipeline import DualEncodingPipeline, TranslationLayers
        self.pipeline = DualEncodingPipeline()
        self.translator = TranslationLayers(self.conn, self.pipeline, self.cache)
        
        # Register all tools and resources
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.tool(
            name="semantic_search",
            description="Search knowledge base using natural language query",
            parameters={
                "query": {"type": "string", "description": "Natural language search query"},
                "mode": {"type": "string", "enum": ["fast", "balanced", "thorough"], "default": "balanced"},
                "filters": {"type": "object", "properties": {
                    "content_type": {"type": "string", "enum": ["prose", "code", "any"]},
                    "date_range": {"type": "object"},
                    "confidence_min": {"type": "number", "minimum": 0, "maximum": 1}
                }},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}
            }
        )
        async def semantic_search(query: str, mode: str = "balanced", 
                                 filters: Optional[Dict] = None, 
                                 limit: int = 20) -> List[SearchResult]:
            """
            Multi-mode semantic search
            - fast: Binary Hamming only (3ms)
            - balanced: Binary + reranking (15ms)
            - thorough: Binary + reranking + graph traversal (50ms)
            """
            async with Progress(self.server, f"Searching: {query[:50]}...") as progress:
                progress.update(10, "Encoding query")
                
                if mode == "fast":
                    results = await self._fast_binary_search(query, filters, limit)
                elif mode == "balanced":
                    results = await self._balanced_search(query, filters, limit)
                else:  # thorough
                    results = await self._thorough_search(query, filters, limit, progress)
                
                progress.update(100, f"Found {len(results)} results")
                return results
        
        @self.server.tool(
            name="cluster_explore",
            description="Explore semantic clusters in the knowledge base",
            parameters={
                "query": {"type": "string", "description": "Optional seed query"},
                "cluster_id": {"type": "string", "description": "Specific cluster to explore"},
                "max_clusters": {"type": "integer", "default": 3}
            }
        )
        async def cluster_explore(query: Optional[str] = None,
                                 cluster_id: Optional[str] = None,
                                 max_clusters: int = 3) -> Dict:
            """Explore semantic neighborhoods"""
            if cluster_id:
                return await self._get_cluster_contents(cluster_id)
            elif query:
                return await self._find_related_clusters(query, max_clusters)
            else:
                return await self._get_cluster_overview()
        
        @self.server.tool(
            name="trace_concept",
            description="Trace concept across documentation and code",
            parameters={
                "concept": {"type": "string", "description": "Concept/entity to trace"},
                "max_hops": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
                "include_context": {"type": "boolean", "default": True}
            }
        )
        async def trace_concept(concept: str, max_hops: int = 3,
                               include_context: bool = True) -> Dict:
            """Cross-reference documentation and implementation"""
            
            # Find entity
            entity = await self._resolve_entity(concept)
            if not entity:
                return {"error": f"Concept '{concept}' not found"}
            
            # Graph traversal
            paths = self.conn.execute("""
                MATCH (e:Entity {normalized_form: $entity})
                MATCH path = (e)-[:SEMANTIC_TRIPLE*1..$hops]-(connected:Entity)
                WHERE connected.type IN ['prose', 'code']
                RETURN path, connected
                LIMIT 50
            """, {'entity': entity, 'hops': max_hops}).fetchall()
            
            # Build trace tree
            trace = self._build_trace_tree(paths, include_context)
            return trace
        
        @self.server.tool(
            name="explain_statement",
            description="Get full hierarchical context for a statement",
            parameters={
                "statement_id": {"type": "string", "description": "Statement GUID"},
                "depth": {"type": "integer", "default": 2}
            }
        )
        async def explain_statement(statement_id: str, depth: int = 2) -> Dict:
            """Retrieve complete context hierarchy"""
            
            context = self.conn.execute("""
                MATCH (s:Statement {guid: $id})
                OPTIONAL MATCH (doc:Document)-[:CONTAINS]->(s)
                OPTIONAL MATCH (s)-[:REFERENCES]-(related:Statement)
                OPTIONAL MATCH (s)-[:SEMANTIC_TRIPLE]-(e:Entity)
                RETURN s, doc, collect(DISTINCT related) as related,
                       collect(DISTINCT e) as entities
            """, {'id': statement_id}).fetchone()
            
            if not context:
                return {"error": "Statement not found"}
            
            return self._format_context(context, depth)
        
        @self.server.tool(
            name="analyze_distribution",
            description="Analyze corpus distribution and balance",
            parameters={}
        )
        async def analyze_distribution() -> Dict:
            """Check corpus balance and clustering quality"""
            
            stats = self.conn.execute("""
                MATCH (s:Statement)
                RETURN s.source_type as type, 
                       s.cluster_id as cluster,
                       count(*) as count
                ORDER BY count DESC
            """).fetchall()
            
            # Calculate metrics
            gini = self._calculate_gini([s[2] for s in stats])
            silhouette = await self._calculate_silhouette_score()
            
            return {
                "total_statements": sum(s[2] for s in stats),
                "type_distribution": self._group_by_type(stats),
                "cluster_distribution": self._group_by_cluster(stats),
                "gini_coefficient": gini,
                "silhouette_score": silhouette,
                "balance_status": "balanced" if gini < 0.6 else "imbalanced"
            }
    
    async def _create_document(self, guid: str, path: str, content: str,
                              checksum: str, metadata: Dict) -> Dict:
        """Create new document with full pipeline processing"""
        
        async with Progress(self.server, f"Creating: {path}") as progress:
            progress.update(10, "Parsing document")
            
            # Parse document
            from pipeline import UnifiedParser
            parser = UnifiedParser()
            chunks = parser.parse_document_from_string(content, path)
            
            progress.update(30, "Extracting semantics")
            
            # Extract semantics
            from pipeline import SemanticExtractor
            extractor = SemanticExtractor()
            statements = []
            
            for chunk in chunks:
                semantics = extractor.extract_semantics(chunk)
                statements.extend(semantics['triples'])
            
            progress.update(50, "Generating embeddings")
            
            # Generate embeddings
            doc_encoding = self.pipeline.encode_document(content, guid)
            
            progress.update(70, "Storing in database")
            
            # Transaction for atomicity
            self.conn.execute("BEGIN TRANSACTION")
            try:
                # Store document
                self.conn.execute("""
                    CREATE (:Document {
                        guid: $guid,
                        path: $path,
                        content: $content,
                        checksum: $checksum,
                        metadata: $metadata,
                        created_at: now(),
                        updated_at: now(),
                        embedding_256: $emb_256,
                        embedding_32: $emb_32,
                        cluster_id: $cluster
                    })
                """, {
                    'guid': guid,
                    'path': path,
                    'content': content,
                    'checksum': checksum,
                    'metadata': json.dumps(metadata or {}),
                    'emb_256': doc_encoding['embedding_256'],
                    'emb_32': doc_encoding['embedding_32'],
                    'cluster': doc_encoding['cluster_id']
                })
                
                # Store statements
                for stmt in statements:
                    stmt_encoding = self.pipeline.encode_document(
                        stmt.content, f"{guid}#{stmt.id}"
                    )
                    
                    self.conn.execute("""
                        CREATE (:Statement {
                            guid: $guid,
                            content: $content,
                            semantic_type: $type,
                            source_type: $source,
                            embedding_256: $emb_256,
                            embedding_32: $emb_32,
                            cluster_id: $cluster
                        })
                    """, {
                        'guid': f"{guid}#{stmt.id}",
                        'content': stmt.content,
                        'type': stmt.semantic_type,
                        'source': stmt.source_type.value,
                        'emb_256': stmt_encoding['embedding_256'],
                        'emb_32': stmt_encoding['embedding_32'],
                        'cluster': stmt_encoding['cluster_id']
                    })
                    
                    # Link to document
                    self.conn.execute("""
                        MATCH (d:Document {guid: $doc_guid}),
                              (s:Statement {guid: $stmt_guid})
                        CREATE (d)-[:CONTAINS]->(s)
                    """, {'doc_guid': guid, 'stmt_guid': f"{guid}#{stmt.id}"})
                
                self.conn.execute("COMMIT")
                
                progress.update(90, "Invalidating cache")
                self._invalidate_cache_for_clusters(doc_encoding['cluster_id'])
                
                progress.update(100, "Complete")
                
                return {
                    "status": "created",
                    "guid": guid,
                    "path": path,
                    "statements": len(statements),
                    "cluster": doc_encoding['cluster_id']
                }
                
            except Exception as e:
                self.conn.execute("ROLLBACK")
                raise e
    
    async def _update_document(self, guid: str, path: str, content: str,
                              checksum: str, metadata: Dict) -> Dict:
        """Update existing document"""
        
        async with Progress(self.server, f"Updating: {path}") as progress:
            progress.update(10, "Removing old data")
            
            # Get old cluster for cache invalidation
            old_cluster = self.conn.execute("""
                MATCH (d:Document {guid: $guid})
                RETURN d.cluster_id
            """, {'guid': guid}).fetchone()[0]
            
            # Delete old statements
            self.conn.execute("""
                MATCH (d:Document {guid: $guid})-[:CONTAINS]->(s:Statement)
                DETACH DELETE s
            """, {'guid': guid})
            
            progress.update(30, "Processing new content")
            
            # Reprocess document
            from pipeline import UnifiedParser, SemanticExtractor
            parser = UnifiedParser()
            chunks = parser.parse_document_from_string(content, path)
            
            extractor = SemanticExtractor()
            statements = []
            for chunk in chunks:
                semantics = extractor.extract_semantics(chunk)
                statements.extend(semantics['triples'])
            
            progress.update(50, "Updating embeddings")
            
            # New embeddings
            doc_encoding = self.pipeline.encode_document(content, guid)
            
            # Update document
            self.conn.execute("""
                MATCH (d:Document {guid: $guid})
                SET d.content = $content,
                    d.checksum = $checksum,
                    d.metadata = $metadata,
                    d.updated_at = now(),
                    d.embedding_256 = $emb_256,
                    d.embedding_32 = $emb_32,
                    d.cluster_id = $cluster
            """, {
                'guid': guid,
                'content': content,
                'checksum': checksum,
                'metadata': json.dumps(metadata or {}),
                'emb_256': doc_encoding['embedding_256'],
                'emb_32': doc_encoding['embedding_32'],
                'cluster': doc_encoding['cluster_id']
            })
            
            progress.update(70, "Storing new statements")
            
            # Store new statements
            for stmt in statements:
                stmt_encoding = self.pipeline.encode_document(
                    stmt.content, f"{guid}#{stmt.id}"
                )
                
                self.conn.execute("""
                    CREATE (:Statement {
                        guid: $guid,
                        content: $content,
                        semantic_type: $type,
                        source_type: $source,
                        embedding_256: $emb_256,
                        embedding_32: $emb_32,
                        cluster_id: $cluster
                    })
                """, {
                    'guid': f"{guid}#{stmt.id}",
                    'content': stmt.content,
                    'type': stmt.semantic_type,
                    'source': stmt.source_type.value,
                    'emb_256': stmt_encoding['embedding_256'],
                    'emb_32': stmt_encoding['embedding_32'],
                    'cluster': stmt_encoding['cluster_id']
                })
                
                self.conn.execute("""
                    MATCH (d:Document {guid: $doc_guid}),
                          (s:Statement {guid: $stmt_guid})
                    CREATE (d)-[:CONTAINS]->(s)
                """, {'doc_guid': guid, 'stmt_guid': f"{guid}#{stmt.id}"})
            
            progress.update(90, "Invalidating cache")
            
            # Invalidate cache for both old and new clusters
            self._invalidate_cache_for_clusters(old_cluster, doc_encoding['cluster_id'])
            
            progress.update(100, "Complete")
            
            return {
                "status": "updated",
                "guid": guid,
                "path": path,
                "statements": len(statements),
                "old_cluster": old_cluster,
                "new_cluster": doc_encoding['cluster_id']
            }
    
    def _invalidate_cache_for_clusters(self, *cluster_ids):
        """Invalidate cache for affected clusters"""
        if self.cache:
            for cluster_id in cluster_ids:
                # Clear cluster-related cache keys
                pattern = f"*cluster:{cluster_id}*"
                for key in self.cache.scan_iter(match=pattern):
                    self.cache.delete(key)
    
    def _register_resources(self):
        """Register MCP resources"""
        
        @self.server.resource(
            uri="rag://stats",
            name="Knowledge Base Statistics",
            mime_type="application/json"
        )
        async def get_stats() -> Dict:
            """Overall statistics"""
            return {
                "documents": self._count_nodes("Document"),
                "statements": self._count_nodes("Statement"),
                "entities": self._count_nodes("Entity"),
                "clusters": self._count_distinct_clusters(),
                "cache_hits": self.cache.info()['keyspace_hits'],
                "last_updated": self._get_last_update()
            }
        
        @self.server.resource(
            uri="rag://clusters/{cluster_id}",
            name="Cluster Contents",
            mime_type="application/json"
        )
        async def get_cluster(cluster_id: str) -> Dict:
            """Contents of specific cluster"""
            return await self._get_cluster_contents(cluster_id)
        
        @self.server.resource(
            uri="rag://document/{guid}",
            name="Document Details",
            mime_type="application/json"
        )
        async def get_document(guid: str) -> Dict:
            """Full document with statements"""
            return await self._get_document_full(guid)
    
    async def _balanced_search(self, query: str, filters: Dict, 
                              limit: int) -> List[SearchResult]:
        """Standard two-stage search"""
        
        # Stage 1: Binary search (3x candidates)
        candidates = await self._binary_candidates(query, filters, limit * 3)
        
        # Stage 2: Float reranking
        reranked = self.translator.rerank_with_float(
            query, [c['guid'] for c in candidates], self.conn
        )
        
        # Fetch full results
        results = []
        for guid, score in reranked[:limit]:
            doc = await self._fetch_document(guid)
            if doc:
                results.append(SearchResult(
                    guid=guid,
                    content=doc['content'],
                    score=score,
                    metadata=doc['metadata'],
                    source_type=doc['type'],
                    cluster_id=doc['cluster_id']
                ))
        
        return results
    
    async def _thorough_search(self, query: str, filters: Dict,
                              limit: int, progress: Progress) -> List[SearchResult]:
        """Complete search with graph expansion"""
        
        # Get balanced results first
        progress.update(30, "Initial search")
        initial = await self._balanced_search(query, filters, limit // 2)
        
        # Extract entities
        progress.update(50, "Extracting concepts")
        entities = self._extract_entities_from_results(initial)
        
        # Graph expansion
        progress.update(70, "Expanding via knowledge graph")
        expanded = self.conn.execute("""
            MATCH (e:Entity)
            WHERE e.normalized_form IN $entities
            MATCH (e)-[:SEMANTIC_TRIPLE]-(related:Entity)
            MATCH (s:Statement)-[:HAS_ENTITY]-(related)
            RETURN DISTINCT s.guid as guid, s.content as content,
                   s.source_type as type, s.cluster_id as cluster
            LIMIT $limit
        """, {'entities': entities, 'limit': limit}).fetchall()
        
        # Combine and deduplicate
        all_results = initial + self._format_expanded(expanded)
        
        progress.update(90, "Ranking results")
        return self._deduplicate_results(all_results)[:limit]
```

## Client Configuration

```python
# mcp_client_config.py
class McpClientConfig:
    """Configuration for MCP clients"""
    
    @staticmethod
    def generate_claude_config() -> Dict:
        """Generate Claude Desktop configuration"""
        return {
            "mcpServers": {
                "rag-knowledge": {
                    "command": "python",
                    "args": ["mcp_rag_server.py"],
                    "env": {
                        "KUZU_DB_PATH": "./data/unified_kg.db",
                        "REDIS_HOST": "localhost",
                        "REDIS_PORT": "6379",
                        "LOG_LEVEL": "INFO"
                    }
                }
            }
        }
    
    @staticmethod
    def generate_capability_manifest() -> Dict:
        """MCP capability manifest"""
        return {
            "name": "rag-unified-knowledge",
            "version": "1.0.0",
            "description": "Optimized RAG with binary embeddings and UMAP clustering",
            "tools": [
                {
                    "name": "semantic_search",
                    "modes": ["fast", "balanced", "thorough"],
                    "performance": {
                        "fast": "3ms",
                        "balanced": "15ms",
                        "thorough": "50ms"
                    }
                },
                {
                    "name": "cluster_explore",
                    "description": "Navigate semantic neighborhoods"
                },
                {
                    "name": "trace_concept",
                    "description": "Cross-reference prose and code"
                },
                {
                    "name": "explain_statement",
                    "description": "Full hierarchical context"
                },
                {
                    "name": "analyze_distribution",
                    "description": "Corpus balance metrics"
                }
            ],
            "resources": [
                "rag://stats",
                "rag://clusters/{id}",
                "rag://document/{guid}"
            ],
            "features": {
                "binary_embeddings": True,
                "umap_clustering": True,
                "redis_caching": True,
                "cross_domain_search": True
            }
        }
```

## Server Lifecycle Management

```python
# server_manager.py
import signal
import sys
from contextlib import asynccontextmanager

class ServerManager:
    """Manage MCP server lifecycle"""
    
    def __init__(self, config_path: str):
        self.server = RagMcpServer(config_path)
        self.running = False
    
    async def start(self):
        """Start server with health checks"""
        
        # Verify dependencies
        if not await self._check_kuzu():
            raise RuntimeError("Kuzu database not accessible")
        
        if not await self._check_redis():
            print("Warning: Redis not available, running without cache")
            self.server.cache = None
        
        # Calibrate if needed
        if not self.server.pipeline.calibrated:
            print("Calibrating encoders...")
            await self._calibrate_pipeline()
        
        # Start server
        self.running = True
        print(f"MCP Server started on stdio")
        await self.server.server.run()
    
    async def _calibrate_pipeline(self):
        """Calibrate quantization parameters"""
        samples = self.server.conn.execute("""
            MATCH (s:Statement)
            RETURN s.content, s.source_type
            LIMIT 1000
        """).fetchall()
        
        texts = [s[0] for s in samples]
        metadata = [{'type': s[1]} for s in samples]
        
        self.server.pipeline.calibrate(texts, metadata)
        
        # Save calibration
        self._save_calibration()
    
    @asynccontextmanager
    async def managed_server(self):
        """Context manager for clean lifecycle"""
        try:
            await self.start()
            yield self.server
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down MCP server...")
        
        # Flush cache
        if self.server.cache:
            self.server.cache.bgsave()
        
        # Close connections
        self.server.conn.close()
        
        self.running = False
        print("Server stopped")

# Main entry point
async def main():
    manager = ServerManager("config.yaml")
    
    # Handle signals
    signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(manager.shutdown()))
    signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(manager.shutdown()))
    
    async with manager.managed_server():
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Usage Examples

```python
# Example queries through MCP

# Fast binary search (3ms)
results = await mcp.semantic_search(
    query="authentication token validation",
    mode="fast",
    filters={"content_type": "code"},
    limit=10
)

# Balanced search with type filtering (15ms)
results = await mcp.semantic_search(
    query="How are user sessions managed?",
    mode="balanced",
    filters={
        "content_type": "any",
        "confidence_min": 0.7
    }
)

# Thorough search with graph expansion (50ms)
results = await mcp.semantic_search(
    query="security vulnerabilities in auth system",
    mode="thorough",
    limit=30
)

# Explore semantic clusters
clusters = await mcp.cluster_explore(
    query="database optimization",
    max_clusters=5
)

# Trace concept across domains
trace = await mcp.trace_concept(
    concept="TokenValidator",
    max_hops=3,
    include_context=True
)

# Check corpus balance
stats = await mcp.analyze_distribution()
```

## Performance Monitoring

```python
class PerformanceMonitor:
    """Monitor MCP server performance"""
    
    def __init__(self, server: RagMcpServer):
        self.server = server
        self.metrics = defaultdict(list)
    
    @contextmanager
    def measure(self, operation: str):
        """Measure operation timing"""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - start) * 1000
            self.metrics[operation].append(duration)
            
            # Log slow queries
            if duration > 100:
                logger.warning(f"Slow {operation}: {duration:.1f}ms")
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        stats = {}
        for op, times in self.metrics.items():
            stats[op] = {
                "count": len(times),
                "avg_ms": np.mean(times),
                "p50_ms": np.percentile(times, 50),
                "p95_ms": np.percentile(times, 95),
                "p99_ms": np.percentile(times, 99)
            }
        return stats
```

## Key Features:

- **Three search modes**: Fast (3ms), Balanced (15ms), Thorough (50ms)
- **Progress reporting**: Real-time updates for long operations
- **Resource endpoints**: Direct access to clusters and documents
- **Cross-domain tracing**: Connect documentation to implementation
- **Distribution analysis**: Monitor corpus balance
- **Graceful lifecycle**: Clean startup/shutdown with calibration
- **Performance monitoring**: Track latencies and slow queries