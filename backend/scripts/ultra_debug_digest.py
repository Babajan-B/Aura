"""
Ultra-detailed debug script to find exactly where digest generation fails.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import get_db_pool
from app.rag.external_retrieval import retrieve_content_by_goal, get_user_goal_embedding  
from app.rag.scoring import score_content_items, select_top_items
from app.rag.summarizer import batch_summarize_content


async def ultra_debug():
    user_id = "12345678-1234-1234-1234-123456789012"
    
    print("="*70)
    print("🔍 ULTRA-DETAILED DIGEST DEBUG")
    print("="*70)
    print()
    
    # Step 1: Get goal
    print("STEP 1: Getting user goal...")
    goal_data = await get_user_goal_embedding(user_id)
    if not goal_data:
        print("❌ FAILED: No active goal!")
        return
    
    goal_id, goal_text, goal_embedding = goal_data
    print(f"✅ Goal ID: {goal_id}")
    print(f"✅ Goal: {goal_text}")
    print(f"✅ Embedding size: {len(goal_embedding) if goal_embedding else 0}")
    print()
    
    # Step 2: Retrieve content
    print("STEP 2: Retrieving content...")
    print("   Parameters: max_items=100, min_similarity=0.15, days_ago=7")
    
    content_items = await retrieve_content_by_goal(
        user_id=user_id,
        goal_embedding=goal_embedding,
        max_items=100,
        min_similarity=0.15,
        days_ago=7
    )
    
    print(f"✅ Retrieved {len(content_items) if content_items else 0} items")
    if not content_items:
        print("❌ FAILED: No content retrieved!")
        print("   This means no content matches the similarity threshold")
        return
    
    print(f"   Sample item: {content_items[0]['title'][:60]}...")
    print(f"   Similarity range: {content_items[0]['similarity']:.3f} to {content_items[-1]['similarity']:.3f}")
    print()
    
    # Step 3: Score items
    print("STEP 3: Scoring items...")
    scored_items = await score_content_items(content_items, goal_text)
    
    print(f"✅ Scored {len(scored_items)} items")
    if scored_items:
        print(f"   Top 5 scores:")
        for i, item in enumerate(scored_items[:5]):
            print(f"     {i+1}. {item['scores']['final']:.3f} - {item['title'][:50]}")
    print()
    
    # Step 4: Select top items
    print("STEP 4: Selecting top items (min_score=0.0, max_items=10)...")
    top_items = await select_top_items(scored_items, min_score=0.0, max_items=10)
    
    print(f"✅ Selected {len(top_items) if top_items else 0} items")
    if not top_items:
        print("❌ FAILED: No items selected!")
        print(f"   All {len(scored_items)} items were below min_score=0.0")
        return
    
    for i, item in enumerate(top_items):
        print(f"   {i+1}. Score={item['scores']['final']:.3f}: {item['title'][:50]}")
    print()
    
    # Step 5: Summarize
    print("STEP 5: Generating summaries...")
    try:
        summarized = await batch_summarize_content(top_items, goal_text)
        print(f"✅ Generated {len(summarized)} summaries")
        print(f"   Sample summary: {summarized[0]['summary'][:100]}...")
        print()
    except Exception as e:
        print(f"❌ FAILED at summarization: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 6: Create digest
    print("STEP 6: Creating digest in database...")
    pool = await get_db_pool()
    
    from datetime import datetime, timedelta
    import uuid
    
    now = datetime.utcnow()
    week_end_date = now.date()
    week_start_date = (now - timedelta(days=7)).date()
    digest_id = str(uuid.uuid4())
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO digests
                (digest_id, user_id, goal_id, week_start_date, week_end_date, generated_at, total_items)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                digest_id, user_id, goal_id, week_start_date, week_end_date, now, len(summarized)
            )
            
            for item in summarized:
                digest_item_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO digest_items
                    (digest_item_id, digest_id, content_id, title, summary, why_it_matters,
                     relevance_score, source_type, link_url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    digest_item_id, digest_id, item['content_id'], item['title'],
                    item['summary'], item['why_it_matters'], item['scores']['final'],
                    item['source_type'], item['original_url']
                )
        
        print(f"✅ Digest created!")
        print(f"   Digest ID: {digest_id}")
        print()
        
    except Exception as e:
        print(f"❌ FAILED at database insert: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("="*70)
    print("🎉 SUCCESS!")
    print("="*70)
    print(f"Digest ID: {digest_id}")
    print(f"View at: http://localhost:3000/digest")
    print()


if __name__ == "__main__":
    asyncio.run(ultra_debug())
