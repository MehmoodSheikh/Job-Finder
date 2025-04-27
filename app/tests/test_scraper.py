"""
Test script for job scrapers with production API format
"""
import asyncio
import json
import logging
from typing import Dict, Any, List

from app.models.job import Job
from app.scrapers.scraper_factory import ScraperFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_scrapers():
    """Test scrapers and format results to match production API output"""
    # Test parameters matching production usage
    position = "Full Stack Engineer"
    location = "Peshawar, Pakistan"
    job_nature = "onsite"
    
    logger.info(f"Testing scrapers with production parameters:")
    logger.info(f"Position: {position}")
    logger.info(f"Location: {location}")
    logger.info(f"Job Nature: {job_nature}")
    
    # Get scrapers from factory
    factory = ScraperFactory()
    scrapers = factory.get_all_scrapers()
    
    logger.info(f"Initialized {len(scrapers)} scrapers")
    
    try:
        # Create tasks for each scraper
        tasks = []
        for scraper in scrapers:
            task = asyncio.create_task(
                scraper.search_jobs(
                    position=position,
                    location=location,
                    job_nature=job_nature
                )
            )
            tasks.append((scraper.name, task))
        
        # Process results from each scraper
        all_jobs = []
        for scraper_name, task in tasks:
            try:
                jobs = await task
                logger.info(f"{scraper_name}: Found {len(jobs)} jobs")
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"{scraper_name} error: {e}")
        
        logger.info(f"Combined results: Found {len(all_jobs)} jobs from all scrapers")
        
        # If no real jobs found, use mock data for testing the output format
        if not all_jobs:
            logger.warning("No real jobs found. Using mock data for testing.")
            all_jobs = create_mock_jobs()
            logger.info(f"Added {len(all_jobs)} mock jobs")
        
        # Format output to match production API
        api_output = format_api_output(all_jobs)
        
        # Save results to JSON in the exact production format
        with open("app/tests/scraper_test_results.json", "w") as f:
            json.dump(api_output, f, indent=2)
            
        logger.info(f"Results saved to scraper_test_results.json in production API format")
        logger.info("API Output Sample:")
        logger.info(json.dumps(api_output, indent=2))
            
    finally:
        # Close all scrapers to release resources
        await factory.close_all_scrapers(scrapers)
        logger.info("Test completed")

def create_mock_jobs() -> List[Job]:
    """Create mock jobs for testing when scrapers don't return results"""
    return [
        Job(
            job_title="Full Stack Engineer",
            company="XYZ Pvt Ltd",
            experience="2+ years",
            jobNature="onsite",
            location="Islamabad, Pakistan",
            salary="100,000 PKR",
            apply_link="https://linkedin.com/job123",
            description="Looking for a Full Stack Engineer with experience in MERN stack.",
            source="LinkedIn"
        ),
        Job(
            job_title="MERN Stack Developer",
            company="ABC Technologies",
            experience="2 years",
            jobNature="onsite",
            location="Lahore, Pakistan",
            salary="90,000 PKR",
            apply_link="https://indeed.com/job456",
            description="We are looking for a MERN Stack Developer.",
            source="Indeed"
        ),
    ]

def format_api_output(jobs: List[Job]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Format jobs to match production API output format exactly
    """
    relevant_jobs = []
    
    for job in jobs:
        # Create job dict with only the fields required in the API output
        job_dict = {
            "job_title": job.job_title,
            "company": job.company,
            "experience": job.experience or "Not specified",
            "jobNature": job.jobNature or "Not specified",
            "location": job.location or "Not specified",
            "salary": job.salary or "Not specified",
            "apply_link": job.apply_link or ""
        }
        relevant_jobs.append(job_dict)
    
    # Format as per production API output exactly
    return {"relevant_jobs": relevant_jobs}

if __name__ == "__main__":
    asyncio.run(test_scrapers()) 