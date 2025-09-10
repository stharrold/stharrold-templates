# Unified Schema Architectures for Semantic Document Representation in RAG Systems

## Executive Summary

Graph-based RAG systems demonstrate **35-80% higher accuracy** compared to vector-only approaches through unified semantic document representation. This research identifies concrete schema implementations combining RDF/OWL standards, hierarchical document models, and production-ready frameworks like Neo4j GraphRAG and Kuzu's structured property graphs. Key findings include the emergence of **GraphQ IR** as a universal intermediate representation, **NIF (NLP Interchange Format)** for statement-level semantics, and practical MCP server implementations enabling seamless graph database integration.

## Existing schemas and ontologies enable granular semantic representation

The semantic web ecosystem provides mature foundations for statement-level document representation through **RDF's subject-predicate-object triple structure**. The Resource Description Framework serves as the atomic unit for semantic statements, with each triple representing machine-readable knowledge that forms directed labeled graphs when combined.

**NLP Interchange Format (NIF)** emerges as the critical bridge between natural language and semantic structures. NIF provides RDF/OWL-based classes for granular text annotation: `nif:Context` for entire documents, `nif:Sentence` for sentence boundaries, and `nif:Word` for token-level semantics. Position-based addressing using RFC 5147 URI schemes (e.g., `#char=0,25`) enables precise semantic role labeling within the RDF framework. Properties like `nif:anchorOf`, `nif:beginIndex`, and `nif:referenceContext` maintain the connection between semantic annotations and source text.

For document-specific vocabularies, **Dublin Core** provides 55+ properties for bibliographic metadata, **FOAF** handles authorship and relationships, while **Schema.org** offers 840+ types with hierarchical document structures including DigitalDocument, Article, and Book types. These vocabularies combine through modular design patterns, avoiding monolithic schemas in favor of composable semantic layers.

Practical implementations demonstrate the effectiveness of these standards. The **pyLODE** library generates human-readable documentation from OWL ontologies, while **NIF libraries** in Java and Python support named entity recognition, entity linking, and semantic role labeling with RDF serialization in Turtle, JSON-LD, and RDF/XML formats.

## Hierarchical models preserve document structure relationships

The **Text Encoding Initiative (TEI)** represents the most mature hierarchical document schema with over 500 elements organized in 21 thematic modules. TEI's XML-based structure with RDF serializations maintains the hierarchy: `text → body → div → p → phrases`, supporting both human readability and machine processing. The ODD (One Document Does it all) customization framework enables project-specific schemas while maintaining interoperability through model classes like `model.pLike` for flexible content hierarchies.

For computational linguistics, **Universal Dependencies** frameworks provide RDF serializations of dependency parse trees, while discourse relation annotations from RST and PDTB enable multi-layered linguistic annotation. These hierarchical structures integrate with knowledge graphs through syntactic-semantic bridging, maintaining both structural and semantic information.

Digital humanities implementations like **METS** (Metadata Encoding and Transmission Standard) demonstrate practical applications with hierarchical structural metadata for digital library objects. The **IIIF** (International Image Interoperability Framework) uses a canvas/annotation model with JSON-LD serialization, showing how hierarchical structures can maintain semantic web compatibility while preserving document organization.

## Kuzu database provides optimized schemas for semantic structures

**Kuzu's structured property graph model** requires pre-defined schemas that optimize performance through strongly-typed column properties and columnar storage. Unlike Neo4j's flexible schema approach, Kuzu enforces primary key constraints on node tables and separate relationship table definitions, achieving **up to 188x faster query performance** in benchmarks.

The basic schema pattern for semantic document representation in Kuzu follows this structure:

```cypher
CREATE NODE TABLE Document(
    id STRING PRIMARY KEY,
    title STRING,
    content STRING,
    document_embedding FLOAT[384],
    created_at TIMESTAMP
);

CREATE NODE TABLE Chunk(
    id STRING PRIMARY KEY,
    text STRING,
    chunk_embedding FLOAT[384],
    chunk_index INT64
);

CREATE REL TABLE CONTAINS(FROM Document TO Chunk, 
    relevance_score FLOAT
);
```

For semantic triple storage, Kuzu implements dedicated patterns:

```cypher
CREATE NODE TABLE Subject(id STRING PRIMARY KEY, label STRING);
CREATE NODE TABLE Object(id STRING PRIMARY KEY, label STRING);
CREATE REL TABLE TRIPLE(FROM Subject TO Object,
    predicate_id STRING,
    confidence FLOAT,
    source_document_id STRING
);
```

Kuzu's native **HNSW (Hierarchical Navigable Small World) vector index** provides disk-based similarity search with two-layer hierarchical structure. Vector indices support cosine, L2, and inner product distance metrics with configurable parameters for precision-recall trade-offs. The integration of vector search with graph traversal enables hybrid queries combining semantic similarity with structural relationships.

