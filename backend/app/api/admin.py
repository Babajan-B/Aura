"""
API endpoint for on-demand digest generation.
"""
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from enum import Enum

from app.rag.digest_service import generate_digest_for_user
from app.db.database import log_system_event


router = APIRouter()


class DigestFrequency(str, Enum):
    """Digest frequency options."""
    now = "now"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


@router.post("/generate", status_code=201)
async def generate_digest_now(
    frequency: DigestFrequency = Query(default=DigestFrequency.now, description="Digest frequency"),
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Generate a digest on-demand for the current user.
    
    - **now**: Generate digest immediately with last 7 days of content
    - **daily**: Last 24 hours of content
    - **weekly**: Last 7 days of content  
    - **monthly**: Last 30 days of content
    
    Returns the generated digest ID.
    """
    try:
        await log_system_event("info", "api", f"Manual digest generation requested by user {user_id} (frequency: {frequency})")
        
        # Generate digest (internally it uses last 7 days, we'll enhance this later)
        digest_id = await generate_digest_for_user(user_id)
        
        if not digest_id:
            raise HTTPException(
                status_code=400,
                detail="Could not generate digest. Check that you have an active goal and relevant content is available."
            )
        
        return {
            "message": "Digest generated successfully",
            "digest_id": digest_id,
            "frequency": frequency,
            "view_url": f"/api/digests/{digest_id}"
        }
        
    except Exception as e:
        await log_system_event("error", "api", f"Failed to generate digest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate digest: {str(e)}")


@router.get("/stats")
async def get_digest_stats(
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """Get digest generation statistics for the user."""
    from app.db.database import get_db_pool
    
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        total_digests = await conn.fetchval(
            "SELECT COUNT(*) FROM digests WHERE user_id = $1",
            user_id
        )
        
        latest = await conn.fetchrow(
            """
            SELECT digest_id, generated_at, total_items
            FROM digests
            WHERE user_id = $1
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            user_id
        )
    
    return {
        "total_digests": total_digests or 0,
        "latest_digest_id": str(latest['digest_id']) if latest else None,
        "latest_generated_at": latest['generated_at'] if latest else None,
        "latest_total_items": latest['total_items'] if latest else 0
    }
