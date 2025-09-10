# LangGraph Integration with langchain-mcp-adapters

## Using the Official Adapter

```python
# langgraph_rag_agent.py
from langchain_mcp import MCPClient
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from typing import TypedDict, Annotated, Sequence
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    search_mode: str
    results: List[Dict]
    context: Dict

class RAGAgent:
    """LangGraph agent using MCP tools via official adapter"""
    
    def __init__(self):
        # Use official adapter
        self.mcp_client = MCPClient(
            server_command=["python", "mcp_rag_server.py"],
            server_env={
                "KUZU_DB_PATH": "./data/unified_kg.db",
                "REDIS_HOST": "localhost",
                "REDIS_PORT": "6379"
            }
        )
        self.tools = self.mcp_client.get_tools()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("search", self.search)
        workflow.add_node("expand_context", self.expand_context)
        workflow.add_node("synthesize", self.synthesize)
        
        # Add edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "search")
        workflow.add_conditional_edges(
            "search",
            self.should_expand,
            {
                "expand": "expand_context",
                "synthesize": "synthesize"
            }
        )
        workflow.add_edge("expand_context", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    async def search(self, state: AgentState) -> AgentState:
        """Execute MCP semantic search"""
        results = await self.mcp_client.call_tool(
            "semantic_search",
            {
                "query": state["query"],
                "mode": state["search_mode"],
                "limit": 20
            }
        )
        state["results"] = results
        return state
    
    async def expand_context(self, state: AgentState) -> AgentState:
        """Use trace_concept for expansion"""
        concepts = self._extract_concepts(state["results"])
        
        expanded = {}
        for concept in concepts[:3]:
            trace = await self.mcp_client.call_tool(
                "trace_concept",
                {"concept": concept, "max_hops": 2}
            )
            expanded[concept] = trace
        
        state["context"] = expanded
        return state
```

## Direct Usage

```python
from langchain_mcp import MCPClient
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI

# Initialize MCP client
mcp = MCPClient(
    server_command=["python", "mcp_rag_server.py"],
    server_env={
        "KUZU_DB_PATH": "./data/unified_kg.db",
        "REDIS_HOST": "localhost"
    }
)

# Get tools
tools = mcp.get_tools()

# Create agent
llm = ChatOpenAI(model="gpt-4")
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Run
result = await agent_executor.ainvoke({
    "input": "How does authentication work in the codebase?"
})
```

## With LangServe

```python
from langserve import add_routes
from fastapi import FastAPI

app = FastAPI()

# Create runnable
rag_agent = RAGAgent()

add_routes(
    app,
    rag_agent.graph,
    path="/rag"
)

# Endpoints available:
# POST /rag/invoke
# POST /rag/stream
# GET /rag/input_schema
```

## Tool-Specific Wrappers

```python
from langchain.tools import tool

@tool
async def smart_search(query: str, depth: str = "balanced") -> str:
    """
    Intelligent search with automatic mode selection
    
    Args:
        query: Search query
        depth: "shallow", "balanced", or "deep"
    """
    mode_map = {"shallow": "fast", "balanced": "balanced", "deep": "thorough"}
    
    results = await mcp.call_tool(
        "semantic_search",
        {"query": query, "mode": mode_map[depth]}
    )
    
    if len(results) < 5 and depth != "deep":
        # Auto-expand
        concepts = extract_concepts(results)
        for concept in concepts:
            trace = await mcp.call_tool(
                "trace_concept", 
                {"concept": concept}
            )
            results.extend(trace)
    
    return format_results(results)
```

## Configuration

```yaml
# pyproject.toml
[tool.poetry.dependencies]
langchain-mcp = "^0.1.0"
langgraph = "^0.2.0"
langserve = "^0.2.0"
```

The official adapter handles:
- Async/sync conversion
- Tool discovery
- Parameter validation
- Connection management
- Error handling