## Vector embedding strategies maintain hierarchical context

**Embedding of Semantic Predications (ESP)** successfully encodes subject-relation-object triplets using reversible vector transformations that preserve semantic roles. Research from NCBI demonstrates adapting Skipgram with Negative Sampling for semantic predications like "haloperidol TREATS schizophrenia," maintaining role information within the embedding space.

**Triple2Vec** moves beyond averaging node embeddings to create native triple representations using line graph concepts and semantic proximity-based edge weighting. Compositional approaches include concatenation-based methods combining subject, predicate, and object embeddings, transformation-based methods applying learned functions preserving semantic roles, and holographic methods using Vector Symbolic Architectures for compositional encoding.

For maintaining hierarchical context, **hierarchical attention mechanisms** operate at multiple document levels. Bidirectional RNNs with hierarchical attention attend to both word-level event triggers and sentence-level contexts, creating document embeddings that enhance sentence-level tasks. **Multi-scale attention** frameworks use BERT-based dynamic fusion across document structure levels, from statements to sections.

**Voyage-context-3** represents state-of-the-art contextualized chunk embedding, producing vectors capturing full document context without manual metadata augmentation. Supporting multiple dimensions (2048, 1024, 512, 256) via Matryoshka learning, it outperforms OpenAI-v3-large by 14.24% on chunk-level tasks while maintaining hierarchical relationships.

## Research advances combine multiple semantic analysis techniques

**TakeFive** (2021) transforms text into frame-oriented knowledge graphs through SRL, achieving competitive F1 scores with SEMAFOR and PathLSTM. The system uses CoreNLP and Word Frame Disambiguation to generate Framester-compliant knowledge graphs, directly converting semantic role labels into graph structures.

For code representation, **cAST** (2025) introduces structure-aware chunking preserving AST structure for code retrieval. Using recursive splitting with semantic boundaries, it achieves 4.3 points Recall@5 improvement on RepoEval and 2.67 points Pass@1 improvement on SWE-bench. The **astchunk** Python toolkit provides tree-sitter support for multi-language AST-based chunking.

**GraphQ IR** (EMNLP 2022) unifies semantic parsing across graph query languages, providing a universal intermediate representation bridging natural language and formal queries (SPARQL, Lambda-DCS, Cypher). With 11% accuracy improvement and 75% training time reduction, GraphQ IR demonstrates the effectiveness of unified semantic representations.

Graph neural network approaches show consistent improvements across domains. **GNN-based dependency parsing** achieves 96.0% UAS and 94.3% LAS on Penn Treebank, while **GNN-Coder** for AST-based code retrieval shows 1-10% MRR improvement on CodeSearchNet with 20% zero-shot performance gains.

## Practical RAG implementations achieve significant performance gains

**Neo4j GraphRAG** provides production-ready implementations with VectorRetriever, HybridRetriever, and Text2CypherRetriever components. The SimpleKGPipeline streamlines knowledge graph creation from documents, supporting OpenAI, Ollama, Google Vertex AI, and other LLM providers. Integration with external vector databases (Weaviate, Pinecone, Qdrant) enables flexible deployment architectures.

**Microsoft GraphRAG** uses community detection with hierarchical Leiden algorithms, generating LLM summaries for each community. This approach enables both global and local search capabilities with "substantial improvement in question-and-answer performance" according to Microsoft's benchmarks.

Performance benchmarks demonstrate GraphRAG's superiority: AWS and Lettria studies show **80% accuracy versus 50.83% for vector-only RAG**, with industry-specific improvements reaching 90.63% versus 46.88% for technical specifications. Data.world's enterprise study found 3x improvement across 43 business questions, while FalkorDB benchmarks show GraphRAG achieving 90%+ accuracy on schema-bound queries where vector RAG scored 0%.

**LlamaIndex PropertyGraphIndex** offers modular retrievers including LLMSynonymRetriever, VectorContextRetriever, and CypherTemplateRetriever. Supporting Neo4j, NebulaGraph, and Kuzu backends, it enables custom retriever implementations for domain-specific needs. The Knowledge Graph RAG Query Engine extracts subgraphs related to key entities using keyword-based, embedding-based, or hybrid entity retrieval modes.

## Unified schemas bridge prose and code semantics

**GraphQ IR** provides concrete unification through natural-language-like syntax with formally defined grammar. For example, the natural language query "What movies did Tom Hanks star in?" translates to GraphQ IR as `[FIND] movies [WHERE] actor = "Tom Hanks" [RELATION] stars_in`, which then compiles to target languages like SPARQL or Cypher without semantic loss.

