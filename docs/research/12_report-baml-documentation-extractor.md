# Using BAML for Documentation Extraction with Graph-Structured Outputs

BAML (Boundary AI Markup Language) provides a powerful schema-first approach to extracting structured documentation from any file type or data source[^1][^2]. This DSL treats prompts as **functions with typed inputs and outputs**, reducing token usage by 60% compared to JSON schemas[^3] while ensuring reliable, structured extraction that forms fully-connected documentation graphs.

## Core BAML Architecture for Documentation Extraction

BAML's fundamental innovation lies in its type-safe approach to LLM outputs[^4]. Rather than wrestling with unpredictable text generation, BAML enforces structured schemas through its **Schema-Aligned Parsing (SAP)** algorithm[^5], which automatically corrects malformed outputs and ensures compliance with defined constraints.

### Setting up the BAML Environment

Installation requires minimal setup[^6]. First, install the BAML VSCode extension for syntax highlighting and interactive testing[^7]. Then add BAML to your project using `pip install baml-py` for Python or the equivalent for other languages[^8]. Initialize with `baml-cli init` to create the standard directory structure:

```
./project/
├── baml_src/
│   ├── clients.baml      # LLM configurations
│   ├── generators.baml   # Code generation settings
│   └── extraction.baml   # Your extraction functions
├── baml_client/          # Auto-generated typed clients
```

Configure your LLM client with appropriate retry policies and model selection:

```baml
client<llm> DocumentationExtractor {
    provider openai
    retry_policy ExponentialBackoff
    options {
        model gpt-4o
        api_key env.OPENAI_API_KEY
        temperature 0  // Deterministic extraction
        max_tokens 4000
    }
}

retry_policy ExponentialBackoff {
    max_retries 3
    strategy {
        type exponential_backoff
        delay_ms 500
        multiplier 2
    }
}
```

## Defining the Output Schema for Graph-Structured Documentation

The key to meeting specific requirements—unique primary keys, cross-references, and fully-connected graphs—lies in careful schema design[^9]. BAML's type system provides the necessary primitives and validation capabilities[^10].

### The Documentation Node Structure

Create a class that models the tuple structure while enforcing uniqueness and cross-reference constraints[^11]:

```baml
class DocumentationNode {
    primary_key string @description("Unique identifier for this documentation element")
                      @assert(this | length > 0, "key_required")

    key_description string @description("Detailed description that references this key and others")
                          @assert(this | length >= 20, "description_too_short")
                          @assert(this | contains(primary_key), "must_reference_own_key")

    referenced_keys string[] @description("Other primary_keys referenced in the description")
                            @assert(this | length > 0, "must_reference_others")

    node_type string @description("Type: module, class, function, variable, concept")

    source_location SourceInfo? @description("Where this was extracted from")
}

class SourceInfo {
    file_path string
    line_number int?
    url string?
}
```

### The Complete Graph Structure

Build a comprehensive schema that ensures all nodes form a connected graph[^12]:

```baml
class DocumentationGraph {
    repository_name string @description("Repository/Project name as the graph head")

    nodes DocumentationNode[] @assert(this | length > 0, "nodes_required")

    edges GraphEdge[] @description("Explicit relationships between nodes")

    metadata ExtractionMetadata

    // Ensure uniqueness of primary keys
    @@assert(nodes | map(attribute="primary_key") | unique | length == (nodes | length),
             "duplicate_primary_keys")

    // Ensure uniqueness of descriptions
    @@assert(nodes | map(attribute="key_description") | unique | length == (nodes | length),
             "duplicate_descriptions")

    // Validate that all referenced keys exist
    @@check(all_references_valid, "Some referenced keys don't exist in the graph")
}

class GraphEdge {
    from_key string @description("Source node primary_key")
    to_key string @description("Target node primary_key")
    relationship_type string @description("imports, extends, implements, calls, references")
    context string? @description("Additional context about the relationship")
}

class ExtractionMetadata {
    extraction_timestamp string
    total_nodes int
    total_edges int
    files_processed int
    extraction_confidence float @assert(this >= 0.0 and this <= 1.0, "invalid_confidence")
}
```

