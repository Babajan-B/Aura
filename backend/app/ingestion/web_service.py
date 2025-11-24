"""
Website scraping service.
Fetches and extracts content from web pages.
"""
import httpx
from typing import Optional
from datetime import datetime
import uuid
from bs4 import BeautifulSoup

from app.db.database import get_db_pool, log_system_event
from app.ingestion.rss_service import clean_html


async def fetch_webpage_content(url: str, timeout: int = 30) -> Optional[dict]:
    """
    Fetch and extract main content from a webpage.
    
    Args:
        url: Webpage URL
        timeout: Request timeout in seconds
        
    Returns:
        Dict with title and cleaned text, or None if failed
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; AI-Learning-Coach/1.0; +http://example.com/bot)"
            }
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string or ""
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "header", "footer", "iframe", "noscript", "aside"]):
                element.decompose()
            
            # Try to find main content
            main_content = None
            
            # Look for common content containers
            for selector in ['article', 'main', '.content', '#content', '.post', '.entry']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # Fallback to body
            if not main_content:
                main_content = soup.body
            
            if not main_content:
                return None
            
            # Extract and clean text
            text = clean_html(str(main_content))
            
            return {
                'title': title.strip(),
                'text': text,
                'url': str(response.url)  # Final URL after redirects
            }
            
    except httpx.TimeoutException:
        await log_system_event("warning", "ingestion", f"Timeout fetching {url}")
        return None
    except httpx.HTTPStatusError as e:
        await log_system_event("warning", "ingestion", f"HTTP error {e.response.status_code} for {url}")
        return None
    except Exception as e:
        await log_system_event("error", "ingestion", f"Failed to fetch webpage {url}: {str(e)}")
        return None


async def ingest_website_sources():
    """
    Main website ingestion job.
    Fetches all active website sources and stores new content items.
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get all active website sources
        sources = await conn.fetch(
            """
            SELECT source_id, value
            FROM sources
            WHERE source_type = 'website' AND status = 'active'
            """
        )
        
        total_new_items = 0
        
        for source in sources:
            source_id = str(source['source_id'])
            url = source['value']
            
            try:
                content = await fetch_webpage_content(url)
                
                if not content:
                    continue
                
                # Skip if content is too short
                if len(content['text']) < 200:
                    continue
                
                # Check for duplicates
                exists = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM content_items
                        WHERE original_url = $1
                    )
                    """,
                    content['url']
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
                        content['title'] or url,
                        content['text'],
                        content['url'],
                        'website',
                        now,  # Use fetched time as published time
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
                await log_system_event("error", "ingestion", f"Error ingesting website {url}: {str(e)}")
                
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
            f"Website ingestion complete: {total_new_items} new items from {len(sources)} sources"
        )
        
        return total_new_items
