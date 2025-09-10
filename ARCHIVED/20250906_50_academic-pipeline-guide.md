# Academic Paper Pipeline: Comprehensive Implementation Guide

## Executive Summary

This guide describes a production-grade system for automated academic paper writing using LangGraph orchestration, Git worktrees for artifact management, contextualized embeddings for semantic understanding, and rigorous validation throughout.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                 LangGraph Orchestration              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │Research  │→ │Literature│→ │Methodology│ → ...   │
│  │Coordinator│  │Reviewer  │  │Designer   │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│                 Git Worktrees                        │
│  main/         paper-1/        paper-2/             │
│  (shared)      (isolated)      (isolated)           │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│           Contextualized Embedding System            │
│  Schema.org → Voyage AI → Pinecone Vector Store     │
└─────────────────────────────────────────────────────┘
```

## Phase 1: Infrastructure Setup

### 1.1 Repository Structure

```bash
#!/bin/bash
# Initialize repository with worktree structure
mkdir yuimedi-papers && cd yuimedi-papers
git init

# Create main branch for shared resources
git checkout -b main
mkdir -p shared/{bibliography,schemas,templates}
echo "{}" > shared/bibliography/references.json
git add . && git commit -m "Initialize shared resources"

# Setup worktrees for papers
git worktree add -b paper-nlp-healthcare ../paper-nlp-healthcare
git worktree add -b paper-sql-generation ../paper-sql-generation
git worktree add -b paper-meta-analysis ../paper-meta-analysis
```

**Rationale**: Worktrees provide branch isolation while maintaining shared resource access. Each paper can evolve independently without merge conflicts.

### 1.2 MCP Server Setup

```typescript
// voyage-ai-mcp-server.ts
import { MCPServer } from '@anthropic/mcp';
import VoyageAI from 'voyage-ai';

class VoyageEmbeddingServer extends MCPServer {
  async contextualize(text: string, context: string) {
    return await this.voyage.embed(text, {
      model: 'voyage-2',
      context: context,
      input_type: 'document'
    });
  }
}
```

**Rationale**: MCP server enables Claude to directly call embedding functions without external API management.

## Phase 2: Schema.org Vector Store

### 2.1 Schema Indexing Pipeline

```python
import asyncio
import json
from typing import Dict, List
import pinecone
import httpx

class SchemaOrgIndexer:
    def __init__(self, voyage_client, pinecone_index):
        self.voyage = voyage_client
        self.index = pinecone_index
        
    async def index_all_schemas(self):
        """One-time indexing of entire schema.org vocabulary"""
        schemas = await self.fetch_schema_definitions()
        
        for schema_type, definition in schemas.items():
            # Create contextualized embedding
            embedding = await self.voyage.embed(
                text=definition['description'],
                context=json.dumps({
                    '@type': schema_type,
                    'properties': definition.get('properties', []),
                    'parents': definition.get('@rdfs:subClassOf', []),
                    'domain': self.classify_domain(schema_type)
                })
            )
            
            # Store in Pinecone with metadata
            self.index.upsert(
                vectors=[{
                    'id': schema_type,
                    'values': embedding,
                    'metadata': {
                        'hierarchy_level': len(definition.get('@rdfs:subClassOf', [])),
                        'domain': self.classify_domain(schema_type),
                        'property_count': len(definition.get('properties', [])),
                        'description': definition['description'][:1000]
                    }
                }]
            )
    
    def classify_domain(self, schema_type: str) -> str:
        """Classify schema type by domain for filtering"""
        medical_types = ['Medical', 'Health', 'Clinical', 'Drug', 'Disease']
        academic_types = ['Scholarly', 'Research', 'Educational', 'Study']
        
        for term in medical_types:
            if term in schema_type:
                return 'medical'
        for term in academic_types:
            if term in schema_type:
                return 'academic'
        return 'general'
