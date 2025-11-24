# AI Learning Coach - Backend

FastAPI backend for the AI Learning Coach application.

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the `.env.template` file to `.env` and fill in your credentials:

```bash
cp .env.template .env
```

Required credentials:
- **Supabase**: Get from [Supabase Dashboard](https://supabase.com/dashboard)
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DATABASE_URL` (Project Settings > Database > Connection String)

- **Gemini API**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - `GEMINI_API_KEY`

- **Other APIs** (already filled from rss.md):
  - Twitter, MailerSend, Google, YouTube API keys

### 4. Setup Database

Run database migrations to create all required tables:

```bash
# From project root
python scripts/setup_database.py full
```

This will:
- Enable pgvector extension
- Create all 10 database tables
- Set up indexes and constraints
- Validate the setup

Verify database is ready:
```bash
python scripts/setup_database.py validate
```

For detailed instructions, see: [Database Setup Guide](../docs/database_setup.md)

### 5. Ingest RAG Knowledge Base

Ingest the masterRAG.md file to enable RAG functionality:

```bash
# From project root
python scripts/ingest_rag.py
```

This will:
- Chunk masterRAG.md into semantic sections
- Generate embeddings using Google Generative AI
- Store in internal_rag_embeddings table

Verify RAG is ready:
```bash
python scripts/ingest_rag.py --stats
```

For detailed instructions, see: [RAG Ingestion Guide](../docs/rag_ingestion.md)

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- Database Status: `http://localhost:8000/db/status`
- RAG Status: `http://localhost:8000/rag/status`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API route handlers
│   ├── core/                # Core configuration
│   │   └── config.py        # Environment settings
│   ├── db/                  # Database connections and queries
│   │   └── database.py      # Supabase/PostgreSQL connection
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas for API
│   ├── services/            # Business logic services
│   ├── rag/                 # RAG retrieval and generation
│   ├── ingestion/           # Content ingestion services
│   └── utils/               # Utility functions
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not committed)
└── .env.template            # Template for environment variables
```

## API Endpoints

See `/docs` for interactive API documentation or `config/apis.md` for the full specification.

### Available Endpoints

- `GET /` - API information
- `GET /health` - Health check and database status

### Coming Soon (Phase 5+)

- `/api/goals` - Learning goals management
- `/api/sources` - Content sources management
- `/api/digests` - Weekly digest access
- `/api/feedback` - User feedback submission

## Development

### Running Tests

```bash
pytest
```

### Code Style

Follow PEP 8 guidelines and use type hints where possible.

## Troubleshooting

### Database Connection Issues

If you see database connection errors:
1. Verify your `DATABASE_URL` is correct in `.env`
2. Check that your Supabase project is active
3. Ensure your IP is allowed in Supabase dashboard

### Import Errors

Make sure you're running from the backend directory and your virtual environment is activated:
```bash
cd backend
source venv/bin/activate
```
