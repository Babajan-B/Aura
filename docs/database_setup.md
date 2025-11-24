# Database Setup Guide

Complete guide for setting up the AI Learning Coach database with Supabase and pgvector.

## Prerequisites

1. **Supabase Account**: Sign up at https://supabase.com
2. **Python 3.9+**: Installed on your system
3. **Backend Dependencies**: Install from `backend/requirements.txt`

## Step 1: Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Fill in project details:
   - Name: `ai-learning-coach`
   - Database Password: Choose a strong password (save it!)
   - Region: Choose closest to you
4. Wait for project to finish setting up (2-3 minutes)

## Step 2: Get Database Credentials

### From Supabase Dashboard

Navigate to: **Project Settings → Database**

You'll need:

1. **Connection String (URI)**:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.mokavdikepjluienxrle.supabase.co:5432/postgres
   ```
   Copy this and replace `[YOUR-PASSWORD]` with your actual database password

2. **API Keys**:
   - Navigate to: **Project Settings → API**
   - Copy `URL` (Project URL)
   - Copy `anon public` key
   - Copy `service_role` key (keep this secret!)

## Step 3: Configure Environment Variables

Update `backend/.env` with your credentials:

```bash
# Supabase Configuration
SUPABASE_URL=https://mokavdikepjluienxrle.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Database Connection String
DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@db.mokavdikepjluienxrle.supabase.co:5432/postgres
```

**Important**: Replace placeholders with your actual values!

## Step 4: Enable pgvector Extension

The migration script will attempt to enable pgvector automatically. If it fails:

1. Go to Supabase Dashboard → **Database → Extensions**
2. Search for "vector"
3. Enable the **vector** extension
4. Click "Enable"

## Step 5: Run Database Migrations

From the project root directory:

```bash
# Install dependencies first (if not already done)
cd backend
pip install -r requirements.txt

# Return to project root
cd ..

# Run full database setup
python scripts/setup_database.py full
```

This will:
1. Apply the initial schema migration
2. Create all 10 required tables
3. Set up indexes and constraints
4. Validate the setup

### Expected Output

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

## Step 6: Verify Installation

### Method 1: Using the Setup Script

```bash
python scripts/setup_database.py validate
```

### Method 2: Using the API

1. Start the FastAPI server:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Visit: http://localhost:8000/db/status

Expected response:
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

1. Go to Supabase Dashboard → **SQL Editor**
2. Run this query:

```sql
-- Check pgvector
SELECT * FROM pg_extension WHERE extname = 'vector';

-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Count records in system_logs
SELECT * FROM system_logs ORDER BY created_at DESC LIMIT 5;
```

## Database Schema Overview

### Tables Created

1. **users** - User profiles
2. **learning_goals** - User learning objectives (with vector embeddings)
3. **sources** - Content sources (RSS, YouTube, etc.)
4. **content_items** - Ingested content
5. **content_embeddings** - Vector embeddings for content
6. **internal_rag_embeddings** - Embeddings from masterRAG.md
7. **digests** - Weekly digest metadata
8. **digest_items** - Individual digest entries
9. **feedback** - User feedback on items
10. **system_logs** - Application logs

### Vector Columns

The following tables use pgvector for semantic search:

- `learning_goals.embedding_vector` (dimension: 768)
- `content_embeddings.embedding_vector` (dimension: 768)
- `internal_rag_embeddings.embedding_vector` (dimension: 768)

All use IVFFlat indexes with cosine similarity.

## Troubleshooting

### Error: "pgvector extension not available"

**Solution**:
1. Enable it manually in Supabase Dashboard → Database → Extensions
2. Or run: `CREATE EXTENSION IF NOT EXISTS vector;` in SQL Editor

### Error: "Could not connect to database"

**Possible causes**:
1. Wrong password in `DATABASE_URL`
2. IP not allowed (check Supabase Dashboard → Settings → Database → Connection Pooling)
3. Project paused (check dashboard)

**Solution**:
- Verify `DATABASE_URL` is correct
- Add your IP to allowed list in Supabase
- Ensure project is active

### Error: "Permission denied"

**Solution**:
- Make sure you're using the `service_role` key for migrations
- Check that `DATABASE_URL` includes the correct password

### Migration already applied?

If tables already exist, the migration will skip creating them (uses `IF NOT EXISTS`).

To start fresh:
1. Go to Supabase SQL Editor
2. Drop all tables: `DROP TABLE IF EXISTS [table_name] CASCADE;`
3. Re-run migration

## Next Steps

After successful database setup:

1. ✅ Database is ready for Phase 4: RAG internal knowledge ingestion
2. Test the connection with the API health check
3. Proceed with implementing backend APIs (Phase 5)

## Security Notes

- **Never commit** `.env` file to version control
- **Keep** `SUPABASE_SERVICE_ROLE_KEY` secret (server-side only)
- **Use** `SUPABASE_ANON_KEY` for frontend (public, but RLS-protected)
- **Enable** Row Level Security (RLS) policies in production
- **Rotate** keys periodically

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Supabase documentation: https://supabase.com/docs
3. Check application logs in `system_logs` table