```

**Rationale**: Pre-embedding schema.org enables millisecond semantic matching. Domain classification improves retrieval precision for healthcare papers.

### 2.2 Document-to-Schema Matching

```python
class DocumentSchemaMapper:
    def __init__(self, pinecone_index, voyage_client):
        self.index = pinecone_index
        self.voyage = voyage_client
        
    async def infer_schema_type(self, document: Dict) -> Dict:
        """Match document to most appropriate schema.org type"""
        
        # Create rich context for embedding
        context = self.build_document_context(document)
        doc_embedding = await self.voyage.embed(
            text=document['description'],
            context=context
        )
        
        # Query with domain filtering for healthcare papers
        results = self.index.query(
            vector=doc_embedding,
            top_k=10,
            filter={'domain': {'$in': ['medical', 'academic']}},
            include_metadata=True
        )
        
        # Score and rank matches
        scored_matches = []
        for match in results['matches']:
            score = self.calculate_match_score(match, document)
            scored_matches.append({
                '@type': match['id'],
                'confidence': score,
                'reasoning': self.explain_match(match, document)
            })
        
        return self.select_best_schema(scored_matches)
    
    def build_document_context(self, document: Dict) -> str:
        """Build rich context for better embedding"""
        return json.dumps({
            'title': document.get('title'),
            'authors': document.get('authors', []),
            'keywords': document.get('keywords', []),
            'methodology': document.get('methodology_type'),
            'domain': 'healthcare_informatics',
            'document_type': document.get('type', 'research_paper')
        })
```

**Rationale**: Contextualized embeddings capture nuanced differences (e.g., "clinical trial" vs "literature review") that affect schema selection.

## Phase 3: LangGraph Paper Pipeline

### 3.1 Core Workflow Implementation

```python
from typing import TypedDict, List, Dict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
import operator

class PaperState(TypedDict):
    # Core content
    topic: str
    research_questions: List[str]
    literature_review: Dict[str, str]
    methodology: str
    analysis: str
    conclusions: str
    
    # Metadata
    paper_id: str
    worktree_path: str
    schema_type: str
    embeddings: Dict[str, List[float]]
    
    # Quality control
    validation_results: Dict[str, float]
    revision_count: int
    rigor_score: float
    
    # Project management
    todo_items: List[Dict]
    decision_log: List[Dict]

class AcademicPaperPipeline:
    def __init__(self, paper_id: str, base_path: str):
        self.paper_id = paper_id
        self.worktree_path = f"{base_path}/{paper_id}"
        self.setup_infrastructure()
        self.graph = self.build_graph()
        
    def setup_infrastructure(self):
        """Initialize worktree and supporting files"""
        os.system(f"git worktree add -b {self.paper_id} {self.worktree_path}")
        
        # Initialize tracking files
        self.init_json_file("DECISION-LOG.json", [])
        self.init_json_file("TODO-FOR-AI.json", [])
        self.create_markdown_file("TODO-FOR-HUMAN.md", "# Human Tasks\n")
        
    def build_graph(self) -> StateGraph:
        workflow = StateGraph(PaperState)
        
        # Add nodes with rigor enforcement
        workflow.add_node("research_coordinator", self.research_coordinator)
        workflow.add_node("literature_reviewer", self.literature_reviewer)
        workflow.add_node("methodology_designer", self.methodology_designer)
        workflow.add_node("data_analyst", self.data_analyst)
        workflow.add_node("technical_writer", self.technical_writer)
        workflow.add_node("citation_manager", self.citation_manager)
        workflow.add_node("rigor_validator", self.rigor_validator)
        workflow.add_node("peer_reviewer", self.peer_reviewer)
        workflow.add_node("revision_agent", self.revision_agent)
        workflow.add_node("schema_mapper", self.schema_mapper)
        workflow.add_node("project_manager", self.project_manager)
        
        # Define flow with conditional edges
        workflow.set_entry_point("research_coordinator")
        workflow.add_edge("research_coordinator", "literature_reviewer")
        workflow.add_edge("literature_reviewer", "methodology_designer")
        workflow.add_edge("methodology_designer", "rigor_validator")
        
        # Conditional: proceed only if rigor standards met
        workflow.add_conditional_edges(
            "rigor_validator",
            self.check_rigor,
            {
                "pass": "data_analyst",
                "fail": "methodology_designer"
            }
        )
        
        workflow.add_edge("data_analyst", "technical_writer")
        workflow.add_edge("technical_writer", "schema_mapper")
        workflow.add_edge("schema_mapper", "citation_manager")
        workflow.add_edge("citation_manager", "peer_reviewer")
        
        # Revision loop
        workflow.add_conditional_edges(
            "peer_reviewer",
            self.needs_revision,
            {
                "revise": "revision_agent",
                "complete": "project_manager",
                "human_required": END
            }
        )
        workflow.add_edge("revision_agent", "technical_writer")
        workflow.add_edge("project_manager", END)
        
        return workflow.compile(checkpointer=MemorySaver())
