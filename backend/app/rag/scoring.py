"""
Content scoring and ranking module.
Scores content items based on multiple factors following masterRAG.md rules.
"""
from typing import List, Dict
from datetime import datetime, timedelta
import re

from app.db.database import get_db_pool


def calculate_keyword_score(content_text: str, title: str, goal_text: str, max_score: float = 0.2) -> float:
    """
    Calculate keyword alignment score.
    
    Args:
        content_text: Content text
        title: Content title
        goal_text: User's learning goal text
        max_score: Maximum score for this component (0.2 per masterRAG.md)
        
    Returns:
        Keyword score (0.0 to max_score)
    """
    # Extract keywords from goal (simple approach: split and lowercase)
    goal_keywords = set(re.findall(r'\b\w+\b', goal_text.lower()))
    
    # Remove common stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'}
    goal_keywords = goal_keywords - stopwords
    
    if not goal_keywords:
        return 0.0
    
    # Check title and content for keyword matches
    combined_text = f"{title} {content_text}".lower()
    
    matches = sum(1 for keyword in goal_keywords if keyword in combined_text)
    match_ratio = matches / len(goal_keywords)
    
    return min(match_ratio * max_score, max_score)


def calculate_recency_score(published_at: datetime, max_score: float = 0.2) -> float:
    """
    Calculate recency bonus score.
    
    Args:
        published_at: Content publication date
        max_score: Maximum score for this component (0.2 per masterRAG.md)
        
    Returns:
        Recency score (0.0 to max_score)
    """
    from datetime import timezone
    now = datetime.now(timezone.utc)
    
    # Handle timezone-aware vs timezone-naive datetimes
    if published_at.tzinfo is None:
        # If published_at is naive, assume it's UTC
        published_at = published_at.replace(tzinfo=timezone.utc)
    
    age_days = (now - published_at).days
    
    # Linear decay over 14 days
    if age_days <= 0:
        return max_score
    elif age_days >= 14:
        return 0.0
    else:
        return max_score * (1 - (age_days / 14))


async def calculate_feedback_score(content_id: str, max_score: float = 0.1) -> float:
    """
    Calculate feedback adjustment score.
    
    Args:
        content_id: Content ID
        max_score: Maximum score for this component (0.1 per masterRAG.md)
        
    Returns:
        Feedback score (-max_score to +max_score)
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Count useful vs not useful feedback for this content
        row = await conn.fetchrow(
            """
            SELECT 
                COUNT(CASE WHEN feedback_value = 'useful' THEN 1 END) as useful_count,
                COUNT(CASE WHEN feedback_value = 'not_useful' THEN 1 END) as not_useful_count
            FROM feedback
            WHERE content_id = $1
            """,
            content_id
        )
        
        if not row:
            return 0.0
        
        useful = row['useful_count'] or 0
        not_useful = row['not_useful_count'] or 0
        total = useful + not_useful
        
        if total == 0:
            return 0.0
        
        # Calculate ratio: positive if more useful, negative if more not_useful
        ratio = (useful - not_useful) / total
        
        return ratio * max_score


async def score_content_items(
    content_items: List[Dict],
    goal_text: str
) -> List[Dict]:
    """
    Score and rank content items according to masterRAG.md scoring framework.
    
    Scoring components:
    - Semantic similarity: 0.0 to 0.5 (already calculated)
    - Keyword alignment: 0.0 to 0.2
    - Recency: 0.0 to 0.2
    - Feedback adjustment: -0.1 to +0.1
    
    Args:
        content_items: List of content items with similarity scores
        goal_text: User's learning goal text
        
    Returns:
        Scored and sorted list of content items
    """
    scored_items = []
    
    for item in content_items:
        # Get base similarity score (already 0.0 to 1.0, scale to 0.0 to 0.5)
        similarity_score = item['similarity'] * 0.5
        
        # Calculate other components
        keyword_score = calculate_keyword_score(
            item['clean_text'],
            item['title'],
            goal_text
        )
        
        recency_score = calculate_recency_score(item['published_at'])
        
        feedback_score = await calculate_feedback_score(item['content_id'])
        
        # Calculate final score
        final_score = (
            similarity_score +
            keyword_score +
            recency_score +
            feedback_score
        )
        
        # Add scores to item
        item['scores'] = {
            'similarity': similarity_score,
            'keyword': keyword_score,
            'recency': recency_score,
            'feedback': feedback_score,
            'final': final_score
        }
        
        scored_items.append(item)
    
    # Sort by final score (descending)
    scored_items.sort(key=lambda x: x['scores']['final'], reverse=True)
    
    return scored_items


async def select_top_items(
    scored_items: List[Dict],
    min_score: float = 0.4,
    max_items: int = 10
) -> List[Dict]:
    """
    Select top N items above minimum score threshold.
    
    Args:
        scored_items: Scored content items
        min_score: Minimum final score threshold
        max_items: Maximum number of items to select (10 per masterRAG.md)
        
    Returns:
        Filtered list of top items
    """
    # Filter by minimum score
    filtered = [item for item in scored_items if item['scores']['final'] >= min_score]
    
    # Take top max_items
    return filtered[:max_items]
