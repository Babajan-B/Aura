"""
API router for content sources.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime
import uuid

from app.schemas.sources import SourceCreate, SourceResponse, SourceListResponse
from app.db.database import get_db_pool, log_system_event


router = APIRouter()


@router.post("", response_model=SourceResponse, status_code=201)
async def add_content_source(
    source_data: SourceCreate,
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Add a new content source for the user.
    
    Supports RSS, YouTube, Reddit, X/Twitter, and website sources.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            source_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            await conn.execute(
                """
                INSERT INTO sources 
                (source_id, user_id, source_type, value, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                source_id,
                user_id,
                source_data.source_type.value,
                source_data.value,
                source_data.status.value,
                now
            )
            
            await log_system_event(
                "info", 
                "api", 
                f"Added {source_data.source_type.value} source for user {user_id}"
            )
            
            return SourceResponse(
                source_id=source_id,
                user_id=user_id,
                source_type=source_data.source_type.value,
                value=source_data.value,
                status=source_data.status.value,
                last_fetched_at=None,
                created_at=now
            )
    
    except Exception as e:
        await log_system_event("error", "api", f"Failed to add source: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add content source: {str(e)}")


@router.get("", response_model=SourceListResponse)
async def list_user_sources(
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    List all content sources for the current user.
    
    Includes both user-specific sources and global default sources (user_id = NULL).
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT source_id, user_id, source_type, value, status, last_fetched_at, created_at
                FROM sources
                WHERE user_id = $1 OR user_id IS NULL
                ORDER BY created_at DESC
                """,
                user_id
            )
            
            sources = [
                SourceResponse(
                    source_id=str(row['source_id']),
                    user_id=str(row['user_id']) if row['user_id'] else None,
                    source_type=row['source_type'],
                    value=row['value'],
                    status=row['status'],
                    last_fetched_at=row['last_fetched_at'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
            
            return SourceListResponse(sources=sources)
    
    except Exception as e:
        await log_system_event("error", "api", f"Failed to list sources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list sources: {str(e)}")