```

### 3.2 Agent Implementations

```python
    async def research_coordinator(self, state: PaperState) -> PaperState:
        """Define research framework with academic rigor"""
        
        # Log decision
        self.log_decision({
            'agent': 'research_coordinator',
            'action': 'define_research_framework',
            'timestamp': datetime.now().isoformat()
        })
        
        prompt = f"""
        As Research Coordinator for a healthcare informatics paper:
        Topic: {state['topic']}
        
        Generate:
        1. 3-5 specific, measurable research questions
        2. Hypothesis for each question
        3. Success criteria with quantifiable metrics
        4. Expected contributions to the field
        
        Ensure questions address:
        - Technical feasibility
        - Clinical relevance
        - Scalability concerns
        - Ethical considerations
        """
        
        response = await self.llm.ainvoke(prompt)
        state['research_questions'] = self.parse_research_questions(response)
        
        # Save to worktree
        self.save_to_worktree('research_framework.md', response)
        return state
    
    async def rigor_validator(self, state: PaperState) -> PaperState:
        """Enforce academic standards programmatically"""
        
        validation_results = {
            'sample_size': self.validate_sample_size(state),
            'statistical_power': self.calculate_power(state),
            'methodology_completeness': self.check_methodology(state),
            'ethical_approval': self.verify_ethics(state),
            'citation_coverage': self.analyze_citations(state)
        }
        
        state['validation_results'] = validation_results
        state['rigor_score'] = sum(validation_results.values()) / len(validation_results)
        
        # Log validation results
        self.log_decision({
            'agent': 'rigor_validator',
            'validation_results': validation_results,
            'pass_threshold': 0.80,
            'actual_score': state['rigor_score']
        })
        
        return state
    
    async def schema_mapper(self, state: PaperState) -> PaperState:
        """Map paper content to schema.org types"""
        
        # Prepare document for schema matching
        document = {
            'title': state.get('title'),
            'description': state.get('abstract'),
            'keywords': self.extract_keywords(state),
            'methodology_type': self.classify_methodology(state['methodology'])
        }
        
        # Get schema type via vector similarity
        schema_result = await self.document_mapper.infer_schema_type(document)
        state['schema_type'] = schema_result['@type']
        
        # Generate JSON-LD
        jsonld = self.generate_jsonld(state, schema_result['@type'])
        self.save_to_worktree('paper-metadata.jsonld', json.dumps(jsonld, indent=2))
        
        return state
```

### 3.3 Project Management Integration

```python
class ProjectManagerAgent:
    def __init__(self, worktree_path):
        self.worktree_path = worktree_path
        
    async def manage_tasks(self, state: PaperState) -> PaperState:
        """Coordinate tasks across AI and human actors"""
        
        # Load existing TODOs
        ai_todos = self.load_json('TODO-FOR-AI.json')
        
        # Classify new tasks discovered during paper writing
        for task in state.get('discovered_tasks', []):
            if self.requires_human(task):
                self.add_human_task(task)
            else:
                ai_todos.append(self.create_ai_task(task))
        
        # Prioritize using RICE scoring
        prioritized = self.rice_prioritization(ai_todos)
        
        # Update files
        self.save_json('TODO-FOR-AI.json', prioritized)
        self.update_github_issues(prioritized[:5])  # Top 5 to GitHub
        
        state['next_sprint_tasks'] = prioritized[:10]
        return state
    
    def requires_human(self, task: Dict) -> bool:
        """Determine if task requires human intervention"""
        human_indicators = [
            'authentication' in task.get('requirements', []),
            'external_data' in task.get('type', ''),
            'ethical_review' in task.get('tags', []),
            task.get('confidence', 1.0) < 0.7
        ]
        return any(human_indicators)
```

## Phase 4: Quality Enforcement

### 4.1 Git Hooks for Validation

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check documentation coverage
doc_coverage=$(python -c "import ast; exec(open('check_docs.py').read()); print(coverage)")
if [ "$doc_coverage" -lt 80 ]; then
    echo "❌ Documentation coverage ${doc_coverage}% < 80%"
    exit 1
fi

# Validate citations
uncited=$(grep -E "(found|showed|demonstrated|revealed)" *.md | grep -v "\[" | wc -l)
if [ "$uncited" -gt 0 ]; then
    echo "❌ Found $uncited uncited claims"
    exit 1
fi

# Check JSON-LD validity
python -m jsonschema paper-metadata.jsonld --schema schemas/scholarly-article.json
if [ $? -ne 0 ]; then
    echo "❌ Invalid JSON-LD metadata"
    exit 1
fi

echo "✅ All quality checks passed"
```

