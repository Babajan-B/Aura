# Quick Start Guide - Database Setup & Testing

## Prerequisites
✅ Supabase project created
✅ Database credentials in `backend/.env`

## Step 1: Enable pgvector Extension

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Navigate to: **Database** → **Extensions** (left sidebar)
4. Search for "**vector**"
5. Click **Enable** on the "vector" extension
6. Wait for confirmation (should take a few seconds)

## Step 2: Get Database Password

1. In Supabase Dashboard, go to: **Project Settings** → **Database**
2. Scroll to **Connection String** section
3. Click on **URI** tab
4. Copy the connection string - it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.szgnxjkajfwkhkvuncdu.supabase.co:5432/postgres
   ```
5. Copy YOUR-PASSWORD from this string

## Step 3: Update DATABASE_URL in .env

Update your `backend/.env` file:

```bash
# Replace [YOUR-PASSWORD] with the actual password
DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.szgnxjkajfwkhkvuncdu.supabase.co:5432/postgres
```

**Note**: The project ref has changed to `szgnxjkajfwkhkvuncdu` (based on your updated keys)

## Step 4: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 5: Run Database Migration

```bash
# From project root directory
python scripts/setup_database.py full
```

Expected output:
```
🚀 Running full database setup...

Step 1: Applying migrations...
✅ Migration migrations/001_initial_schema.sql applied successfully

Step 2: Validating database...
==================================================
Database Validation Starting...
==================================================

Step 1: Checking pgvector extension...
✓ pgvector extension is enabled

Step 2: Validating database tables...
Expected tables: 10
Existing tables: 10
✓ All expected tables are present

==================================================
Database Validation: PASSED ✓
==================================================

✅ Full database setup completed successfully!
```

## Step 6: Verify Database Setup

### Method 1: Using CLI Validator
```bash
python scripts/setup_database.py validate
```

### Method 2: Using API
Start the server:
```bash
cd backend
uvicorn app.main:app --reload
```

Then check endpoints:
```bash
# Health check
curl http://localhost:8000/health

# Database status
curl http://localhost:8000/db/status
```

Expected response from `/db/status`:
```json
{
  "status": "ok",
  "pgvector": {
    "enabled": true,
    "message": "pgvector extension is enabled"
  },
  "tables": {
    "expected": 10,
    "existing": 10,
    "all_present": true,
    "missing": [],
    "list": [
      "content_embeddings",
      "content_items",
      "digest_items",
      "digests",
      "feedback",
      "internal_rag_embeddings",
      "learning_goals",
      "sources",
      "system_logs",
      "users"
    ]
  },
  "ready": true
}
```

### Method 3: Using Supabase SQL Editor
1. Go to **SQL Editor** in Supabase Dashboard
2. Run these queries:

```sql
-- Check pgvector is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- List all tables
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Count rows in system_logs (should have at least 1 entry)
SELECT * FROM system_logs ORDER BY created_at DESC LIMIT 5;
```

## Step 7: Run RAG Ingestion (Phase 4)

Once database is validated, ingest the RAG knowledge base:

```bash
# From project root
python scripts/ingest_rag.py
```

Expected output:
```
============================================================
RAG Ingestion Pipeline Starting...
============================================================

✓ Found masterRAG.md at: /path/to/docs/masterRAG.md

Step 1: Clearing existing RAG embeddings...
✓ Cleared 0 existing embeddings

Step 2: Loading and chunking masterRAG.md...
Found 14 sections in document
Total chunks created: 15
✓ Created 15 chunks

Step 3: Generating embeddings...
Processing batch 1/1 (15 texts)...
✓ Generated 15 embeddings

Step 4: Storing chunks and embeddings in database...
✓ Stored 15 chunks with embeddings

============================================================
RAG Ingestion: SUCCESS ✓
  - Chunks processed: 15
  - Embeddings generated: 15
  - Embeddings stored: 15
============================================================
```

Verify RAG:
```bash
python scripts/ingest_rag.py --stats

# Or via API
curl http://localhost:8000/rag/status
```

## Troubleshooting

### Error: "pgvector extension not available"
- Go to Supabase Dashboard → Database → Extensions
- Enable the "vector" extension manually

### Error: "could not connect to database"
- Check `DATABASE_URL` has correct password
- Ensure Supabase project is not paused
- Check your IP is allowed (Supabase → Settings → Database → Connection Pooling)

### Error: "GOOGLE_API_KEY not found"
- Verify `GOOGLE_API_KEY` is in `backend/.env`
- Get key from: https://makersuite.google.com/app/apikey

## Success Checklist

- [ ] pgvector extension enabled in Supabase
- [ ] DATABASE_URL configured with correct password
- [ ] Database migration completed (10 tables created)
- [ ] Database validation passed
- [ ] RAG ingestion completed (~15 chunks)
- [ ] API server running and responding

## Next Steps

Once all checks pass:
✅ **Phase 3 Complete**: Database setup
✅ **Phase 4 Complete**: RAG ingestion
➡️ **Phase 5 Next**: Backend domain APIs

Ready to proceed with implementing the API endpoints!
