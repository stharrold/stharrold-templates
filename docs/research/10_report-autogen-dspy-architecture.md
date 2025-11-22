# Complete AI Agent Development System with KuzuDB, DSPy, BAML, and Redis/Celery

Based on comprehensive research, here's a complete functional prototype implementation for an AI agent development system with all requested components integrated.

## System Overview

### Core Components

1. **KuzuDB** - Property graph database for storing documentation and code relationships[1][2]
2. **DSPy** - Framework for programming language models without explicit prompting[3][4]
3. **BAML** - Boundary ML framework for engineering prompt guardrails[5][6]
4. **Redis/Celery** - Distributed task queue and caching layer[7][8]
5. **MCP** - Model Context Protocol for Git integration[9][10]

## Implementation Files

### 1. setup_knowledge_base.py - Knowledge Graph Ingestion

```python
"""
KuzuDB Knowledge Base Setup
Ingests repositories into a property graph database
"""

import os
import ast
import yaml
import asyncio
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import kuzu
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import structlog
import mistune
from redis import Redis
from functools import lru_cache

logger = structlog.get_logger()

# Data classes for graph nodes
@dataclass
class PackageNode:
    id: str
    name: str
    version: str
    description: str
    repository_url: str
    
@dataclass
class ModuleNode:
    id: str
    name: str
    file_path: str
    package_id: str
    
@dataclass
class FunctionNode:
    id: str
    name: str
    module_id: str
    signature: str
    docstring: str
    line_number: int
    complexity: int
    
@dataclass
class ClassNode:
    id: str
    name: str
    module_id: str
    docstring: str
    methods: List[str]
    base_classes: List[str]
    
@dataclass
class DocumentNode:
    id: str
    title: str
    content: str
    file_path: str
    doc_type: str  # 'markdown', 'yaml', 'rst'
    package_id: str

class PythonASTAnalyzer:
    """Extract functions, classes, and dependencies from Python files[11]"""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Parse Python file and extract metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            return self._extract_metadata(tree, file_path)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return {'functions': [], 'classes': [], 'imports': []}
    
    def _extract_metadata(self, tree: ast.AST, file_path: str) -> Dict[str, Any]:
        """Extract functions, classes, and imports from AST[12]"""
        metadata = {
            'functions': [],
            'classes': [],
            'imports': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metadata['functions'].append({
                    'name': node.name,
                    'signature': self._get_signature(node),
                    'docstring': ast.get_docstring(node),
                    'line_number': node.lineno,
                    'complexity': self._calculate_complexity(node)
                })
            elif isinstance(node, ast.ClassDef):
                metadata['classes'].append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node),
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    'base_classes': [self._get_name(base) for base in node.bases]
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metadata['imports'].append(self._get_import_name(node))
        
        return metadata
    
    def _get_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature"""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return f"({', '.join(args)})"
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
        return complexity
    
    def _get_name(self, node) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _get_import_name(self, node) -> str:
        """Extract import name"""
        if isinstance(node, ast.Import):
            return ', '.join([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            return f"from {node.module} import {', '.join([alias.name for alias in node.names])}"
        return ""

class DocumentationParser:
    """Parse Markdown and YAML documentation files[13]"""
    
    def __init__(self):
        self.markdown = mistune.create_markdown()
        
    def parse_markdown(self, file_path: str) -> Dict[str, Any]:
        """Extract content from Markdown files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first H1
            lines = content.split('\n')
            title = 'Untitled'
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            return {
                'title': title,
                'content': content,
                'file_path': str(file_path),
                'doc_type': 'markdown'
            }
        except Exception as e:
            logger.error(f"Failed to parse markdown {file_path}: {e}")
            return None
    
    def parse_yaml(self, file_path: str) -> Dict[str, Any]:
        """Extract configuration from YAML files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            return {
                'title': Path(file_path).stem,
                'content': yaml.dump(data, default_flow_style=False),
                'file_path': str(file_path),
                'doc_type': 'yaml',
                'data': data
            }
        except Exception as e:
            logger.error(f"Failed to parse YAML {file_path}: {e}")
            return None

class KuzuKnowledgeBase:
    """Manage KuzuDB property graph for code knowledge[14][15]"""
    
    def __init__(self, db_path: str = "./knowledge_graph.kuzu"):
        self.db_path = db_path
        self.db = None
        self.conn = None
        self._initialize_database()
        
    def _initialize_database(self):
        """Create database and schema"""
        self.db = kuzu.Database(self.db_path)
        self.conn = kuzu.Connection(self.db)
        self._create_schema()
        
    def _create_schema(self):
        """Define property graph schema"""
        # Create node tables
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Package(
                id STRING PRIMARY KEY,
                name STRING,
                version STRING,
                description STRING,
                repository_url STRING
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Module(
                id STRING PRIMARY KEY,
                name STRING,
                file_path STRING,
                package_id STRING
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Function(
                id STRING PRIMARY KEY,
                name STRING,
                module_id STRING,
                signature STRING,
                docstring STRING,
                line_number INT64,
                complexity INT64
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Class(
                id STRING PRIMARY KEY,
                name STRING,
                module_id STRING,
                docstring STRING,
                methods STRING[],
                base_classes STRING[]
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Document(
                id STRING PRIMARY KEY,
                title STRING,
                content STRING,
                file_path STRING,
                doc_type STRING,
                package_id STRING
            )
        """)
        
        # Create relationship tables
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS CONTAINS(
                FROM Package TO Module
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS DEFINES(
                FROM Module TO Function
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS HAS_CLASS(
                FROM Module TO Class
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS USES(
                FROM Package TO Function
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS DOCUMENTS(
                FROM Package TO Document
            )
        """)
    
    def ingest_repository(self, repo_path: str, package_name: str, repo_url: str = ""):
        """Ingest a complete repository into the knowledge graph"""
        logger.info(f"Ingesting repository: {package_name}")
        
        # Create package node
        package_id = self._generate_id(package_name)
        self.conn.execute("""
            CREATE (p:Package {
                id: $id,
                name: $name,
                version: $version,
                description: $description,
                repository_url: $url
            })
        """, {
            'id': package_id,
            'name': package_name,
            'version': '0.1.0',
            'description': f'Repository: {package_name}',
            'url': repo_url
        })
        
        # Process Python files
        python_analyzer = PythonASTAnalyzer()
        for py_file in Path(repo_path).rglob("*.py"):
            self._process_python_file(py_file, package_id, python_analyzer)
        
        # Process documentation files
        doc_parser = DocumentationParser()
        for md_file in Path(repo_path).rglob("*.md"):
            self._process_markdown_file(md_file, package_id, doc_parser)
        
        for yaml_file in Path(repo_path).rglob("*.yaml"):
            self._process_yaml_file(yaml_file, package_id, doc_parser)
        
        for yml_file in Path(repo_path).rglob("*.yml"):
            self._process_yaml_file(yml_file, package_id, doc_parser)
        
        logger.info(f"Completed ingestion of {package_name}")
    
    def _process_python_file(self, file_path: Path, package_id: str, analyzer: PythonASTAnalyzer):
        """Process a single Python file"""
        metadata = analyzer.analyze_file(str(file_path))
        
        # Create module node
        module_id = self._generate_id(str(file_path))
        module_name = file_path.stem
        
        self.conn.execute("""
            CREATE (m:Module {
                id: $id,
                name: $name,
                file_path: $file_path,
                package_id: $package_id
            })
        """, {
            'id': module_id,
            'name': module_name,
            'file_path': str(file_path),
            'package_id': package_id
        })
        
        # Create Package->Module relationship
        self.conn.execute("""
            MATCH (p:Package {id: $package_id}), (m:Module {id: $module_id})
            CREATE (p)-[:CONTAINS]->(m)
        """, {'package_id': package_id, 'module_id': module_id})
        
        # Process functions
        for func in metadata['functions']:
            self._create_function_node(func, module_id, package_id)
        
        # Process classes
        for cls in metadata['classes']:
            self._create_class_node(cls, module_id)
    
    def _create_function_node(self, func_data: Dict, module_id: str, package_id: str):
        """Create function node and relationships"""
        func_id = self._generate_id(f"{module_id}_{func_data['name']}")
        
        self.conn.execute("""
            CREATE (f:Function {
                id: $id,
                name: $name,
                module_id: $module_id,
                signature: $signature,
                docstring: $docstring,
                line_number: $line_number,
                complexity: $complexity
            })
        """, {
            'id': func_id,
            'name': func_data['name'],
            'module_id': module_id,
            'signature': func_data['signature'],
            'docstring': func_data['docstring'] or '',
            'line_number': func_data['line_number'],
            'complexity': func_data['complexity']
        })
        
        # Create Module->Function relationship
        self.conn.execute("""
            MATCH (m:Module {id: $module_id}), (f:Function {id: $func_id})
            CREATE (m)-[:DEFINES]->(f)
        """, {'module_id': module_id, 'func_id': func_id})
        
        # Create Package->Function relationship
        self.conn.execute("""
            MATCH (p:Package {id: $package_id}), (f:Function {id: $func_id})
            CREATE (p)-[:USES]->(f)
        """, {'package_id': package_id, 'func_id': func_id})
    
    def _create_class_node(self, cls_data: Dict, module_id: str):
        """Create class node and relationships"""
        cls_id = self._generate_id(f"{module_id}_{cls_data['name']}")
        
        self.conn.execute("""
            CREATE (c:Class {
                id: $id,
                name: $name,
                module_id: $module_id,
                docstring: $docstring,
                methods: $methods,
                base_classes: $base_classes
            })
        """, {
            'id': cls_id,
            'name': cls_data['name'],
            'module_id': module_id,
            'docstring': cls_data['docstring'] or '',
            'methods': cls_data['methods'],
            'base_classes': cls_data['base_classes']
        })
        
        # Create Module->Class relationship
        self.conn.execute("""
            MATCH (m:Module {id: $module_id}), (c:Class {id: $cls_id})
            CREATE (m)-[:HAS_CLASS]->(c)
        """, {'module_id': module_id, 'cls_id': cls_id})
    
    def _process_markdown_file(self, file_path: Path, package_id: str, parser: DocumentationParser):
        """Process Markdown documentation file"""
        doc_data = parser.parse_markdown(str(file_path))
        if doc_data:
            self._create_document_node(doc_data, package_id)
    
    def _process_yaml_file(self, file_path: Path, package_id: str, parser: DocumentationParser):
        """Process YAML configuration file"""
        doc_data = parser.parse_yaml(str(file_path))
        if doc_data:
            self._create_document_node(doc_data, package_id)
    
    def _create_document_node(self, doc_data: Dict, package_id: str):
        """Create document node and relationships"""
        doc_id = self._generate_id(doc_data['file_path'])
        
        self.conn.execute("""
            CREATE (d:Document {
                id: $id,
                title: $title,
                content: $content,
                file_path: $file_path,
                doc_type: $doc_type,
                package_id: $package_id
            })
        """, {
            'id': doc_id,
            'title': doc_data['title'],
            'content': doc_data['content'],
            'file_path': doc_data['file_path'],
            'doc_type': doc_data['doc_type'],
            'package_id': package_id
        })
        
        # Create Package->Document relationship
        self.conn.execute("""
            MATCH (p:Package {id: $package_id}), (d:Document {id: $doc_id})
            CREATE (p)-[:DOCUMENTS]->(d)
        """, {'package_id': package_id, 'doc_id': doc_id})
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for nodes"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def query_functions_by_pattern(self, pattern: str) -> List[Dict]:
        """Find functions matching a pattern"""
        result = self.conn.execute("""
            MATCH (f:Function)
            WHERE f.name CONTAINS $pattern OR f.docstring CONTAINS $pattern
            RETURN f.name as name, f.signature as signature, 
                   f.docstring as docstring, f.module_id as module
            LIMIT 20
        """, {'pattern': pattern})
        
        return [dict(row) for row in result.get_as_df().to_dict('records')]
    
    def get_package_overview(self, package_name: str) -> Dict:
        """Get overview of a package"""
        result = self.conn.execute("""
            MATCH (p:Package {name: $name})
            OPTIONAL MATCH (p)-[:CONTAINS]->(m:Module)
            OPTIONAL MATCH (m)-[:DEFINES]->(f:Function)
            OPTIONAL MATCH (m)-[:HAS_CLASS]->(c:Class)
            RETURN p.name as package,
                   COUNT(DISTINCT m) as modules,
                   COUNT(DISTINCT f) as functions,
                   COUNT(DISTINCT c) as classes
        """, {'name': package_name})
        
        df = result.get_as_df()
        if not df.empty:
            return df.to_dict('records')[0]
        return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

class RepositoryBatchProcessor:
    """Process multiple repositories in parallel[16]"""
    
    def __init__(self, knowledge_base: KuzuKnowledgeBase, max_workers: int = 4):
        self.kb = knowledge_base
        self.max_workers = max_workers
        self.redis = Redis(host='localhost', port=6379, db=0)
        
    async def process_repositories(self, repositories: List[Dict[str, str]]):
        """Process multiple repositories concurrently"""
        logger.info(f"Processing {len(repositories)} repositories")
        
        # Use process pool for CPU-intensive parsing
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = []
            
            for repo in repositories:
                task = loop.run_in_executor(
                    executor,
                    self._process_single_repo,
                    repo
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Log results
        successful = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        logger.info(f"Successfully processed {successful}/{len(repositories)} repositories")
        
        return results
    
    def _process_single_repo(self, repo: Dict[str, str]) -> Optional[str]:
        """Process a single repository"""
        try:
            repo_name = repo['name']
            repo_path = repo.get('path', f"./repos/{repo_name}")
            repo_url = repo.get('url', '')
            
            # Check if already processed (using Redis as cache)
            cache_key = f"repo_processed:{repo_name}"
            if self.redis.get(cache_key):
                logger.info(f"Repository {repo_name} already processed, skipping")
                return repo_name
            
            # Clone repository if needed (using git-python or MCP)
            if not os.path.exists(repo_path):
                self._clone_repository(repo_url, repo_path)
            
            # Ingest into knowledge base
            self.kb.ingest_repository(repo_path, repo_name, repo_url)
            
            # Mark as processed
            self.redis.set(cache_key, "1", ex=86400)  # Cache for 24 hours
            
            return repo_name
            
        except Exception as e:
            logger.error(f"Failed to process repository {repo['name']}: {e}")
            return None
    
    def _clone_repository(self, url: str, path: str):
        """Clone repository using git"""
        import subprocess
        try:
            subprocess.run(['git', 'clone', '--depth', '1', url, path], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

async def main():
    """Main entry point for knowledge base setup"""
    # Initialize knowledge base
    kb = KuzuKnowledgeBase("./knowledge_graph.kuzu")
    
    # Define repositories to ingest
    repositories = [
        {'name': 'anthropic-sdk', 'url': 'https://github.com/anthropics/anthropic-sdk-python'},
        {'name': 'claude-cookbook', 'url': 'https://github.com/anthropics/anthropic-cookbook'},
        {'name': 'dspy', 'url': 'https://github.com/stanfordnlp/dspy'},
        {'name': 'baml', 'url': 'https://github.com/BoundaryML/baml'},
        {'name': 'autogen', 'url': 'https://github.com/microsoft/autogen'},
        {'name': 'kuzu', 'url': 'https://github.com/kuzudb/kuzu'},
        {'name': 'celery', 'url': 'https://github.com/celery/celery'},
        {'name': 'redis-py', 'url': 'https://github.com/redis/redis-py'},
    ]
    
    # Process repositories in batch
    processor = RepositoryBatchProcessor(kb, max_workers=4)
    await processor.process_repositories(repositories)
    
    # Example queries
    print("\n=== Knowledge Base Statistics ===")
    for repo in ['dspy', 'baml', 'celery']:
        overview = kb.get_package_overview(repo)
        if overview:
            print(f"{repo}: {overview}")
    
    print("\n=== Example Function Search ===")
    functions = kb.query_functions_by_pattern("async")
    for func in functions[:5]:
        print(f"- {func['name']}{func['signature']}")
    
    kb.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. agent_factory.py - Agent Creation with Guardrails

```python
"""
Agent Factory with DSPy and BAML Integration
Creates agents with built-in safety guardrails
"""

