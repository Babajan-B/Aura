"""
Test script to verify digest generation fix.
Creates a test user, goal, and triggers digest generation.
"""
import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_EMAIL = "test@example.com"


async def main():
    """Run digest generation test."""
    print("=" * 60)
    print("DIGEST GENERATION FIX TEST")
    print("=" * 60)

    # Connect with statement_cache_size=0 for pgbouncer compatibility
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'),
        statement_cache_size=0
    )

    try:
        # Step 1: Check if user exists, create if not
        print("\n[1] Checking for test user...")
        user = await conn.fetchrow(
            "SELECT user_id, email FROM users WHERE user_id = $1",
            TEST_USER_ID
        )

        if not user:
            print(f"   Creating test user: {TEST_EMAIL}")
            await conn.execute(
                """
                INSERT INTO users (user_id, email, name, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO NOTHING
                """,
                TEST_USER_ID,
                TEST_EMAIL,
                "Test User",
                datetime.utcnow()
            )
            print("   ✓ Test user created")
        else:
            print(f"   ✓ Test user exists: {user['email']}")

        # Step 2: Check for active goal
        print("\n[2] Checking for active goal...")
        goal = await conn.fetchrow(
            """
            SELECT goal_id, goal_text, is_active
            FROM learning_goals
            WHERE user_id = $1 AND is_active = true
            LIMIT 1
            """,
            TEST_USER_ID
        )

        if goal:
            print(f"   ✓ Active goal found: {goal['goal_text'][:60]}...")
            goal_id = goal['goal_id']
        else:
            print("   ✗ No active goal found")
            print("   Please create a goal via the API first")
            return

        # Step 3: Check content availability
        print("\n[3] Checking content availability...")
        content_count = await conn.fetchval(
            "SELECT COUNT(*) FROM content_items"
        )
        embedding_count = await conn.fetchval(
            "SELECT COUNT(*) FROM content_embeddings"
        )
        print(f"   Content items: {content_count}")
        print(f"   Content embeddings: {embedding_count}")

        if content_count == 0 or embedding_count == 0:
            print("   ✗ No content available for digest generation")
            return

        # Step 4: Check sources
        print("\n[4] Checking sources...")
        sources = await conn.fetch(
            """
            SELECT source_id, source_type, value, status
            FROM sources
            WHERE user_id = $1 OR user_id IS NULL
            LIMIT 10
            """,
            TEST_USER_ID
        )
        print(f"   Found {len(sources)} sources")
        for s in sources[:3]:
            print(f"   - {s['source_type']}: {s['value'][:50]}... ({s['status']})")

        # Step 5: Test content retrieval with goal embedding
        print("\n[5] Testing content retrieval...")
        goal_with_embedding = await conn.fetchrow(
            """
            SELECT goal_id, goal_text, embedding_vector
            FROM learning_goals
            WHERE goal_id = $1
            """,
            goal_id
        )

        if not goal_with_embedding['embedding_vector']:
            print("   ✗ Goal has no embedding vector")
            return

        print(f"   ✓ Goal embedding dimension: {len(goal_with_embedding['embedding_vector'])}")

        # Convert embedding to string format (CRITICAL FIX)
        embedding_vector = goal_with_embedding['embedding_vector']
        embedding_str = '[' + ','.join(map(str, embedding_vector)) + ']'

        # Test retrieval with different similarity thresholds
        for min_sim in [0.3, 0.2, 0.1, 0.05]:
            retrieved = await conn.fetch(
                """
                SELECT
                    ci.content_id,
                    ci.title,
                    1 - (ce.embedding_vector <=> $1::vector) as similarity
                FROM content_items ci
                JOIN content_embeddings ce ON ci.content_id = ce.content_id
                JOIN sources s ON ci.source_id = s.source_id
                WHERE
                    (s.user_id = $2 OR s.user_id IS NULL)
                    AND 1 - (ce.embedding_vector <=> $1::vector) >= $3
                ORDER BY ce.embedding_vector <=> $1::vector
                LIMIT 10
                """,
                embedding_str,  # Use string format, not list
                TEST_USER_ID,
                min_sim
            )

            print(f"   Min similarity {min_sim}: {len(retrieved)} items retrieved")
            if len(retrieved) > 0:
                print(f"      Top similarity score: {retrieved[0]['similarity']:.4f}")
                print(f"      Top title: {retrieved[0]['title'][:60]}...")

        # Step 6: Check existing digests
        print("\n[6] Checking existing digests...")
        digest_count = await conn.fetchval(
            "SELECT COUNT(*) FROM digests WHERE user_id = $1",
            TEST_USER_ID
        )
        print(f"   Total digests: {digest_count}")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        print("\nTo generate a digest, use:")
        print(f'curl -X POST "http://localhost:8000/api/admin/generate" \\')
        print(f'  -H "x-user-id: {TEST_USER_ID}"')
        print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
