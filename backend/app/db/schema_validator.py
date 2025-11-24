"""
Database schema validator for AI Learning Coach.
Validates presence of tables and pgvector extension.
"""
import asyncpg
from typing import List, Dict, Any
from app.db.database import get_db_pool, log_system_event


EXPECTED_TABLES = [
    "users",
    "learning_goals",
    "sources",
    "content_items",
    "content_embeddings",
    "internal_rag_embeddings",
    "digests",
    "digest_items",
    "feedback",
    "system_logs"
]


async def check_pgvector_extension() -> Dict[str, Any]:
    """
    Check if pgvector extension is enabled in the database.

    Returns:
        Dict with status and details
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM pg_extension WHERE extname = 'vector'"
            )

            if result:
                return {
                    "enabled": True,
                    "message": "pgvector extension is enabled",
                    "details": dict(result)
                }
            else:
                return {
                    "enabled": False,
                    "message": "pgvector extension is NOT enabled",
                    "details": None
                }
    except Exception as e:
        return {
            "enabled": False,
            "message": f"Error checking pgvector: {str(e)}",
            "details": None
        }


async def enable_pgvector_extension() -> Dict[str, Any]:
    """
    Attempt to enable pgvector extension.

    Returns:
        Dict with status and message
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await log_system_event("info", "api", "pgvector extension enabled")
            return {
                "success": True,
                "message": "pgvector extension enabled successfully"
            }
    except Exception as e:
        error_msg = f"Failed to enable pgvector: {str(e)}"
        await log_system_event("error", "api", error_msg)
        return {
            "success": False,
            "message": error_msg
        }


async def get_existing_tables() -> List[str]:
    """
    Get list of all existing tables in the database.

    Returns:
        List of table names
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            return [row['tablename'] for row in rows]
    except Exception as e:
        print(f"Error fetching tables: {e}")
        return []


async def validate_table_schema(table_name: str) -> Dict[str, Any]:
    """
    Validate schema for a specific table.

    Args:
        table_name: Name of the table to validate

    Returns:
        Dict with validation results
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get column information
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """, table_name)

            # Get indexes
            indexes = await conn.fetch("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public' AND tablename = $1
            """, table_name)

            return {
                "exists": True,
                "columns": [dict(col) for col in columns],
                "indexes": [dict(idx) for idx in indexes],
                "column_count": len(columns),
                "index_count": len(indexes)
            }
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }


async def validate_all_tables() -> Dict[str, Any]:
    """
    Validate all expected tables exist and have proper structure.

    Returns:
        Dict with validation results for all tables
    """
    existing_tables = await get_existing_tables()

    results = {
        "total_expected": len(EXPECTED_TABLES),
        "total_existing": len(existing_tables),
        "all_tables_present": True,
        "missing_tables": [],
        "existing_tables": existing_tables,
        "table_details": {}
    }

    # Check which expected tables are missing
    for table in EXPECTED_TABLES:
        if table not in existing_tables:
            results["all_tables_present"] = False
            results["missing_tables"].append(table)
        else:
            # Get detailed schema info for existing tables
            schema_info = await validate_table_schema(table)
            results["table_details"][table] = schema_info

    return results


async def run_full_validation() -> Dict[str, Any]:
    """
    Run complete database validation including pgvector and tables.

    Returns:
        Dict with complete validation results
    """
    print("\n" + "="*50)
    print("Database Validation Starting...")
    print("="*50 + "\n")

    validation_results = {
        "pgvector": {},
        "tables": {},
        "overall_status": "pending"
    }

    # Step 1: Check pgvector extension
    print("Step 1: Checking pgvector extension...")
    pgvector_status = await check_pgvector_extension()
    validation_results["pgvector"] = pgvector_status

    if pgvector_status["enabled"]:
        print("✓ pgvector extension is enabled")
    else:
        print("✗ pgvector extension is NOT enabled")
        print("  Attempting to enable...")
        enable_result = await enable_pgvector_extension()
        validation_results["pgvector"]["enable_attempt"] = enable_result
        if enable_result["success"]:
            print("✓ pgvector extension enabled successfully")
        else:
            print(f"✗ Failed to enable pgvector: {enable_result['message']}")

    # Step 2: Validate tables
    print("\nStep 2: Validating database tables...")
    table_validation = await validate_all_tables()
    validation_results["tables"] = table_validation

    print(f"Expected tables: {table_validation['total_expected']}")
    print(f"Existing tables: {table_validation['total_existing']}")

    if table_validation["all_tables_present"]:
        print("✓ All expected tables are present")
        overall_status = "success"
    else:
        print(f"✗ Missing tables: {', '.join(table_validation['missing_tables'])}")
        overall_status = "missing_tables"

    # Step 3: Log validation results
    validation_results["overall_status"] = overall_status

    print("\n" + "="*50)
    if overall_status == "success":
        print("Database Validation: PASSED ✓")
        await log_system_event("info", "api", "Database validation passed")
    else:
        print("Database Validation: FAILED ✗")
        await log_system_event(
            "warning",
            "api",
            f"Database validation failed. Missing tables: {table_validation['missing_tables']}"
        )
    print("="*50 + "\n")

    return validation_results


async def apply_migration(migration_file: str) -> Dict[str, Any]:
    """
    Apply a SQL migration file to the database.

    Args:
        migration_file: Path to the SQL migration file

    Returns:
        Dict with migration results
    """
    try:
        # Read migration file
        with open(migration_file, 'r') as f:
            sql_content = f.read()

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(sql_content)
            await log_system_event(
                "info",
                "api",
                f"Migration applied: {migration_file}"
            )

        return {
            "success": True,
            "message": f"Migration {migration_file} applied successfully"
        }
    except Exception as e:
        error_msg = f"Failed to apply migration {migration_file}: {str(e)}"
        await log_system_event("error", "api", error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