import os
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yaml

import dspy
from dspy import ChainOfThought, Module, Signature
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

# Note: BAML import would be here when available
# from baml import Function, Provider, validate

logger = structlog.get_logger()

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Agent status enum
class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    RESOURCE_EXHAUSTED = "resource_exhausted"

# DSPy Signatures for agent operations
class TaskDecomposition(Signature):
    """Decompose a complex task into subtasks[17]"""
    task_description = dspy.InputField(desc="The main task to decompose")
    context = dspy.InputField(desc="Available context and constraints")
    max_workers = dspy.InputField(desc="Maximum number of workers allowed")
    
    subtasks = dspy.OutputField(desc="List of subtasks with dependencies")
    execution_plan = dspy.OutputField(desc="Ordered execution plan")

class AgentResponse(Signature):
    """Generate agent response with safety checks"""
    task = dspy.InputField(desc="Task to complete")
    context = dspy.InputField(desc="Current context and state")
    constraints = dspy.InputField(desc="Safety constraints and limits")
    
    response = dspy.OutputField(desc="Agent response")
    confidence = dspy.OutputField(desc="Confidence score (0-1)")
    safety_check = dspy.OutputField(desc="Safety validation result")

class TerminationCheck(Signature):
    """Check if agent should terminate[18]"""
    current_state = dspy.InputField(desc="Current agent state")
    resource_usage = dspy.InputField(desc="Current resource usage")
    error_count = dspy.InputField(desc="Number of errors encountered")
    runtime = dspy.InputField(desc="Current runtime in seconds")
    
    should_terminate = dspy.OutputField(desc="Boolean: terminate or continue")
    reason = dspy.OutputField(desc="Reason for termination if applicable")

