"""
Manually generate a digest for testing.
This bypasses the weekly schedule and creates a digest immediately.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.rag.digest_service import generate_digest_for_user

async def main():
    user_id = "12345678-1234-1234-1234-123456789012"
    
    print("🔄 Manually generating digest...")
    print(f"   User ID: {user_id}")
    print("")
    
    digest_id = await generate_digest_for_user(user_id)
    
    if digest_id:
        print(f"✅ Digest generated successfully!")
        print(f"   Digest ID: {digest_id}")
        print("")
        print("📧 Check your logs to see if email was sent:")
        print("   tail -f /tmp/backend.log | grep -i email")
        print("")
        print("🌐 View in frontend:")
        print(f"   http://localhost:3000/digest")
    else:
        print("❌ Failed to generate digest")
        print("   Check that you have:")
        print("   - An active learning goal")
        print("   - Content sources added")
        print("   - Content ingested (wait for scheduler or run manually)")

if __name__ == "__main__":
    asyncio.run(main())
