"""
Configuration settings for the Job Finder API
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings
    """
    # API settings
    API_TITLE: str = "Job Finder API"
    API_DESCRIPTION: str = "API for finding relevant jobs across multiple platforms"
    API_VERSION: str = "1.0.0"
    
    # Server settings
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"
    
    # Scraper settings
    SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "30"))
    
    # Relevance filtering settings
    MIN_RELEVANCE_SCORE: float = float(os.getenv("MIN_RELEVANCE_SCORE", "0.2"))
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

# Create settings instance
settings = Settings()