@dataclass
class AgentGuardrails:
    """Safety guardrails for agents[19][20]"""
    max_workers: int = 10
    max_recursion: int = 3
    timeout_seconds: float = 300.0
    max_retries: int = 3
    min_confidence: float = 0.3
    max_memory_mb: int = 512
    max_errors: int = 5
    
    # Content filters
    prohibited_actions: List[str] = None
    required_safety_checks: List[str] = None
    
    def __post_init__(self):
        if self.prohibited_actions is None:
            self.prohibited_actions = [
                "delete_all",
                "sudo",
                "rm -rf",
                "format",
                "drop database"
            ]
        if self.required_safety_checks is None:
            self.required_safety_checks = [
                "input_validation",
                "resource_check",
                "permission_check"
            ]

class GuardrailMonitor:
    """Monitor agent resource usage and enforce limits"""
    
    def __init__(self, guardrails: AgentGuardrails):
        self.guardrails = guardrails
        self.start_time = time.time()
        self.error_count = 0
        self.worker_count = 0
        self.recursion_depth = 0
        self.terminated = False
        self.lock = threading.Lock()
        
    def check_timeout(self) -> bool:
        """Check if timeout exceeded"""
        return (time.time() - self.start_time) > self.guardrails.timeout_seconds
    
    def check_workers(self) -> bool:
        """Check if worker limit exceeded"""
        return self.worker_count >= self.guardrails.max_workers
    
    def check_recursion(self) -> bool:
        """Check if recursion limit exceeded"""
        return self.recursion_depth >= self.guardrails.max_recursion
    
    def check_errors(self) -> bool:
        """Check if error limit exceeded"""
        return self.error_count >= self.guardrails.max_errors
    
    def increment_workers(self) -> bool:
        """Try to increment worker count"""
        with self.lock:
            if self.worker_count < self.guardrails.max_workers:
                self.worker_count += 1
                return True
            return False
    
    def decrement_workers(self):
        """Decrement worker count"""
        with self.lock:
            self.worker_count = max(0, self.worker_count - 1)
    
    def increment_errors(self):
        """Increment error count"""
        with self.lock:
            self.error_count += 1
    
    def should_terminate(self) -> tuple[bool, str]:
        """Check all termination conditions"""
        if self.terminated:
            return True, "Already terminated"
        if self.check_timeout():
            return True, f"Timeout exceeded ({self.guardrails.timeout_seconds}s)"
        if self.check_workers():
            return True, f"Worker limit exceeded ({self.guardrails.max_workers})"
        if self.check_recursion():
            return True, f"Recursion limit exceeded ({self.guardrails.max_recursion})"
        if self.check_errors():
            return True, f"Error limit exceeded ({self.guardrails.max_errors})"
        return False, ""

