"""
Create a test user in the database with a valid UUID.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import get_db_pool
import uuid
from datetime import datetime


async def create_test_user():
    """Create a test user in the users table."""
    pool = await get_db_pool()
    
    # Use a consistent UUID for test user
    test_user_id = str(uuid.UUID('12345678-1234-1234-1234-123456789012'))
    test_email = "test@example.com"
    test_name = "Test User"
    
    print(f"🔧 Creating test user...")
    print(f"   User ID: {test_user_id}")
    print(f"   Email: {test_email}")
    print(f"   Name: {test_name}")
    
    async with pool.acquire() as conn:
        # Check if user already exists
        exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM users WHERE user_id = $1)",
            test_user_id
        )
        
        if exists:
            print(f"\n⏭️  Test user already exists!")
        else:
            # Create user
            now = datetime.utcnow()
            
            await conn.execute(
                """
                INSERT INTO users (user_id, email, name, created_at)
                VALUES ($1, $2, $3, $4)
                """,
                test_user_id,
                test_email,
                test_name,
                now
            )
            
            print(f"\n✅ Test user created successfully!")
        
        print(f"\n📝 Update your .env.local file:")
        print(f"   NEXT_PUBLIC_USER_ID={test_user_id}")
        print(f"\n✨ Done!")


if __name__ == "__main__":
    asyncio.run(create_test_user())
