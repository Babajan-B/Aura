"""
Pydantic schemas for learning goals API.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty level options."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Frequency(str, Enum):
    """Frequency options."""
    NOW = "now"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"


class GoalCreate(BaseModel):
    """Request schema for creating a learning goal."""
    goal_text: str = Field(..., min_length=10, max_length=1000, description="Learning goal description")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level")
    frequency: Frequency = Field(..., description="Frequency of digests")


class GoalResponse(BaseModel):
    """Response schema for learning goal."""
    goal_id: str
    user_id: str
    goal_text: str
    difficulty_level: str
    frequency: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Response schema for user profile."""
    user_id: str
    digest_time: str
    email_notifications: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Request schema for updating user profile."""
    digest_time: Optional[str] = None
    email_notifications: Optional[bool] = None
