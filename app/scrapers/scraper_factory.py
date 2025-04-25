"""
Scraper factory for creating and managing job scrapers
"""
from typing import Dict, Type, List, Optional

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.linkedin_scraper import LinkedInScraper
from app.scrapers.indeed_scraper import IndeedScraper
from app.scrapers.google_jobs_scraper import GoogleJobsScraper
from app.scrapers.glassdoor_scraper import GlassdoorScraper
from app.scrapers.rozee_pk_scraper import RozeePkScraper


class ScraperFactory:
    """
    Factory class for creating and managing job scrapers
    """
    
    def __init__(self):
        self._scrapers: Dict[str, Type[BaseScraper]] = {
            "linkedin": LinkedInScraper,
            "indeed": IndeedScraper,
            "google_jobs": GoogleJobsScraper,
            "glassdoor": GlassdoorScraper,
            "rozee_pk": RozeePkScraper
        }
        
    def get_scraper(self, name: str) -> Optional[BaseScraper]:
        """
        Get a scraper instance by name
        
        Args:
            name: Name of the scraper
            
        Returns:
            Scraper instance or None if not found
        """
        scraper_class = self._scrapers.get(name.lower())
        if scraper_class:
            return scraper_class()
        return None
    
    def get_all_scrapers(self) -> List[BaseScraper]:
        """
        Get instances of all available scrapers
        
        Returns:
            List of scraper instances
        """
        return [scraper_class() for scraper_class in self._scrapers.values()]
    
    def get_available_scrapers(self) -> List[str]:
        """
        Get names of all available scrapers
        
        Returns:
            List of scraper names
        """
        return list(self._scrapers.keys())
