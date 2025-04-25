"""
API routes for the Job Finder API
"""
import asyncio
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.models.job import JobRequest, Job
from app.scrapers.scraper_factory import ScraperFactory
from app.services.simple_relevance_filtering import SimpleRelevanceFilteringService
from app.core.config import settings

# Create router
router = APIRouter()

# Create scraper factory
scraper_factory = ScraperFactory()

# Create relevance filtering service
relevance_service = SimpleRelevanceFilteringService()

@router.post("/search", response_model=Dict[str, List[Job]])
async def search_jobs(job_request: JobRequest):
    """
    Search for jobs across multiple platforms based on the provided criteria
    
    Args:
        job_request: Job search criteria
        
    Returns:
        Dictionary with list of relevant jobs
    """
    try:
        # Get all scrapers
        scrapers = scraper_factory.get_all_scrapers()
        
        # Search for jobs across all platforms
        all_jobs = []
        tasks = []
        
        for scraper in scrapers:
            task = asyncio.create_task(
                scraper.search_jobs(
                    position=job_request.position,
                    location=job_request.location,
                    experience=job_request.experience,
                    job_nature=job_request.jobNature
                )
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                # Log the exception but continue with other results
                print(f"Error in scraper: {result}")
                continue
            
            all_jobs.extend(result)
        
        # Filter jobs by relevance
        relevant_jobs = relevance_service.filter_jobs_by_relevance(
            all_jobs, 
            job_request,
            threshold=settings.MIN_RELEVANCE_SCORE
        )
        
        return {"relevant_jobs": relevant_jobs}
    
    except Exception as e:
        # Log the exception
        print(f"Error in search_jobs: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while searching for jobs: {str(e)}")

@router.get("/platforms", response_model=Dict[str, List[str]])
async def get_platforms():
    """
    Get a list of available job platforms
    
    Returns:
        Dictionary with list of platform names
    """
    try:
        platforms = scraper_factory.get_available_scrapers()
        return {"platforms": platforms}
    
    except Exception as e:
        # Log the exception
        print(f"Error in get_platforms: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving platforms: {str(e)}")
