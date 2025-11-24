# RAG Internal Knowledge Ingestion

Guide for ingesting and managing the internal RAG knowledge base (masterRAG.md).

## Overview

The RAG (Retrieval Augmented Generation) internal knowledge ingestion system processes the `masterRAG.md` file, which contains operational rules, guidelines, and templates for the AI Learning Coach system.

## Process

The ingestion pipeline:

1. **Loads** `docs/masterRAG.md`
2. **Chunks** the document into manageable pieces (300-1500 characters)
3. **Generates** embeddings using Google Generative AI (Gemini)
4. **Stores** chunks and embeddings in `internal_rag_embeddings` table

## Prerequisites

- ✅ Phase 3 completed (database setup)
- ✅ `GOOGLE_API_KEY` configured in `.env`
- ✅ `docs/masterRAG.md` file exists

## Running RAG Ingestion

### Method 1: CLI Script (Recommended)

```bash
# Full ingestion (clears existing and re-ingests)
python scripts/ingest_rag.py

# Show statistics only
python scripts/ingest_rag.py --stats

# Keep existing embeddings (add new ones)
python scripts/ingest_rag.py --keep
```

### Method 2: Python Code

```python
import asyncio
from app.rag.rag_ingestion_service import ingest_master_rag

async def run():
    results = await ingest_master_rag(
        master_rag_path="docs/masterRAG.md",
        clear_existing=True,
        min_chunk_size=300,
        max_chunk_size=1500,
        overlap=100
    )
    print(f"Success: {results['success']}")
    print(f"Chunks stored: {results['embeddings_stored']}")

asyncio.run(run())
```

### Method 3: API Endpoint

Check RAG status via API:

```bash
curl http://localhost:8000/rag/status
```

Response:
```json
{
  "status": "ok",
  "ready": true,
  "total_chunks": 15,
  "statistics": {
    "total_chunks": 15,
    "sections": [
      {"section_name": "Summarization Guidelines", "chunk_count": 2},
      {"section_name": "Why This Matters Rules", "chunk_count": 1}
    ],
    "average_chunk_size": 850,
    "embedding_dimension": 768
  }
}
```

## Chunking Strategy

The system uses intelligent chunking:

- **Section-aware**: Respects markdown headers
- **Min size**: 300 characters (configurable)
- **Max size**: 1500 characters (configurable)
- **Overlap**: 100 characters between chunks (for context continuity)
- **Boundary-respecting**: Splits on paragraph boundaries

### Example

```
Original document:
├── Section 1: Purpose (500 chars)
├── Section 2: Summarization (2000 chars)
│   ├── Chunk 2.1 (1400 chars)
│   └── Chunk 2.2 (700 chars, with 100 char overlap)
└── Section 3: Scoring (800 chars)

Result: 4 chunks stored with embeddings
```

## Embedding Generation

Uses **Google Generative AI (Gemini)**:

- Model: `models/embedding-001`
- Dimension: **768**
- Task type: `retrieval_document`
- Batch processing: 50 chunks at a time
- Rate limiting: 0.5s delay between batches

## Database Schema

Chunks are stored in `internal_rag_embeddings`:

```sql
CREATE TABLE internal_rag_embeddings (
    chunk_id UUID PRIMARY KEY,
    section_name VARCHAR(255),
    chunk_text TEXT NOT NULL,
    embedding_vector vector(768),
    created_at TIMESTAMP
);
```

## Expected Output

