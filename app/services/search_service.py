"""
Service for searching jobs across multiple platforms
"""
import asyncio
import logging
from typing import List, Optional

from app.models.job import Job
from app.scrapers.scraper_factory import ScraperFactory

logger = logging.getLogger(__name__)

class SearchService:
    """
    Service for searching jobs across multiple platforms
    """
    
    def __init__(self):
        try:
            self.scraper_factory = ScraperFactory()
            logger.info("SearchService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SearchService: {e}")
            raise
        
    async def search_jobs(
        self,
        position: str,
        location: Optional[str] = None,
        experience: Optional[str] = None,
        job_nature: Optional[str] = None,
        platforms: Optional[List[str]] = None,
    ) -> List[Job]:
        """
        Search for jobs across multiple platforms
        
        Args:
            position: Job title or position
            location: Job location
            experience: Required experience
            job_nature: Job nature (onsite, remote, hybrid)
            platforms: List of platforms to search (default: all)
            
        Returns:
            List of Job objects
        """
        all_jobs = []
        
        try:
            # Get scrapers
            scrapers = self.scraper_factory.get_all_scrapers()
            if not scrapers:
                logger.error("No scrapers available")
                return []
            
            logger.info(f"Initialized {len(scrapers)} scrapers")
            
            # Create tasks for each scraper
            tasks = []
            for scraper in scrapers:
                task = asyncio.create_task(
                    self._safe_search_with_scraper(
                        scraper,
                        position=position,
                        location=location,
                        experience=experience,
                        job_nature=job_nature
                    )
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Scraper error: {result}")
                    continue
                if isinstance(result, list):
                    all_jobs.extend(result)
            
            logger.info(f"Found total of {len(all_jobs)} jobs")
            
            # Apply job nature filtering if specified
            if job_nature:
                filtered_jobs = self._filter_by_job_nature(all_jobs, job_nature)
                if len(filtered_jobs) >= 3:
                    logger.info(f"Filtered to {len(filtered_jobs)} jobs matching nature: {job_nature}")
                    all_jobs = filtered_jobs
            
            return all_jobs
            
        except Exception as e:
            logger.exception(f"Error in search_jobs: {e}")
            return []
    
    async def _safe_search_with_scraper(self, scraper, **kwargs) -> List[Job]:
        """Safely execute search with a single scraper"""
        try:
            logger.info(f"Searching with {scraper.__class__.__name__}")
            jobs = await scraper.search_jobs(**kwargs)
            if jobs:
                logger.info(f"Found {len(jobs)} jobs from {scraper.__class__.__name__}")
                # Standardize job nature for all jobs
                for job in jobs:
                    self.standardize_job_nature(job)
                return jobs
            return []
        except Exception as e:
            logger.error(f"Error with {scraper.__class__.__name__}: {e}")
            return []

    def standardize_job_nature(self, job: Job) -> None:
        """
        Standardize job nature based on title and description
        """
        if not hasattr(job, 'jobNature'):
            job.jobNature = "Not specified"
            return
            
        title_lower = job.job_title.lower() if job.job_title else ""
        nature_lower = job.jobNature.lower() if job.jobNature else ""
        desc_lower = job.description.lower() if job.description else ""
        
        # Keywords for job nature detection
        remote_keywords = ["remote", "work from home", "wfh", "virtual"]
        hybrid_keywords = ["hybrid", "flexible", "part remote"]
        onsite_keywords = ["onsite", "on-site", "in office", "on location", "in-person"]
        
        # Check title first (most reliable)
        if any(keyword in title_lower for keyword in remote_keywords):
            job.jobNature = "Remote"
        elif any(keyword in title_lower for keyword in hybrid_keywords):
            job.jobNature = "Hybrid"
        elif any(keyword in title_lower for keyword in onsite_keywords):
            job.jobNature = "Onsite"
        # Then check job nature field
        elif any(keyword in nature_lower for keyword in remote_keywords):
            job.jobNature = "Remote"
        elif any(keyword in nature_lower for keyword in hybrid_keywords):
            job.jobNature = "Hybrid"
        elif any(keyword in nature_lower for keyword in onsite_keywords):
            job.jobNature = "Onsite"
        # Finally check description
        elif any(keyword in desc_lower for keyword in remote_keywords):
            job.jobNature = "Remote"
        elif any(keyword in desc_lower for keyword in hybrid_keywords):
            job.jobNature = "Hybrid"
        elif any(keyword in desc_lower for keyword in onsite_keywords):
            job.jobNature = "Onsite"
        else:
            job.jobNature = "Not specified"

    def _filter_by_job_nature(self, jobs: List[Job], requested_nature: Optional[str]) -> List[Job]:
        """Filter jobs by job nature"""
        if not requested_nature:
            return jobs
        
        nature_matching_jobs = [
            job for job in jobs
            if job.jobNature and job.jobNature.lower() == requested_nature.lower()
        ]
        
        if nature_matching_jobs:
            logger.info(f"Found {len(nature_matching_jobs)} jobs matching requested nature '{requested_nature}'")
            return nature_matching_jobs
        
        logger.warning(f"No jobs found with exact match for nature '{requested_nature}', returning all jobs")
        return jobs