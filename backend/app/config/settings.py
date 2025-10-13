"""Application settings and configuration."""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql+psycopg://health:health@localhost:5432/health",
        description="PostgreSQL database URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for Celery"
    )
    
    # File storage
    files_bucket_path: str = Field(
        default=".bucket",
        description="Local file storage path"
    )
    
    # Gemini API
    gemini_api_key: str = Field(
        default="<YOUR_KEY_HERE>",
        description="Google Gemini API key"
    )
    gemini_model_vision: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model for vision tasks"
    )
    gemini_model_text: str = Field(
        default="gemini-2.0-flash", 
        description="Gemini model for text tasks"
    )
    
    # Application
    debug: bool = Field(default=False, description="Debug mode")
    offline_mode: bool = Field(default=False, description="Skip live API checks")
    
    # File upload limits
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes (10MB)")
    allowed_mime_types: list[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "application/pdf"],
        description="Allowed MIME types for uploads"
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