## Generic BAML Function for Multi-Format File Extraction

The extraction function handles any file format through content-aware parsing[^13]:

```baml
function ExtractDocumentationGraph(
    source_identifier: string,  // URL, file path, or project name
    file_contents: FileContent[],
    extraction_mode: string  // "code", "markdown", "mixed", "structured", "unstructured"
) -> DocumentationGraph {
    client DocumentationExtractor

    prompt #"
    You are an expert at extracting structured documentation from various file types.

    CRITICAL REQUIREMENTS:
    1. Every primary_key must be UNIQUE across all nodes
    2. Every key_description must be UNIQUE across all nodes
    3. Every primary_key must appear in its own key_description
    4. Every primary_key must be referenced in at least one OTHER key_description
    5. Every key_description must reference at least one other primary_key
    6. All descriptions must be causal, explaining relationships and purposes
    7. The project/repository name serves as the root/head of the graph

    FILE TYPE HANDLING:
    - Code files (.py, .js, .java, etc.): Extract classes, functions, modules
    - Markdown/Docs (.md, .rst, .txt): Extract sections, concepts, references
    - Config files (.json, .yaml, .toml): Extract settings, dependencies
    - Data files (.csv, .parquet): Extract schema, relationships
    - Binary docs (.pdf, .docx): Extract from provided text representation

    EXTRACTION MODE: {{ extraction_mode }}

    SOURCE: {{ source_identifier }}

    Files to Process:
    {% for file in file_contents %}
    ---
    File: {{ file.path }}
    Type: {{ file.file_type }}
    Encoding: {{ file.encoding }}
    Size: {{ file.size_bytes }} bytes
    Content:
    {{ file.content }}
    {% endfor %}

    {{ ctx.output_format }}
    "#
}

class FileContent {
    path string
    file_type string  // Extension or MIME type
    encoding string   // utf-8, base64, etc.
    size_bytes int
    content string    // Actual content or extracted text
    metadata map<string, string>?  // Additional file-specific metadata
}
```

## Implementing Multi-Format Extraction with Constraint Validation

The extraction process leverages BAML's **Schema-Aligned Parsing** to handle various file formats[^14][^15]:

### Universal File Reader Implementation

