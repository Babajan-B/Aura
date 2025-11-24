"""
YouTube content ingestion service.
Fetches video metadata from YouTube channels/playlists.
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from app.core.config import get_settings
from app.db.database import get_db_pool, log_system_event
from app.ingestion.rss_service import clean_html


async def fetch_youtube_videos(channel_id: Optional[str] = None, playlist_id: Optional[str] = None, max_results: int = 50) -> List[Dict]:
    """
    Fetch videos from a YouTube channel or playlist.
    
    Args:
        channel_id: YouTube channel ID
        playlist_id: YouTube playlist ID
        max_results: Maximum number of videos to fetch
        
    Returns:
        List of video metadata
    """
    settings = get_settings()
    api_key = settings.youtube_api_key
    
    if not api_key:
        await log_system_event("error", "ingestion", "YOUTUBE_API_KEY not configured")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            videos = []
            
            # If channel_id is provided, first get the uploads playlist
            if channel_id:
                channel_url = f"https://www.googleapis.com/youtube/v3/channels"
                channel_params = {
                    "key": api_key,
                    "id": channel_id,
                    "part": "contentDetails"
                }
                
                response = await client.get(channel_url, params=channel_params)
                response.raise_for_status()
                data = response.json()
                
                if data.get('items'):
                    playlist_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Fetch videos from playlist
            if playlist_id:
                playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems"
                params = {
                    "key": api_key,
                    "playlistId": playlist_id,
                    "part": "snippet",
                    "maxResults": min(max_results, 50)
                }
                
                response = await client.get(playlist_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('items', []):
                    snippet = item['snippet']
                    
                    # Parse published date
                    published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
                    
                    videos.append({
                        'title': snippet['title'],
                        'description': snippet['description'],
                        'video_id': snippet['resourceId']['videoId'],
                        'published_at': published_at
                    })
            
            return videos
            
    except Exception as e:
        await log_system_event("error", "ingestion", f"Failed to fetch YouTube videos: {str(e)}")
        return []


async def ingest_youtube_sources():
    """
    Main YouTube ingestion job.
    Fetches all active YouTube sources and stores new content items.
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get all active YouTube sources
        sources = await conn.fetch(
            """
            SELECT source_id, value
            FROM sources
            WHERE source_type = 'youtube' AND status = 'active'
            """
        )
        
        total_new_items = 0
        
        for source in sources:
            source_id = str(source['source_id'])
            value = source['value']  # Could be channel ID or playlist ID
            
            try:
                # Determine if it's a channel or playlist ID
                # For simplicity, assume format: "channel:UC..." or "playlist:PL..."
                videos = []
                if value.startswith('channel:'):
                    channel_id = value.replace('channel:', '')
                    videos = await fetch_youtube_videos(channel_id=channel_id)
                elif value.startswith('playlist:'):
                    playlist_id = value.replace('playlist:', '')
                    videos = await fetch_youtube_videos(playlist_id=playlist_id)
                else:
                    # Try as channel ID by default
                    videos = await fetch_youtube_videos(channel_id=value)
                
                for video in videos:
                    # Create content text from title + description
                    clean_text = f"{video['title']}. {clean_html(video['description'])}"
                    
                    # Skip if content is too short
                    if len(clean_text) < 50:
                        continue
                    
                    # Create URL
                    video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
                    
                    # Check for duplicates
                    exists = await conn.fetchval(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM content_items
                            WHERE original_url = $1
                        )
                        """,
                        video_url
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
                            video['title'],
                            clean_text,
                            video_url,
                            'youtube',
                            video['published_at'],
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
                await log_system_event("error", "ingestion", f"Error ingesting YouTube source {value}: {str(e)}")
                
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
            f"YouTube ingestion complete: {total_new_items} new items from {len(sources)} sources"
        )
        
        return total_new_items
