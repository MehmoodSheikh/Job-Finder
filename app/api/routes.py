"""
API routes for the Job Finder application
"""
import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

class JobSearchRequest(BaseModel):
    position: str
    location: Optional[str] = None
    experience: Optional[str] = None
    jobNature: Optional[str] = None
    salary: Optional[str] = None
    skills: Optional[str] = None

# Import services after router definition
try:
    # Updated import path for search service
    from app.services.search_service import SearchService
    from app.services.ai_relevance_filtering import AIRelevanceFilteringService
    
    # Initialize services
    search_service = SearchService()
    ai_relevance_service = AIRelevanceFilteringService()
    logger.info("✅ Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    raise

@router.post("/search")
async def search_jobs(request: JobSearchRequest):
    """
    Search for jobs across multiple platforms with AI-powered relevance filtering
    """
    logger.info(f"Received search request: {request.dict()}")
    
    try:
        # Search for jobs using the search service
        all_jobs = await search_service.search_jobs(
            position=request.position,
            location=request.location,
            experience=request.experience,
            job_nature=request.jobNature
        )
        
        if not all_jobs:
            logger.warning("No jobs found from any source")
            return {"relevant_jobs": []}
        
        logger.info(f"Found {len(all_jobs)} jobs before relevance filtering")
        
        # Filter jobs by relevance
        try:
            relevant_jobs = await ai_relevance_service.filter_jobs_by_relevance(
                jobs=all_jobs,
                job_request=request
            )
            logger.info(f"Returning {len(relevant_jobs)} relevant jobs")
            return {"relevant_jobs": relevant_jobs}
        except Exception as e:
            logger.error(f"Error in relevance filtering: {e}")
            # If relevance filtering fails, return all jobs
            logger.info("Returning all jobs without relevance filtering")
            return {"relevant_jobs": all_jobs}
    
    except Exception as e:
        logger.exception(f"Error in search_jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the application shuts down"""
    try:
        await ai_relevance_service.close()
        logger.info("Successfully closed AI relevance filtering service")
    except Exception as e:
        logger.error(f"Error closing AI relevance filtering service: {e}")