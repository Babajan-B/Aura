"""
Test database connection directly with asyncpg.
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def test_connection():
    # Load environment variables
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    print(f"Testing connection with URL: {database_url}")
    print("-" * 80)

    try:
        # Try to connect
        print("Attempting to create connection pool...")
        pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=2,
            command_timeout=10
        )
        print("✓ Connection pool created successfully!")

        # Try a simple query
        print("\nTesting query execution...")
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT current_database()")
            print(f"✓ Connected to database: {result}")

            # Check pgvector
            pg_ext = await conn.fetchrow(
                "SELECT * FROM pg_extension WHERE extname = 'vector'"
            )
            if pg_ext:
                print(f"✓ pgvector extension is enabled (version: {pg_ext['extversion']})")
            else:
                print("✗ pgvector extension not found")

            # List tables
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            print(f"\n✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table['tablename']}")

        await pool.close()
        print("\n" + "="*80)
        print("CONNECTION TEST: SUCCESS ✓")
        print("="*80)

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\n" + "="*80)
        print("CONNECTION TEST: FAILED ✗")
        print("="*80)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
