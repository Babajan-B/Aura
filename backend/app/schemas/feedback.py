"""
Pydantic schemas for feedback API.
"""
from pydantic import BaseModel, Field
from enum import Enum


class FeedbackValue(str, Enum):
    """Feedback value options."""
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"


class FeedbackCreate(BaseModel):
    """Request schema for submitting feedback."""
    digest_item_id: str = Field(..., description="ID of the digest item")
    content_id: str = Field(..., description="ID of the content")
    feedback_value: FeedbackValue = Field(..., description="Feedback value")


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""
    feedback_id: str
    message: str = "Feedback recorded successfully"
