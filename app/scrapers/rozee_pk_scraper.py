"""
Rozee.pk job scraper implementation
"""
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import logging

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: bs4 module not found. Please install it with: pip install beautifulsoup4")
    # Create a dummy class to avoid errors
    class BeautifulSoup:
        def __init__(self, *args, **kwargs):
            pass

from app.models.job import Job
from app.scrapers.base_scraper import BaseScraper


class RozeePkScraper(BaseScraper):
    """
    Scraper for Rozee.pk jobs
    
    Rozee.pk doesn't provide a public API, so this implementation uses web scraping.
    """
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.rozee.pk/job/jsearch"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
    
    async def search_jobs(self, 
                    position: str,
                    location: Optional[str] = None,
                    experience: Optional[str] = None,
                    job_nature: Optional[str] = None,
                    **kwargs) -> List[Job]:
        """
        Search for jobs on Rozee.pk based on the provided criteria
        
        Args:
            position: Job title or position
            location: Job location
            experience: Required experience
            job_nature: Job nature (onsite, remote, hybrid)
            **kwargs: Additional search parameters
            
        Returns:
            List of Job objects
        """
        query_params = {
            "q": position,
            "by": "title",  # Search by job title
        }
        
        # Add location if provided
        if location:
            query_params["loc"] = location
            
        # Add experience level if provided
        if experience:
            exp_level = self._map_experience_to_rozee_filter(experience)
            if exp_level:
                query_params["exp"] = exp_level
                
        # Add job type if provided
        if job_nature:
            job_type = self._map_job_nature_to_rozee_filter(job_nature)
            if job_type:
                query_params["job_type"] = job_type
        
        search_url = f"{self.base_url}?{urlencode(query_params)}"
        
        try:
            resp = await self._make_request("get", search_url, headers=self.headers)
            if isinstance(resp, dict):
                self.logger.error("Unexpected JSON response from Rozee.pk. Expected HTML.")
                return []
            
            return self._parse_search_results(resp, position, location, job_nature)
            
        except Exception as e:
            self.logger.error(f"Error searching Rozee.pk jobs: {e}")
            return []
    
    def _map_experience_to_rozee_filter(self, experience: str) -> Optional[str]:
        """Map experience string to Rozee.pk filter value"""
        experience = experience.lower()
        
        if re.search(r'0|fresh|entry|intern', experience):
            return "0-1"  # 0-1 years
        elif re.search(r'1|2|junior', experience):
            return "1-3"  # 1-3 years
        elif re.search(r'3|4|5|mid', experience):
            return "3-5"  # 3-5 years
        elif re.search(r'5|6|7|senior', experience):
            return "5-8"  # 5-8 years
        elif re.search(r'8|9|10|lead|manager', experience):
            return "8-10"  # 8-10 years
        elif re.search(r'10|11|12|13|14|15|director', experience):
            return "10+"  # 10+ years
        
        return None
    
    def _map_job_nature_to_rozee_filter(self, job_nature: str) -> Optional[str]:
        """Map job nature string to Rozee.pk filter value"""
        job_nature = job_nature.lower()
        
        if job_nature == "remote":
            return "12"  # Remote/Work from Home
        elif job_nature == "onsite" or job_nature == "in-office":
            return "1"  # Full-time
        elif job_nature == "hybrid":
            return "11"  # Part-time/Contractual
        
        return None
    
    def _parse_search_results(self, html: str, position: str, location: Optional[str], job_nature: Optional[str]) -> List[Job]:
        """Parse Rozee.pk search results"""
        jobs = []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find job listings
        job_cards = soup.select('li.job-listing') or soup.select('div.job-box')
        
        for card in job_cards[:10]:  # Limit to 10 results
            try:
                # Extract job details
                title_elem = card.select_one('h3.job-title a') or card.select_one('h3 a')
                if not title_elem:
                    continue
                
                job_title = title_elem.text.strip()
                job_url = title_elem.get('href', '')
                
                # Fix relative URLs
                if job_url and job_url.startswith('/'):
                    job_url = f"https://www.rozee.pk{job_url}"
                
                # Company
                company_elem = card.select_one('h4.company a') or card.select_one('div.company a')
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                
                # Location
                location_elem = card.select_one('span.location') or card.select_one('div.location')
                job_location = location_elem.text.strip() if location_elem else location or "Location not specified"
                
                # Experience
                exp_elem = card.select_one('span.exp') or card.select_one('div.exp')
                if exp_elem:
                    exp = exp_elem.text.strip()
                else:
                    exp = "Not specified"
                
                # Salary
                salary_elem = card.select_one('span.salary') or card.select_one('div.salary')
                salary = salary_elem.text.strip() if salary_elem else "Not specified"
                
                # Description
                desc_elem = card.select_one('div.desc') or card.select_one('div.job-desc')
                description = desc_elem.text.strip() if desc_elem else "No description available"
                
                # Job nature
                job_type_elem = card.select_one('span.job-type') or card.select_one('div.job-type')
                job_type = job_type_elem.text.strip() if job_type_elem else job_nature or "Not specified"
                
                # Create Job object
                job = Job(
                    job_title=job_title,
                    company=company,
                    experience=exp,
                    jobNature=self._normalize_job_nature(job_type),
                    location=job_location,
                    salary=salary,
                    apply_link=job_url,
                    description=description,
                    source="Rozee.pk"
                )
                
                jobs.append(job)
                
            except Exception as e:
                self.logger.error(f"Error parsing Rozee.pk job listing: {e}")
        
        # If no jobs were found using the main selectors, try an alternative approach
        if not jobs:
            # Try to extract job information using regex patterns from script tags
            script_tags = soup.select('script')
            for script in script_tags:
                script_content = script.string
                if script_content and 'joblist' in script_content:
                    try:
                        # Try to extract JSON data using regex
                        job_data_match = re.search(r'var joblist\s*=\s*(\[.*?\]);', script_content, re.DOTALL)
                        if job_data_match:
                            job_data_str = job_data_match.group(1)
                            job_data = json.loads(job_data_str)
                            
                            for job_item in job_data[:10]:
                                try:
                                    job = Job(
                                        job_title=job_item.get('title', ''),
                                        company=job_item.get('company', ''),
                                        experience=job_item.get('experience', 'Not specified'),
                                        jobNature=self._normalize_job_nature(job_item.get('job_type', '')),
                                        location=job_item.get('location', location or 'Not specified'),
                                        salary=job_item.get('salary', 'Not specified'),
                                        apply_link=f"https://www.rozee.pk/job/view/{job_item.get('id', '')}",
                                        description=job_item.get('description', 'No description available'),
                                        source="Rozee.pk"
                                    )
                                    jobs.append(job)
                                except Exception as e:
                                    self.logger.error(f"Error creating job from script data: {e}")
                    except Exception as e:
                        self.logger.error(f"Error extracting job data from script: {e}")
        
        return jobs
    
    def _normalize_job_nature(self, job_type: str) -> str:
        """Normalize job nature string"""
        job_type = job_type.lower()
        
        if "remote" in job_type or "work from home" in job_type or "wfh" in job_type:
            return "Remote"
        elif "part" in job_type or "contract" in job_type or "hybrid" in job_type:
            return "Hybrid"
        elif "full" in job_type or "permanent" in job_type or "onsite" in job_type or "on-site" in job_type:
            return "Onsite"
        
        return job_type.capitalize() if job_type else "Not specified"
