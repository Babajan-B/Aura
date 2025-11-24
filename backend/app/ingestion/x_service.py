"""
X (Twitter) content ingestion service.
Fetches tweets from configured accounts using Twitter API v2.
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from app.core.config import get_settings
from app.db.database import get_db_pool, log_system_event


async def fetch_user_tweets(username: str, max_results: int = 100) -> List[Dict]:
    """
    Fetch recent tweets from a Twitter user.
    
    Args:
        username: Twitter username (without @)
        max_results: Maximum number of tweets to fetch
        
    Returns:
        List of tweet data
    """
    settings = get_settings()
    bearer_token = settings.twitter_bearer_token
    
    if not bearer_token:
        await log_system_event("error", "ingestion", "TWITTER_BEARER_TOKEN not configured")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            # First, get user ID from username
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            response = await client.get(user_url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            
            if 'data' not in user_data:
                await log_system_event("error", "ingestion", f"User {username} not found")
                return []
            
            user_id = user_data['data']['id']
            
            # Get tweets
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,text",
                "exclude": "retweets,replies"  # Only original tweets
            }
            
            response = await client.get(tweets_url, headers=headers, params=params)
            response.raise_for_status()
            tweets_data = response.json()
            
            tweets = []
            for tweet in tweets_data.get('data', []):
                created_at = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
                
                tweets.append({
                    'text': tweet['text'],
                    'tweet_id': tweet['id'],
                    'created_at': created_at,
                    'username': username
                })
            
            return tweets
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            await log_system_event("warning", "ingestion", "Twitter API rate limit exceeded")
        else:
            await log_system_event("error", "ingestion", f"Twitter API error: {str(e)}")
        return []
    except Exception as e:
        await log_system_event("error", "ingestion", f"Failed to fetch tweets: {str(e)}")
        return []


async def ingest_twitter_sources():
    """
    Main Twitter ingestion job.
    Fetches all active Twitter sources and stores new content items.
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get all active X/Twitter sources
        sources = await conn.fetch(
            """
            SELECT source_id, value
            FROM sources
            WHERE source_type = 'x_api' AND status = 'active'
            """
        )
        
        total_new_items = 0
        
        for source in sources:
            source_id = str(source['source_id'])
            username = source['value'].lstrip('@')  # Remove @ if present
            
            try:
                tweets = await fetch_user_tweets(username)
                
                for tweet in tweets:
                    # Skip very short tweets
                    if len(tweet['text']) < 30:
                        continue
                    
                    # Create URL
                    tweet_url = f"https://twitter.com/{username}/status/{tweet['tweet_id']}"
                    
                    # Check for duplicates
                    exists = await conn.fetchval(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM content_items
                            WHERE original_url = $1
                        )
                        """,
                        tweet_url
                    )
                    
                    if not exists:
                        content_id = str(uuid.uuid4())
                        now = datetime.utcnow()
                        
                        await conn.execute(
                            """
                            INSERT INTO content_items
                            (content_id, source_id, title, clean_text, original_url,
                             source_type, published_at, fetched_at, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            """,
                            content_id,
                            source_id,
                            f"Tweet from @{username}",
                            tweet['text'],
                            tweet_url,
                            'x_api',
                            tweet['created_at'],
                            now,
                            now
                        )
                        total_new_items += 1
                
                # Update last_fetched_at
                await conn.execute(
                    """
                    UPDATE sources
                    SET last_fetched_at = $1
                    WHERE source_id = $2
                    """,
                    datetime.utcnow(),
                    source_id
                )
                
            except Exception as e:
                await log_system_event("error", "ingestion", f"Error ingesting Twitter @{username}: {str(e)}")
                
                await conn.execute(
                    """
                    UPDATE sources
                    SET status = 'error'
                    WHERE source_id = $1
                    """,
                    source_id
                )
        
        await log_system_event(
            "info",
            "ingestion",
            f"Twitter ingestion complete: {total_new_items} new items from {len(sources)} sources"
        )
        
        return total_new_items
