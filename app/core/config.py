"""
Configuration settings for the application
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings
    """
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # Relevance filtering
    MIN_RELEVANCE_SCORE: float = 0.2
    
    # API keys and credentials will be loaded from environment
    GOOGLE_API_KEY: str = ""
    
    # Allow any extra fields from environment variables
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"  # This allows extra fields from environment variables
    )

# Create settings instance
settings = Settings()
