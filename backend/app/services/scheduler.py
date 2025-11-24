"""
Scheduler service for periodic background jobs.
Uses APScheduler to run ingestion and embedding tasks.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.ingestion.rss_service import ingest_rss_feeds, seed_default_rss_feeds
from app.ingestion.youtube_service import ingest_youtube_sources
from app.ingestion.x_service import ingest_twitter_sources
from app.ingestion.web_service import ingest_website_sources
from app.ingestion.content_embedding_service import generate_content_embeddings
from app.rag.digest_service import generate_all_digests
from app.db.database import log_system_event


# Global scheduler instance
scheduler = None


async def run_all_ingestion_jobs():
    """
    Run all content ingestion jobs sequentially.
    """
    await log_system_event("info", "scheduler", "Starting all ingestion jobs")
    
    try:
        # Run all ingestion services
        rss_count = await ingest_rss_feeds()
        youtube_count = await ingest_youtube_sources()
        twitter_count = await ingest_twitter_sources()
        website_count = await ingest_website_sources()
        
        total_items = rss_count + youtube_count + twitter_count + website_count
        
        await log_system_event(
            "info",
            "scheduler",
            f"Ingestion jobs complete: {total_items} total new items"
        )
        
    except Exception as e:
        await log_system_event("error", "scheduler", f"Ingestion jobs failed: {str(e)}")


async def run_embedding_generation():
    """
    Run content embedding generation job.
    """
    await log_system_event("info", "scheduler", "Starting embedding generation")
    
    try:
        count = await generate_content_embeddings(batch_size=100, max_items=500)
        
        await log_system_event(
            "info",
            "scheduler",
            f"Embedding generation complete: {count} embeddings created"
        )
        
    except Exception as e:
        await log_system_event("error", "scheduler", f"Embedding generation failed: {str(e)}")


async def run_digest_generation():
    """
    Run weekly digest generation for all users.
    """
    await log_system_event("info", "scheduler", "Starting weekly digest generation")
    
    try:
        count = await generate_all_digests()
        
        await log_system_event(
            "info",
            "scheduler",
            f"Digest generation complete: {count} digests created"
        )
        
    except Exception as e:
        await log_system_event("error", "scheduler", f"Digest generation failed: {str(e)}")


async def run_initial_setup():
    """
    Run one-time initial setup tasks.
    """
    await log_system_event("info", "scheduler", "Running initial setup")
    
    try:
        # Seed default RSS feeds
        count = await seed_default_rss_feeds()
        await log_system_event("info", "scheduler", f"Seeded {count} default RSS feeds")
        
    except Exception as e:
        await log_system_event("error", "scheduler", f"Initial setup failed: {str(e)}")


def start_scheduler():
    """
    Initialize and start the APScheduler.
    """
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = AsyncIOScheduler()
    
    # Run initial setup on first start
    scheduler.add_job(
        run_initial_setup,
        trigger='date',  # Run once immediately
        id='initial_setup',
        replace_existing=True
    )
    
    # Schedule ingestion jobs to run every 12 hours
    scheduler.add_job(
        run_all_ingestion_jobs,
        trigger=IntervalTrigger(hours=12),
        id='ingestion_jobs',
        replace_existing=True,
        next_run_time=datetime.now()  # Run immediately on start
    )
    
    # Schedule embedding generation to run every 2 hours
    # (frequent enough to process new content quickly)
    scheduler.add_job(
        run_embedding_generation,
        trigger=IntervalTrigger(hours=2),
        id='embedding_generation',
        replace_existing=True,
        next_run_time=datetime.now()  # Run immediately on start
    )
    
    # Digest generation - runs every hour to check for users with matching digest times
    scheduler.add_job(
        run_digest_generation,
        trigger=IntervalTrigger(hours=1),
        id='digest_generation',
        replace_existing=True,
        next_run_time=datetime.now()  # Run immediately on start
    )
    
    scheduler.start()
    
    print("✓ Scheduler started with jobs:")
    print("  - Initial setup (one-time)")
    print("  - Content ingestion (every 12 hours)")
    print("  - Embedding generation (every 2 hours)")
    print("  - Weekly digest generation (Sundays, 6 AM)")
    
    return scheduler
    
    # Remove duplicate code
    return scheduler


def stop_scheduler():
    """
    Stop the scheduler gracefully.
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        print("✓ Scheduler stopped")


def get_scheduler_status():
    """
    Get current scheduler status and jobs.
    """
    if scheduler is None:
        return {"running": False, "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time.isoformat() if job.next_run_time else None
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": next_run,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs
    }
