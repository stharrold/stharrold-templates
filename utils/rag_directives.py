# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""RAG query directives: preset prompt templates for different analysis modes."""

# ---------------------------------------------------------------------------
# CUSTOMIZE: Adapt RAG prompt templates for your domain. This example provides
# email-focused directives (qa, compare, timeline, summarize, connections).
# ---------------------------------------------------------------------------

DIRECTIVES = {
    "qa": {
        "name": "Question & Answer",
        "description": "Free-form Q&A with inline citations (default)",
        "prompt": """You are an assistant for a document knowledge graph. Your job is to answer
questions using ONLY the provided context derived from document data (senders, recipients,
subjects, dates, folders, and extracted entities). If the context doesn't contain enough
information, say so explicitly.

Include inline citations referencing the source numbers [1], [2], etc.

**Question:** {{QUERY}}

**Context:**
{{CONTEXT}}

**Answer:**""",
    },
    "compare": {
        "name": "Compare & Contrast",
        "description": "Compare entities, people, projects, or topics mentioned in documents",
        "prompt": """You are an analyst comparing entities in a document knowledge graph.
Using ONLY the provided context, identify similarities and differences between the
subjects mentioned in the query. Structure your response as:

1. **Similarities** - What they have in common
2. **Differences** - How they differ
3. **Connections** - Any relationships between them

Include inline citations [1], [2], etc.

**Query:** {{QUERY}}

**Context:**
{{CONTEXT}}

**Analysis:**""",
    },
    "timeline": {
        "name": "Timeline Analysis",
        "description": "Arrange information chronologically based on document dates",
        "prompt": """You are a chronological analyst for a document knowledge graph.
Using ONLY the provided context, arrange the relevant information in chronological order.
Pay special attention to dates, sent timestamps, and temporal references.

Format as a timeline with dates/periods and what happened. Include inline citations [1], [2], etc.
If exact dates aren't available, use relative ordering based on context.

**Query:** {{QUERY}}

**Context:**
{{CONTEXT}}

**Timeline:**""",
    },
    "summarize": {
        "name": "Comprehensive Summary",
        "description": "Provide a thorough summary of all information about a topic",
        "prompt": """You are a research analyst summarizing information from a document knowledge graph.
Using ONLY the provided context, provide a comprehensive summary covering:

1. **Overview** - What this is about
2. **Key People** - Who is involved and their roles
3. **Key Facts** - Important details and data points
4. **Status/Outcome** - Current state or resolution if known

Be thorough but concise. Include inline citations [1], [2], etc.

**Topic:** {{QUERY}}

**Context:**
{{CONTEXT}}

**Summary:**""",
    },
    "connections": {
        "name": "Connection Mapping",
        "description": "Identify all connections and relationships between entities",
        "prompt": """You are a network analyst mapping connections in a document knowledge graph.
Using ONLY the provided context, identify all connections and relationships.
For each connection, describe:

- **Who/What** is connected
- **How** they are connected (sent document, mentioned together, same project, etc.)
- **Strength** of the connection (frequent interaction vs. one-time mention)

Include inline citations [1], [2], etc.

**Query:** {{QUERY}}

**Context:**
{{CONTEXT}}

**Connection Map:**""",
    },
}


def get_directive(directive_id):
    """Get a directive by ID, defaulting to 'qa'."""
    return DIRECTIVES.get(directive_id, DIRECTIVES["qa"])


def build_prompt(directive_id, query, context):
    """Build a complete prompt from a directive template."""
    directive = get_directive(directive_id)
    return directive["prompt"].replace("{{QUERY}}", query).replace("{{CONTEXT}}", context)


def list_directives():
    """Return a list of (id, name, description) for all directives."""
    return [(did, d["name"], d["description"]) for did, d in DIRECTIVES.items()]
