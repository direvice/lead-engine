"""Application configuration from environment."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_places_api_key: str = ""
    # Free-tier Places alternative (https://www.geoapify.com/) — use instead of / in addition to Google
    geoapify_api_key: str = ""
    gemini_api_key: str = ""
    yelp_api_key: str = ""
    ollama_host: str = "http://localhost:11434"
    facebook_access_token: str = ""

    gmail_address: str = ""
    gmail_app_password: str = ""
    digest_recipient: str = ""

    database_url: str = "sqlite:///./leads.db"
    screenshot_dir: str = "./screenshots"
    audio_dir: str = "./audio"
    default_location: str = "Geneva, IL"
    default_radius_miles: float = 15.0
    max_concurrent_scrapers: int = 5
    scan_schedule_enabled: bool = True

    # Includes this project’s deployed Vercel origins; override with CORS_ORIGINS in .env.
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "https://frontend-two-taupe-12.vercel.app,"
        "https://frontend-hi8q12wtt-linkboreds-projects.vercel.app"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def parse_cors_origins(raw: str) -> list[str]:
    return [o.strip() for o in raw.split(",") if o.strip()]
