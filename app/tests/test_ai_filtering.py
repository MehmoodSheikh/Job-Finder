"""
Test script for AI relevance filtering with production API format
"""
import os
import asyncio
import sys
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models.job import Job, JobRequest
from app.services.ai_relevance_filtering import AIRelevanceFilteringService

async def test_ai_filtering():
    """Test the AI relevance filtering service with production API format"""
    print("Testing AI relevance filtering with production API format...")
    
    # Create a test job request matching the production API input format
    job_request = JobRequest(
        position="Full Stack Engineer",
        experience="2 years",
        salary="70,000 PKR to 120,000 PKR",
        jobNature="onsite",
        location="Peshawar, Pakistan",
        skills="full stack, MERN, Node.js, Express.js, React.js, Next.js, Firebase, TailwindCSS, CSS Frameworks, Tokens handling"
    )
    
    print(f"API Input: {json.dumps(job_request.model_dump(), indent=2)}")
    
    # Create test jobs that match production data structure
    test_jobs = create_test_jobs()
    print(f"Created {len(test_jobs)} test jobs")
    
    # Initialize the AI relevance filtering service
    ai_service = AIRelevanceFilteringService()
    
    try:
        logger.info("Testing AI-based filtering...")
        # Filter jobs by relevance
        filtered_jobs = await ai_service.filter_jobs_by_relevance(test_jobs, job_request, threshold=0.2)
        
        # Format according to production API output format
        output = format_api_output(filtered_jobs)
        
        # Save results to a JSON file
        with open("app/tests/ai_filtering_test_results.json", "w") as f:
            json.dump(output, f, indent=2)
        
        # Print sample output for verification
        print(f"Found {len(filtered_jobs)} relevant jobs")
        print("API Output Sample:")
        print(json.dumps(output, indent=2))
        
        return output
            
    except Exception as e:
        logger.error(f"Error testing AI filtering: {e}")
        return {"relevant_jobs": []}
    finally:
        # Clean up
        await ai_service.close()
        logger.info("Test completed")

def create_test_jobs():
    """Create test jobs that match production data structure"""
    return [
        Job(
            job_title="Senior Full Stack Engineer",
            company="XYZ Corp",
            experience="3-5 years",
            jobNature="onsite",  # Matching job nature
            location="Lahore, Pakistan",
            salary="120,000 PKR",
            apply_link="https://example.com/job1",
            description="Looking for a Full Stack Engineer with experience in MERN stack, React, and Node.js. Position requires knowledge of CSS frameworks like TailwindCSS and handling user authentication with tokens.",
            source="LinkedIn"
        ),
        Job(
            job_title="Full Stack Developer",
            company="ABC Inc",
            experience="1-2 years",
            jobNature="hybrid",  # Non-matching job nature
            location="Karachi, Pakistan",
            salary="80,000 PKR",
            apply_link="https://example.com/job2",
            description="We need a Full Stack Developer with React, Next.js and Node.js skills. Experience with Firebase required.",
            source="Indeed"
        ),
        Job(
            job_title="MERN Stack Engineer",
            company="Web Technologies",
            experience="2 years",
            jobNature="onsite",  # Matching job nature
            location="Peshawar, Pakistan",
            salary="95,000 PKR",
            apply_link="https://example.com/job4",
            description="MERN Stack Developer with React, Node.js, and TailwindCSS experience needed. This position is based in our Peshawar office.",
            source="LinkedIn"
        ),
        Job(
            job_title="Full Stack JavaScript Developer",
            company="Tech Innovators",
            experience="2-3 years",
            jobNature="onsite",  # Matching job nature
            location="Peshawar, Pakistan",
            salary="90,000 PKR",
            apply_link="https://example.com/job5",
            description="Full Stack Developer with Express.js, Next.js, and React.js experience. Implementation of token-based authentication required.",
            source="Rozee.pk"
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
            "apply_link": job.apply_link or "",
            "relevance_percentage": job.relevance_percentage  # Include the match percentage
        }
        relevant_jobs.append(job_dict)
    
    # Format as per production API output
    return {"relevant_jobs": relevant_jobs}

if __name__ == "__main__":
    asyncio.run(test_ai_filtering()) 