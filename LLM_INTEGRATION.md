# LLM Integration with LangGraph Document Processing Pipeline

## Overview

This project combines **LangGraph** for graph-based workflows with **LLM integration** (Claude, GPT-4, etc.) to create an intelligent document processing and analysis pipeline.

## Features

- **LangGraph Workflow**: Multi-step document processing pipeline with clear node definitions
- **Semantic Search**: FAISS-powered vector search for finding relevant document chunks
- **LLM Summaries**: AI-generated summaries of search results using Claude or OpenAI
- **Flexible LLM Configuration**: Support for multiple LLM providers via environment variables
- **Index Persistence**: Save and load FAISS indices for reuse
- **Multiple Document Formats**: Support for PDF, CSV, TXT, DOCX, HTML

## Setup

### 1. Environment Configuration

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your LLM provider credentials:

**Option A: Anthropic Claude (Recommended)**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**Option B: OpenAI GPT-4**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install python-dotenv langchain-anthropic langchain-openai
```

## Usage

### Interactive Mode

```bash
python main_langgraph.py
```

This launches an interactive CLI where you can:
1. Load a document (PDF, CSV, TXT, DOCX, HTML)
2. Create semantic chunks and embeddings
3. Search for relevant information
4. Generate AI summaries of results
5. Save/load indices for reuse

### Programmatic Usage

```python
from main_langgraph import DocumentPipelineGraph, display_results_with_summary

# Initialize pipeline
pipeline = DocumentPipelineGraph()

# Process a document
pipeline.process_document("financial_report_pages.pdf")

# Search with AI summary
results, summary = pipeline.search_with_summary("revenue and expenses", top_k=3)
display_results_with_summary(results, summary)
```

### Demo Script

```bash
python demo_llm_integration.py
```

## Pipeline Architecture

### LangGraph Workflow Nodes

1. **validate** - Validates file path and extension
2. **load** - Loads document content (supports multiple formats)
3. **chunk** - Splits text into semantic chunks with metadata
4. **index** - Creates FAISS embeddings and index
5. **search** - Performs semantic search on the index
6. **summarize** - Generates LLM-powered summaries (NEW)

### State Management

Pipeline state includes:
- Document metadata and chunks
- Search results with similarity scores
- LLM-generated summaries
- Error tracking

## Configuration

### Environment Variables

```env
# LLM Provider (anthropic, openai)
LLM_PROVIDER=anthropic

# API Keys (required for chosen provider)
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key

# Model Selection
ANTHROPIC_MODEL=claude-3-sonnet-20240229
OPENAI_MODEL=gpt-4

# LLM Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024

# Document Processing
CHUNK_SIZE=500
CHUNK_OVERLAP=50
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Storage
INDEX_PERSISTENCE_DIR=faiss_indices

# Logging
LOG_LEVEL=INFO
```

## API Methods

### DocumentPipelineGraph Class

#### Core Methods

- `process_document(file_path)` - Process a document file
- `search(query, top_k=5)` - Search without summary
- `search_with_summary(query, top_k=5)` - Search with LLM summary (NEW)
- `save_index(index_name)` - Persist FAISS index
- `load_index(index_name)` - Load saved index
- `list_saved_indices()` - List available indices

#### LLM Integration

The pipeline automatically initializes the configured LLM from environment variables:

```python
pipeline = DocumentPipelineGraph()
print(f"LLM: {pipeline.llm.model_name}")
print(f"Provider: {pipeline.llm.__class__.__name__}")
```

## Examples

### Example 1: Process and Summarize

```python
from main_langgraph import DocumentPipelineGraph, display_results_with_summary

pipeline = DocumentPipelineGraph()
pipeline.process_document("financial_report.pdf")

results, summary = pipeline.search_with_summary(
    "quarterly revenue growth",
    top_k=3
)
display_results_with_summary(results, summary)
```

### Example 2: Batch Processing

```python
documents = ["doc1.pdf", "doc2.csv", "doc3.txt"]

for doc in documents:
    pipeline.process_document(doc)
    pipeline.save_index(doc.split('.')[0] + "_index")

# Later: Load and search
pipeline.load_index("doc1_index")
results = pipeline.search("specific query")
```

## Pre-commit Hooks

The project includes pre-commit hooks for code quality:

```bash
pre-commit run --all-files
```

Checks:
- Code formatting (black)
- Linting (flake8)
- Import sorting (isort)
- YAML validation
- File endings

## Project Structure

```
document_loader/
├── main_langgraph.py          # Main LangGraph pipeline with LLM
├── src/
│   ├── chunking.py            # Text chunking logic
│   ├── loaders.py             # Document format handlers
│   ├── retriever.py           # FAISS and embedding logic
│   ├── config.py              # Configuration management
│   └── utils.py               # Utility functions
├── config/
│   └── config.yaml            # Pipeline configuration
├── faiss_indices/             # Saved FAISS indices
├── .env                       # Environment variables (add your API keys)
├── .env.example               # Example environment file
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Troubleshooting

### LLM Not Responding

1. Check API key in `.env`: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
2. Verify internet connection
3. Check API rate limits

### Import Errors

```bash
pip install langchain-anthropic langchain-openai python-dotenv
```

### FAISS Index Issues

- Clear `faiss_indices/` directory and reprocess documents
- Ensure consistency in embedding model

## Future Enhancements

- [ ] Support for more LLM providers (Cohere, HuggingFace)
- [ ] Streaming responses for large summaries
- [ ] Multi-document cross-referencing
- [ ] Custom prompt templates
- [ ] Result caching for repeated queries
- [ ] FastAPI endpoint for API access
- [ ] Web UI dashboard

## License

MIT

## Support

For issues or questions, please refer to the documentation or create an issue in the repository.
