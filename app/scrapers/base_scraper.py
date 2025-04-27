"""
Base scraper class for job platforms
"""
import abc
import asyncio
import logging
import random
from typing import List, Dict, Any, Optional, Union, Callable

import httpx
from bs4 import BeautifulSoup

from app.models.job import Job


class BaseScraper(abc.ABC):
    """
    Abstract base class for all job scrapers with enhanced robustness
    """
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(self.name)
        
        # Create a new client for each scraper instance
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": random.choice(self.USER_AGENTS)}
        )
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
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
    
    async def _make_request(self, method: str, url: str, 
                          params: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None,
                          json_data: Optional[Dict[str, Any]] = None,
                          retries: int = 3) -> Union[Dict[str, Any], str]:
        """
        Make an HTTP request with retry logic and rotating user agents
        """
        combined_headers = {
            "User-Agent": random.choice(self.USER_AGENTS)
        }
        if headers:
            combined_headers.update(headers)
            
        for attempt in range(retries):
            try:
                # Add random delay to avoid rate limiting
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
                if method.lower() == "get":
                    response = await self.client.get(url, params=params, headers=combined_headers)
                elif method.lower() == "post":
                    response = await self.client.post(url, params=params, headers=combined_headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                if "application/json" in response.headers.get("Content-Type", ""):
                    return response.json()
                return response.text
                
            except httpx.HTTPStatusError as e:
                self.logger.error(f"HTTP error {e.response.status_code} on attempt {attempt+1}: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
            except httpx.RequestError as e:
                self.logger.error(f"Request error on attempt {attempt+1}: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    
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

    async def get_mock_jobs(self, position: str, location: Optional[str] = None, 
                        experience: Optional[str] = None, job_nature: Optional[str] = None) -> List[Job]:
        """
        Generate mock jobs when real scraping fails
        
        Args:
            position: Job title or position
            location: Job location
            experience: Required experience
            job_nature: Job nature
            
        Returns:
            List of mock Job objects
        """
        self.logger.warning(f"Falling back to mock data for {self.name}")
        
        # Create platform-specific mock jobs
        jobs = []
        source = self.name.replace("Scraper", "")
        
        # Each platform should have 3 mock jobs with different titles and details
        job_titles = [
            f"{position} Engineer", 
            f"Senior {position}", 
            f"{position} Developer"
        ]
        
        companies = [
            f"{source} Solutions Inc.", 
            f"Global {source} Technologies", 
            f"Tech {source} Partners"
        ]
        
        for i in range(3):
            # Make sure job nature matches the requested one if specified
            job_nature_value = job_nature or ["Remote", "Onsite", "Hybrid"][i % 3]
            
            jobs.append(Job(
                job_title=job_titles[i],
                company=companies[i],
                experience=experience or "Not specified",
                jobNature=job_nature_value,  # Use requested job nature
                location=location or "Any Location",
                salary="Competitive",
                apply_link=f"https://example.com/{source.lower()}/jobs/{i}",
                description=f"This is a mock {job_titles[i]} position created as a fallback because real scraping failed.",
                source=source
            ))
        
        # Standardize job nature for all jobs
        for job in jobs:
            job.jobNature = self.standardize_job_nature(job)
        
        return jobs

    def standardize_job_nature(self, job: Job) -> None:
        """
        Standardize job nature based on title and description
        """
        # First, check job title as it's the most reliable indicator
        title_lower = job.job_title.lower() if job.job_title else ""
        
        # The keyword checks to identify job nature from title
        remote_keywords = ["remote", "work from home", "wfh", "virtual"]
        hybrid_keywords = ["hybrid", "flexible", "part remote"]
        onsite_keywords = ["onsite", "on-site", "in office", "on location", "in-person"]
        
        # Check title first - it's usually most explicitly stated there
        if any(keyword in title_lower for keyword in remote_keywords):
            job.jobNature = "Remote"
        elif any(keyword in title_lower for keyword in hybrid_keywords):
            job.jobNature = "Hybrid"
        elif any(keyword in title_lower for keyword in onsite_keywords):
            job.jobNature = "Onsite"
        # If not explicitly in title, check job nature field
        elif job.jobNature:
            nature_lower = job.jobNature.lower()
            if any(keyword in nature_lower for keyword in remote_keywords):
                job.jobNature = "Remote"
            elif any(keyword in nature_lower for keyword in hybrid_keywords):
                job.jobNature = "Hybrid"
            elif any(keyword in nature_lower for keyword in onsite_keywords):
                job.jobNature = "Onsite"
        # If still not determined, check description as last resort
        elif job.description:
            desc_lower = job.description.lower()
            if any(keyword in desc_lower for keyword in remote_keywords):
                job.jobNature = "Remote"
            elif any(keyword in desc_lower for keyword in hybrid_keywords):
                job.jobNature = "Hybrid"
            elif any(keyword in desc_lower for keyword in onsite_keywords):
                job.jobNature = "Onsite"
            else:
                job.jobNature = "Not specified"
        else:
            job.jobNature = "Not specified"

    async def retry_with_backup_strategies(self, scraping_func, *args, **kwargs):
        """
        Try multiple scraping strategies before giving up
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add random delay between attempts
                if attempt > 0:
                    await asyncio.sleep(random.uniform(1.0, 3.0))
                
                # Try the scraping function
                jobs = await scraping_func(*args, **kwargs)
                
                # If we got jobs, standardize them and return
                if jobs:
                    for job in jobs:
                        self.standardize_job_nature(job)
                    return jobs
                    
                self.logger.warning(f"Attempt {attempt + 1} returned no jobs in {self.__class__.__name__}")
                
            except Exception as e:
                self.logger.error(f"Error in {self.__class__.__name__} attempt {attempt + 1}: {e}")
                
                # On last attempt, try one final time with different user agent
                if attempt == max_retries - 1:
                    try:
                        self.client.headers["User-Agent"] = random.choice(self.USER_AGENTS)
                        jobs = await scraping_func(*args, **kwargs)
                        if jobs:
                            for job in jobs:
                                self.standardize_job_nature(job)
                            return jobs
                    except Exception as final_e:
                        self.logger.error(f"Final attempt failed: {final_e}")
        
        # If all attempts failed, return empty list
        return []
