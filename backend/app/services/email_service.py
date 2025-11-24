"""
Email service using MailerSend.
Generates and sends digest emails to users.
"""
from typing import List, Dict, Optional
from datetime import date
import httpx

from app.core.config import get_settings
from app.db.database import get_db_pool, log_system_event


def generate_digest_html(
    goal_text: str,
    week_start: date,
    week_end: date,
    items: List[Dict]
) -> str:
    """
    Generate HTML email template for digest.
    
    Args:
        goal_text: User's learning goal
        week_start: Week start date
        week_end: Week end date
        items: List of digest items
        
    Returns:
        HTML string
    """
    # Build items HTML
    items_html = ""
    for idx, item in enumerate(items, 1):
        items_html += f"""
        <div style="margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 4px;">
            <h3 style="margin: 0 0 10px 0; color: #212529;">
                {idx}. {item['title']}
            </h3>
            <p style="margin: 0 0 10px 0; color: #495057; line-height: 1.6;">
                {item['summary']}
            </p>
            <p style="margin: 0 0 15px 0; color: #007bff; font-style: italic;">
                <strong>Why this matters:</strong> {item['why_it_matters']}
            </p>
            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid #dee2e6;">
                <span style="font-size: 12px; color: #6c757d; text-transform: uppercase;">
                    {item['source_type']}
                </span>
                <a href="{item['link_url']}" style="color: #007bff; text-decoration: none; font-weight: 500;">
                    Read More →
                </a>
            </div>
        </div>
        """
    
    # Complete HTML template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Weekly AI Learning Digest</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 0 auto; background: white;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
                <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 600;">
                    AI Learning Coach
                </h1>
                <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                    Your Weekly Personalized Digest
                </p>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px 20px;">
                <!-- Week Range -->
                <div style="text-align: center; margin-bottom: 30px; padding: 15px; background: #e7f3ff; border-radius: 8px;">
                    <p style="margin: 0; color: #004085; font-size: 14px; font-weight: 500;">
                        {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}
                    </p>
                </div>
                
                <!-- Goal -->
                <div style="margin-bottom: 30px;">
                    <h2 style="margin: 0 0 10px 0; color: #212529; font-size: 20px;">Your Learning Goal</h2>
                    <p style="margin: 0; color: #495057; padding: 15px; background: #fff3cd; border-radius: 4px; line-height: 1.6;">
                        {goal_text}
                    </p>
                </div>
                
                <!-- Items -->
                <div style="margin-bottom: 30px;">
                    <h2 style="margin: 0 0 20px 0; color: #212529; font-size: 20px;">
                        This Week's Top Picks ({len(items)} items)
                    </h2>
                    {items_html}
                </div>
                
                <!-- Footer Message -->
                <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                    <p style="margin: 0 0 10px 0; color: #6c757d; font-size: 14px;">
                        These items were selected based on semantic relevance, keywords, recency, and your feedback.
                    </p>
                    <p style="margin: 0; color: #6c757d; font-size: 12px;">
                        Help us improve: Rate items as useful or not useful when you review them.
                    </p>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #343a40; padding: 20px; text-align: center;">
                <p style="margin: 0; color: #adb5bd; font-size: 12px;">
                    © 2024 AI Learning Coach. Powered by AI, personalized for you.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


async def send_digest_email(
    to_email: str,
    to_name: str,
    goal_text: str,
    week_start: date,
    week_end: date,
    items: List[Dict]
) -> bool:
    """
    Send digest email via MailerSend.
    
    Args:
        to_email: Recipient email
        to_name: Recipient name
        goal_text: User's learning goal
        week_start: Week start date
        week_end: Week end date
        items: List of digest items
        
    Returns:
        True if successful, False otherwise
    """
    settings = get_settings()
    
    if not settings.mailersend_api_key:
        await log_system_event("error", "email", "MailerSend API key not configured")
        return False
    
    try:
        # Generate HTML content
        html_content = generate_digest_html(goal_text, week_start, week_end, items)
        
        # Prepare MailerSend request
        url = "https://api.mailersend.com/v1/email"
        
        headers = {
            "Authorization": f"Bearer {settings.mailersend_api_key}",
            "Content-Type": "application/json"
        }
        
        subject = f"Your AI Learning Digest: {week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}"
        
        payload = {
            "from": {
                "email": settings.mailersend_from_email,
                "name": settings.mailersend_from_name or "AI Learning Coach"
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name
                }
            ],
            "subject": subject,
            "html": html_content,
            "text": f"Your weekly AI learning digest from {week_start} to {week_end}. {len(items)} curated items for your goal: {goal_text}"
        }
        
        # Add BCC to admin if configured
        if settings.mailersend_admin_email:
            payload["bcc"] = [
                {
                    "email": settings.mailersend_admin_email
                }
            ]
        
        # Send email
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
        await log_system_event(
            "info",
            "email",
            f"Digest email sent to {to_email}"
        )
        
        return True
        
    except httpx.HTTPStatusError as e:
        await log_system_event(
            "error",
            "email",
            f"MailerSend API error: {e.response.status_code} - {e.response.text}"
        )
        return False
    except Exception as e:
        await log_system_event("error", "email", f"Failed to send email: {str(e)}")
        return False


async def send_digest_to_user(user_id: str, digest_id: str) -> bool:
    """
    Send digest email to a specific user.
    Retrieves user info and digest data, then sends email.
    
    Args:
        user_id: User ID
        digest_id: Digest ID
        
    Returns:
        True if successful, False otherwise
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get user info
        user = await conn.fetchrow(
            "SELECT email, name FROM users WHERE user_id = $1",
            user_id
        )
        
        if not user:
            await log_system_event("error", "email", f"User {user_id} not found")
            return False
        
        # Get digest with items
        digest = await conn.fetchrow(
            """
            SELECT d.week_start_date, d.week_end_date, lg.goal_text
            FROM digests d
            JOIN learning_goals lg ON d.goal_id = lg.goal_id
            WHERE d.digest_id = $1
            """,
            digest_id
        )
        
        if not digest:
            await log_system_event("error", "email", f"Digest {digest_id} not found")
            return False
        
        # Get digest items
        items = await conn.fetch(
            """
            SELECT title, summary, why_it_matters, source_type, link_url
            FROM digest_items
            WHERE digest_id = $1
            ORDER BY relevance_score DESC
            """,
            digest_id
        )
        
        if not items:
            await log_system_event("warning", "email", f"Digest {digest_id} has no items")
            return False
        
        # Convert to dict format
        items_list = [dict(item) for item in items]
        
        # Send email
        return await send_digest_email(
            to_email=user['email'],
            to_name=user['name'] or "there",
            goal_text=digest['goal_text'],
            week_start=digest['week_start_date'],
            week_end=digest['week_end_date'],
            items=items_list
        )
