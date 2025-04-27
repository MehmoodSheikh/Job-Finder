from pydantic import BaseModel
from typing import Optional, List, Union


class JobRequest(BaseModel):
    """
    Model for job search request parameters
    """
    position: str
    experience: Optional[str] = None
    salary: Optional[str] = None
    jobNature: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[str] = None


class Job(BaseModel):
    """
    Model for job data
    """
    job_title: str
    company: str
    experience: Optional[str] = None
    jobNature: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    apply_link: str
    description: Optional[str] = None
    source: str
    relevance_score: Optional[float] = None
    relevance_percentage: Optional[str] = None
