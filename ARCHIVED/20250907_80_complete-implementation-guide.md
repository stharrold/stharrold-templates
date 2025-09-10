# Complete Implementation Guide: User → LangGraph → MCP-RAG-Voyage-UMAP-Kuzu

## System Architecture Overview

```
User Prompt → LangGraph Agent → MCP Client → MCP Server → Kuzu DB
                    ↓                             ↓           ↓
                Decision Flow            Binary Search   UMAP Clusters
                    ↓                             ↓           ↓
              Response Synthesis ← Redis Cache ← Voyage Embeddings
```

## 1. Initial Setup

### Prerequisites
```bash
# Install dependencies
pip install langgraph langchain-mcp kuzu redis sentence-transformers umap-learn voyage-ai
pip install spacy && python -m spacy download en_core_web_sm
pip install tree-sitter tree-sitter-python

# Start Redis
redis-server --port 6379

# Create directories
mkdir -p data corpus logs
```

### Configuration
```yaml
# config.yaml
system:
  mode: production
  log_level: INFO

kuzu:
  path: "./data/unified_kg.db"
  
redis:
  host: localhost
  port: 6379
  db: 0

embeddings:
  model: "voyage-large-2-instruct"  # or sentence-transformers/all-MiniLM-L6-v2
  dimension: 256
  umap_dimension: 32
  
mcp:
  server_command: ["python", "mcp_rag_server.py"]
  timeout: 30
```

## 2. Data Ingestion Pipeline

### Step 1: Prepare Corpus
```python
# ingest.py
import asyncio
from pathlib import Path

async def ingest_corpus():
    """One-time corpus ingestion"""
    
    # Initialize MCP client for ingestion
    from langchain_mcp import MCPClient
    
    mcp = MCPClient(
        server_command=["python", "mcp_rag_server.py"],
        server_env={
            "KUZU_DB_PATH": "./data/unified_kg.db",
            "REDIS_HOST": "localhost"
        }
    )
    
    # Ingest documentation
    await mcp.call_tool("ingest_batch", {
        "glob_pattern": "./corpus/docs/**/*.md",
        "recursive": True
    })
    
    # Ingest code
    await mcp.call_tool("ingest_batch", {
        "glob_pattern": "./corpus/src/**/*.py",
        "recursive": True
    })
    
    # Check distribution
    stats = await mcp.call_tool("analyze_distribution", {})
    print(f"Corpus balance: {stats['balance_status']}")
    print(f"Total documents: {stats['total_statements']}")
    
if __name__ == "__main__":
    asyncio.run(ingest_corpus())
```

## 3. MCP Server Implementation

See [MCP Server Implementation](artifacts:mcp-server-implementation) for full server code.

Key components:
- Dual encoding pipeline (256d binary + 32d UMAP)
- Ingest/query modes
- Redis caching
- Three search modes (fast/balanced/thorough)

## 4. LangGraph Agent

### Core Agent
```python
# rag_agent.py
from langgraph.graph import StateGraph, END
from langchain_mcp import MCPClient
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from typing import TypedDict, Annotated, Sequence, Literal
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    intent: str
    search_mode: Literal["fast", "balanced", "thorough"]
    results: list
    context: dict
    needs_expansion: bool

class RAGAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.mcp = MCPClient(
            server_command=["python", "mcp_rag_server.py"],
            server_env=self._load_env(config_path)
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("classify_intent", self.classify_intent)
        workflow.add_node("search", self.search)
        workflow.add_node("check_quality", self.check_quality)
        workflow.add_node("expand", self.expand_context)
        workflow.add_node("synthesize", self.synthesize)
        
        # Define flow
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "search")
        workflow.add_edge("search", "check_quality")
        
        workflow.add_conditional_edges(
            "check_quality",
            lambda x: "expand" if x["needs_expansion"] else "synthesize",
            {"expand": "expand", "synthesize": "synthesize"}
        )
        
        workflow.add_edge("expand", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    async def classify_intent(self, state: AgentState) -> AgentState:
        """Determine query intent and search strategy"""
        query = state["messages"][-1].content
        
        # Intent patterns
        if any(word in query.lower() for word in ["how", "explain", "why"]):
            state["intent"] = "explanation"
            state["search_mode"] = "thorough"
        elif any(word in query.lower() for word in ["where", "find", "locate"]):
            state["intent"] = "location"
            state["search_mode"] = "balanced"
        elif any(word in query.lower() for word in ["list", "what", "which"]):
            state["intent"] = "enumeration"
            state["search_mode"] = "fast"
        else:
            state["intent"] = "general"
            state["search_mode"] = "balanced"
        
        state["query"] = query
        return state
    
    async def search(self, state: AgentState) -> AgentState:
        """Execute semantic search via MCP"""
        
        # Determine filters based on intent
        filters = {}
        if "code" in state["query"].lower():
            filters["content_type"] = "code"
        elif "document" in state["query"].lower():
            filters["content_type"] = "prose"
        
        results = await self.mcp.call_tool("semantic_search", {
            "query": state["query"],
            "mode": state["search_mode"],
            "filters": filters,
            "limit": 20
        })
        
        state["results"] = results
        return state
    
    async def check_quality(self, state: AgentState) -> AgentState:
        """Assess if results need expansion"""
        results = state["results"]
        
        # Quality metrics
        avg_score = sum(r.get("score", 0) for r in results) / len(results) if results else 0
        has_both_types = len(set(r.get("source_type") for r in results)) > 1
        
        state["needs_expansion"] = (
            len(results) < 5 or 
            avg_score < 0.7 or
            (state["intent"] == "explanation" and not has_both_types)
        )
        
        return state
    
    async def expand_context(self, state: AgentState) -> AgentState:
        """Expand using cluster exploration and concept tracing"""
        
        # Get clusters from initial results
        clusters = set(r.get("cluster_id") for r in state["results"][:3])
        
        expanded = {}
        
        # Explore related clusters
        for cluster_id in clusters:
            cluster_contents = await self.mcp.call_tool("cluster_explore", {
                "cluster_id": cluster_id,
                "max_clusters": 2
            })
            expanded[f"cluster_{cluster_id}"] = cluster_contents
        
        # Trace key concepts
        concepts = self._extract_concepts(state["results"])
        for concept in concepts[:2]:
            trace = await self.mcp.call_tool("trace_concept", {
                "concept": concept,
                "max_hops": 2
            })
            expanded[f"concept_{concept}"] = trace
        
        state["context"] = expanded
        return state
    
    async def synthesize(self, state: AgentState) -> AgentState:
        """Generate final response"""
        
        # Build response from results and context
        response = self._build_response(
            query=state["query"],
            intent=state["intent"],
            results=state["results"],
            context=state.get("context", {})
        )
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    def _build_response(self, query: str, intent: str, 
                       results: list, context: dict) -> str:
        """Format response based on intent"""
        
        if intent == "explanation":
            # Structured explanation
            response = f"Based on the codebase and documentation:\n\n"
            
            # Group by type
            prose_results = [r for r in results if r.get("source_type") == "prose"]
            code_results = [r for r in results if r.get("source_type") == "code"]
            
            if prose_results:
                response += "**Documentation:**\n"
                for r in prose_results[:3]:
                    response += f"- {r['content'][:200]}...\n"
            
            if code_results:
                response += "\n**Implementation:**\n"
                for r in code_results[:3]:
                    response += f"- {r['content'][:200]}...\n"
            
            if context:
                response += "\n**Related concepts:**\n"
                for key, value in list(context.items())[:2]:
                    response += f"- {key}: {str(value)[:100]}...\n"
                    
        elif intent == "location":
            response = "Found in the following locations:\n"
            for r in results[:5]:
                response += f"- {r.get('document', 'Unknown')}: {r['content'][:100]}...\n"
                
        else:
            # General response
            response = f"Found {len(results)} relevant results:\n"
            for r in results[:5]:
                response += f"- {r['content'][:150]}...\n"
        
        return response
```

