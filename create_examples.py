"""
Example API request and response for the Job Finder API
"""
import json

# Example request
request_example = {
    "position": "Full Stack Engineer",
    "experience": "2 years",
    "salary": "70,000 PKR to 120,000 PKR",
    "jobNature": "onsite",
    "location": "Peshawar, Pakistan",
    "skills": "MERN, Node.js, Express.js, React.js, Firebase, TailwindCSS"
}

# Example response
response_example = {
    "relevant_jobs": [
        {
            "job_title": "MERN Stack Engineer",
            "company": "Software House",
            "experience": "2-3 years",
            "jobNature": "onsite",
            "location": "Peshawar, Pakistan",
            "salary": "95,000 PKR",
            "apply_link": "https://rozee.pk/job505",
            "description": "MERN Stack Engineer with MongoDB, Express.js, React.js, Node.js, and TailwindCSS experience needed for our client projects.",
            "source": "Rozee.pk",
            "relevance_score": 0.69
        },
        {
            "job_title": "Full Stack Engineer",
            "company": "XYZ Pvt Ltd",
            "experience": "2+ years",
            "jobNature": "onsite",
            "location": "Islamabad, Pakistan",
            "salary": "100,000 PKR",
            "apply_link": "https://linkedin.com/job123",
            "description": "Looking for a Full Stack Engineer with experience in MERN stack, Node.js, Express.js, React.js, and TailwindCSS.",
            "source": "LinkedIn",
            "relevance_score": 0.67
        },
        {
            "job_title": "MERN Stack Developer",
            "company": "ABC Technologies",
            "experience": "2 years",
            "jobNature": "onsite",
            "location": "Lahore, Pakistan",
            "salary": "90,000 PKR",
            "apply_link": "https://indeed.com/job456",
            "description": "We are looking for a MERN Stack Developer with experience in MongoDB, Express.js, React.js, and Node.js.",
            "source": "Indeed",
            "relevance_score": 0.55
        }
    ]
}

# Save to files
with open("example_request.json", "w") as f:
    json.dump(request_example, f, indent=2)
    
with open("example_response.json", "w") as f:
    json.dump(response_example, f, indent=2)
    
print("Example request and response files created successfully.")
