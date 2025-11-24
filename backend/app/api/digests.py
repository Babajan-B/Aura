"""
API router for digests.
"""
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from datetime import datetime

from app.schemas.digests import (
    DigestResponse, 
    DigestHistoryResponse, 
    DigestItemResponse,
    DigestSummaryResponse
)
from app.db.database import get_db_pool, log_system_event
from app.services.email_service import send_digest_to_user


router = APIRouter()


@router.get("/current", response_model=Optional[DigestResponse])
async def get_current_digest(
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Get the current/latest digest for the user.
    
    Returns None if no digest exists.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get the latest digest for this user
            digest_row = await conn.fetchrow(
                """
                SELECT d.digest_id, d.user_id, d.goal_id, d.week_start_date, d.week_end_date,
                       d.generated_at, d.total_items, lg.goal_text
                FROM digests d
                JOIN learning_goals lg ON d.goal_id = lg.goal_id
                WHERE d.user_id = $1
                ORDER BY d.generated_at DESC
                LIMIT 1
                """,
                user_id
            )
            
            if not digest_row:
                return None
            
            # Get all digest items for this digest
            item_rows = await conn.fetch(
                """
                SELECT digest_item_id, digest_id, content_id, title, summary,
                       why_it_matters, relevance_score, source_type, link_url
                FROM digest_items
                WHERE digest_id = $1
                ORDER BY relevance_score DESC
                """,
                digest_row['digest_id']
            )
            
            items = [
                DigestItemResponse(
                    digest_item_id=str(row['digest_item_id']),
                    title=row['title'],
                    summary=row['summary'],
                    why_it_matters=row['why_it_matters'],
                    relevance_score=float(row['relevance_score']),
                    source_type=row['source_type'],
                    link_url=row['link_url']
                )
                for row in item_rows
            ]
            
            return DigestResponse(
                digest_id=str(digest_row['digest_id']),
                goal_text=digest_row['goal_text'],
                week_start_date=digest_row['week_start_date'],
                week_end_date=digest_row['week_end_date'],
                generated_at=digest_row['generated_at'],
                total_items=digest_row['total_items'],
                items=items
            )
    
    except Exception as e:
        await log_system_event("error", "api", f"Failed to fetch current digest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch current digest: {str(e)}")


@router.get("/history", response_model=DigestHistoryResponse)
async def get_digest_history(
    user_id: str = Header(default="test-user", alias="x-user-id"),
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0)
):
    """
    Get digest history for the user.
    
    Returns paginated list of past digests.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get total count
            total_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM digests
                WHERE user_id = $1
                """,
                user_id
            )
            
            # Get paginated digests
            digest_rows = await conn.fetch(
                """
                SELECT d.digest_id, d.week_start_date, d.week_end_date,
                       d.generated_at, d.total_items, lg.goal_text
                FROM digests d
                JOIN learning_goals lg ON d.goal_id = lg.goal_id
                WHERE d.user_id = $1
                ORDER BY d.generated_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset
            )
            
            digests = [
                DigestSummaryResponse(
                    digest_id=str(row['digest_id']),
                    goal_text=row['goal_text'],
                    week_start_date=row['week_start_date'],
                    week_end_date=row['week_end_date'],
                    generated_at=row['generated_at'],
                    total_items=row['total_items']
                )
                for row in digest_rows
            ]
            
            return DigestHistoryResponse(
                digests=digests,
                total_count=total_count or 0
            )
    
    except Exception as e:
        await log_system_event("error", "api", f"Failed to fetch digest history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch digest history: {str(e)}")


@router.get("/{digest_id}", response_model=DigestResponse)
async def get_specific_digest(
    digest_id: str,
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Get a specific digest by ID.
    
    Ensures the digest belongs to the requesting user.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get the digest
            digest_row = await conn.fetchrow(
                """
                SELECT d.digest_id, d.user_id, d.goal_id, d.week_start_date, d.week_end_date,
                       d.generated_at, d.total_items, lg.goal_text
                FROM digests d
                JOIN learning_goals lg ON d.goal_id = lg.goal_id
                WHERE d.digest_id = $1 AND d.user_id = $2
                """,
                digest_id,
                user_id
            )
            
            if not digest_row:
                raise HTTPException(status_code=404, detail="Digest not found")
            
            # Get all digest items
            item_rows = await conn.fetch(
                """
                SELECT digest_item_id, digest_id, content_id, title, summary,
                       why_it_matters, relevance_score, source_type, link_url
                FROM digest_items
                WHERE digest_id = $1
                ORDER BY relevance_score DESC
                """,
                digest_id
            )
            
            items = [
                DigestItemResponse(
                    digest_item_id=str(row['digest_item_id']),
                    title=row['title'],
                    summary=row['summary'],
                    why_it_matters=row['why_it_matters'],
                    relevance_score=float(row['relevance_score']),
                    source_type=row['source_type'],
                    link_url=row['link_url']
                )
                for row in item_rows
            ]
            
            return DigestResponse(
                digest_id=str(digest_row['digest_id']),
                goal_text=digest_row['goal_text'],
                week_start_date=digest_row['week_start_date'],
                week_end_date=digest_row['week_end_date'],
                generated_at=digest_row['generated_at'],
                total_items=digest_row['total_items'],
                items=items
            )
    
    except HTTPException:
        raise
    except Exception as e:
        await log_system_event("error", "api", f"Failed to fetch digest {digest_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch digest: {str(e)}")


@router.post("/{digest_id}/email", status_code=204)
async def send_digest_email(
    digest_id: str,
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Send a digest email to the user.
    
    Triggers email delivery for a specific digest.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Verify the digest belongs to the user
            digest_row = await conn.fetchrow(
                """
                SELECT digest_id, user_id
                FROM digests
                WHERE digest_id = $1 AND user_id = $2
                """,
                digest_id,
                user_id
            )
            
            if not digest_row:
                raise HTTPException(status_code=404, detail="Digest not found")
            
            # Send the email
            email_sent = await send_digest_to_user(user_id, digest_id)
            
            if email_sent:
                await log_system_event("info", "api", f"Email sent for digest {digest_id}")
                return None
            else:
                await log_system_event("error", "api", f"Failed to send email for digest {digest_id}")
                raise HTTPException(status_code=500, detail="Failed to send email")
    
    except HTTPException:
        raise
    except Exception as e:
        await log_system_event("error", "api", f"Failed to send digest email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send digest email: {str(e)}")
