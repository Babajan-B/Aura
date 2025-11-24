"""
API router for learning goals.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime
import uuid

from app.schemas.goals import GoalCreate, GoalResponse, UserProfileResponse, UserProfileUpdate
from app.db.database import get_db_pool, log_system_event
from app.rag.embedding_service import generate_goal_embedding
from app.rag.digest_service import generate_digest_for_user


router = APIRouter()


# For MVP, we'll use a header-based user_id
# In production, this would come from JWT token/Supabase auth
async def get_current_user_id(x_user_id: Optional[str] = Header(default="test-user")) -> str:
    """Extract user ID from header. For MVP only."""
    return x_user_id


@router.post("", response_model=GoalResponse, status_code=201)
async def create_learning_goal(
    goal_data: GoalCreate,
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Create a new learning goal.
    
    - Deactivates any existing active goals for the user
    - Generates embedding for the goal text
    - Stores the goal in the database
    """
    try:
        pool = await get_db_pool()
        
        # Generate embedding for the goal
        embedding = await generate_goal_embedding(goal_data.goal_text)
        
        async with pool.acquire() as conn:
            # Deactivate all existing goals for this user
            await conn.execute(
                """
                UPDATE learning_goals 
                SET is_active = false 
                WHERE user_id = $1 AND is_active = true
                """,
                user_id
            )
            
            # Create new goal
            goal_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Convert embedding list to pgvector format string
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            await conn.execute(
                """
                INSERT INTO learning_goals 
                (goal_id, user_id, goal_text, difficulty_level, frequency, is_active, created_at, embedding_vector)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector)
                """,
                goal_id,
                user_id,
                goal_data.goal_text,
                goal_data.difficulty_level.value,
                goal_data.frequency.value,
                True,
                now,
                embedding_str
            )
            
            await log_system_event("info", "api", f"Created learning goal for user {user_id}")
            
            # If frequency is 'now', generate digest immediately
            if goal_data.frequency.value == 'now':
                await log_system_event("info", "api", f"Frequency set to 'now', generating immediate digest for user {user_id}")
                digest_id = await generate_digest_for_user(user_id)
                if digest_id:
                    await log_system_event("info", "api", f"Immediate digest generated: {digest_id} for user {user_id}")
                else:
                    await log_system_event("warning", "api", f"Failed to generate immediate digest for user {user_id}")
            
            return GoalResponse(
                goal_id=goal_id,
                user_id=user_id,
                goal_text=goal_data.goal_text,
                difficulty_level=goal_data.difficulty_level.value,
                frequency=goal_data.frequency.value,
                is_active=True,
                created_at=now
            )
    
    except Exception as e:
        await log_system_event("error", "api", f"Failed to create goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create learning goal: {str(e)}")


@router.get("/active", response_model=Optional[GoalResponse])
async def get_active_goal(
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Get the active learning goal for the current user.
    
    Returns None if no active goal exists.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT goal_id, user_id, goal_text, difficulty_level, frequency, is_active, created_at
                FROM learning_goals
                WHERE user_id = $1 AND is_active = true
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id
            )
            
            if not row:
                return None
            
            return GoalResponse(
                goal_id=str(row['goal_id']),
                user_id=str(row['user_id']),
                goal_text=row['goal_text'],
                difficulty_level=row['difficulty_level'],
                frequency=row['frequency'],
                is_active=row['is_active'],
                created_at=row['created_at']
            )
    
    except Exception as e:
        await log_system_event("error", "api", f"Failed to fetch active goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch active goal: {str(e)}")


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Get user profile settings.
    
    Returns digest time and email notification preferences.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get or create user profile
            row = await conn.fetchrow(
                """
                SELECT user_id, digest_time, email_notifications, created_at, updated_at
                FROM user_profiles
                WHERE user_id = $1
                """,
                user_id
            )
            
            if not row:
                # Create default profile if it doesn't exist
                await conn.execute(
                    """
                    INSERT INTO user_profiles (user_id, digest_time, email_notifications)
                    VALUES ($1, '08:00:00', true)
                    """,
                    user_id
                )
                
                row = await conn.fetchrow(
                    """
                    SELECT user_id, digest_time, email_notifications, created_at, updated_at
                    FROM user_profiles
                    WHERE user_id = $1
                    """,
                    user_id
                )
            
            return UserProfileResponse(
                user_id=str(row['user_id']),
                digest_time=str(row['digest_time']),
                email_notifications=row['email_notifications'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    except Exception as e:
        await log_system_event("error", "api", f"Failed to fetch user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user profile: {str(e)}")


@router.patch("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    user_id: str = Header(default="test-user", alias="x-user-id")
):
    """
    Update user profile settings.
    
    Allows updating digest time and email notification preferences.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Build update query dynamically based on provided fields
            updates = []
            values = []
            
            if profile_data.digest_time is not None:
                updates.append("digest_time = $%d" % (len(values) + 1))
                values.append(profile_data.digest_time)
            
            if profile_data.email_notifications is not None:
                updates.append("email_notifications = $%d" % (len(values) + 1))
                values.append(profile_data.email_notifications)
            
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            # Add updated_at and user_id to values
            values.append(user_id)
            
            # Execute update
            await conn.execute(
                f"""
                UPDATE user_profiles
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE user_id = ${len(values)}
                """,
                *values
            )
            
            # Return updated profile
            row = await conn.fetchrow(
                """
                SELECT user_id, digest_time, email_notifications, created_at, updated_at
                FROM user_profiles
                WHERE user_id = $1
                """,
                user_id
            )
            
            await log_system_event("info", "api", f"Updated user profile for {user_id}")
            
            return UserProfileResponse(
                user_id=str(row['user_id']),
                digest_time=str(row['digest_time']),
                email_notifications=row['email_notifications'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    except Exception as e:
        await log_system_event("error", "api", f"Failed to update user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")
