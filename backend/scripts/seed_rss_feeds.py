"""
Seed RSS feeds from config file into the database.
Run this script to add all RSS feeds to the sources table.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import get_db_pool
from app.core.config import get_settings
import uuid
from datetime import datetime


# All RSS feeds to seed
RSS_FEEDS = [
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
    "https://towardsdatascience.com/feed",
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
    "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
]


async def seed_rss_feeds():
    """Seed all RSS feeds into the database."""
    pool = await get_db_pool()
    
    added_count = 0
    existing_count = 0
    
    print(f"🌱 Seeding {len(RSS_FEEDS)} RSS feeds...")
    print("=" * 50)
    
    async with pool.acquire() as conn:
        for feed_url in RSS_FEEDS:
            # Check if feed already exists
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM sources
                    WHERE source_type = 'rss' AND value = $1
                )
                """,
                feed_url
            )
            
            if exists:
                existing_count += 1
                print(f"⏭️  Already exists: {feed_url}")
                continue
            
            # Insert new feed (global source, user_id = NULL)
            source_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            await conn.execute(
                """
                INSERT INTO sources
                (source_id, user_id, source_type, value, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                source_id,
                None,  # Global source
                'rss',
                feed_url,
                'active',
                now
            )
            
            added_count += 1
            print(f"✅ Added: {feed_url}")
    
    print("=" * 50)
    print(f"\n📊 Summary:")
    print(f"  ✅ Added: {added_count} new feeds")
    print(f"  ⏭️  Skipped: {existing_count} existing feeds")
    print(f"  📚 Total: {len(RSS_FEEDS)} feeds")
    print("\n✨ RSS feeds seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_rss_feeds())