```python
from baml_client import b
import aiohttp
import mimetypes
import base64
from pathlib import Path
import PyPDF2
import docx
import pandas as pd
import json
import yaml
import toml

class UniversalFileExtractor:
    """Extract content from any file type for BAML processing"""

    async def extract_from_file(self, file_path: str) -> dict:
        """Extract content from any local or remote file"""

        if file_path.startswith(('http://', 'https://')):
            return await self._extract_from_url(file_path)
        else:
            return await self._extract_from_local(Path(file_path))

    async def _extract_from_url(self, url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content_type = response.headers.get('content-type', '')
                content = await response.read()

                return self._process_content(
                    content=content,
                    file_type=content_type,
                    path=url
                )

    async def _extract_from_local(self, path: Path) -> dict:
        mime_type, _ = mimetypes.guess_type(str(path))

        # Read file based on type
        if path.suffix in ['.pdf']:
            text = self._extract_pdf(path)
        elif path.suffix in ['.docx']:
            text = self._extract_docx(path)
        elif path.suffix in ['.xlsx', '.xls']:
            text = self._extract_excel(path)
        elif path.suffix in ['.csv']:
            text = self._extract_csv(path)
        elif path.suffix in ['.json']:
            text = self._extract_json(path)
        elif path.suffix in ['.yaml', '.yml']:
            text = self._extract_yaml(path)
        elif path.suffix in ['.toml']:
            text = self._extract_toml(path)
        elif path.suffix in ['.parquet']:
            text = self._extract_parquet(path)
        elif path.suffix in ['.png', '.jpg', '.jpeg', '.gif']:
            text = self._extract_image_metadata(path)
        else:
            # Try to read as text
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Read as binary and encode
                text = base64.b64encode(path.read_bytes()).decode('utf-8')

        return {
            'path': str(path),
            'file_type': path.suffix,
            'encoding': 'utf-8',
            'size_bytes': path.stat().st_size,
            'content': text
        }

    def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF files"""
        text = []
        with open(path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text.append(f"[Page {page_num + 1}]\n{page.extract_text()}")
        return '\n'.join(text)

    def _extract_docx(self, path: Path) -> str:
        """Extract text from Word documents"""
        doc = docx.Document(str(path))
        paragraphs = [para.text for para in doc.paragraphs]
        return '\n'.join(paragraphs)

    def _extract_excel(self, path: Path) -> str:
        """Extract data from Excel files"""
        xls = pd.ExcelFile(path)
        sheets_text = []
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            sheets_text.append(f"[Sheet: {sheet_name}]\n{df.to_string()}")
        return '\n'.join(sheets_text)

    def _extract_csv(self, path: Path) -> str:
        """Extract data from CSV files"""
        df = pd.read_csv(path)
        return f"[CSV Schema]\nColumns: {', '.join(df.columns)}\nRows: {len(df)}\n\n{df.head(20).to_string()}"

    def _extract_json(self, path: Path) -> str:
        """Extract and format JSON content"""
        with open(path) as f:
            data = json.load(f)
        return json.dumps(data, indent=2)

    def _extract_yaml(self, path: Path) -> str:
        """Extract and format YAML content"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return yaml.dump(data, default_flow_style=False)

    def _extract_toml(self, path: Path) -> str:
        """Extract and format TOML content"""
        with open(path) as f:
            data = toml.load(f)
        return toml.dumps(data)

    def _extract_parquet(self, path: Path) -> str:
        """Extract schema and sample from Parquet files"""
        df = pd.read_parquet(path)
        return f"[Parquet Schema]\nColumns: {df.dtypes.to_string()}\nRows: {len(df)}\n\n{df.head(10).to_string()}"

    def _extract_image_metadata(self, path: Path) -> str:
        """Extract metadata from image files"""
        from PIL import Image
        img = Image.open(path)
        return f"[Image Metadata]\nFormat: {img.format}\nSize: {img.size}\nMode: {img.mode}"
```

### Extraction Orchestration

```python
async def extract_documentation_from_any_source(
    source_path: str,
    file_patterns: list[str] = None,
    extraction_mode: str = "mixed"
):
    """
    Extract documentation from any source type

    Args:
        source_path: File path, directory, URL, or repository
        file_patterns: List of glob patterns to match files
        extraction_mode: "code", "markdown", "mixed", "structured", "unstructured"
    """

    extractor = UniversalFileExtractor()
    file_contents = []

    # Determine source type
    if source_path.startswith(('http://', 'https://')):
        # Handle URLs
        if 'github.com' in source_path:
            file_contents = await extract_github_repo(source_path)
        else:
            content = await extractor.extract_from_file(source_path)
            file_contents.append(content)

    elif Path(source_path).is_dir():
        # Handle directories
        directory = Path(source_path)
        patterns = file_patterns or ['**/*']

        for pattern in patterns:
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    try:
                        content = await extractor.extract_from_file(str(file_path))
                        file_contents.append(content)
                    except Exception as e:
                        print(f"Skipping {file_path}: {e}")

    else:
        # Handle single file
        content = await extractor.extract_from_file(source_path)
        file_contents.append(content)

    # Execute BAML extraction
    result = b.ExtractDocumentationGraph(
        source_identifier=source_path,
        file_contents=file_contents,
        extraction_mode=extraction_mode
    )

    return result
```

### Format-Specific Extraction Strategies

BAML functions can be specialized for different file types[^16]:

