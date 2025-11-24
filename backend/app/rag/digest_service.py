"""
Digest generation service.
Creates weekly personalized learning digests for users.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid

from app.db.database import get_db_pool, log_system_event
from app.rag.external_retrieval import retrieve_content_by_goal, get_user_goal_embedding
from app.rag.scoring import score_content_items, select_top_items
from app.rag.summarizer import batch_summarize_content
from app.services.email_service import send_digest_to_user


async def generate_digest_for_user(user_id: str) -> Optional[str]:
    """
    Generate a weekly digest for a specific user.
    
    Args:
        user_id: User ID
        
    Returns:
        Digest ID if successful, None otherwise
    """
    try:
        pool = await get_db_pool()
        
        # Get user's active goal
        goal_data = await get_user_goal_embedding(user_id)
        if not goal_data:
            await log_system_event(
                "warning",
                "rag",
                f"User {user_id} has no active goal, skipping digest generation"
            )
            return None
        
        goal_id, goal_text, goal_embedding = goal_data
        
        # Retrieve relevant content
        content_items = await retrieve_content_by_goal(
            user_id=user_id,
            goal_embedding=goal_embedding,
            max_items=100,  # Retrieve more than needed for better selection
            min_similarity=0.15,  # Lowered threshold for broader results
            days_ago=7  # Last week's content
        )
        
        if not content_items:
            await log_system_event(
                "warning",
                "rag",
                f"No content found for user {user_id}, skipping digest"
            )
            return None
        
        # Score and rank content
        scored_items = await score_content_items(content_items, goal_text)
        
        # Log top scores for debugging
        if scored_items:
            await log_system_event(
                "info",
                "rag",
                f"Top 3 scores: {[round(item['scores']['final'], 3) for item in scored_items[:3]]}"
            )
        
        # Select top items - LOWERED threshold to 0.0 to ensure selection
        top_items = await select_top_items(scored_items, min_score=0.0, max_items=10)
        
        if not top_items:
            await log_system_event(
                "warning",
                "rag",
                f"No items met minimum score for user {user_id}"
            )
            return None
        
        # Generate summaries
        summarized_items = await batch_summarize_content(top_items, goal_text)
        
        # Calculate week range
        now = datetime.utcnow()
        week_end_date = now.date()
        week_start_date = (now - timedelta(days=7)).date()
        
        # Create digest record
        digest_id = str(uuid.uuid4())
        
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO digests
                (digest_id, user_id, goal_id, week_start_date, week_end_date, generated_at, total_items)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                digest_id,
                user_id,
                goal_id,
                week_start_date,
                week_end_date,
                now,
                len(summarized_items)
            )
            
            # Create digest items
            for item in summarized_items:
                digest_item_id = str(uuid.uuid4())
                
                await conn.execute(
                    """
                    INSERT INTO digest_items
                    (digest_item_id, digest_id, content_id, title, summary, why_it_matters,
                     relevance_score, source_type, link_url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    digest_item_id,
                    digest_id,
                    item['content_id'],
                    item['title'],
                    item['summary'],
                    item['why_it_matters'],
                    item['scores']['final'],
                    item['source_type'],
                    item['original_url']
                )
        
        await log_system_event(
            "info",
            "rag",
            f"Generated digest {digest_id} for user {user_id} with {len(summarized_items)} items"
        )
        
        # Send email
        email_sent = await send_digest_to_user(user_id, digest_id)
        if email_sent:
            await log_system_event(
                "info",
                "rag",
                f"Email sent for digest {digest_id}"
            )
        else:
            await log_system_event(
                "warning",
                "rag",
                f"Failed to send email for digest {digest_id}"
            )
        
        return digest_id
        
    except Exception as e:
        await log_system_event("error", "rag", f"Failed to generate digest for user {user_id}: {str(e)}")
        return None


async def generate_all_digests():
    """
    Generate digests for all users with active goals.
    This is called by the weekly scheduler.
    
    Returns:
        Number of digests generated
    """
    await log_system_event("info", "rag", "Starting weekly digest generation for all users")
    
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get all users with active goals
        users = await conn.fetch(
            """
            SELECT DISTINCT user_id
            FROM learning_goals
            WHERE is_active = true
            """
        )
    
    digest_count = 0
    
    for user in users:
        user_id = str(user['user_id'])
        digest_id = await generate_digest_for_user(user_id)
        
        if digest_id:
            digest_count += 1
    
    await log_system_event(
        "info",
        "rag",
        f"Weekly digest generation complete: {digest_count} digests created for {len(users)} users"
    )
    
    return digest_count


async def get_digest_statistics() -> Dict:
    """
    Get digest generation statistics.
    
    Returns:
        Dict with digest stats
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        total_digests = await conn.fetchval(
            "SELECT COUNT(*) FROM digests"
        )
        
        total_items = await conn.fetchval(
            "SELECT COUNT(*) FROM digest_items"
        )
        
        latest_digest = await conn.fetchrow(
            """
            SELECT generated_at, total_items
            FROM digests
            ORDER BY generated_at DESC
            LIMIT 1
            """
        )
        
        return {
            "total_digests": total_digests or 0,
            "total_digest_items": total_items or 0,
            "latest_digest_at": latest_digest['generated_at'] if latest_digest else None,
            "latest_digest_items": latest_digest['total_items'] if latest_digest else 0
        }
