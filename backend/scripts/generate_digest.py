"""
Flexible digest generation CLI script.
Generate digests on-demand with different frequencies.
"""
import asyncio
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.rag.digest_service import generate_digest_for_user
from app.db.database import get_db_pool


async def generate_digest(user_id: str, frequency: str = "weekly"):
    """
    Generate a digest for the specified user and frequency.
    
    Args:
        user_id: User ID
        frequency: daily, weekly, or monthly
    """
    print("=" * 60)
    print(f"📊 Generating {frequency.upper()} Digest")
    print("=" * 60)
    print()
    print(f"User ID: {user_id}")
    print(f"Frequency: {frequency}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check prerequisites
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        goal_count = await conn.fetchval(
            "SELECT COUNT(*) FROM learning_goals WHERE user_id = $1 AND is_active = true",
            user_id
        )
        content_count = await conn.fetchval("SELECT COUNT(*) FROM content_items")
        embedding_count = await conn.fetchval("SELECT COUNT(*) FROM content_embeddings")
    
    print(f"Prerequisites:")
    print(f"  ✓ Active goals: {goal_count}")
    print(f"  ✓ Content items: {content_count}")
    print(f"  ✓ Embeddings: {embedding_count}")
    print()
    
    if goal_count == 0:
        print("❌ ERROR: No active goal found!")
        print("   Create a goal at: http://localhost:3000/goals")
        return None
    
    if embedding_count == 0:
        print("❌ ERROR: No embeddings available!")
        print("   Run: python scripts/test_digest_workflow.py")
        return None
    
    # Generate digest
    print("🔄 Generating digest...")
    print("   (This may take 30-60 seconds...)")
    print()
    
    try:
        digest_id = await generate_digest_for_user(user_id)
        
        if digest_id:
            print("=" * 60)
            print("✅ SUCCESS! Digest Generated")
            print("=" * 60)
            print()
            print(f"Digest ID: {digest_id}")
            print()
            print("📧 Email Status:")
            print("   ✓ Automatically sent (if MailerSend configured)")
            print()
            print("🌐 View digest:")
            print(f"   Frontend: http://localhost:3000/digest")
            print(f"   API: curl http://localhost:8000/api/digests/{digest_id}")
            print()
            
            # Get digest stats
            async with pool.acquire() as conn:
                digest = await conn.fetchrow(
                    "SELECT total_items, generated_at FROM digests WHERE digest_id = $1",
                    digest_id
                )
            
            print(f"📊 Digest Stats:")
            print(f"   Items: {digest['total_items']}")
            print(f"   Generated: {digest['generated_at']}")
            print()
            
            return digest_id
        else:
            print("=" * 60)
            print("❌ Digest Generation Failed")
            print("=" * 60)
            print()
            print("Possible reasons:")
            print("  1. Not enough relevant content")
            print("  2. Content doesn't match your learning goal")
            print("  3. Minimum score threshold not met")
            print()
            print("Solutions:")
            print("  - Wait for more content to be ingested")
            print("  - Adjust your learning goal to be more specific")
            print("  - Check backend logs: tail -f /tmp/backend.log")
            print()
            return None
            
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR During Generation")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return None


async def main():
    parser = argparse.ArgumentParser(description='Generate AI Learning Coach digest on-demand')
    parser.add_argument(
        '--user-id',
        default='12345678-1234-1234-1234-123456789012',
        help='User ID (default: test user)'
    )
    parser.add_argument(
        '--frequency',
        choices=['daily', 'weekly', 'monthly', 'now'],
        default='now',
        help='Digest frequency (default: now)'
    )
    
    args = parser.parse_args()
    
    await generate_digest(args.user_id, args.frequency)


if __name__ == "__main__":
    asyncio.run(main())