## 5. API Server

```python
# app.py
from fastapi import FastAPI, HTTPException
from langserve import add_routes
from pydantic import BaseModel
import asyncio

app = FastAPI(title="RAG System")

# Initialize agent
agent = RAGAgent("config.yaml")

class QueryRequest(BaseModel):
    query: str
    mode: str = "balanced"

class QueryResponse(BaseModel):
    answer: str
    sources: list
    confidence: float

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """Main query endpoint"""
    
    initial_state = {
        "messages": [HumanMessage(content=request.query)],
        "search_mode": request.mode,
        "results": [],
        "context": {}
    }
    
    try:
        final_state = await agent.graph.ainvoke(initial_state)
        
        return QueryResponse(
            answer=final_state["messages"][-1].content,
            sources=[r.get("document", "") for r in final_state["results"][:5]],
            confidence=sum(r.get("score", 0) for r in final_state["results"][:5]) / 5
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add LangServe routes
add_routes(
    app,
    agent.graph,
    path="/langgraph"
)

# Health check
@app.get("/health")
async def health():
    # Check MCP server
    try:
        stats = await agent.mcp.call_tool("analyze_distribution", {})
        return {
            "status": "healthy",
            "documents": stats.get("total_statements", 0)
        }
    except:
        return {"status": "unhealthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 6. Client Usage

```python
# client.py
import requests

# Query the system
response = requests.post("http://localhost:8000/query", json={
    "query": "How does the authentication system validate JWT tokens?",
    "mode": "thorough"
})

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Sources: {result['sources']}")
```

## 7. Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Start services
CMD ["./start.sh"]
```

```bash
#!/bin/bash
# start.sh

# Start Redis
redis-server --daemonize yes

# Start MCP server in background
python mcp_rag_server.py &

# Start API server
python app.py
```

## 8. Monitoring

```python
# monitor.py
async def monitor_system():
    """System health monitoring"""
    
    mcp = MCPClient(server_command=["python", "mcp_rag_server.py"])
    
    while True:
        # Check distribution
        stats = await mcp.call_tool("analyze_distribution", {})
        
        if stats["gini_coefficient"] > 0.7:
            print("WARNING: Corpus imbalance detected")
            
        # Check cache hit rate
        cache_stats = await mcp.call_resource("rag://stats")
        hit_rate = cache_stats["cache_hits"] / cache_stats.get("total_queries", 1)
        
        if hit_rate < 0.3:
            print("INFO: Low cache hit rate, consider warming cache")
        
        await asyncio.sleep(300)  # Check every 5 minutes
```

## Data Flow Summary

1. **User Query** → FastAPI endpoint
2. **LangGraph Agent** → Classifies intent, determines search mode
3. **MCP Client** → Calls appropriate tools (semantic_search, trace_concept)
4. **MCP Server** → Processes request with optimized pipeline
5. **Kuzu Query** → Binary Hamming search → Float reranking
6. **Redis Cache** → Returns cached embeddings/results if available
7. **Response Synthesis** → Agent builds structured response
8. **User Response** → Formatted answer with sources and confidence

See referenced artifacts for:
- [Optimized Pipeline](artifacts:optimized-vector-pipeline) - Binary/UMAP encoding details
- [MCP Server](artifacts:mcp-server-implementation) - Complete server implementation
- [LangGraph Adapter](artifacts:langgraph-mcp-adapter) - Integration details