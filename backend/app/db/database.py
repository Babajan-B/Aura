"""
Database connection and helper functions for Supabase/PostgreSQL.
"""
import asyncpg
from typing import Optional
from app.core.config import get_settings

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create the database connection pool.
    """
    global _pool
    if _pool is None:
        settings = get_settings()

        # Construct PostgreSQL connection string from Supabase URL
        # Supabase URL format: https://xxx.supabase.co
        # PostgreSQL format: postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres

        # For now, we'll use a direct connection string if provided,
        # otherwise construct from Supabase URL
        if settings.database_url:
            connection_string = settings.database_url
        else:
            # Extract project ref from Supabase URL
            # This is a simplified approach - users should provide DATABASE_URL in .env
            raise ValueError(
                "DATABASE_URL not provided. Please add DATABASE_URL to your .env file.\n"
                "Get it from: Supabase Dashboard > Project Settings > Database > Connection String (URI)"
            )

        _pool = await asyncpg.create_pool(
            connection_string,
            min_size=2,
            max_size=10,
            command_timeout=60,
            statement_cache_size=0  # Required for pgbouncer transaction mode
        )

    return _pool


async def close_db_pool():
    """
    Close the database connection pool.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def execute_query(query: str, *args):
    """
    Execute a query and return results.

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        Query results
    """
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        return await connection.fetch(query, *args)


async def execute_one(query: str, *args):
    """
    Execute a query and return a single result.

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        Single query result or None
    """
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, *args)


async def execute_write(query: str, *args):
    """
    Execute a write query (INSERT, UPDATE, DELETE).

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        Status message
    """
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        return await connection.execute(query, *args)


async def log_system_event(
    log_type: str,
    component: str,
    message: str
):
    """
    Log a system event to the system_logs table.

    Args:
        log_type: Type of log (info, warning, error)
        component: Component name (ingestion, rag, email, api, scheduler)
        message: Log message
    """
    try:
        query = """
            INSERT INTO system_logs (log_type, component, message, created_at)
            VALUES ($1, $2, $3, NOW())
        """
        await execute_write(query, log_type, component, message)
    except Exception as e:
        # If logging fails, print to console to avoid recursive errors
        print(f"Failed to log system event: {e}")
