"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import get_settings
from app.db.database import get_db_pool, close_db_pool, log_system_event
from app.db.schema_validator import (
    check_pgvector_extension,
    validate_all_tables
)
from app.rag.rag_ingestion_service import (
    get_rag_statistics,
    get_rag_embeddings_count
)
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name}...")

    try:
        # Initialize database connection pool
        await get_db_pool()
        print("Database connection pool initialized")
        await log_system_event("info", "api", "Application started successfully")
        
        # Start background scheduler
        start_scheduler()
        print("Background scheduler started")
        
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Application starting without database connection")

    yield

    # Shutdown
    print("Shutting down application...")
    try:
        # Stop scheduler
        stop_scheduler()
        
        await log_system_event("info", "api", "Application shutting down")
        await close_db_pool()
        print("Database connection pool closed")
    except Exception as e:
        print(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="AI Learning Coach API",
    description="Backend API for personalized AI learning digest generation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - Allow all localhost ports for development
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_base_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "app": "AI Learning Coach API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns the current status of the application.
    """
    try:
        # Test database connection
        pool = await get_db_pool()
        async with pool.acquire() as connection:
            result = await connection.fetchval("SELECT NOW()")
            db_status = "connected"
            db_time = str(result)
    except Exception as e:
        db_status = "disconnected"
        db_time = str(e)

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "status": db_status,
            "server_time": db_time
        }
    }


@app.get("/db/status")
async def database_status():
    """
    Detailed database status endpoint.
    Returns information about pgvector and table schema.
    """
    try:
        # Check pgvector
        pgvector_status = await check_pgvector_extension()

        # Validate tables
        table_validation = await validate_all_tables()

        return {
            "status": "ok",
            "pgvector": {
                "enabled": pgvector_status.get("enabled", False),
                "message": pgvector_status.get("message", "Unknown")
            },
            "tables": {
                "expected": table_validation["total_expected"],
                "existing": table_validation["total_existing"],
                "all_present": table_validation["all_tables_present"],
                "missing": table_validation["missing_tables"],
                "list": table_validation["existing_tables"]
            },
            "ready": pgvector_status.get("enabled", False) and table_validation["all_tables_present"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "ready": False
        }


@app.get("/rag/status")
async def rag_status():
    """
    RAG knowledge base status endpoint.
    Returns information about internal RAG embeddings.
    """
    try:
        count = await get_rag_embeddings_count()
        stats = await get_rag_statistics()

        return {
            "status": "ok",
            "ready": count > 0,
            "total_chunks": count,
            "statistics": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "ready": False
        }


# Import and include routers
from app.api import goals, sources, digests, feedback, admin

app.include_router(goals.router, prefix="/api/goals", tags=["goals"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(digests.router, prefix="/api/digests", tags=["digests"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
