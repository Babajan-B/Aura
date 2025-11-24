"""
RSS feed ingestion service.
Fetches and processes RSS feeds, stores content items.
"""
import feedparser
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
import uuid
from bs4 import BeautifulSoup

from app.db.database import get_db_pool, log_system_event
from app.core.config import get_settings


async def seed_default_rss_feeds():
    """
    Seed default RSS feed sources from configuration.
    Only adds feeds that don't already exist.
    """
    # Default RSS feeds from rss.md
    default_feeds = [
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/category/business/latest/rss",
        "https://www.technologyreview.com/feed/",
        "https://techcrunch.com/feed/",
        "https://openai.com/blog/rss.xml",
        "https://huggingface.co/blog/feed.xml",
        "https://machinelearningmastery.com/feed/",
        "https://distill.pub/rss.xml",
        "https://paperswithcode.com/feeds/latest.xml",
        "https://towardsdatescience.com/feed",
        "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",
        "https://hai.stanford.edu/news/rss.xml",
        "https://thegradient.pub/rss/",
        "https://jack-clark.net/feed/",
        "https://lastweekin.ai/feed",
        "https://news.ycombinator.com/rss",
        "https://lobste.rs/rss",
        "https://lobste.rs/t/ai.rss",
        "https://lobste.rs/t/ml.rss",
        "http://rss.slashdot.org/Slashdot/slashdotMain",
        "https://www.producthunt.com/feed",
        "https://blog.google/technology/ai/rss/",
        "https://blogs.microsoft.com/ai/feed/",
        "https://aws.amazon.com/blogs/machine-learning/feed/",
        "http://bair.berkeley.edu/blog/feed.xml",
        "https://aitrends.com/feed/",
        "https://www.unite.ai/feed/",
        "https://www.marktechpost.com/feed/",
        "https://www.analyticsvidhya.com/feed/",
        "https://www.artificialintelligence-news.com/feed/",
        "https://www.kdnuggets.com/feed",
        "https://www.oreilly.com/radar/topics/ai-ml/feed/",
        "https://www.therundown.ai/feed",
        "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml"
    ]
    
    pool = await get_db_pool()
    inserted_count = 0
    
    async with pool.acquire() as conn:
        for feed_url in default_feeds:
            # Check if this feed already exists
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM sources 
                    WHERE value = $1 AND source_type = 'rss'
                )
                """,
                feed_url
            )
            
            if not exists:
                source_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO sources 
                    (source_id, user_id, source_type, value, status, created_at)
                    VALUES ($1, NULL, 'rss', $2, 'active', $3)
                    """,
                    source_id,
                    feed_url,
                    datetime.utcnow()
                )
                inserted_count += 1
    
    await log_system_event(
        "info",
        "ingestion",
        f"Seeded {inserted_count} default RSS feeds"
    )
    
    return inserted_count


def clean_html(html_text: str) -> str:
    """
    Clean HTML content, removing tags and extracting text.
    
    Args:
        html_text: Raw HTML text
        
    Returns:
        Cleaned plain text
    """
    if not html_text:
        return ""
    
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "iframe", "noscript"]):
        script.decompose()
    
    # Get text
    text = soup.get_text(separator=' ', strip=True)
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def generate_content_hash(url: str, title: str) -> str:
    """
    Generate a unique hash for content deduplication.
    
    Args:
        url: Content URL
        title: Content title
        
    Returns:
        MD5 hash string
    """
    content = f"{url}|{title}".encode('utf-8')
    return hashlib.md5(content).hexdigest()


async def fetch_rss_feed(feed_url: str, max_items: int = 50) -> List[Dict]:
    """
    Fetch and parse an RSS feed.
    
    Args:
        feed_url: RSS feed URL
        max_items: Maximum number of items to return
        
    Returns:
        List of feed items with title, description, link, published date
    """
    try:
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:  # Feed parsing error
            await log_system_event(
                "warning",
                "ingestion",
                f"RSS feed parsing warning for {feed_url}: {feed.bozo_exception}"
            )
        
        items = []
        for entry in feed.entries[:max_items]:
            # Extract content
            title = entry.get('title', '')
            
            # Try multiple fields for content
            description = (
                entry.get('description', '') or 
                entry.get('summary', '') or 
                entry.get('content', [{}])[0].get('value', '')
            )
            
            link = entry.get('link', '')
            
            # Parse published date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except:
                    pass
            
            if not published_at:
                published_at = datetime.utcnow()
            
            items.append({
                'title': title,
                'description': description,
                'link': link,
                'published_at': published_at
            })
        
        return items
        
    except Exception as e:
        await log_system_event(
            "error",
            "ingestion",
            f"Failed to fetch RSS feed {feed_url}: {str(e)}"
        )
        return []


async def ingest_rss_feeds():
    """
    Main RSS ingestion job.
    Fetches all active RSS sources and stores new content items.
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get all active RSS sources
        sources = await conn.fetch(
            """
            SELECT source_id, value
            FROM sources
            WHERE source_type = 'rss' AND status = 'active'
            """
        )
        
        total_new_items = 0
        
        for source in sources:
            source_id = str(source['source_id'])
            feed_url = source['value']
            
            try:
                # Fetch feed items
                items = await fetch_rss_feed(feed_url)
                
                for item in items:
                    # Clean the description
                    clean_text = clean_html(item['description'])
                    
                    # Skip if content is too short
                    if len(clean_text) < 100:
                        continue
                    
                    # Check for duplicates
                    content_hash = generate_content_hash(item['link'], item['title'])
                    
                    exists = await conn.fetchval(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM content_items
                            WHERE original_url = $1
                        )
                        """,
                        item['link']
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
                            item['title'],
                            clean_text,
                            item['link'],
                            'rss',
                            item['published_at'],
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
                await log_system_event(
                    "error",
                    "ingestion",
                    f"Error ingesting RSS feed {feed_url}: {str(e)}"
                )
                
                # Update source status to error
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
            f"RSS ingestion complete: {total_new_items} new items from {len(sources)} feeds"
        )
        
        return total_new_items
