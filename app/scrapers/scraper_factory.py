"""
Scraper factory for creating and managing job scrapers
"""
import logging
from typing import Dict, Type, List, Optional
import random
import asyncio

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.linkedin_scraper import LinkedInScraper
from app.scrapers.indeed_scraper import IndeedScraper
from app.scrapers.google_jobs_scraper import GoogleJobsScraper
from app.scrapers.glassdoor_scraper import GlassdoorScraper
from app.scrapers.rozee_pk_scraper import RozeePkScraper
from app.scrapers.google_search_scraper import GoogleSearchScraper


class ScraperFactory:
    """
    Factory class for creating and managing job scrapers
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Use two variants for each platform - direct and Google Search based
        self._scrapers: Dict[str, Type[BaseScraper]] = {
            # Direct scrapers
            "linkedin": LinkedInScraper,
            "indeed": IndeedScraper,
            "google_jobs": GoogleJobsScraper,
            "glassdoor": GlassdoorScraper,
            "rozee_pk": RozeePkScraper,
            
            # Google Search based scrapers (fallbacks)
            "linkedin_google": lambda: GoogleSearchScraper(platform_name="LinkedIn"),
            "indeed_google": lambda: GoogleSearchScraper(platform_name="Indeed"),
            "glassdoor_google": lambda: GoogleSearchScraper(platform_name="Glassdoor"),
            "rozee_google": lambda: GoogleSearchScraper(platform_name="Rozee"),
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
            try:
                if callable(scraper_class) and not isinstance(scraper_class, type):
                    # For lambda functions
                    return scraper_class()
                else:
                    # For class types
                    return scraper_class()
            except Exception as e:
                self.logger.error(f"Error creating scraper {name}: {e}")
                return None
        return None
    
    def get_all_scrapers(self) -> List[BaseScraper]:
        """
        Get instances of all available scrapers
        """
        scrapers = []
        scraper_classes = [
            LinkedInScraper,
            IndeedScraper,
            GoogleJobsScraper,
            GlassdoorScraper,
            RozeePkScraper
        ]
        
        for scraper_class in scraper_classes:
            try:
                scraper = scraper_class()
                scrapers.append(scraper)
                self.logger.info(f"Successfully initialized {scraper_class.__name__}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {scraper_class.__name__}: {e}")
        
        if not scrapers:
            self.logger.error("No scrapers could be initialized!")
        
        return scrapers
    
    def get_available_scrapers(self) -> List[str]:
        """
        Get names of all available scrapers
        
        Returns:
            List of scraper names
        """
        return list(self._scrapers.keys())
    
    async def close_all_scrapers(self, scrapers: List[BaseScraper]) -> None:
        """
        Close all scraper instances to release resources
        
        Args:
            scrapers: List of scraper instances to close
        """
        for scraper in scrapers:
            try:
                await scraper.close()
            except Exception as e:
                self.logger.error(f"Error closing scraper {scraper.name}: {e}")

    async def _random_delay(self):
        """Add random delay to avoid rate limiting"""
        delay = random.uniform(1.0, 3.0)
        await asyncio.sleep(delay)

    def _get_random_user_agent(self):
        """Return a random user agent from a pool of common ones"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"
        ]
        return random.choice(user_agents)
