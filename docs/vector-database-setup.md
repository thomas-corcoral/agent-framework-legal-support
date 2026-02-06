# Vector Database Setup for Semantic Case Search

This guide explains how to set up and use the semantic case search feature for Swiss Federal Court (BGER) decisions.

## Overview

The `semantic_case_search` tool enables natural language search over Swiss Federal Court decisions using vector embeddings and FAISS similarity search. The system supports:

- **Multilingual queries**: German, French, Italian, and English
- **Efficient search**: Sub-second search over thousands of cases
- **Open-source friendly**: Pre-built indexes hosted on Hugging Face Hub

## Quick Start (For Users)

### Installation

```bash
# Install with vector search dependencies
pip install legal-support[vector]
```

### Usage

```python
from legal_support.tools import semantic_case_search, LegalArea

# Search for similar cases
result = semantic_case_search(
    query="Kündigung Mietvertrag wegen Zahlungsverzug",
    legal_area=LegalArea.CIVIL,
    limit=5
)

for case in result.cases:
    print(f"{case.case_id}: {case.similarity_score:.2%}")
    print(f"  {case.title}")
```

### CLI Search

```bash
# Search from command line
legal-support search "Arbeitsvertrag fristlose Kündigung" --legal-area civil

# Download pre-built index
legal-support download-index
```

## Building Your Own Index (For Contributors)

If you want to build the vector index from BGER data, follow these steps:

### 1. Prepare Your Data

Create a JSON file with BGER cases in this format:

```json
{
  "cases": [
    {
      "case_id": "BGE 147 III 451",
      "title": "Mietvertrag; Zahlungsverzug des Mieters",
      "legal_area": "civil",
      "chamber": "I_civil",
      "decision_date": "2021-09-15",
      "language": "de",
      "regeste": "Art. 257d OR. Kündigung wegen Zahlungsverzugs...",
      "keywords": ["Mietrecht", "Zahlungsverzug", "Kündigung"],
      "cited_laws": ["OR 257d", "OR 266a"],
      "bger_url": "https://www.bger.ch/ext/eurospider/live/de/php/clir/http/index.php?lang=de&type=highlight_simple_query&page=1&from_date=&to_date=&from_year=2021&to_year=2021&sort=relevance&insertion_date=&from_date_push=&top_subcollection_clir=bge&query_words=147+III+451",
      "full_text": "Optional full decision text..."
    }
  ]
}
```

**Supported formats:**
- JSON (`.json`) - Array of cases or object with `cases` array
- JSONL (`.jsonl`) - One case per line
- CSV (`.csv`) - Comma-separated with headers

**Required fields:**
- `case_id` (or `id`, `reference`)

**Recommended fields for good search quality:**
- `title` / `summary`
- `regeste` (case headnote)
- `keywords`
- `legal_area`

### 2. Build the Index

```bash
# Build index from data file
legal-support build-index --input data/bger_cases.json

# Specify custom output directory
legal-support build-index --input data/bger_cases.json --output ./my_index

# Use a different embedding model
legal-support build-index --input data/bger_cases.json \
    --model sentence-transformers/distiluse-base-multilingual-cased-v2
```

### 3. Upload to Hugging Face Hub (Open Source Distribution)

To share your index with others:

```bash
# Login to Hugging Face
huggingface-cli login

# Build and upload
legal-support build-index --input data/bger_cases.json \
    --upload \
    --repo-id your-username/bger-semantic-index \
    --index-version 1.0.0
```

This creates a dataset repository on Hugging Face Hub with:
- `bger.index` - FAISS index file
- `bger_metadata.json` - Case metadata
- `version.json` - Build information
- `README.md` - Dataset documentation

## Data Sources for BGER Cases

### Official Sources

1. **BGer Website**: https://www.bger.ch
   - Official federal court decisions
   - Available in DE, FR, IT
   - Free access

2. **Entscheidsuche.ch**: https://entscheidsuche.ch
   - Aggregated Swiss court decisions
   - Structured data available

3. **Swisslex**: https://www.swisslex.ch (subscription required)
   - Professional legal database
   - Enhanced metadata

### Open Data Initiatives

1. **Swiss Open Legal Data**:
   - Check for existing datasets on Hugging Face Hub
   - Look for Swiss legal NLP projects on GitHub

2. **Academic Sources**:
   - University of Zurich Legal Tech projects
   - ETH Zurich NLP resources

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Query                               │
│            "Mietvertrag Kündigung Zahlungsverzug"           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Sentence Transformer Model                      │
│    (paraphrase-multilingual-MiniLM-L12-v2)                  │
│         Converts query to 384-dim embedding                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FAISS Index                               │
│          Inner Product Search (IndexFlatIP)                  │
│         Returns top-k most similar vectors                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Metadata Lookup                              │
│      Maps vector indices to case metadata                    │
│           Applies filters (legal_area, date)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Search Results                               │
│    CaseSearchResult with ranked CaseDecision objects         │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Options

### Embedding Models

The default model (`paraphrase-multilingual-MiniLM-L12-v2`) is chosen for:
- Good multilingual support (DE, FR, IT, EN)
- Reasonable size (~400MB)
- Fast inference

Alternative models:
```python
# Larger, more accurate
"sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Smaller, faster
"sentence-transformers/all-MiniLM-L6-v2"

# Legal domain specific (if available)
"your-org/legal-bert-multilingual"
```

### Index Types

Currently using `IndexFlatIP` (exact inner product search). For larger datasets (>100k cases), consider:

```python
# Approximate search with IVF
index = faiss.IndexIVFFlat(quantizer, d, nlist)

# With product quantization for memory efficiency
index = faiss.IndexIVFPQ(quantizer, d, nlist, m, nbits)
```

## Troubleshooting

### Import Errors

```
ImportError: faiss-cpu is required for semantic search
```

**Solution**: Install vector dependencies:
```bash
pip install legal-support[vector]
```

### Index Not Found

```
RuntimeError: Failed to download index from Hugging Face Hub
```

**Solutions**:
1. Check internet connection
2. Build index locally: `legal-support build-index -i your_data.json`
3. Check if HF repository exists

### Memory Issues

For large indexes, reduce memory usage:
```python
# Use memory-mapped index
index = faiss.read_index("bger.index", faiss.IO_FLAG_MMAP)
```

## Contributing

### Improving the Index

1. **Add more cases**: More data = better coverage
2. **Improve metadata**: Better regestes improve search quality
3. **Fine-tune embeddings**: Domain-specific fine-tuning

### Reporting Issues

- Report search quality issues with example queries
- Include expected vs. actual results
- Note the index version (`result.index_version`)

## License

- **Code**: Apache 2.0
- **BGER Decisions**: Public domain (Swiss federal court decisions)
- **Pre-built Index**: CC-BY-SA 4.0

## References

- [FAISS Documentation](https://faiss.ai/)
- [Sentence Transformers](https://www.sbert.net/)
- [Hugging Face Datasets](https://huggingface.co/docs/datasets/)
- [BGer Website](https://www.bger.ch/)
