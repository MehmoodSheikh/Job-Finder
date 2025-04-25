"""
Updated simplified test script for the Job Finder API
"""
import json
from app.models.job import JobRequest, Job
from app.services.simple_relevance_filtering import SimpleRelevanceFilteringService

def test_relevance_filtering():
    """
    Test the relevance filtering functionality with mock data
    """
    print("Testing relevance filtering functionality...")
    
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
    
    # Create mock jobs
    mock_jobs = create_mock_jobs()
    
    print(f"Found {len(mock_jobs)} jobs before filtering")
    
    # Filter jobs by relevance
    relevance_service = SimpleRelevanceFilteringService()
    relevant_jobs = relevance_service.filter_jobs_by_relevance(mock_jobs, job_request)
    
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

def create_mock_jobs():
    """
    Create mock job data for testing
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
            job_title="React Native Developer",
            company="Mobile Apps Inc",
            experience="2-4 years",
            jobNature="onsite",
            location="Islamabad, Pakistan",
            salary="95,000 PKR",
            apply_link="https://linkedin.com/job202",
            description="React Native Developer needed for mobile app development projects.",
            source="LinkedIn"
        ),
        Job(
            job_title="DevOps Engineer",
            company="Cloud Solutions",
            experience="4+ years",
            jobNature="remote",
            location="Lahore, Pakistan",
            salary="130,000 PKR",
            apply_link="https://indeed.com/job303",
            description="DevOps Engineer with AWS and Docker experience needed for our cloud infrastructure team.",
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
    test_relevance_filtering()
