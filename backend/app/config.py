"""
Application configuration management using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "DocuMind"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # MongoDB
    MONGODB_URL: str
    MONGODB_DATABASE: str = "documind"

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: float = 0.3

    # Storage
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 200

    # Allowed file types
    ALLOWED_PDF_MIMETYPES: List[str] = ["application/pdf"]
    ALLOWED_AUDIO_MIMETYPES: List[str] = ["audio/mpeg", "audio/wav", "audio/mp3", "audio/x-m4a"]
    ALLOWED_VIDEO_MIMETYPES: List[str] = ["video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo"]

    # JWT Auth
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
