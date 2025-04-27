"""
Configuration settings for the application
"""
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    # Relevance filtering settings
    MIN_RELEVANCE_SCORE: float = 0.2
    
    # API server settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings()