```
============================================================
RAG Ingestion Pipeline Starting...
============================================================

✓ Found masterRAG.md at: /path/to/docs/masterRAG.md

Step 1: Clearing existing RAG embeddings...
✓ Cleared 0 existing embeddings

Step 2: Loading and chunking masterRAG.md...
Found 14 sections in document
  Section 'Purpose of This Document': 1 chunks
  Section 'System Identity': 1 chunks
  Section 'Summarization Guidelines': 1 chunks
  Section 'Why This Matters Rules': 1 chunks
  Section 'Relevance Scoring Framework': 2 chunks
  Section 'Digest Structure Template': 1 chunks
  Section 'User Intent Interpretation': 1 chunks
  Section 'Topic Classification': 2 chunks
  Section 'Content Cleaning Rules': 1 chunks
  Section 'Retrieval Process': 1 chunks
  Section 'Feedback Reinforcement': 1 chunks
  Section 'Forbidden Behaviors': 1 chunks
  Section 'End-to-End Flow Overview': 1 chunks
  Section 'Purpose Reminder': 1 chunks
Total chunks created: 15
✓ Created 15 chunks

Step 3: Generating embeddings...
Processing batch 1/1 (15 texts)...
✓ Generated 15 embeddings

Step 4: Storing chunks and embeddings in database...
  Stored 5/15 chunks...
  Stored 10/15 chunks...
  Stored 15/15 chunks...
✓ Stored 15 chunks with embeddings

============================================================
RAG Ingestion: SUCCESS ✓
  - Chunks processed: 15
  - Embeddings generated: 15
  - Embeddings stored: 15
============================================================
```

## Verification

### Check via CLI

```bash
python scripts/ingest_rag.py --stats
```

Output:
```
📊 RAG Knowledge Base Statistics

Total Chunks: 15
Average Chunk Size: 850 characters
Embedding Dimension: 768

Chunks by Section:
  • Relevance Scoring Framework: 2 chunks
  • Topic Classification: 2 chunks
  • Summarization Guidelines: 1 chunks
  • System Identity: 1 chunks
  ...
```

### Check via API

```bash
curl http://localhost:8000/rag/status | jq
```

### Check via Database

```sql
-- Count total chunks
SELECT COUNT(*) FROM internal_rag_embeddings;

-- Count by section
SELECT section_name, COUNT(*) as chunk_count
FROM internal_rag_embeddings
GROUP BY section_name
ORDER BY chunk_count DESC;

-- Sample chunks
SELECT chunk_id, section_name, LEFT(chunk_text, 100)
FROM internal_rag_embeddings
LIMIT 5;
```

## Troubleshooting

### Error: "GOOGLE_API_KEY not found"

**Solution**: Add your Google AI API key to `backend/.env`:
```bash
GOOGLE_API_KEY=your-actual-api-key-here
```

Get your key from: https://makersuite.google.com/app/apikey

### Error: "masterRAG.md not found"

**Solution**: Ensure `docs/masterRAG.md` exists:
```bash
ls -la docs/masterRAG.md
```

### Error: "Failed to generate embedding"

**Possible causes**:
1. Invalid or expired `GOOGLE_API_KEY`
2. Rate limit exceeded
3. Network issues

**Solutions**:
- Verify API key is valid
- Wait a few minutes and retry
- Check network connectivity

### Error: "Database connection failed"

**Solution**: Ensure database is set up (Phase 3):
```bash
python scripts/setup_database.py validate
```

## Re-ingestion

To update the RAG knowledge base after modifying `masterRAG.md`:

```bash
# Clear old embeddings and regenerate
python scripts/ingest_rag.py

# Or keep old ones and add new (not recommended)
python scripts/ingest_rag.py --keep
```

## Usage in Digest Generation

Once ingested, these embeddings are used in Phase 7 for:

1. **Context retrieval**: Find relevant rules for digest generation
2. **Tone guidance**: Apply correct writing style
3. **Structure templates**: Use proper formatting
4. **Scoring rules**: Apply relevance calculations

Example retrieval query:
```python
from app.rag.internal_retrieval import retrieve_internal_rules

rules = await retrieve_internal_rules(
    query="How to write why this matters?",
    top_k=3
)
# Returns top 3 most relevant chunks from masterRAG.md
```

## Performance

- **Ingestion time**: ~30-60 seconds (for ~15 chunks)
- **Storage**: ~150KB per 1000 chunks (text + metadata)
- **Embeddings**: ~3KB per embedding (768 floats)
- **Retrieval**: <50ms for top-k search with pgvector

## Next Steps

After successful RAG ingestion:

1. ✅ RAG knowledge base is ready
2. ➡️ Proceed to Phase 5: Backend domain APIs
3. Later use in Phase 7: RAG retrieval and digest generation
