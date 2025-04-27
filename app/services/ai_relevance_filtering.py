"""
Advanced AI-powered relevance filtering service using LangChain with Google Gemini
"""
import os
import re
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try importing required dependencies with fallbacks
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables
    HAS_DOTENV = True
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables must be set manually.")
    HAS_DOTENV = False

# Try importing LangChain components
try:
    import google.generativeai as genai
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.prompts import ChatPromptTemplate
    # Don't use JsonOutputParser, just use raw output and regex
    HAS_LANGCHAIN = True
except ImportError:
    logger.warning("Required packages not installed. Run: pip install langchain langchain-google-genai google-generativeai")
    HAS_LANGCHAIN = False

# Try importing app config
try:
    from app.core.config import settings
except ImportError:
    logger.warning("app.config not found. Using default settings.")
    class DummySettings:
        MIN_RELEVANCE_SCORE = 0.2
    settings = DummySettings()

# Try importing Job models
try:
    from app.models.job import Job, JobRequest
except ImportError:
    logger.error("app.models.job not found. This is critical and must be fixed.")
    # Define dummy models for development
    from typing import List, Optional
    from pydantic import BaseModel
    
    class JobRequest(BaseModel):
        position: str
        location: Optional[str] = None
        experience: Optional[str] = None
        jobNature: Optional[str] = None
        skills: Optional[str] = None
        
    class Job(BaseModel):
        job_title: str
        company: str
        experience: Optional[str] = None
        jobNature: Optional[str] = None
        location: Optional[str] = None
        salary: Optional[str] = None
        apply_link: Optional[str] = None
        description: Optional[str] = None
        source: Optional[str] = None
        relevance_score: Optional[float] = None
        relevance_percentage: Optional[str] = None