**UniST (Unified Semantic Typing)** framework handles entity typing, relation classification, and event typing in a single system. Using joint semantic space embeddings with margin ranking loss, it transfers semantic knowledge across domains with limited training data, enabling compact multi-task models.

For mixed documents, **Jupyter notebook schema extensions** provide unified cell schemas with semantic metadata distinguishing prose, code, and mixed content types. The schema includes:

```json
{
  "semantic_metadata": {
    "content_type": "prose|code|mixed",
    "code_semantics": {
      "ast_representation": "structured_ast",
      "semantic_triples": ["subject-predicate-object"]
    },
    "prose_semantics": {
      "discourse_structure": "rhetorical_relations",
      "semantic_frames": ["predicate_argument_structures"]
    }
  }
}
```

Event-based unified schemas provide common ground between prose and code through shared event types (Creation, Modification, Communication) with role mappings linking Agent to Subject, Theme to Object, and Instrument to Method across domains.

## Kuzu storage patterns optimize vector and graph integration

Best practices for storing document embeddings alongside graph structure in Kuzu include using FLOAT[] arrays with consistent dimensions, enabling cache_embeddings for faster index construction, and implementing multi-modal vector storage:

```cypher
CREATE NODE TABLE MultiModalDocument(
    id STRING PRIMARY KEY,
    text_embedding FLOAT[384],
    image_embedding FLOAT[512],
    summary_embedding FLOAT[768]
);

CALL CREATE_VECTOR_INDEX('MultiModalDocument', 'text_idx', 'text_embedding');
```

Hybrid retrieval combines vector similarity with graph traversal:

```cypher
CALL QUERY_VECTOR_INDEX('Document', 'doc_title_index', $query_vector, 5) 
WITH node AS doc, distance
MATCH (doc)-[:CONTAINS]->(c:Chunk)-[:MENTIONS]->(e:Entity)
RETURN doc.title, e.name, distance
ORDER BY distance;
```

Performance optimization strategies include high-precision configurations with increased connectivity parameters (mu=50, ml=100, efc=500), projected graphs for filtered searches reducing search space, and batch loading using COPY FROM statements for efficient data ingestion.

## Model Context Protocol enables semantic search integration

**Neo4j MCP servers** provide the most comprehensive ecosystem with three main implementations. The **mcp-neo4j-cypher** server enables schema extraction and Cypher query execution, **mcp-neo4j-memory** implements knowledge graph-based persistent memory with entity and relation management, while **mcp-neo4j-data-modeling** offers tools for creating and visualizing graph data models with Mermaid export capabilities.

Configuration for Claude Desktop demonstrates simple integration:

```json
{
  "mcpServers": {
    "neo4j-cypher": {
      "command": "uvx",
      "args": ["mcp-neo4j-cypher"],
      "env": {
        "NEO4J_URL": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
      }
    }
  }
}
```

MCP servers integrate with major agent frameworks through adapters. LangChain integration allows Neo4j MCP servers to function as LangChain tools, Semantic Kernel converts MCP tools to kernel functions, while PydanticAI supports three modes: agents as MCP clients, agents within MCP servers, and purpose-built MCP servers.

## Cross-domain challenges require sophisticated alignment strategies

**Ambiguity resolution** across prose and code domains employs multi-modal context resolution combining prose context embeddings, code AST structure embeddings, and cross-modal attention weights. Ontology-based disambiguation uses hierarchical domain concepts with bridge concepts linking mechanisms and conflict resolution rules.

**Semantic alignment** achieves 37% improvement in group captioning and 22% in storytelling tasks through bidirectional semantic guidance. Alignment mechanisms extract semantic anchors from both domains, minimize cross-domain semantic distance through specialized loss functions, and handle one-to-many mappings through uncertainty-aware alignment.

**Context preservation** in mixed documents maintains semantic coherence through hierarchical document structures with global, section, and local context embeddings. Cross-reference resolution systems implement entity linking between prose mentions and code variables, concept mapping between documentation and implementation, and consistency checking for specification-implementation alignment.

## Conclusion

The convergence of semantic web standards, graph databases, and neural language models enables powerful unified schema architectures for RAG systems. **NIF and RDF/OWL** provide atomic semantic representation, **Kuzu's structured property graphs** offer performance-optimized storage, while **GraphQ IR** demonstrates successful cross-domain unification. Production implementations achieving 35-80% accuracy improvements validate these approaches, with comprehensive MCP server ecosystems enabling seamless integration. Success requires careful attention to hierarchical context preservation, hybrid retrieval strategies combining vector and graph search, and sophisticated alignment mechanisms for cross-domain semantic coherence. Organizations should leverage established frameworks like Neo4j GraphRAG or LlamaIndex PropertyGraph for rapid prototyping while customizing schemas based on domain-specific requirements.