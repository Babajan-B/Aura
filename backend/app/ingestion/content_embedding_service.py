"""
Content embedding generation service.
Processes content items without embeddings and generates vector embeddings.
"""
from typing import List
from datetime import datetime
import uuid

from app.db.database import get_db_pool, log_system_event
from app.rag.embedding_service import generate_content_embedding


async def generate_content_embeddings(batch_size: int = 50, max_items: int = 500):
    """
    Generate embeddings for content items that don't have embeddings yet.
    
    Args:
        batch_size: Number of items to process in one run
        max_items: Maximum total items to process
        
    Returns:
        Number of embeddings generated
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get content items without embeddings
        items = await conn.fetch(
            """
            SELECT ci.content_id, ci.title, ci.clean_text
            FROM content_items ci
            LEFT JOIN content_embeddings ce ON ci.content_id = ce.content_id
            WHERE ce.embedding_id IS NULL
            ORDER BY ci.created_at DESC
            LIMIT $1
            """,
            min(batch_size, max_items)
        )
        
        if not items:
            await log_system_event("info", "rag", "No content items need embeddings")
            return 0
        
        generated_count = 0
        
        for item in items:
            try:
                content_id = str(item['content_id'])
                
                # Combine title and text for embedding
                # Truncate if too long (Gemini has input limits)
                combined_text = f"{item['title']}. {item['clean_text']}"
                if len(combined_text) > 10000:
                    combined_text = combined_text[:10000]
                
                # Generate embedding
                embedding = await generate_content_embedding(combined_text)
                
                # Convert embedding list to pgvector format string
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                # Store embedding
                embedding_id = str(uuid.uuid4())
                now = datetime.utcnow()
                
                await conn.execute(
                    """
                    INSERT INTO content_embeddings
                    (embedding_id, content_id, embedding_vector, created_at)
                    VALUES ($1, $2, $3::vector, $4)
                    """,
                    embedding_id,
                    content_id,
                    embedding_str,
                    now
                )
                
                generated_count += 1
                
            except Exception as e:
                await log_system_event(
                    "error",
                    "rag",
                    f"Failed to generate embedding for content {item['content_id']}: {str(e)}"
                )
        
        await log_system_event(
            "info",
            "rag",
            f"Generated {generated_count} content embeddings"
        )
        
        return generated_count


async def get_content_embeddings_stats() -> dict:
    """
    Get statistics on content embeddings.
    
    Returns:
        Dict with embedding statistics
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        total_content = await conn.fetchval(
            "SELECT COUNT(*) FROM content_items"
        )
        
        total_embeddings = await conn.fetchval(
            "SELECT COUNT(*) FROM content_embeddings"
        )
        
        pending = total_content - total_embeddings if total_content and total_embeddings else 0
        
        return {
            "total_content_items": total_content or 0,
            "total_embeddings": total_embeddings or 0,
            "pending_embeddings": max(0, pending)
        }