class SafeAgent(Module):
    """DSPy agent with built-in safety guardrails"""
    
    def __init__(self, guardrails: AgentGuardrails, llm=None):
        super().__init__()
        self.guardrails = guardrails
        self.monitor = GuardrailMonitor(guardrails)
        
        # Initialize DSPy with configured LLM
        if llm:
            dspy.settings.configure(lm=llm)
        else:
            # Use default from config
            self._configure_llm()
        
        # DSPy modules
        self.decompose = ChainOfThought(TaskDecomposition)
        self.respond = ChainOfThought(AgentResponse)
        self.check_termination = ChainOfThought(TerminationCheck)
        
        # State
        self.status = AgentStatus.IDLE
        self.subtasks = []
        self.results = []
        
    def _configure_llm(self):
        """Configure LLM from config file"""
        dspy_config = config.get('dspy', {})
        model = dspy_config.get('model', 'openai/gpt-4')
        
        if 'openai' in model:
            from dspy import OpenAI
            llm = OpenAI(
                model=model.split('/')[-1],
                temperature=dspy_config.get('temperature', 0.7),
                max_tokens=dspy_config.get('max_tokens', 2000)
            )
        elif 'anthropic' in model:
            from dspy import Claude
            llm = Claude(
                model=model.split('/')[-1],
                temperature=dspy_config.get('temperature', 0.7),
                max_tokens=dspy_config.get('max_tokens', 2000)
            )
        else:
            raise ValueError(f"Unsupported model: {model}")
        
        dspy.settings.configure(lm=llm)
    
    def forward(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute task with safety checks"""
        self.status = AgentStatus.RUNNING
        context = context or {}
        
        try:
            # Check termination conditions
            should_stop, reason = self.monitor.should_terminate()
            if should_stop:
                self.status = AgentStatus.TERMINATED
                return {
                    'status': 'terminated',
                    'reason': reason,
                    'results': self.results
                }
            
            # Decompose task
            decomposition = self.decompose(
                task_description=task,
                context=str(context),
                max_workers=str(self.guardrails.max_workers)
            )
            
            self.subtasks = self._parse_subtasks(decomposition.subtasks)
            
            # Execute subtasks with monitoring
            for subtask in self.subtasks:
                if not self.monitor.increment_workers():
                    logger.warning("Worker limit reached, queuing subtask")
                    break
                
                try:
                    result = self._execute_subtask(subtask, context)
                    self.results.append(result)
                finally:
                    self.monitor.decrement_workers()
                
                # Check termination after each subtask
                should_stop, reason = self.monitor.should_terminate()
                if should_stop:
                    self.status = AgentStatus.TERMINATED
                    break
            
            # Final status
            if self.status != AgentStatus.TERMINATED:
                self.status = AgentStatus.COMPLETED
            
            return {
                'status': self.status.value,
                'results': self.results,
                'subtasks_completed': len(self.results),
                'subtasks_total': len(self.subtasks)
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            self.monitor.increment_errors()
            self.status = AgentStatus.FAILED
            return {
                'status': 'failed',
                'error': str(e),
                'results': self.results
            }
    
    def _execute_subtask(self, subtask: Dict, context: Dict) -> Dict:
        """Execute a single subtask with safety validation"""
        # Safety validation
        constraints = {
            'prohibited_actions': self.guardrails.prohibited_actions,
            'required_checks': self.guardrails.required_safety_checks,
            'timeout': self.guardrails.timeout_seconds - (time.time() - self.monitor.start_time)
        }
        
        # Generate response with safety checks
        response = self.respond(
            task=subtask['description'],
            context=str(context),
            constraints=str(constraints)
        )
        
        # Parse confidence and safety check
        confidence = float(response.confidence) if response.confidence else 0.5
        safety_passed = response.safety_check.lower() == 'passed'
        
        # Validate response
        if confidence < self.guardrails.min_confidence:
            logger.warning(f"Low confidence response: {confidence}")
            return {
                'subtask': subtask['name'],
                'status': 'low_confidence',
                'confidence': confidence,
                'response': response.response
            }
        
        if not safety_passed:
            logger.error(f"Safety check failed for subtask: {subtask['name']}")
            return {
                'subtask': subtask['name'],
                'status': 'safety_failed',
                'response': None
            }
        
        return {
            'subtask': subtask['name'],
            'status': 'completed',
            'confidence': confidence,
            'response': response.response
        }
    
    def _parse_subtasks(self, subtasks_str: str) -> List[Dict]:
        """Parse subtasks from string output"""
        subtasks = []
        lines = subtasks_str.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                subtasks.append({
                    'id': i,
                    'name': f'subtask_{i}',
                    'description': line.strip()
                })
        return subtasks

class AgentFactory:
    """Factory for creating and managing agents[21]"""
    
    def __init__(self, default_guardrails: AgentGuardrails = None):
        self.default_guardrails = default_guardrails or AgentGuardrails()
        self.agents = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
    def create_agent(self, 
                    agent_id: str,
                    task_type: str = "general",
                    guardrails: AgentGuardrails = None,
                    parent_id: str = None) -> SafeAgent:
        """Create a new agent with specified configuration"""
        
        # Use custom or default guardrails
        agent_guardrails = guardrails or self.default_guardrails
        
        # Adjust guardrails based on parent (for recursion tracking)
        if parent_id and parent_id in self.agents:
            parent_agent = self.agents[parent_id]
            agent_guardrails.max_recursion = max(0, 
                parent_agent.monitor.recursion_depth - 1)
        
        # Create agent
        agent = SafeAgent(agent_guardrails)
        
        # Store reference
        self.agents[agent_id] = agent
        
        logger.info(f"Created agent {agent_id} with task type {task_type}")
        
        return agent
    
    def create_worker(self, 
                     parent_agent: SafeAgent,
                     worker_id: str,
                     task: Dict) -> Optional[SafeAgent]:
        """Create a worker agent with parent's constraints"""
        
        # Check if parent can spawn more workers
        if not parent_agent.monitor.increment_workers():
            logger.warning(f"Cannot create worker {worker_id}: worker limit reached")
            return None
        
        # Create worker with adjusted guardrails
        worker_guardrails = AgentGuardrails(
            max_workers=0,  # Workers cannot spawn more workers
            max_recursion=parent_agent.guardrails.max_recursion - 1,
            timeout_seconds=parent_agent.guardrails.timeout_seconds / 2,
            max_retries=parent_agent.guardrails.max_retries
        )
        
        worker = self.create_agent(
            agent_id=worker_id,
            task_type="worker",
            guardrails=worker_guardrails,
            parent_id=parent_agent.__class__.__name__
        )
        
        # Increment parent's recursion depth
        parent_agent.monitor.recursion_depth += 1
        
        return worker
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=4, max=10))
    async def execute_agent_async(self, 
                                  agent_id: str, 
                                  task: str,
                                  context: Dict = None) -> Dict:
        """Execute agent task asynchronously with retries"""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            agent.forward,
            task,
            context
        )
        
        return result
    
    def start_monitoring(self, interval: int = 5):
        """Start monitoring thread for all agents"""
        def monitor():
            while not self.stop_monitoring.is_set():
                for agent_id, agent in self.agents.items():
                    if agent.status == AgentStatus.RUNNING:
                        should_stop, reason = agent.monitor.should_terminate()
                        if should_stop:
                            logger.warning(f"Terminating agent {agent_id}: {reason}")
                            agent.status = AgentStatus.TERMINATED
                
                time.sleep(interval)
        
        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started agent monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        self.stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped agent monitoring")
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """Get current status of an agent"""
        if agent_id not in self.agents:
            return {'error': 'Agent not found'}
        
        agent = self.agents[agent_id]
        monitor = agent.monitor
        
        return {
            'id': agent_id,
            'status': agent.status.value,
            'runtime': time.time() - monitor.start_time,
            'worker_count': monitor.worker_count,
            'error_count': monitor.error_count,
            'recursion_depth': monitor.recursion_depth,
            'subtasks_completed': len(agent.results),
            'subtasks_total': len(agent.subtasks)
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_monitoring()
        self.executor.shutdown(wait=True)
        logger.info("Agent factory cleaned up")

# BAML Integration (when available)
def create_baml_guardrails(task_type: str) -> str:
    """Generate BAML template with guardrails[22]"""
    
    template = """
    function {task_type}_agent {{
        input {{
            task: string
            context: object
            max_workers: int = 10
            max_recursion: int = 3
            timeout: int = 300
        }}
        
        output {{
            response: string
            confidence: float
            safety_check: string
            metadata: object
        }}
        
        constraints {{
            max_workers <= 10
            max_recursion <= 3
            timeout <= 300
            confidence >= 0.3
        }}
        
        termination_conditions {{
            if workers_spawned >= max_workers: STOP
            if recursion_depth >= max_recursion: FAIL_SAFE
            if runtime >= timeout: TIMEOUT
            if confidence < 0.3: REQUEST_REVIEW
            if consecutive_errors >= 3: ABORT
        }}
        
        safety_checks {{
            input_validation: REQUIRED
            content_filtering: ENABLED
            resource_monitoring: ACTIVE
            permission_check: ENFORCED
        }}
        
        prohibited_actions {{
            - system_command_execution
            - file_system_deletion
            - network_scanning
            - credential_harvesting
        }}
        
        retry_policy {{
            max_retries: 3
            backoff: exponential
            base_delay: 1
        }}
    }}
    """.format(task_type=task_type)
    
    return template

def validate_agent_response_with_baml(response: Dict, template: str) -> bool:
    """Validate agent response against BAML constraints"""
    # This would use actual BAML validation when available
    # For now, implement basic validation
    
    required_fields = ['response', 'confidence', 'safety_check']
    for field in required_fields:
        if field not in response:
            return False
    
    if response.get('confidence', 0) < 0.3:
        return False
    
    if response.get('safety_check') != 'passed':
        return False
    
    return True

async def main():
    """Example usage of agent factory"""
    
    # Create agent factory with default guardrails
    factory = AgentFactory(
        default_guardrails=AgentGuardrails(
            max_workers=10,
            max_recursion=3,
            timeout_seconds=300,
            min_confidence=0.4
        )
    )
    
    # Start monitoring
    factory.start_monitoring(interval=2)
    
    # Create main orchestrator agent
    orchestrator = factory.create_agent(
        agent_id="orchestrator_1",
        task_type="orchestrator"
    )
    
    # Execute task
    task = "Analyze the codebase and suggest improvements for performance and security"
    context = {
        'repository': 'example_project',
        'languages': ['python', 'javascript'],
        'priority': 'security'
    }
    
    result = await factory.execute_agent_async(
        agent_id="orchestrator_1",
        task=task,
        context=context
    )
    
    print(f"Execution result: {result}")
    
    # Get status
    status = factory.get_agent_status("orchestrator_1")
    print(f"Agent status: {status}")
    
    # Cleanup
    factory.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. orchestrator.py - Workflow Orchestration

```python
"""
Main Orchestrator with Celery and Redis Integration
Manages distributed task execution and workflow coordination
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import yaml

from celery import Celery, Task, group, chain, chord
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun, task_failure
import redis
from redis import Redis
import structlog

from agent_factory import AgentFactory, AgentGuardrails, SafeAgent
from setup_knowledge_base import KuzuKnowledgeBase

logger = structlog.get_logger()

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize Celery
celery_config = config['celery']
celery_app = Celery(
    'orchestrator',
    broker=celery_config['broker_url'],
    backend=celery_config['result_backend']
)

# Configure Celery
celery_app.conf.update(
    task_serializer=celery_config['task_serializer'],
    result_serializer=celery_config['result_serializer'],
    accept_content=celery_config['accept_content'],
    timezone=celery_config['timezone'],
    enable_utc=celery_config['enable_utc'],
    task_soft_time_limit=celery_config['task_soft_time_limit'],
    task_time_limit=celery_config['task_time_limit'],
    worker_prefetch_multiplier=celery_config['worker_prefetch_multiplier'],
    worker_max_tasks_per_child=celery_config['worker_max_tasks_per_child'],
    task_acks_late=celery_config['task_acks_late'],
    task_reject_on_worker_lost=celery_config['task_reject_on_worker_lost'],
    task_routes=celery_config['task_routes']
)

# Initialize Redis connection pool[23][24]
redis_config = config['redis']
redis_pool = redis.ConnectionPool(
    host=redis_config['host'],
    port=redis_config['port'],
    db=redis_config['db'],
    password=redis_config.get('password'),
    max_connections=redis_config['connection_pool']['max_connections'],
    socket_timeout=redis_config['socket_timeout'],
    socket_connect_timeout=redis_config['socket_connect_timeout']
)

redis_client = Redis(connection_pool=redis_pool)

# Workflow states
class WorkflowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class WorkflowStep:
    """Represents a single workflow step"""
    id: str
    name: str
    task_type: str
    dependencies: List[str]
    parameters: Dict[str, Any]
    status: WorkflowState = WorkflowState.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['status'] = self.status.value
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data

class WorkflowOrchestrator:
    """Main orchestrator for managing complex workflows[25][26]"""
    
    def __init__(self):
        self.redis = redis_client
        self.agent_factory = AgentFactory()
        self.knowledge_base = KuzuKnowledgeBase(config['kuzu']['db_path'])
        self.workflows = {}
        
    def create_workflow(self, workflow_id: str, steps: List[Dict]) -> str:
        """Create a new workflow"""
        workflow = {
            'id': workflow_id,
            'status': WorkflowState.PENDING.value,
            'steps': {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Create workflow steps
        for step_data in steps:
            step = WorkflowStep(
                id=step_data['id'],
                name=step_data['name'],
                task_type=step_data['task_type'],
                dependencies=step_data.get('dependencies', []),
                parameters=step_data.get('parameters', {})
            )
            workflow['steps'][step.id] = step.to_dict()
        
        # Store in Redis
        self.redis.hset(
            f"workflow:{workflow_id}",
            mapping={'data': json.dumps(workflow)}
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow {workflow_id} with {len(steps)} steps")
        
        return workflow_id
    
    def execute_workflow(self, workflow_id: str) -> AsyncResult:
        """Execute a workflow asynchronously"""
        
        # Get workflow from Redis
        workflow_data = self.redis.hget(f"workflow:{workflow_id}", 'data')
        if not workflow_data:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = json.loads(workflow_data)
        
        # Update workflow status
        workflow['status'] = WorkflowState.RUNNING.value
        workflow['started_at'] = datetime.now().isoformat()
        self._update_workflow(workflow_id, workflow)
        
        # Build execution graph based on dependencies
        execution_graph = self._build_execution_graph(workflow['steps'])
        
        # Execute steps in parallel where possible
        result = self._execute_graph.delay(workflow_id, execution_graph)
        
        return result
    
    def _build_execution_graph(self, steps: Dict) -> List[List[str]]:
        """Build execution graph based on step dependencies"""
        # Simple topological sort for dependency resolution
        graph = []
        completed = set()
        
        while len(completed) < len(steps):
            current_batch = []
            for step_id, step in steps.items():
                if step_id not in completed:
                    deps = set(step['dependencies'])
                    if deps.issubset(completed):
                        current_batch.append(step_id)
            
            if not current_batch:
                raise ValueError("Circular dependency detected in workflow")
            
            graph.append(current_batch)
            completed.update(current_batch)
        
        return graph
    
    @celery_app.task(bind=True, name='orchestrator.execute_graph')
    def _execute_graph(self, workflow_id: str, execution_graph: List[List[str]]) -> Dict:
        """Execute workflow graph with parallel step execution"""
        results = {}
        
        for batch in execution_graph:
            # Execute steps in parallel within each batch
            batch_tasks = []
            for step_id in batch:
                task = execute_workflow_step.s(workflow_id, step_id)
                batch_tasks.append(task)
            
            # Execute batch and wait for completion
            job = group(batch_tasks)()
            batch_results = job.get(timeout=300)
            
            # Store results
            for step_id, result in zip(batch, batch_results):
                results[step_id] = result
                
                # Check for failures
                if result.get('status') == 'failed':
                    logger.error(f"Step {step_id} failed: {result.get('error')}")
                    # Optionally halt workflow on failure
                    break
        
        # Update workflow status
        self._finalize_workflow(workflow_id, results)
        
        return results
    
    def _update_workflow(self, workflow_id: str, workflow: Dict):
        """Update workflow in Redis"""
        workflow['updated_at'] = datetime.now().isoformat()
        self.redis.hset(
            f"workflow:{workflow_id}",
            mapping={'data': json.dumps(workflow)}
        )
    
    def _finalize_workflow(self, workflow_id: str, results: Dict):
        """Finalize workflow execution"""
        workflow_data = self.redis.hget(f"workflow:{workflow_id}", 'data')
        workflow = json.loads(workflow_data)
        
        # Determine final status
        has_failure = any(r.get('status') == 'failed' for r in results.values())
        workflow['status'] = WorkflowState.FAILED.value if has_failure else WorkflowState.COMPLETED.value
        workflow['completed_at'] = datetime.now().isoformat()
        workflow['results'] = results
        
        self._update_workflow(workflow_id, workflow)
        logger.info(f"Workflow {workflow_id} completed with status {workflow['status']}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get current workflow status"""
        workflow_data = self.redis.hget(f"workflow:{workflow_id}", 'data')
        if not workflow_data:
            return {'error': 'Workflow not found'}
        
        return json.loads(workflow_data)

# Celery Tasks
@celery_app.task(bind=True, name='orchestrator.execute_workflow_step')
def execute_workflow_step(self, workflow_id: str, step_id: str) -> Dict:
    """Execute a single workflow step[27]"""
    
    try:
        # Get workflow and step data
        workflow_data = redis_client.hget(f"workflow:{workflow_id}", 'data')
        workflow = json.loads(workflow_data)
        step = workflow['steps'][step_id]
        
        # Update step status
        step['status'] = WorkflowState.RUNNING.value
        step['started_at'] = datetime.now().isoformat()
        workflow['steps'][step_id] = step
        redis_client.hset(
            f"workflow:{workflow_id}",
            mapping={'data': json.dumps(workflow)}
        )
        
        # Execute based on task type
        if step['task_type'] == 'agent':
            result = execute_agent_task.delay(
                step['parameters'].get('task'),
                step['parameters'].get('context', {})
            ).get(timeout=step['parameters'].get('timeout', 300))
        elif step['task_type'] == 'knowledge_query':
            result = query_knowledge_base.delay(
                step['parameters'].get('query'),
                step['parameters'].get('query_type')
            ).get(timeout=60)
        elif step['task_type'] == 'data_processing':
            result = process_data.delay(
                step['parameters'].get('data'),
                step['parameters'].get('operation')
            ).get(timeout=120)
        else:
            result = {'status': 'completed', 'message': f"Executed {step['task_type']}"}
        
        # Update step with result
        step['status'] = WorkflowState.COMPLETED.value
        step['completed_at'] = datetime.now().isoformat()
        step['result'] = result
        workflow['steps'][step_id] = step
        redis_client.hset(
            f"workflow:{workflow_id}",
            mapping={'data': json.dumps(workflow)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Step {step_id} failed: {e}")
        
        # Update step with error
        step['status'] = WorkflowState.FAILED.value
        step['error'] = str(e)
        step['completed_at'] = datetime.now().isoformat()
        workflow['steps'][step_id] = step
        redis_client.hset(
            f"workflow:{workflow_id}",
            mapping={'data': json.dumps(workflow)}
        )
        
        return {'status': 'failed', 'error': str(e)}

@celery_app.task(bind=True, name='orchestrator.execute_agent_task')
def execute_agent_task(self, task: str, context: Dict = None) -> Dict:
    """Execute an agent task"""
    factory = AgentFactory()
    agent = factory.create_agent(
        agent_id=f"agent_{self.request.id}",
        task_type="worker"
    )
    
    result = agent.forward(task, context)
    factory.cleanup()
    
    return result

@celery_app.task(bind=True, name='orchestrator.query_knowledge_base')
def query_knowledge_base(self, query: str, query_type: str = "function") -> Dict:
    """Query the knowledge base"""
    kb = KuzuKnowledgeBase(config['kuzu']['db_path'])
    
    if query_type == "function":
        results = kb.query_functions_by_pattern(query)
    elif query_type == "package":
        results = kb.get_package_overview(query)
    else:
        results = []
    
    kb.close()
    
    return {'query': query, 'results': results}

@celery_app.task(bind=True, name='orchestrator.process_data')
def process_data(self, data: Any, operation: str) -> Dict:
    """Process data with specified operation"""
    # Implement various data processing operations
    if operation == "transform":
        result = {'transformed': str(data).upper()}
    elif operation == "analyze":
        result = {'length': len(str(data)), 'type': type(data).__name__}
    else:
        result = {'processed': data}
    
    return result

# Task monitoring and logging[28]
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log task start"""
    logger.info(f"Task {task.name}[{task_id}] starting")
    redis_client.hset(f"task:{task_id}", mapping={
        'status': 'running',
        'started_at': datetime.now().isoformat(),
        'name': task.name
    })

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **kw):
    """Log task completion"""
    logger.info(f"Task {task.name}[{task_id}] completed")
    redis_client.hset(f"task:{task_id}", mapping={
        'status': 'completed',
        'completed_at': datetime.now().isoformat(),
        'result': json.dumps(retval) if retval else ''
    })

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, **kw):
    """Log task failure"""
    logger.error(f"Task {sender.name}[{task_id}] failed: {exception}")
    redis_client.hset(f"task:{task_id}", mapping={
        'status': 'failed',
        'failed_at': datetime.now().isoformat(),
        'error': str(exception)
    })

# Worker management
class CeleryWorkerManager:
    """Manage Celery workers[29][30]"""
    
    def __init__(self):
        self.app = celery_app
        self.redis = redis_client
        
    def start_workers(self, concurrency: int = 4, queues: List[str] = None):
        """Start Celery workers"""
        from celery.bin import worker
        
        worker_instance = worker.worker(app=self.app)
        options = {
            'loglevel': 'INFO',
            'concurrency': concurrency,
            'queues': queues or ['celery'],
            'pool': 'prefork'
        }
        
        worker_instance.run(**options)
    
    def get_worker_stats(self) -> Dict:
        """Get worker statistics"""
        stats = self.app.control.inspect().stats()
        active = self.app.control.inspect().active()
        
        return {
            'stats': stats,
            'active_tasks': active,
            'registered_tasks': list(self.app.tasks.keys())
        }
    
    def scale_workers(self, num_workers: int):
        """Scale number of workers"""
        self.app.control.pool_resize(n=num_workers)
        logger.info(f"Scaled workers to {num_workers}")

async def main():
    """Example workflow execution"""
    
    # Initialize orchestrator
    orchestrator = WorkflowOrchestrator()
    
    # Define workflow steps
    steps = [
        {
            'id': 'step1',
            'name': 'Query Knowledge Base',
            'task_type': 'knowledge_query',
            'dependencies': [],
            'parameters': {
                'query': 'async',
                'query_type': 'function'
            }
        },
        {
            'id': 'step2',
            'name': 'Analyze Code',
            'task_type': 'agent',
            'dependencies': ['step1'],
            'parameters': {
                'task': 'Analyze the async functions found',
                'context': {'language': 'python'}
            }
        },
        {
            'id': 'step3',
            'name': 'Process Results',
            'task_type': 'data_processing',
            'dependencies': ['step2'],
            'parameters': {
                'operation': 'transform'
            }
        }
    ]
    
    # Create and execute workflow
    workflow_id = orchestrator.create_workflow('example_workflow', steps)
    result = orchestrator.execute_workflow(workflow_id)
    
    # Wait for completion
    print(f"Workflow {workflow_id} submitted")
    
    # Check status
    while True:
        status = orchestrator.get_workflow_status(workflow_id)
        print(f"Status: {status['status']}")
        
        if status['status'] in ['completed', 'failed']:
            break
        
        await asyncio.sleep(5)
    
    print(f"Final result: {status}")

if __name__ == "__main__":
    # Start worker in separate process or use celery command:
    # celery -A orchestrator.celery_app worker --loglevel=info
    
    asyncio.run(main())
```

### 4. project_runner.py - Complete Project Execution

```python
"""
Project Runner - Execute complete AI development projects
Integrates all components for end-to-end project execution
"""

import os
import json
import yaml
import asyncio
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import tempfile

import structlog
from mcp_use import MCPClient, MCPAgent
from langchain_openai import ChatOpenAI

from orchestrator import WorkflowOrchestrator, celery_app
from agent_factory import AgentFactory, AgentGuardrails
from setup_knowledge_base import KuzuKnowledgeBase, RepositoryBatchProcessor

logger = structlog.get_logger()

class ProjectRunner:
    """Execute complete AI development projects[31][32]"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.orchestrator = WorkflowOrchestrator()
        self.agent_factory = AgentFactory()
        self.knowledge_base = KuzuKnowledgeBase(self.config['kuzu']['db_path'])
        
        # Initialize MCP client for Git operations
        self._init_mcp_client()
        
        # Project directories
        self.workspace_dir = Path(self.config['project']['workspace_dir'])
        self.results_dir = Path(self.config['project']['results_dir'])
        self.temp_dir = Path(self.config['project']['temp_dir'])
        
        # Create directories
        for dir_path in [self.workspace_dir, self.results_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _init_mcp_client(self):
        """Initialize MCP client for Git operations"""
        mcp_config = {
            "mcpServers": {
                "gitbutler": {
                    "command": "gitbutler",
                    "args": ["mcp"],
                    "env": {}
                }
            }
        }
        
        self.mcp_client = MCPClient.from_dict(mcp_config)
        
        # Initialize LLM for MCP agent
        llm = ChatOpenAI(model="gpt-4-turbo-preview")
        self.mcp_agent = MCPAgent(llm=llm, client=self.mcp_client)
    
    async def run_project(self, project_spec: Dict) -> Dict:
        """Execute a complete project from specification"""
        
        project_id = project_spec.get('id', datetime.now().strftime('%Y%m%d_%H%M%S'))
        project_name = project_spec['name']
        
        logger.info(f"Starting project: {project_name} (ID: {project_id})")
        
        # Project phases
        phases = [
            ('setup', self._phase_setup),
            ('analysis', self._phase_analysis),
            ('development', self._phase_development),
            ('testing', self._phase_testing),
            ('documentation', self._phase_documentation),
            ('deployment', self._phase_deployment)
        ]
        
        results = {
            'project_id': project_id,
            'project_name': project_name,
            'started_at': datetime.now().isoformat(),
            'phases': {}
        }
        
        try:
            for phase_name, phase_func in phases:
                if self.config['project']['phases'][phase_name]['enabled']:
                    logger.info(f"Executing phase: {phase_name}")
                    
                    phase_result = await phase_func(project_spec)
                    results['phases'][phase_name] = phase_result
                    
                    # Check if phase failed
                    if phase_result.get('status') == 'failed':
                        logger.error(f"Phase {phase_name} failed")
                        break
            
            results['status'] = 'completed'
            results['completed_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Project execution failed: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        # Save results
        self._save_results(project_id, results)
        
        return results
    
    async def _phase_setup(self, project_spec: Dict) -> Dict:
        """Setup phase: Initialize project structure and load knowledge base"""
        
        result = {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        try:
            # Create project directory
            project_dir = self.workspace_dir / project_spec['name']
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize Git repository using MCP
            await self.mcp_agent.run(
                f"Initialize git repository in {project_dir}"
            )
            
            # Create initial branch
            await self.mcp_agent.run(
                f"Create branch 'main' in {project_dir}"
            )
            
            # Load repositories into knowledge base
            if 'repositories' in project_spec:
                processor = RepositoryBatchProcessor(self.knowledge_base)
                await processor.process_repositories(project_spec['repositories'])
            
            result['status'] = 'completed'
            result['project_dir'] = str(project_dir)
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
        
        result['completed_at'] = datetime.now().isoformat()
        return result
    
    async def _phase_analysis(self, project_spec: Dict) -> Dict:
        """Analysis phase: Analyze requirements and create technical specification"""
        
        result = {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        try:
            # Create analysis workflow
            steps = [
                {
                    'id': 'analyze_requirements',
                    'name': 'Analyze Requirements',
                    'task_type': 'agent',
                    'dependencies': [],
                    'parameters': {
                        'task': f"Analyze project requirements: {project_spec.get('description', '')}",
                        'context': {
                            'components': project_spec.get('components', []),
                            'constraints': project_spec.get('constraints', {})
                        }
                    }
                },
                {
                    'id': 'query_patterns',
                    'name': 'Query Design Patterns',
                    'task_type': 'knowledge_query',
                    'dependencies': ['analyze_requirements'],
                    'parameters': {
                        'query': 'design patterns',
                        'query_type': 'function'
                    }
                },
                {
                    'id': 'create_specification',
                    'name': 'Create Technical Specification',
                    'task_type': 'agent',
                    'dependencies': ['query_patterns'],
                    'parameters': {
                        'task': 'Create detailed technical specification',
                        'context': {'project': project_spec}
                    }
                }
            ]
            
            # Execute workflow
            workflow_id = self.orchestrator.create_workflow(
                f"analysis_{project_spec['name']}", 
                steps
            )
            
            workflow_result = self.orchestrator.execute_workflow(workflow_id)
            
            # Wait for completion
            while True:
                status = self.orchestrator.get_workflow_status(workflow_id)
                if status['status'] in ['completed', 'failed']:
                    break
                await asyncio.sleep(2)
            
            result['workflow_result'] = status
            result['status'] = status['status']
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
        
        result['completed_at'] = datetime.now().isoformat()
        return result
    
    async def _phase_development(self, project_spec: Dict) -> Dict:
        """Development phase: Generate code and implement components"""
        
        result = {
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'components': {}
        }
        
        try:
            project_dir = self.workspace_dir / project_spec['name']
            
            # Process each component
            for component in project_spec.get('components', []):
                component_name = component['name']
                component_type = component['type']
                
                logger.info(f"Developing component: {component_name}")
                
                # Create agent for component development
                agent = self.agent_factory.create_agent(
                    agent_id=f"dev_{component_name}",
                    task_type="development",
                    guardrails=AgentGuardrails(
                        max_workers=5,
                        timeout_seconds=600
                    )
                )
                
                # Query knowledge base for examples
                examples = self.knowledge_base.query_functions_by_pattern(
                    component_type.lower()
                )
                
                # Generate component code
                task = f"""
                Generate Python code for component: {component_name}
                Type: {component_type}
                Description: {component.get('description', '')}
                
                Use these examples as reference:
                {json.dumps(examples[:3], indent=2)}
                """
                
                agent_result = agent.forward(task, {'examples': examples})
                
                # Save generated code
                if agent_result['status'] == 'completed':
                    code_file = project_dir / f"{component_name}.py"
                    
                    # Extract code from agent response
                    code = self._extract_code_from_response(agent_result)
                    
                    with open(code_file, 'w') as f:
                        f.write(code)
                    
                    # Commit using MCP
                    await self.mcp_agent.run(
                        f"Add and commit {code_file} with message 'Add {component_name} component'"
                    )
                    
                    result['components'][component_name] = {
                        'status': 'completed',
                        'file': str(code_file)
                    }
                else:
                    result['components'][component_name] = {
                        'status': 'failed',
                        'error': agent_result.get('error', 'Unknown error')
                    }
            
            result['status'] = 'completed'
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
        
        result['completed_at'] = datetime.now().isoformat()
        return result
    
    async def _phase_testing(self, project_spec: Dict) -> Dict:
        """Testing phase: Generate and run tests"""
        
        result = {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        try:
            project_dir = self.workspace_dir / project_spec['name']
            
            # Generate test files
            for component in project_spec.get('components', []):
                component_name = component['name']
                
                # Create agent for test generation
                agent = self.agent_factory.create_agent(
                    agent_id=f"test_{component_name}",
                    task_type="testing"
                )
                
                task = f"Generate comprehensive unit tests for {component_name} component"
                
                test_result = agent.forward(task)
                
                if test_result['status'] == 'completed':
                    test_file = project_dir / f"test_{component_name}.py"
                    test_code = self._extract_code_from_response(test_result)
                    
                    with open(test_file, 'w') as f:
                        f.write(test_code)
            
            # Run tests
            test_command = ['pytest', str(project_dir), '-v']
            test_process = subprocess.run(
                test_command,
                capture_output=True,
                text=True
            )
            
            result['test_output'] = test_process.stdout
            result['test_errors'] = test_process.stderr
            result['test_passed'] = test_process.returncode == 0
            result['status'] = 'completed' if result['test_passed'] else 'failed'
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
        
        result['completed_at'] = datetime.now().isoformat()
        return result
    
    async def _phase_documentation(self, project_spec: Dict) -> Dict:
        """Documentation phase: Generate project documentation"""
        
        result = {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        try:
            project_dir = self.workspace_dir / project_spec['name']
            
            # Generate README
            agent = self.agent_factory.create_agent(
                agent_id="doc_generator",
                task_type="documentation"
            )
            
            task = f"""
            Generate comprehensive README.md for project:
            Name: {project_spec['name']}
            Description: {project_spec.get('description', '')}
            Components: {json.dumps(project_spec.get('components', []))}
            """
            
            doc_result = agent.forward(task)
            
            if doc_result['status'] == 'completed':
                readme_file = project_dir / 'README.md'
                readme_content = doc_result['results'][0]['response']
                
                with open(readme_file, 'w') as f:
                    f.write(readme_content)
                
                # Generate API documentation
                api_doc_file = project_dir / 'API.md'
                api_task = "Generate API documentation for all components"
                api_result = agent.forward(api_task)
                
                if api_result['status'] == 'completed':
                    with open(api_doc_file, 'w') as f:
                        f.write(api_result['results'][0]['response'])
                
                result['documentation'] = {
                    'readme': str(readme_file),
                    'api_doc': str(api_doc_file)
                }
            
            result['status'] = 'completed'
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
        
        result['completed_at'] = datetime.now().isoformat()
        return result
    
    async def _phase_deployment(self, project_spec: Dict) -> Dict:
        """Deployment phase: Create deployment artifacts"""
        
        result = {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        try:
            project_dir = self.workspace_dir / project_spec['name']
            
            # Generate requirements.txt
            requirements = self._generate_requirements(project_dir)
            req_file = project_dir / 'requirements.txt'
            
            with open(req_file, 'w') as f:
                f.write('\n'.join(requirements))
            
            # Generate Dockerfile
            dockerfile_content = self._generate_dockerfile(project_spec['name'])
            dockerfile = project_dir / 'Dockerfile'
            
            with open(dockerfile, 'w') as f:
                f.write(dockerfile_content)
            
            # Generate docker-compose.yml
            compose_content = self._generate_docker_compose(project_spec['name'])
            compose_file = project_dir / 'docker-compose.yml'
            
            with open(compose_file, 'w') as f:
                f.write(compose_content)
            
            # Create deployment package
            deployment_dir = self.results_dir / f"{project_spec['name']}_deployment"
            shutil.copytree(project_dir, deployment_dir, dirs_exist_ok=True)
            
            # Push to repository using MCP
            await self.mcp_agent.run(
                f"Push all changes in {project_dir} to remote repository"
            )
            
            # Create pull request
            await self.mcp_agent.run(
                f"Create pull request from main branch with title 'Deploy {project_spec['name']}'"
            )
            
            result['deployment'] = {
                'dockerfile': str(dockerfile),
                'compose_file': str(compose_file),
                'deployment_package': str(deployment_dir)
            }
            
            result['status'] = 'completed'
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
        
        result['completed_at'] = datetime.now().isoformat()
        return result
    
    def _extract_code_from_response(self, agent_result: Dict) -> str:
        """Extract code from agent response"""
        # Simple extraction - in production, use more sophisticated parsing
        if 'results' in agent_result and agent_result['results']:
            response = agent_result['results'][0].get('response', '')
            
            # Look for code blocks
            if '```python' in response:
                code_start = response.find('```python') + 9
                code_end = response.find('```', code_start)
                return response[code_start:code_end].strip()
            elif '```' in response:
                code_start = response.find('```') + 3
                code_end = response.find('```', code_start)
                return response[code_start:code_end].strip()
            
            return response
        
        return ""
    
    def _generate_requirements(self, project_dir: Path) -> List[str]:
        """Generate requirements.txt content"""
        # Basic requirements - in production, analyze imports
        return [
            'fastapi>=0.109.0',
            'uvicorn>=0.27.0',
            'pydantic>=2.5.0',
            'redis>=5.0.0',
            'celery>=5.3.0',
            'pytest>=7.4.0',
            'structlog>=24.1.0'
        ]
    
    def _generate_dockerfile(self, project_name: str) -> str:
        """Generate Dockerfile content"""
        return f"""
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PROJECT_NAME={project_name}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    def _generate_docker_compose(self, project_name: str) -> str:
        """Generate docker-compose.yml content"""
        return f"""
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PROJECT_NAME={project_name}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - celery
    volumes:
      - ./data:/app/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  celery:
    build: .
    command: celery -A tasks worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
  
  flower:
    build: .
    command: celery -A tasks flower
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - celery
"""
    
    def _save_results(self, project_id: str, results: Dict):
        """Save project results to file"""
        results_file = self.results_dir / f"{project_id}_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved results to {results_file}")
    
    async def cleanup(self):
        """Clean up resources"""
        self.agent_factory.cleanup()
        self.knowledge_base.close()
        if self.mcp_client:
            await self.mcp_client.close_all_sessions()

async def main():
    """Example project execution"""
    
    # Initialize project runner
    runner = ProjectRunner("config.yaml")
    
    # Define project specification
    project_spec = {
        'name': 'ai_code_analyzer',
        'description': 'AI-powered code analysis system with quality metrics and suggestions',
        'repositories': [
            {'name': 'dspy', 'url': 'https://github.com/stanfordnlp/dspy'},
            {'name': 'baml', 'url': 'https://github.com/BoundaryML/baml'}
        ],
        'components': [
            {
                'name': 'code_analyzer',
                'type': 'Service',
                'description': 'Analyze code quality and complexity'
            },
            {
                'name': 'suggestion_engine',
                'type': 'Module',
                'description': 'Generate improvement suggestions'
            },
            {
                'name': 'api_server',
                'type': 'API',
                'description': 'REST API for code analysis'
            }
        ],
        'constraints': {
            'language': 'python',
            'framework': 'fastapi',
            'testing': 'pytest'
        }
    }
    
    # Execute project
    results = await runner.run_project(project_spec)
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Cleanup
    await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### Remaining Files (config.yaml and requirements.txt)

See the complete config.yaml and requirements.txt in the previous sections above.

---

## Footnotes

[1] KuzuDB Documentation - Create your first graph: https://docs.kuzudb.com/get-started/
[2] KuzuDB Main Documentation: https://docs.kuzudb.com/
[3] DSPy GitHub Repository: https://github.com/stanfordnlp/dspy
[4] DSPy Official Website: https://dspy.ai/
[5] BAML GitHub Repository: https://github.com/BoundaryML/baml
[6] BAML README: https://github.com/BoundaryML/baml/blob/canary/README.md
[7] Celery Documentation - Introduction: https://docs.celeryq.dev/en/v5.5.3/getting-started/introduction.html
[8] Redis Python Client: https://github.com/redis/redis-py
[9] Model Context Protocol Official Site: https://modelcontextprotocol.io/
[10] Anthropic's Model Context Protocol Announcement: https://www.anthropic.com/news/model-context-protocol
[11] Python AST Documentation: https://docs.python.org/3/library/ast.html
[12] Green Tree Snakes - Python AST Guide: https://greentreesnakes.readthedocs.io/
[13] Python Markdown Parsing Discussion: https://stackoverflow.com/questions/40945364/parsing-elements-from-a-markdown-file-in-python-3
[14] KuzuDB Python API: https://docs.kuzudb.com/client-apis/python/
[15] KuzuDB API Documentation: https://kuzudb.com/api-docs/python/kuzu.html
[16] Python Batch Processing: https://stackoverflow.com/questions/27003609/python-batch-processing-of-multiple-existing-scripts
[17] DSPy Programming Framework: https://github.com/stanfordnlp/dspy
[18] DSPy Hacker News Discussion: https://news.ycombinator.com/item?id=42343692
[19] AWS Guardrails for Generative AI: https://aws.amazon.com/blogs/machine-learning/build-safe-and-responsible-generative-ai-applications-with-guardrails/
[20] Safeguarding LLMs with Guardrails: https://medium.com/data-science/safeguarding-llms-with-guardrails-4f5d9f57cff2
[21] Microsoft Agent Factory Design Patterns: https://azure.microsoft.com/en-us/blog/agent-factory-the-new-era-of-agentic-ai-common-use-cases-and-design-patterns/
[22] AI Agent Orchestration Patterns: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
[23] Redis Connection Pooling: https://redis.io/docs/latest/develop/clients/pools-and-muxing/
[24] Effective Redis with Python and Connection Pool: https://fahadahammed.com/effective-use-of-redis-with-python-and-connection-pool/
[25] IBM AI Agent Orchestration: https://www.ibm.com/think/topics/ai-agent-orchestration
[26] Event-Driven Multi-Agent Systems: https://www.confluent.io/blog/event-driven-multi-agent-systems/
[27] Celery Tasks Documentation: https://docs.celeryq.dev/en/stable/userguide/tasks.html
[28] Celery Task Retry Guide: https://www.ines-panker.com/2020/10/29/retry-celery-tasks.html
[29] Celery Workers Guide: https://docs.celeryq.dev/en/stable/userguide/workers.html
[30] Celery Worker Pool: https://celery.school/the-worker-and-the-pool
[31] LangGraph & DSPy Multi-Agent Workflows: https://medium.com/@akankshasinha247/langgraph-dspy-orchestrating-multi-agent-ai-workflows-declarative-prompting-93b2bd06e995
[32] Zero to One: Learning Agentic Patterns: https://www.philschmid.de/agentic-pattern