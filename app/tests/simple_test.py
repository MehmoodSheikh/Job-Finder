"""
Test script for rule-based filtering that matches production API format
"""
import json
import logging
from app.models.job import JobRequest, Job
from app.services.ai_relevance_filtering import AIRelevanceFilteringService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rule_based_filtering():
    """
    Test the rule-based fallback filtering following production API format
    """
    print("Testing rule-based filtering with production API format...")
    
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
    
    # Create mock jobs
    mock_jobs = create_mock_jobs()
    
    print(f"Found {len(mock_jobs)} jobs before filtering")
    
    # Filter jobs by relevance using rule-based scoring from AI service
    ai_service = AIRelevanceFilteringService()
    # Use the rule-based method directly
    relevant_jobs = ai_service._score_jobs_with_rules(mock_jobs, job_request, threshold=0.2)
    
    print(f"Found {len(relevant_jobs)} relevant jobs after rule-based filtering")
    
    # Format the output to match production API output format
    output = format_api_output(relevant_jobs)
    
    # Save results to a JSON file
    with open("app/tests/simple_test_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("Test results saved to simple_test_results.json")
    print("API Output Sample:")
    print(json.dumps(output, indent=2))
    
    return output

def create_mock_jobs():
    """
    Create mock job data for testing that matches production data structure
    """
    jobs = [
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
            job_title="Frontend Developer",
            company="Tech Solutions",
            experience="1-3 years",
            jobNature="remote",
            location="Karachi, Pakistan",
            salary="80,000 PKR",
            apply_link="https://glassdoor.com/job789",
            description="Frontend Developer with React.js and TailwindCSS experience needed for our growing team.",
            source="Glassdoor"
        ),
        Job(
            job_title="Backend Engineer",
            company="Digital Innovations",
            experience="3 years",
            jobNature="hybrid",
            location="Peshawar, Pakistan",
            salary="110,000 PKR",
            apply_link="https://rozee.pk/job101",
            description="Backend Engineer with Node.js and Express.js experience needed for our enterprise applications.",
            source="Rozee.pk"
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
        Job(
            job_title="MERN Stack Engineer",
            company="Software House",
            experience="2-3 years",
            jobNature="onsite",
            location="Peshawar, Pakistan",
            salary="95,000 PKR",
            apply_link="https://rozee.pk/job505",
            description="MERN Stack Engineer with MongoDB, Express.js, React.js, Node.js, and TailwindCSS experience needed for our client projects.",
            source="Rozee.pk"
        ),
    ]
    
    return jobs

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
    test_rule_based_filtering()
