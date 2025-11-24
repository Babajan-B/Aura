"""
Summarization service using Gemini.
Generates summaries and "why this matters" statements for content items.
"""
import google.generativeai as genai
from typing import Dict, Optional, List

from app.core.config import get_settings
from app.rag.internal_retrieval import get_rag_rules_for_summarization
from app.db.database import log_system_event


_gemini_configured = False


def configure_gemini():
    """Configure Gemini API."""
    global _gemini_configured
    if not _gemini_configured:
        settings = get_settings()
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        genai.configure(api_key=settings.google_api_key)
        _gemini_configured = True


async def summarize_content(
    title: str,
    content_text: str,
    goal_text: str,
    max_content_length: int = 8000
) -> Dict[str, str]:
    """
    Generate summary and "why this matters" for a content item.
    
    Args:
        title: Content title
        content_text: Content text
        goal_text: User's learning goal
        max_content_length: Maximum content length to process
        
    Returns:
        Dict with 'summary' and 'why_it_matters' keys
    """
    try:
        configure_gemini()
        
        # Truncate content if too long
        if len(content_text) > max_content_length:
            content_text = content_text[:max_content_length] + "..."
        
        # Get RAG rules for context
        rag_context = await get_rag_rules_for_summarization()
        
        # Create prompt
        prompt = f"""
{rag_context}

USER'S LEARNING GOAL:
{goal_text}

CONTENT TO SUMMARIZE:
Title: {title}
Content: {content_text}

TASK:
1. Write a 2-4 sentence summary of this content. Focus on facts, key findings, and actionable insights. No speculation.
2. Write exactly one sentence explaining "why this matters" for the user's learning goal. Be specific - link the content to their goal directly.

FORMAT YOUR RESPONSE EXACTLY AS:
SUMMARY: [your 2-4 sentence summary]
WHY_IT_MATTERS: [your one sentence explanation]
"""
        
        # Generate with Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Parse response
        text = response.text.strip()
        
        summary = ""
        why_it_matters = ""
        
        for line in text.split('\n'):
            if line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
            elif line.startswith('WHY_IT_MATTERS:'):
                why_it_matters = line.replace('WHY_IT_MATTERS:', '').strip()
        
        # Fallback parsing if format wasn't followed
        if not summary or not why_it_matters:
            parts = text.split('\n\n', 1)
            if len(parts) >= 2:
                summary = parts[0].strip()
                why_it_matters = parts[1].strip()
            else:
                summary = text[:500]
                why_it_matters = "This content is relevant to your learning goal."
        
        return {
            'summary': summary,
            'why_it_matters': why_it_matters
        }
        
    except Exception as e:
        await log_system_event(
            "error",
            "rag",
            f"Failed to summarize content: {str(e)}"
        )
        
        # Return fallback
        return {
            'summary': f"{title}. {content_text[:300]}..." if len(content_text) > 300 else content_text,
            'why_it_matters': "This content relates to your AI learning goal."
        }


async def batch_summarize_content(
    content_items: List[Dict],
    goal_text: str
) -> List[Dict]:
    """
    Generate summaries for multiple content items.
    
    Args:
        content_items: List of content items
        goal_text: User's learning goal
        
    Returns:
        Content items with added 'summary' and 'why_it_matters' fields
    """
    for item in content_items:
        result = await summarize_content(
            item['title'],
            item['clean_text'],
            goal_text
        )
        
        item['summary'] = result['summary']
        item['why_it_matters'] = result['why_it_matters']
    
    return content_items
