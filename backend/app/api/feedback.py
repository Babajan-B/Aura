"""
API router for feedback.
"""
from fastapi import APIRouter, HTTPException, Header
from datetime import datetime
import uuid

from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.db.database import get_db_pool, log_system_event


router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Submit feedback on a digest item.
    
    Records whether the user found the content useful or not useful.
    This will be used later to improve relevance scoring.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Verify the digest item exists and belongs to the user's digest
            item_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM digest_items di
                    JOIN digests d ON di.digest_id = d.digest_id
                    WHERE di.digest_item_id = $1 
                    AND d.user_id = $2
                )
                """,
                feedback_data.digest_item_id,
                user_id
            )
            
            if not item_exists:
                raise HTTPException(
                    status_code=404, 
                    detail="Digest item not found or does not belong to user"
                )
            
            # Create feedback record
            feedback_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            await conn.execute(
                """
                INSERT INTO feedback 
                (feedback_id, user_id, digest_item_id, content_id, feedback_value, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                feedback_id,
                user_id,
                feedback_data.digest_item_id,
                feedback_data.content_id,
                feedback_data.feedback_value.value,
                now
            )
            
            await log_system_event(
                "info",
                "api",
                f"User {user_id} submitted {feedback_data.feedback_value.value} feedback"
            )
            
            return FeedbackResponse(
                feedback_id=feedback_id,
                message="Feedback recorded successfully"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        await log_system_event("error", "api", f"Failed to submit feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")