```baml
function ExtractFromSpreadsheet(
    spreadsheet_content: string,
    sheet_names: string[]
) -> DocumentationNode[] {
    client DocumentationExtractor

    prompt #"
    Extract documentation from spreadsheet data.

    Focus on:
    1. Column names and their purposes (as primary_keys)
    2. Relationships between sheets (foreign keys, lookups)
    3. Calculated fields and their dependencies
    4. Data validation rules and constraints
    5. Named ranges and their uses

    Create nodes for:
    - Each significant column or field
    - Each sheet as a module
    - Formulas as functions
    - Validation rules as constraints

    Spreadsheet Content:
    {{ spreadsheet_content }}

    Sheet Names: {{ sheet_names | join(", ") }}

    {{ ctx.output_format }}
    "#
}

function ExtractFromNotebook(
    notebook_cells: NotebookCell[]
) -> DocumentationGraph {
    client DocumentationExtractor

    prompt #"
    Extract documentation from Jupyter/Colab notebook.

    Focus on:
    1. Code cells defining functions and classes
    2. Markdown cells explaining concepts
    3. Variable definitions and data transformations
    4. Import statements and dependencies
    5. Output visualizations and their inputs

    Cell Types:
    {% for cell in notebook_cells %}
    [Cell {{ cell.index }}] Type: {{ cell.cell_type }}
    {{ cell.content }}
    {% endfor %}

    {{ ctx.output_format }}
    "#
}

class NotebookCell {
    index int
    cell_type string  // "code", "markdown", "output"
    content string
    outputs string[]?
}
```

## Testing and Validation Strategies

BAML's built-in testing framework enables comprehensive validation across file types[^17][^18]:

```baml
test ExtractFromMultipleFormats {
    functions [ExtractDocumentationGraph]
    args {
        source_identifier "test_project"
        file_contents [
            {
                path: "config.yaml"
                file_type: "yaml"
                encoding: "utf-8"
                size_bytes: 256
                content: #"
                database:
                  host: localhost
                  port: 5432
                auth:
                  provider: oauth2
                  token_expiry: 3600
                "#
            },
            {
                path: "main.py"
                file_type: "python"
                encoding: "utf-8"
                size_bytes: 512
                content: #"
                from auth import TokenValidator
                class APIServer:
                    def __init__(self, config):
                        self.validator = TokenValidator(config['auth'])
                "#
            }
        ]
        extraction_mode: "mixed"
    }

    @@assert(this.nodes | length >= 4, "should_extract_from_both_files")
    @@check(cross_file_references, "should_link_config_to_code")
}
```

### Interactive Testing with VSCode Playground

The BAML VSCode extension provides testing capabilities[^19]:
- **Test extraction functions** with various file formats
- **Visualize graph structures** from different sources
- **Debug constraint violations** across file types
- **Optimize prompts** for specific formats

## Best Practices for Production Deployment

### Performance Optimization

BAML's type definitions reduce token usage significantly[^20], with additional optimizations:

1. **Format-aware batching**: Group similar file types together
2. **Progressive extraction**: Start with structure, then details
3. **Content summarization**: Pre-process large files to key sections
4. **Parallel processing**: Extract from multiple files concurrently

### Error Handling for Various Formats

```python
class RobustExtractor:
    def __init__(self):
        self.fallback_strategies = {
            'pdf': [self._ocr_fallback, self._metadata_only],
            'binary': [self._hex_dump, self._file_info_only],
            'corrupted': [self._partial_extraction, self._skip_with_note]
        }

    async def extract_with_fallback(self, file_path: str):
        try:
            return await self.primary_extraction(file_path)
        except Exception as e:
            file_type = self._detect_type(file_path)
            for fallback in self.fallback_strategies.get(file_type, []):
                try:
                    return await fallback(file_path)
                except:
                    continue
            return self._create_error_node(file_path, str(e))
```

### Integration Patterns

BAML generates typed clients for seamless integration[^21]:

```python
# FastAPI endpoint for universal extraction
from fastapi import FastAPI, UploadFile, File
from typing import List

app = FastAPI()

@app.post("/extract")
async def extract_documentation(
    files: List[UploadFile] = File(...),
    extraction_mode: str = "mixed"
):
    extractor = UniversalFileExtractor()
    file_contents = []

    for file in files:
        content = await file.read()
        processed = extractor._process_content(
            content=content,
            file_type=file.content_type,
            path=file.filename
        )
        file_contents.append(processed)

    graph = b.ExtractDocumentationGraph(
        source_identifier=f"upload_{datetime.now().isoformat()}",
        file_contents=file_contents,
        extraction_mode=extraction_mode
    )

    # Validate graph connectivity
    if not validate_graph_connectivity(graph):
        return {"error": "Graph not fully connected"}

    return {
        "project": graph.repository_name,
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "formats_processed": list(set(f['file_type'] for f in file_contents)),
        "data": graph.model_dump()
    }
```

