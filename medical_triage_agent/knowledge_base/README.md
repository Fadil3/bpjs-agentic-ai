# Chroma Vector Database for Knowledge Base

This module implements Chroma vector database for semantic search over PDF knowledge base documents.

## Overview

The knowledge base uses Chroma to vectorize and store:
- **BPJS Criteria PDF** (`Pedoman-BPJS-Kriteria-Gawat-Darurat.pdf`)
- **PPK Kemenkes PDF** (`ppk-kemenkes.pdf`)
- **Bates Guide PDF** (`Bates_Guide_to_Physical_Examination.pdf`)

## Setup

### 1. Initialize Knowledge Base

First, initialize Chroma and ingest all PDFs:

```bash
# From project root
python -m medical_triage_agent.knowledge_base.initialize_chroma
```

To force reload (delete existing and re-ingest):

```bash
python -m medical_triage_agent.knowledge_base.initialize_chroma --force-reload
```

### 2. Verify Setup

The Chroma database will be created in `chroma_db/` directory at project root.

## Usage

### In Python Code

```python
from medical_triage_agent.knowledge_base import (
    query_knowledge_base_tool,
    query_bpjs_criteria_tool,
    query_ppk_kemenkes_tool,
    query_bates_guide_tool
)

# Query all knowledge bases
result = query_knowledge_base_tool.func(
    query="What are the criteria for emergency cases?",
    n_results=5
)

# Query specific knowledge base
bpjs_result = query_bpjs_criteria_tool.func(
    query="kriteria gawat darurat",
    n_results=3
)
```

### In ADK Agents

Add the tools to your agent:

```python
from medical_triage_agent.knowledge_base import query_knowledge_base_tool
from google.adk.agents import Agent

agent = Agent(
    model="gemini-2.5-flash",
    tools=[query_knowledge_base_tool],
    # ... other config
)
```

## Architecture

### Files

- `chroma_setup.py`: Chroma initialization, PDF ingestion, embedding generation
- `chroma_tools.py`: Query tools for agents
- `initialize_chroma.py`: CLI script for initialization

### Collections

- `bpjs_criteria`: BPJS emergency criteria
- `ppk_kemenkes`: Primary health care guidelines
- `bates_guide`: Physical examination guide

### Embeddings

Uses Google's `text-embedding-004` model (768 dimensions) via Vertex AI.

## How It Works

1. **PDF Extraction**: Extracts text from PDFs using `pypdf`
2. **Chunking**: Splits text into ~1000 character chunks with 200 character overlap
3. **Embedding**: Generates embeddings using Google's text-embedding-004
4. **Storage**: Stores chunks and embeddings in Chroma collections
5. **Query**: Semantic search using query embeddings

## Benefits Over Direct PDF Access

- ✅ **Faster**: Only relevant chunks retrieved, not entire PDF
- ✅ **Scalable**: Can handle many PDFs efficiently
- ✅ **Semantic Search**: Finds relevant content even with different wording
- ✅ **Contextual**: Returns most relevant passages for the query

## Storage

- **Location**: `chroma_db/` at project root
- **Size**: ~35-80 MB for all PDFs
- **RAM**: ~10-20 MB for vectors in memory

## Troubleshooting

### Error: "Could not generate embedding"

- Check `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` environment variables
- Verify Vertex AI API is enabled
- Check authentication: `gcloud auth application-default login`

### Error: "PDF not found"

- Ensure PDFs are in correct directories:
  - `medical_triage_agent/sub_agents/reasoning_agent/knowlegde/` (note: typo in "knowlegde")
  - `medical_triage_agent/sub_agents/interview_agent/knowledge/`

### Empty Results

- Run initialization script to ingest PDFs
- Check if collections exist: `chroma_db/` directory should have data
- Verify embeddings were generated successfully

## Migration from Direct PDF Access

The current implementation uses direct PDF access (passing entire PDF to Gemini). To migrate to Chroma:

1. Initialize Chroma (see Setup above)
2. Replace direct PDF access with Chroma queries in agent tools
3. Test and verify results match or improve

Example migration:

**Before (Direct PDF):**
```python
with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()
    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
```

**After (Chroma):**
```python
from medical_triage_agent.knowledge_base import query_knowledge_base_tool
relevant_info = query_knowledge_base_tool.func(query="your question", n_results=5)
```

