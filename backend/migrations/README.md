# Database Migrations

This directory contains SQL migration files for the AI Learning Coach database schema.

## Files

- `001_initial_schema.sql` - Initial database schema with all tables and indexes

## Running Migrations

### Automated Setup (Recommended)

Use the setup script from the project root:

```bash
# Full setup (migrate + validate)
python scripts/setup_database.py full

# Just apply migrations
python scripts/setup_database.py migrate

# Just validate existing schema
python scripts/setup_database.py validate
```

### Manual Setup

If you prefer to run migrations manually:

1. Ensure you have the database password in your `.env` file:
   ```
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.mokavdikepjluienxrle.supabase.co:5432/postgres
   ```

2. Connect to your Supabase database using psql or the Supabase SQL editor

3. Copy the contents of `001_initial_schema.sql` and execute it

## Database Schema

The schema includes:

### Core Tables
- `users` - User profiles and authentication
- `learning_goals` - User learning goals with embeddings
- `sources` - Content sources (RSS, YouTube, Twitter, etc.)
- `content_items` - Ingested and cleaned content
- `content_embeddings` - Vector embeddings for content

### RAG Tables
- `internal_rag_embeddings` - Embeddings from masterRAG.md

### Digest Tables
- `digests` - Weekly digest metadata
- `digest_items` - Individual items in each digest
- `feedback` - User feedback on digest items

### System Tables
- `system_logs` - Application logs and events

## Vector Search (pgvector)

The schema uses the `pgvector` extension for semantic similarity search:

- Embedding dimension: **768** (Gemini embeddings)
- Index type: **IVFFlat** with cosine similarity
- Tables with vectors:
  - `learning_goals.embedding_vector`
  - `content_embeddings.embedding_vector`
  - `internal_rag_embeddings.embedding_vector`

## Indexes

The schema includes optimized indexes for:
- Fast user lookups
- Content retrieval by date
- Vector similarity search
- Foreign key relationships

## Verifying Installation

After running migrations, verify the setup:

```bash
python scripts/setup_database.py validate
```

This will check:
- ✓ pgvector extension is enabled
- ✓ All 10 expected tables exist
- ✓ Proper indexes are created
- ✓ Vector columns are configured correctly

## Troubleshooting

### pgvector not enabled

If you get an error about pgvector not being available:

1. Go to Supabase Dashboard → Database → Extensions
2. Enable the `vector` extension
3. Re-run the migration

### Permission denied

Ensure you're using the correct credentials:
- Use `SUPABASE_SERVICE_ROLE_KEY` for migrations
- Use `DATABASE_URL` with the correct password

### Connection timeout

Check that:
1. Your Supabase project is active
2. Your IP is allowed in the Supabase dashboard
3. The `DATABASE_URL` is correct