## Conclusion

BAML transforms documentation extraction from any file type into a **reliable, type-safe data extraction pipeline**[^22]. Its schema-first approach, combined with powerful validation constraints and graph modeling capabilities, ensures that extracted documentation forms fully-connected, cross-referenced structures regardless of source format. The framework's **10x faster development cycles**[^23], **98% cost reduction**[^24], and production-ready features make it the optimal choice for building scalable documentation extraction systems that maintain complex relationships across diverse data sources.

---

## References

[^1]: BoundaryML Documentation - Welcome. https://docs.boundaryml.com/home
[^2]: GitHub - BoundaryML/baml: The AI framework that adds the engineering to prompt engineering. https://github.com/BoundaryML/baml
[^3]: Your prompts are using 4x more tokens than you need - BAML Blog. https://boundaryml.com/blog/type-definition-prompting-baml
[^4]: Prompting vs JSON Mode vs Function Calling vs Constrained Generation vs SAP - BAML Blog. https://boundaryml.com/blog/schema-aligned-parsing
[^5]: Schema-Aligned Parsing Algorithm - BoundaryML. https://boundaryml.com/blog/schema-aligned-parsing
[^6]: Python Installation - Boundary Documentation. https://docs.boundaryml.com/guide/installation-language/python
[^7]: Seven Features That Make BAML Ideal for AI Developers - Gradient Flow. https://gradientflow.com/seven-features-that-make-baml-ideal-for-ai-developers/
[^8]: BAML Installation Guide - Boundary Documentation. https://docs.boundaryml.com/guide/installation-language/python
[^9]: Types - Boundary Documentation. https://docs.boundaryml.com/ref/baml/types
[^10]: BAML Type System Reference. https://docs.boundaryml.com/ref/baml/types
[^11]: Class Definitions - Boundary Documentation. https://docs.boundaryml.com/ref/baml/class
[^12]: Why I'm excited about BAML and the future of agentic workflows - The Data Quarry. https://thedataquarry.com/blog/baml-and-future-agentic-workflows/
[^13]: Converting Images to Structured Data with BAML - Medium. https://medium.com/@_jalakoo_/images-to-structured-data-with-baml-19adc3ea9135
[^14]: Get structured output from a Language Model using BAML - Thomas Queste. https://www.tomsquest.com/blog/2024/08/get-structured-output-from-llm-using-baml/
[^15]: Structured Prompt Engineering Made Easy - Gradient Flow. https://gradientflow.com/structured-prompt-engineering-made-easy/
[^16]: Prompting in BAML - Boundary Documentation. https://docs.boundaryml.com/guide/baml-basics/prompting-with-baml
[^17]: Testing functions - Boundary Documentation. https://docs.boundaryml.com/guide/baml-basics/testing-functions
[^18]: Test Reference - Boundary Documentation. https://docs.boundaryml.com/ref/baml/test
[^19]: Checks and Asserts - Boundary Documentation. https://docs.boundaryml.com/guide/baml-advanced/checks-and-asserts
[^20]: Token Optimization in BAML - BoundaryML Blog. https://boundaryml.com/blog/type-definition-prompting-baml
[^21]: BAML is like building blocks for AI engineers - The Data Quarry. https://thedataquarry.com/blog/baml-is-building-blocks-for-ai-engineers/
[^22]: Prompts as Functions: The BAML Revolution in AI Engineering - The Data Exchange. https://thedataexchange.media/baml-revolution-in-ai-engineering/
[^23]: Seven Features That Make BAML Ideal - Gradient Flow. https://gradientflow.com/seven-features-that-make-baml-ideal-for-ai-developers/
[^24]: BoundaryML/baml Repository Statistics - Ecosyste.ms. https://awesome.ecosyste.ms/projects/github.com/BoundaryML/baml