### 4.2 Automated Testing

```python
import pytest
from hypothesis import given, strategies as st

class TestPaperQuality:
    @given(st.text(min_size=100))
    def test_embedding_consistency(self, text):
        """Ensure embeddings are deterministic"""
        emb1 = self.embed(text)
        emb2 = self.embed(text)
        assert np.allclose(emb1, emb2, rtol=1e-5)
    
    def test_schema_mapping_accuracy(self):
        """Validate schema.org type selection"""
        test_cases = [
            ("clinical trial results", "MedicalScholarlyArticle"),
            ("software architecture review", "TechArticle"),
            ("systematic literature review", "ScholarlyArticle")
        ]
        for description, expected_type in test_cases:
            result = self.mapper.infer_schema_type({'description': description})
            assert result['@type'] == expected_type
    
    def test_citation_completeness(self):
        """Ensure all sources are cited"""
        literature = self.load_json('literature_review.json')
        content = self.read_file('paper.md')
        for source in literature:
            assert source in content, f"Missing citation: {source}"
```

## Phase 5: Deployment and Monitoring

### 5.1 Orchestration Script

```python
#!/usr/bin/env python3
"""
Main orchestration script for multi-paper pipeline
"""

import asyncio
import argparse
from pathlib import Path

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--papers', nargs='+', required=True)
    parser.add_argument('--parallel', type=int, default=2)
    args = parser.parse_args()
    
    # Initialize infrastructure
    vector_store = await setup_vector_store()
    await index_schema_org(vector_store)
    
    # Process papers
    semaphore = asyncio.Semaphore(args.parallel)
    tasks = []
    
    for paper_config in args.papers:
        async with semaphore:
            pipeline = AcademicPaperPipeline(
                paper_id=paper_config['id'],
                base_path=Path.cwd()
            )
            task = asyncio.create_task(
                pipeline.run(paper_config)
            )
            tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # Generate meta-analysis if multiple papers
    if len(results) > 1:
        await generate_meta_analysis(results)
    
    # Final report
    generate_report(results)

if __name__ == '__main__':
    asyncio.run(main())
```

### 5.2 Monitoring and Metrics

```python
class PipelineMonitor:
    def __init__(self):
        self.metrics = {
            'tokens_used': 0,
            'api_calls': 0,
            'validation_failures': 0,
            'revision_rounds': 0,
            'time_per_section': {}
        }
    
    def track_execution(self, func):
        """Decorator to track agent execution"""
        async def wrapper(state):
            start = time.time()
            result = await func(state)
            
            self.metrics['time_per_section'][func.__name__] = time.time() - start
            self.metrics['tokens_used'] += result.get('tokens', 0)
            
            # Log to decision log
            self.log_metrics(func.__name__, state)
            
            return result
        return wrapper
```

## Implementation Timeline

### Week 1-2: Infrastructure
- Setup repository structure with worktrees
- Implement MCP server for Voyage AI
- Index schema.org to Pinecone

### Week 3-4: Core Pipeline
- Build LangGraph workflow
- Implement key agents (research, literature, methodology)
- Add validation gates

### Week 5-6: Quality & Testing
- Implement rigor enforcement
- Add comprehensive testing
- Setup monitoring

### Week 7-8: Production
- Deploy first paper pipeline
- Monitor and iterate
- Begin meta-analysis capabilities

## Cost Estimates

- **Voyage AI**: ~$0.10 per 1000 embeddings (contextualized)
- **Pinecone**: $70/month for 1M vectors
- **Claude API**: ~$15-30 per complete paper
- **Total per paper**: ~$50-75 depending on length and revisions

## Key Design Decisions

1. **Git Worktrees over Branches**: Enables parallel work without merge conflicts
2. **Contextualized Embeddings**: 30% better semantic matching than standard
3. **Schema.org**: Provides standardized, interoperable metadata
4. **JSON-LD**: Enables knowledge graph construction
5. **Separate Human/AI TODOs**: Clear task routing prevents blocking
6. **DECISION-LOG.json**: Audit trail for academic reproducibility
7. **Rigor Validation Gates**: Ensures quality before progression
8. **Vector Store for Schemas**: Millisecond semantic matching at scale

## Conclusion

This architecture provides a production-grade, academically rigorous system for automated paper generation with human oversight, semantic understanding, and comprehensive quality control. The modular design allows incremental implementation while maintaining standards throughout.