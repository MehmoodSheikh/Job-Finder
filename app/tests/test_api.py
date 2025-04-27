"""
Integration test for the Job Finder API with production API format
"""
import asyncio
import json
import logging
from app.models.job import JobRequest, Job
from app.services.search_service import SearchService
from app.services.ai_relevance_filtering import AIRelevanceFilteringService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_job_search_api():
    """
    Test the integrated job search API with exact production input/output formats
    """
    logger.info("Testing integrated job search API with production format...")
    
    # Create a test job request matching the production API input format exactly
    job_request = JobRequest(
        position="Full Stack Engineer",
        experience="2 years",
        salary="70,000 PKR to 120,000 PKR",
        jobNature="onsite",
        location="Peshawar, Pakistan",
        skills="full stack, MERN, Node.js, Express.js, React.js, Next.js, Firebase, TailwindCSS, CSS Frameworks, Tokens handling"
    )
    
    # Log the input in the exact format expected by the API
    api_input = job_request.model_dump()
    logger.info("API Input:")
    logger.info(json.dumps(api_input, indent=2))
    
    # Initialize services
    search_service = SearchService()
    ai_service = AIRelevanceFilteringService()
    
    try:
        # Search for jobs using the search service (simulating API route)
        all_jobs = await search_service.search_jobs(
            position=job_request.position,
            location=job_request.location,
            experience=job_request.experience,
            job_nature=job_request.jobNature
        )
        
        logger.info(f"Found {len(all_jobs)} jobs from scrapers")
        
        # If no real jobs found, use mock data for testing purposes
        if not all_jobs:
            logger.warning("No real jobs found. Using mock data for testing.")
            all_jobs = create_mock_jobs()
        
        # Filter jobs by relevance using AI service (simulating API route processing)
        relevant_jobs = await ai_service.filter_jobs_by_relevance(all_jobs, job_request)
        
        logger.info(f"Found {len(relevant_jobs)} relevant jobs after filtering")
        
        # Format the results to match the production API output format exactly
        api_output = format_api_output(relevant_jobs)
        
        # Save results to a JSON file
        with open("app/tests/api_test_results.json", "w") as f:
            json.dump(api_output, f, indent=2)
        
        logger.info("API Output Format:")
        logger.info(json.dumps(api_output, indent=2))
        
        return api_output
    
    finally:
        # Close the AI service to clean up resources
        await ai_service.close()

def create_mock_jobs():
    """Create mock jobs for testing when real scrapers don't return data"""
    return [
        Job(
            job_title="Full Stack Engineer",
            company="XYZ Pvt Ltd",
            experience="2+ years",
            jobNature="onsite",
            location="Islamabad, Pakistan",
            salary="100,000 PKR",
            apply_link="https://linkedin.com/job123",
            description="Looking for a Full Stack Engineer with experience in MERN stack, Node.js, Express.js, React.js, and TailwindCSS.",
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
            description="We are looking for a MERN Stack Developer with experience in MongoDB, Express.js, React.js, and Node.js.",
            source="Indeed"
        ),
        Job(
            job_title="Full Stack JavaScript Developer",
            company="Web Wizards",
            experience="2 years",
            jobNature="onsite",
            location="Peshawar, Pakistan",
            salary="85,000 PKR",
            apply_link="https://glassdoor.com/job404",
            description="Full Stack JavaScript Developer with Node.js, Express.js, and React.js experience needed for our web applications.",
            source="Glassdoor"
        ),
    ]

def format_api_output(jobs):
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
    asyncio.run(test_job_search_api())
