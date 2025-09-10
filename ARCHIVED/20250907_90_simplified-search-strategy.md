# Simplified Cache-First Search Strategy

## Search Logic

```python
class SimplifiedRAGSearch:
    def __init__(self, cache, mcp_client):
        self.cache = cache
        self.mcp = mcp_client
        self.ttl = 3600  # 1 hour
    
    async def search(self, query: str, limit: int = 20) -> Dict:
        """Simple two-mode search"""
        
        # Check cache first
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cache_key = f"results:{query_hash}:{limit}"
        
        cached = self.cache.get(cache_key)
        if cached:
            return {
                "results": json.loads(cached),
                "mode": "cache",
                "latency_ms": 3
            }
        
        # No cache - do thorough search and cache it
        start = time.perf_counter()
        
        # Thorough search: binary → rerank → graph expansion
        results = await self.mcp.call_tool("semantic_search", {
            "query": query,
            "mode": "thorough",  # Always thorough for uncached
            "limit": limit
        })
        
        # Cache for future
        self.cache.setex(cache_key, self.ttl, json.dumps(results))
        
        # Also cache intermediate embeddings
        query_embedding = await self._get_query_embedding(query)
        self.cache.setex(f"emb:{query_hash}", self.ttl, query_embedding)
        
        latency = (time.perf_counter() - start) * 1000
        
        return {
            "results": results,
            "mode": "computed",
            "latency_ms": latency
        }
```

## Simplified MCP Server

```python
@self.server.tool(name="semantic_search")
async def semantic_search(query: str, limit: int = 20) -> List[Dict]:
    """Only two paths: cache hit or full computation"""
    
    # Check cache
    cached = self._check_cache(query, limit)
    if cached:
        return cached
    
    # Full pipeline for uncached
    # 1. Binary search (3x candidates)
    candidates = await self._binary_search(query, limit * 3)
    
    # 2. Float reranking (2x candidates) 
    reranked = await self._float_rerank(query, candidates[:limit * 2])
    
    # 3. Graph expansion (final candidates)
    expanded = await self._graph_expand(reranked[:limit])
    
    # Cache everything
    self._cache_results(query, expanded)
    
    return expanded
```

## Simplified Agent

```python
class SimplifiedAgent:
    def __init__(self):
        self.mcp = MCPClient(server_command=["python", "mcp_rag_server.py"])
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        # Just 3 nodes now
        workflow.add_node("search", self.search)
        workflow.add_node("synthesize", self.synthesize)
        
        workflow.set_entry_point("search")
        workflow.add_edge("search", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    async def search(self, state: AgentState) -> AgentState:
        """Single search strategy"""
        result = await self.mcp.call_tool("semantic_search", {
            "query": state["query"],
            "limit": 20
        })
        
        state["results"] = result["results"]
        state["cache_hit"] = result["mode"] == "cache"
        state["latency"] = result["latency_ms"]
        
        return state
```

## Cache Warming Strategy

```python
class CacheWarmer:
    """Precompute common queries"""
    
    async def warm_cache(self):
        common_queries = [
            "authentication",
            "database schema",
            "API endpoints",
            "error handling",
            "configuration"
        ]
        
        for base_query in common_queries:
            # Generate variations
            variations = [
                f"How does {base_query} work?",
                f"Where is {base_query} implemented?",
                f"Explain {base_query}"
            ]
            
            for query in variations:
                await self.search_client.search(query)
                await asyncio.sleep(0.1)  # Rate limit
```

## Benefits

| Aspect | Before (3 modes) | After (2 modes) |
|--------|-----------------|-----------------|
| Logic complexity | High | Low |
| Cache utilization | Variable | Optimal |
| Latency variance | 3-50ms | 3ms or 50ms |
| Code lines | ~200 | ~50 |
| Decision overhead | Per-query analysis | None |

## Configuration

```yaml
search:
  cache_ttl: 3600
  always_thorough_on_miss: true
  warm_cache_on_startup: true
```