class AIRelevanceFilteringService:
    """
    Advanced AI-powered service for filtering jobs based on relevance using LangChain and Google Gemini
    """
    
    def __init__(self):
        """Initialize the AI relevance filtering service with Google Gemini"""
        self.using_ai = False
        self.score_cache = {}
        
        # Skip if LangChain is not available
        if not HAS_LANGCHAIN:
            logger.warning("LangChain not available. Using rule-based filtering only.")
            return
        
        # Get Google API key
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ GOOGLE_API_KEY not found. AI filtering will not be available.")
            logger.warning("Set this in your .env file or environment variables.")
            return
            
        try:
            # Configure Google Gemini API
            genai.configure(api_key=self.api_key)
            
            # Initialize the model with the latest available model
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",  # Using latest available model
                    temperature=0,
                    google_api_key=self.api_key,
                    convert_system_message_to_human=True
                )
                logger.info("Using gemini-2.0-flash model for relevance scoring")
            except Exception as e:
                logger.warning(f"Error initializing gemini-2.0-flash: {e}")
                logger.warning("Falling back to gemini-2.0-flash-lite model")
                try:
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-2.0-flash-lite",
                        temperature=0,
                        google_api_key=self.api_key,
                        convert_system_message_to_human=True
                    )
                    logger.info("Using gemini-2.0-flash-lite model as fallback for relevance scoring")
                except Exception as fallback_e:
                    logger.error(f"Error initializing fallback model: {fallback_e}")
                    return
            
            # Create prompt template with simple JSON instructions
            self.scoring_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a professional job recruiter who specializes in matching job seekers with appropriate positions.
                Your task is to assess how well a job posting matches a job seeker's requirements.
                
                Consider these factors in order of importance:
                1. Job Nature (Remote/Onsite/Hybrid) - This MUST match exactly or score should be very low (below 30)
                2. Position Title - How well the job title matches the desired position
                3. Skills - How many required skills are mentioned in the job description
                4. Experience - Whether the job's required experience matches the candidate's experience
                5. Location - How well the job location matches the desired location
                
                Return your response in the following format:
                SCORE: [number between 0-100]
                EXPLANATION: [brief explanation of the score]"""),
                ("human", """CANDIDATE REQUIREMENTS:
                Position: {position}
                Skills: {skills}
                Experience: {experience}
                Job Nature: {job_nature}
                Location: {location}
                
                JOB DETAILS:
                Title: {job_title}
                Company: {company}
                Job Nature: {job_job_nature}
                Experience: {job_experience}
                Location: {job_location}
                Description: {job_description}
                
                Score this job match from 0-100, where 100 is a perfect match and 0 is completely irrelevant.
                If the job nature doesn't match the requested job nature, the score MUST be 30 or lower.""")
            ])
            
            self.using_ai = True
            logger.info("✅ AI relevance filtering service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI relevance filtering: {e}")
            logger.warning("Falling back to rule-based relevance filtering")
    
    async def filter_jobs_by_relevance(self, jobs: List[Job], job_request: JobRequest, threshold: float = 0.2) -> List[Job]:
        """Filter jobs based on relevance using AI or rules"""
        if not jobs:
            return []
            
        # Apply STRICT job nature filtering first - only matching nature jobs
        nature_matching_jobs = self._strict_filter_by_job_nature(jobs, job_request.jobNature)
        non_matching_jobs = [job for job in jobs if job not in nature_matching_jobs]
        
        # Score the matching jobs first
        if self.using_ai:
            try:
                scored_matching_jobs = await self._score_jobs_with_ai_batch(nature_matching_jobs, job_request, threshold)
                
                # If we have enough matching jobs, just return those
                if len(scored_matching_jobs) >= 5:
                    logger.info(f"Returning {len(scored_matching_jobs)} jobs that match requested nature '{job_request.jobNature}'")
                    return scored_matching_jobs
                
                # If we don't have enough matching jobs, score non-matching jobs but with severe penalty
                if non_matching_jobs:
                    logger.warning(f"Only found {len(scored_matching_jobs)} '{job_request.jobNature}' jobs, adding some non-matching jobs as fallbacks")
                    scored_non_matching = await self._score_jobs_with_ai_batch(non_matching_jobs, job_request, threshold)
                    
                    # Combine and sort results (matching always come first)
                    combined_jobs = scored_matching_jobs + scored_non_matching
                    combined_jobs.sort(key=lambda x: x.relevance_score, reverse=True)
                    
                    # Return combined results, but ensure matching jobs come first
                    return self._prioritize_jobs_by_nature(combined_jobs, job_request.jobNature)
                
                return scored_matching_jobs
                
            except Exception as e:
                logger.error(f"AI scoring failed, falling back to rule-based scoring: {e}")
                return self._score_jobs_with_rules(jobs, job_request, threshold)
        else:
            return self._score_jobs_with_rules(jobs, job_request, threshold)
    
    def _strict_filter_by_job_nature(self, jobs: List[Job], requested_nature: Optional[str]) -> List[Job]:
        """Strictly filter jobs by exact job nature match"""
        if not requested_nature:
            return jobs
            
        # Get jobs with matching nature only
        matching_jobs = [
            job for job in jobs 
            if job.jobNature and job.jobNature.lower() == requested_nature.lower()
        ]
        
        if matching_jobs:
            logger.info(f"Found {len(matching_jobs)} jobs matching requested nature '{requested_nature}'")
        else:
            logger.warning(f"No jobs found with nature '{requested_nature}'")
            
        return matching_jobs
    
    def _prioritize_jobs_by_nature(self, jobs: List[Job], requested_nature: Optional[str]) -> List[Job]:
        """Ensure jobs with matching nature are prioritized"""
        if not requested_nature or not jobs:
            return jobs
            
        # Sort by nature match first, then by relevance score
        return sorted(jobs, key=lambda j: (
            0 if j.jobNature and j.jobNature.lower() == requested_nature.lower() else 1,
            -j.relevance_score
        ))
    
    async def _score_jobs_with_ai_batch(self, 
                                  jobs: List[Job], 
                                  job_request: JobRequest,
                                  threshold: float, 
                                  batch_size: int = 3) -> List[Job]:
        """Score jobs using the LangChain AI pipeline with batch processing"""
        all_scored_jobs = []
        
        # Create a cache key base from the job request
        request_key = f"{job_request.position}_{job_request.location}_{job_request.jobNature}_{job_request.experience}"
        
        # Process jobs in batches
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i+batch_size]
            tasks = []
            
            for job in batch:
                # Create a job cache key
                job_key = f"{job.job_title}_{job.company}_{job.jobNature}"
                cache_key = f"{request_key}_{job_key}"
                
                # Check cache first
                if cache_key in self.score_cache:
                    logger.debug(f"Using cached score for job: {job.job_title}")
                    score_data = self.score_cache[cache_key]
                    job.relevance_score = score_data["score"] / 100.0  # Convert to 0-1 range
                    job.relevance_percentage = f"{int(score_data['score'])}%"
                    
                    if job.relevance_score >= threshold:
                        all_scored_jobs.append(job)
                else:
                    # Create task for scoring
                    tasks.append((job, cache_key, self._score_single_job(job, job_request, cache_key)))
            
            # Process all tasks for this batch
            for job, cache_key, task_coroutine in tasks:
                try:
                    score_data = await task_coroutine
                    job.relevance_score = score_data["score"] / 100.0
                    job.relevance_percentage = f"{int(score_data['score'])}%"
                    
                    # Add to cache
                    self.score_cache[cache_key] = score_data
                    
                    # Log the result
                    logger.info(f"AI scored job '{job.job_title}' ({job.jobNature}) with score {job.relevance_percentage} - {score_data['explanation']}")
                    
                    # Add job if it meets threshold
                    if job.relevance_score >= threshold:
                        all_scored_jobs.append(job)
                        
                except Exception as e:
                    logger.error(f"Error scoring job {job.job_title}: {e}")
                    # Use fallback scoring
                    rule_score = self._calculate_rule_based_score(job, job_request)
                    job.relevance_score = rule_score
                    job.relevance_percentage = f"{int(rule_score * 100)}%"
                    
                    logger.info(f"Fallback scored job '{job.job_title}' with rule-based score {job.relevance_percentage}")
                    
                    if job.relevance_score >= threshold:
                        all_scored_jobs.append(job)
        
        # Sort by score
        all_scored_jobs.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_scored_jobs

    async def _score_single_job(self, job: Job, job_request: JobRequest, cache_key: str) -> Dict[str, Any]:
        """Score a single job using the AI pipeline and parse the result manually"""
        try:
            # Prepare variables for prompt
            variables = {
                # Job seeker's requirements
                "position": job_request.position,
                "skills": job_request.skills or "Not specified",
                "experience": job_request.experience or "Not specified",
                "job_nature": job_request.jobNature or "Not specified",
                "location": job_request.location or "Not specified",
                
                # Job posting details
                "job_title": job.job_title,
                "company": job.company,
                "job_experience": job.experience or "Not specified",
                "job_job_nature": job.jobNature or "Not specified",
                "job_location": job.location or "Not specified",
                "job_description": job.description or "No description available"
            }
            
            # Get response from LLM
            response = await self.llm.ainvoke(self.scoring_prompt.format_messages(**variables))
            
            # Extract the content from response
            content = response.content
            
            # Parse the response using regex
            score_match = re.search(r'SCORE:\s*(\d+)', content)
            explanation_match = re.search(r'EXPLANATION:\s*(.+?)(?:\n|$)', content)
            
            if score_match:
                score = float(score_match.group(1))
                explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided"
                
                # Apply severe penalty for job nature mismatch if AI didn't
                if (job_request.jobNature and job.jobNature and 
                    job_request.jobNature.lower() != job.jobNature.lower() and score > 30):
                    score = min(30, score * 0.3)  # More severe penalty
                    explanation += " (Score reduced for job nature mismatch)"
                
                return {
                    "score": score,
                    "explanation": explanation
                }
            else:
                # Try alternative regex patterns
                # Look for a number that could be a score
                numeric_match = re.search(r'(\d+)/100|(\d+)%|score.*?(\d+)|(\d+)(?:\s*point)', content, re.IGNORECASE)
                if numeric_match:
                    # Get the first non-None group
                    score_str = next(group for group in numeric_match.groups() if group is not None)
                    score = float(score_str)
                    
                    # Get some text that could be an explanation
                    explanation = re.search(r'(?:because|as|since|explanation).*?(.*?)(?:\.|$)', content, re.IGNORECASE)
                    explanation_text = explanation.group(1).strip() if explanation else "Extracted from AI response"
                    
                    # Apply nature mismatch penalty
                    if (job_request.jobNature and job.jobNature and 
                        job_request.jobNature.lower() != job.jobNature.lower() and score > 30):
                        score = min(30, score * 0.3)
                        explanation_text += " (Score reduced for job nature mismatch)"
                    
                    return {
                        "score": score,
                        "explanation": explanation_text
                    }
                
                # If all parsing attempts fail, use rule-based scoring
                rule_score = self._calculate_rule_based_score(job, job_request) * 100
                return {
                    "score": rule_score,
                    "explanation": "Used rule-based scoring due to parsing failure"
                }
                
        except Exception as e:
            logger.error(f"Error in AI scoring for job {job.job_title}: {e}")
            
            # Fallback to rule-based scoring
            rule_score = self._calculate_rule_based_score(job, job_request) * 100
            return {
                "score": rule_score,
                "explanation": f"Rule-based scoring due to error: {str(e)}"
            }
    
    def _score_jobs_with_rules(self, 
                        jobs: List[Job], 
                        job_request: JobRequest,
                        threshold: float) -> List[Job]:
        """Score jobs using rule-based heuristics (fallback method)"""
        scored_jobs = []
        
        for job in jobs:
            # Calculate score based on rules
            score = self._calculate_rule_based_score(job, job_request)
            job.relevance_score = score
            
            # Add relevance percentage for display
            job.relevance_percentage = f"{int(score * 100)}%"
            
            if score >= threshold:
                scored_jobs.append(job)
        
        # Sort by relevance score
        scored_jobs.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Prioritize jobs matching the requested nature
        return self._prioritize_jobs_by_nature(scored_jobs, job_request.jobNature)
    
    def _calculate_rule_based_score(self, job: Job, job_request: JobRequest) -> float:
        """Calculate a relevance score using rule-based heuristics"""
        # Start with a base score
        score = 0.3
        
        # Job nature match (highest priority)
        if job_request.jobNature and job.jobNature:
            if job_request.jobNature.lower() == job.jobNature.lower():
                score += 0.4  # Major boost for matching job nature
            else:
                score -= 0.2  # Major penalty for non-matching job nature
                # Set maximum score for non-matching nature
                score = min(score, 0.3)
        
        # Position match in title (high weight)
        position_lower = job_request.position.lower()
        title_lower = job.job_title.lower()
        
        # Check for exact match
        if position_lower in title_lower:
            score += 0.3
        # Check for partial match of words
        elif any(word in title_lower for word in position_lower.split()):
            score += 0.15
        
        # Skills match (if provided)
        if job_request.skills and job.description:
            skills = [s.strip().lower() for s in job_request.skills.split(',')]
            description_lower = job.description.lower()
            matched_skills = sum(1 for skill in skills if skill in description_lower)
            if skills:
                skill_score = 0.2 * (matched_skills / len(skills))
                score += skill_score
        
        # Location match
        if job_request.location and job.location:
            location_parts = job_request.location.lower().split(',')
            job_location_lower = job.location.lower()
            
            if any(part.strip() in job_location_lower for part in location_parts):
                score += 0.1
        
        # Experience match (if provided)
        if job_request.experience and job.experience:
            # Extract years from experience strings
            user_years = self._extract_years_from_experience(job_request.experience)
            job_years = self._extract_years_from_experience(job.experience)
            
            if user_years and job_years:
                # If job requires less experience than user has, it's a good match
                if job_years <= user_years:
                    score += 0.1
        
        # Cap score based on job nature match
        if job_request.jobNature and job.jobNature and job_request.jobNature.lower() != job.jobNature.lower():
            score = min(score, 0.3)  # Hard cap at 30% for nature mismatch
            
        # Ensure score is between 0 and 1
        return min(1.0, max(0.0, score))
    
    def _extract_years_from_experience(self, experience: str) -> Optional[int]:
        """Extract years from experience string"""
        try:
            # Find numbers in the experience string
            matches = re.findall(r'\b(\d+)(?:\+)?\s*(?:year|yr)s?\b', experience.lower())
            if matches:
                return int(matches[0])
            return None
        except Exception:
            return None
    
    async def close(self):
        """Clean up resources when service is no longer needed"""
        # Skip if AI wasn't initialized
        if not self.using_ai:
            return
            
        # Clear the cache to free memory
        self.score_cache.clear()
        # Close any open connections
        if hasattr(self, 'llm') and hasattr(self.llm, 'aclose'):
            await self.llm.aclose() 