"""
Pydantic schemas for digests API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date


class DigestItemResponse(BaseModel):
    """Response schema for a single digest item."""
    digest_item_id: str
    title: str
    summary: str
    why_it_matters: str
    relevance_score: float
    source_type: str
    link_url: str

    class Config:
        from_attributes = True


class DigestResponse(BaseModel):
    """Response schema for a complete digest."""
    digest_id: str
    goal_text: str
    week_start_date: date
    week_end_date: date
    generated_at: datetime
    total_items: int
    items: List[DigestItemResponse]

    class Config:
        from_attributes = True


class DigestSummaryResponse(BaseModel):
    """Response schema for digest summary (history)."""
    digest_id: str
    goal_text: str
    week_start_date: date
    week_end_date: date
    generated_at: datetime
    total_items: int

    class Config:
        from_attributes = True


class DigestHistoryResponse(BaseModel):
    """Response schema for digest history."""
    digests: List[DigestSummaryResponse]
    total_count: int
