"""
Test script for the Job Finder API
"""
import asyncio
import json
from app.models.job import JobRequest
from app.scrapers.scraper_factory import ScraperFactory
from app.services.simple_relevance_filtering import SimpleRelevanceFilteringService

async def test_job_search():
    """
    Test the job search functionality with mock data
    """
    print("Testing job search functionality...")
    
    # Create a test job request
    job_request = JobRequest(
        position="Full Stack Engineer",
        experience="2 years",
        salary="70,000 PKR to 120,000 PKR",
        jobNature="onsite",
        location="Peshawar, Pakistan",
        skills="MERN, Node.js, Express.js, React.js, Firebase, TailwindCSS"
    )
    
    print(f"Job request: {job_request.model_dump()}")
    
    # Get all scrapers
    scraper_factory = ScraperFactory()
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
            print(f"Error in scraper: {result}")
            continue
        
        all_jobs.extend(result)
    
    print(f"Found {len(all_jobs)} jobs before filtering")
    
    # Filter jobs by relevance
    relevance_service = SimpleRelevanceFilteringService()
    relevant_jobs = relevance_service.filter_jobs_by_relevance(all_jobs, job_request)
    
    print(f"Found {len(relevant_jobs)} relevant jobs after filtering")
    
    # Print the top 3 most relevant jobs
    print("\nTop 3 most relevant jobs:")
    for i, job in enumerate(relevant_jobs[:3], 1):
        print(f"{i}. {job.job_title} at {job.company} - Relevance: {job.relevance_score:.2f}")
        print(f"   Location: {job.location}")
        print(f"   Experience: {job.experience}")
        print(f"   Apply: {job.apply_link}")
        print()
    
    # Save results to a JSON file
    save_results_to_json(relevant_jobs)
    
    return relevant_jobs

def save_results_to_json(jobs):
    """
    Save job results to a JSON file
    """
    # Convert jobs to dict for JSON serialization
    jobs_dict = {"relevant_jobs": []}
    for job in jobs:
        job_dict = job.model_dump()
        # Convert float to string for JSON serialization
        if job_dict.get('relevance_score') is not None:
            job_dict['relevance_score'] = str(job_dict['relevance_score'])
        jobs_dict["relevant_jobs"].append(job_dict)
    
    # Save to file
    with open("test_results.json", "w") as f:
        json.dump(jobs_dict, f, indent=2)
    
    print("Test results saved to test_results.json")

if __name__ == "__main__":
    asyncio.run(test_job_search())
