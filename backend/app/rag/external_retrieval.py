"""
External content retrieval service.
Retrieves relevant content items based on user goals and learning preferences.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from app.db.database import get_db_pool
from app.rag.embedding_service import generate_goal_embedding


async def retrieve_content_by_goal(
    user_id: str,
    goal_embedding: List[float],
    max_items: int = 50,
    min_similarity: float = 0.1,  # Lowered from 0.3 to be more lenient
    days_ago: int = 14
) -> List[Dict]:
    """
    Retrieve content items relevant to a user's learning goal.

    Args:
        user_id: User ID
        goal_embedding: Goal embedding vector
        max_items: Maximum number of items to retrieve
        min_similarity: Minimum similarity threshold (0.0 to 1.0)
        days_ago: Only retrieve content from last N days

    Returns:
        List of content items with metadata and similarity scores
    """
    pool = await get_db_pool()

    cutoff_date = datetime.utcnow() - timedelta(days=days_ago)

    # Convert embedding to pgvector string format
    if isinstance(goal_embedding, list):
        # If it's already a list, convert to string format
        embedding_str = '[' + ','.join(map(str, goal_embedding)) + ']'
    elif isinstance(goal_embedding, str):
        # If it's already a string, use it directly
        embedding_str = goal_embedding
    else:
        # Fallback: try to convert to string
        embedding_str = str(goal_embedding)

    async with pool.acquire() as conn:
        # Get user's sources (both user-specific and global)
        rows = await conn.fetch(
            """
            SELECT
                ci.content_id,
                ci.title,
                ci.clean_text,
                ci.original_url,
                ci.source_type,
                ci.published_at,
                ci.fetched_at,
                1 - (ce.embedding_vector <=> $1::vector) as similarity
            FROM content_items ci
            JOIN content_embeddings ce ON ci.content_id = ce.content_id
            JOIN sources s ON ci.source_id = s.source_id
            WHERE
                (s.user_id = $2 OR s.user_id IS NULL)
                AND ci.published_at >= $3
                AND 1 - (ce.embedding_vector <=> $1::vector) >= $4
            ORDER BY
                ce.embedding_vector <=> $1::vector,
                ci.published_at DESC
            LIMIT $5
            """,
            embedding_str,  # Pass as string, not list
            user_id,
            cutoff_date,
            min_similarity,
            max_items
        )
        
        return [
            {
                'content_id': str(row['content_id']),
                'title': row['title'],
                'clean_text': row['clean_text'],
                'original_url': row['original_url'],
                'source_type': row['source_type'],
                'published_at': row['published_at'],
                'fetched_at': row['fetched_at'],
                'similarity': float(row['similarity'])
            }
            for row in rows
        ]


async def get_user_goal_embedding(user_id: str) -> Optional[tuple]:
    """
    Get the active goal and its embedding for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Tuple of (goal_id, goal_text, embedding_vector) or None
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT goal_id, goal_text, embedding_vector
            FROM learning_goals
            WHERE user_id = $1 AND is_active = true
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id
        )
        
        if not row:
            return None
        
        # Handle embedding vector - convert from string to list if needed
        embedding_vector = row['embedding_vector']
        if isinstance(embedding_vector, str):
            # If it's a string representation, convert to list of floats
            import json
            try:
                embedding_vector = json.loads(embedding_vector)
            except:
                # Fallback: if string is corrupted, generate new embedding
                from app.rag.embedding_service import generate_goal_embedding
                embedding_vector = await generate_goal_embedding(row['goal_text'])
        
        return (
            str(row['goal_id']),
            row['goal_text'],
            embedding_vector
        )
