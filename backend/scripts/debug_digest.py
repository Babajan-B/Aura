"""
Debug version of digest generation with detailed error logging.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import get_db_pool
from app.rag.external_retrieval import get_active_goal_for_retrieval, retrieve_relevant_content
from app.rag.scoring import score_content_items
from app.rag.summarizer import summarize_content_batch
import traceback


async def debug_digest():
    user_id = "12345678-1234-1234-1234-123456789012"
    
    print("=" * 60)
    print("🔍 Detailed Digest Generation Debug")
    print("=" * 60)
    print()
    
    try:
        # Step 1: Get goal and embedding
        print("Step 1: Retrieving active goal...")
        goal_data = await get_active_goal_for_retrieval(user_id)
        if not goal_data:
            print("❌ No active goal found!")
            return
        
        goal_id, goal_text, goal_embedding = goal_data
        print(f"✅ Goal: {goal_text[:100]}...")
        print(f"   Goal ID: {goal_id}")
        print(f"   Embedding length: {len(goal_embedding) if goal_embedding else 0}")
        print()
        
        # Step 2: Retrieve relevant content
        print("Step 2: Retrieving relevant content...")
        print("   Retrieving top 50 items...")
        
        retrieved_items = await retrieve_relevant_content(
            user_id=user_id,
            goal_embedding=goal_embedding,
            limit=50,
            similarity_threshold=0.3
        )
        
        print(f"✅ Retrieved {len(retrieved_items)} items")
        if retrieved_items:
            print(f"   Top item similarity: {retrieved_items[0]['similarity']:.3f}")
            print(f"   Lowest item similarity: {retrieved_items[-1]['similarity']:.3f}")
        else:
            print("❌ No items retrieved! Possible issues:")
            print("   - Similarity threshold too high (0.3)")
            print("   - Content embeddings don't match goal")
            print("   - No content from user's sources")
            return
        print()
        
        # Step 3: Score items
        print("Step 3: Scoring content items...")
        scored_items = await score_content_items(
            items=retrieved_items,
            goal_text=goal_text,
            user_id=user_id
        )
        
        print(f"✅ Scored {len(scored_items)} items")
        if scored_items:
            print(f"   Top score: {scored_items[0]['final_score']:.3f}")
            print(f"   Top item: {scored_items[0]['title'][:60]}...")
        print()
        
        # Step 4: Select top items
        print("Step 4: Selecting top 10 items...")
        top_items = scored_items[:10]
        print(f"✅ Selected {len(top_items)} items for digest")
        print()
        
        # Step 5: Summarize
        print("Step 5: Generating summaries...")
        try:
            summaries = await summarize_content_batch(top_items, goal_text)
            print(f"✅ Generated {len(summaries)} summaries")
            print()
        except Exception as e:
            print(f"❌ Summarization failed: {e}")
            traceback.print_exc()
            return
        
        # Step 6: Store digest
        print("Step 6: Creating digest in database...")
        pool = await get_db_pool()
        
        from datetime import datetime, timedelta
        import uuid
        
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)
        
        digest_id = str(uuid.uuid4())
        
        async with pool.acquire() as conn:
            # Insert digest
            await conn.execute(
                """
                INSERT INTO digests
                (digest_id, user_id, goal_id, week_start_date, week_end_date, generated_at, total_items, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                digest_id, user_id, goal_id, week_start.date(), week_end.date(),
                now, len(summaries), 'completed'
            )
            
            # Insert digest items
            for idx, (item, summary_data) in enumerate(zip(top_items, summaries)):
                item_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO digest_items
                    (digest_item_id, digest_id, content_id, rank_position, title, summary, 
                     why_it_matters, relevance_score, source_type, link_url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    item_id, digest_id, item['content_id'], idx + 1,
                    item['title'], summary_data['summary'], summary_data['why_it_matters'],
                    item['final_score'], item['source_type'], item['link_url']
                )
        
        print(f"✅ Digest created successfully!")
        print(f"   Digest ID: {digest_id}")
        print()
        
        print("=" * 60)
        print("🎉 SUCCESS! Digest generated")
        print("=" * 60)
        print()
        print("View at: http://localhost:3000/digest")
        print()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_digest())
