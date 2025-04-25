"""
Base scraper class for job platforms
"""
import abc
from typing import List, Dict, Any, Optional

from app.models.job import Job


class BaseScraper(abc.ABC):
    """
    Abstract base class for all job scrapers
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abc.abstractmethod
    async def search_jobs(self, 
                    position: str,
                    location: Optional[str] = None,
                    experience: Optional[str] = None,
                    job_nature: Optional[str] = None,
                    **kwargs) -> List[Job]:
        """
        Search for jobs based on the provided criteria
        
        Args:
            position: Job title or position
            location: Job location
            experience: Required experience
            job_nature: Job nature (onsite, remote, hybrid)
            **kwargs: Additional search parameters
            
        Returns:
            List of Job objects
        """
        pass
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and newlines
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = " ".join(text.split())
        return text.strip()
