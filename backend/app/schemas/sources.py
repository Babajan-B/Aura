"""
Pydantic schemas for content sources API.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Content source types."""
    RSS = "rss"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    X_API = "x_api"
    WEBSITE = "website"


class SourceStatus(str, Enum):
    """Source status options."""
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class SourceCreate(BaseModel):
    """Request schema for adding a content source."""
    source_type: SourceType = Field(..., description="Type of content source")
    value: str = Field(..., min_length=1, max_length=500, description="URL, channel ID, handle, etc.")
    status: SourceStatus = Field(default=SourceStatus.ACTIVE, description="Source status")


class SourceResponse(BaseModel):
    """Response schema for a content source."""
    source_id: str
    user_id: Optional[str] = None  # None for global default sources
    source_type: str
    value: str
    status: str
    last_fetched_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SourceListResponse(BaseModel):
    """Response schema for listing sources."""
    sources: List[SourceResponse]
