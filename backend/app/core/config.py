"""
Configuration module for loading environment variables.
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys from rss.md
    twitter_bearer_token: str = ""
    mailersend_api_key: str = ""
    mailersend_from_email: str = ""
    mailersend_from_name: str = "AI Learning Coach"
    mailersend_admin_email: str = ""
    google_api_key: str = ""
    youtube_api_key: str = ""

    # Supabase Configuration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Backend/Frontend URLs
    backend_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"

    # RSS Feeds (comma-separated string, will be split into list)
    rss_feeds: str = ""

    # Database settings
    database_url: str = ""  # Constructed from Supabase URL if needed

    # Application settings
    app_name: str = "AI Learning Coach"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

    def get_rss_feeds_list(self) -> List[str]:
        """Parse RSS_FEEDS string into a list of URLs."""
        if not self.rss_feeds:
            return []
        return [feed.strip() for feed in self.rss_feeds.split(",") if feed.strip()]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()
