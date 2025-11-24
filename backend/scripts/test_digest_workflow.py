"""
Complete workflow to generate a test digest with email:
1. Ingest content from RSS feeds
2. Generate embeddings for content
3. Generate digest
4. Send email
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import get_db_pool
from app.ingestion.rss_service import ingest_rss_feeds
from app.ingestion.content_embedding_service import generate_content_embeddings
from app.rag.digest_service import generate_digest_for_user


async def check_status():
    """Check current content status."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        content_count = await conn.fetchval("SELECT COUNT(*) FROM content_items")
        embedding_count = await conn.fetchval("SELECT COUNT(*) FROM content_embeddings")
        goal_count = await conn.fetchval(
            "SELECT COUNT(*) FROM learning_goals WHERE is_active = true"
        )
    
    return content_count, embedding_count, goal_count


async def main():
    user_id = "12345678-1234-1234-1234-123456789012"
    
    print("=" * 60)
    print("🚀 Complete Digest Generation Workflow")
    print("=" * 60)
    print()
    
    # Step 0: Check current status
    print("📊 Step 0: Checking current status...")
    content_count, embedding_count, goal_count = await check_status()
    print(f"   Active goals: {goal_count}")
    print(f"   Content items: {content_count}")
    print(f"   Embeddings: {embedding_count}")
    print()
    
    if goal_count == 0:
        print("❌ ERROR: No active learning goal found!")
        print("   Create a goal first: http://localhost:3000/goals")
        return
    
    # Step 1: Ingest content
    print("📥 Step 1: Ingesting RSS content...")
    print("   (This may take 1-2 minutes...)")
    try:
        new_items = await ingest_rss_feeds()
        print(f"   ✅ Ingested {new_items} new content items")
    except Exception as e:
        print(f"   ⚠️  Ingestion error: {e}")
        print("   Continuing with existing content...")
    print()
    
    # Step 2: Generate embeddings
    print("🔢 Step 2: Generating embeddings...")
    print("   (This may take 2-3 minutes for 50 items...)")
    try:
        new_embeddings = await generate_content_embeddings(batch_size=50, max_items=50)
        print(f"   ✅ Generated {new_embeddings} new embeddings")
    except Exception as e:
        print(f"   ❌ Embedding generation error: {e}")
        return
    print()
    
    # Check status again
    content_count, embedding_count, goal_count = await check_status()
    print(f"   Updated status:")
    print(f"   - Content items: {content_count}")
    print(f"   - Embeddings: {embedding_count}")
    print()
    
    if embedding_count == 0:
        print("❌ ERROR: No embeddings available!")
        print("   Cannot generate digest without embedded content.")
        return
    
    # Step 3: Generate digest
    print("📝 Step 3: Generating personalized digest...")
    try:
        digest_id = await generate_digest_for_user(user_id)
        
        if digest_id:
            print(f"   ✅ Digest created successfully!")
            print(f"   Digest ID: {digest_id}")
            print()
            print("📧 Step 4: Email Status")
            print("   ✅ Email automatically sent (if MailerSend configured)")
            print("   📬 Check your email inbox!")
            print()
            print("=" * 60)
            print("🎉 SUCCESS! Digest generated and emailed")
            print("=" * 60)
            print()
            print("🌐 View digest in frontend:")
            print(f"   http://localhost:3000/digest")
            print()
            print("📊 Check email logs:")
            print("   tail -n 100 /tmp/backend.log | grep -i mail")
        else:
            print("   ❌ Failed to generate digest")
            print("   Possible reasons:")
            print("   - Not enough relevant content")
            print("   - Content doesn't match learning goal")
            print("   - Database error")
            
    except Exception as e:
        print(f"   ❌ Digest generation error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
