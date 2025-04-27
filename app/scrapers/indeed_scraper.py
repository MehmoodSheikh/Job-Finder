"""
Indeed job scraper implementation
"""
import asyncio
import json
import os
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from app.models.job import Job
from app.scrapers.base_scraper import BaseScraper


class IndeedScraper(BaseScraper):
    """
    Scraper for Indeed jobs
    
    Indeed offers a Publisher API but requires approval:
    https://developer.indeed.com/docs/indeed-jobs
    
    This implementation attempts to use the API if credentials are available,
    otherwise falls back to web scraping.
    """
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.indeed.com/jobs"
        self.api_url = "https://api.indeed.com/ads/apisearch"
        self.publisher_id = os.environ.get("INDEED_PUBLISHER_ID", "")
        self.use_api = bool(self.publisher_id)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        }
    
    async def search_jobs(self, 
                    position: str,
                    location: Optional[str] = None,
                    experience: Optional[str] = None,
                    job_nature: Optional[str] = None,
                    **kwargs) -> List[Job]:
        """
        Search for jobs on Indeed based on the provided criteria
        
        Args:
            position: Job title or position
            location: Job location
            experience: Required experience
            job_nature: Job nature (onsite, remote, hybrid)
            **kwargs: Additional search parameters
            
        Returns:
            List of Job objects
        """
        try:
            # Try official API if credentials are available
            if self.use_api:
                try:
                    jobs = await self._search_jobs_api(position, location, experience, job_nature, **kwargs)
                    if jobs:
                        # Standardize job nature
                        for job in jobs:
                            self.standardize_job_nature(job)
                        return jobs
                except Exception as e:
                    self.logger.error(f"Indeed API search failed: {e}")
            
            # Try direct HTML scraping
            try:
                self.logger.info("Trying Indeed HTML scraping")
                jobs = await self._search_jobs_scraping(position, location, job_nature)
                if jobs:
                    # Standardize job nature
                    for job in jobs:
                        self.standardize_job_nature(job)
                    return jobs
            except Exception as e:
                self.logger.error(f"Indeed HTML scraping failed: {e}")
            
            # Try alternative scraping method (mobile site)
            try:
                self.logger.info("Trying Indeed mobile site scraping")
                jobs = await self._search_jobs_mobile(position, location, job_nature)
                if jobs:
                    # Standardize job nature
                    for job in jobs:
                        self.standardize_job_nature(job)
                    return jobs
            except Exception as e:
                self.logger.error(f"Indeed mobile site scraping failed: {e}")
            
            # If all methods fail, return empty list
            return []
            
        except Exception as e:
            self.logger.error(f"All Indeed scraping methods failed: {e}")
            return []
    
    async def _search_jobs_api(self, position: str, location: Optional[str], 
                         experience: Optional[str], job_nature: Optional[str], **kwargs) -> List[Job]:
        """Search for jobs using Indeed API"""
        params = {
            "publisher": self.publisher_id,
            "q": position,
            "l": location or "",
            "format": "json",
            "v": "2",
            "limit": 25,
            "fromage": kwargs.get("days_old", 30),
            "highlight": 0,
        }
        
        # Add job type filter
        if job_nature:
            job_type_map = {
                "remote": "remote",
                "onsite": "",  # Indeed doesn't have a specific onsite filter
                "hybrid": "parttime",  # Closest match 
            }
            if job_nature.lower() in job_type_map and job_type_map[job_nature.lower()]:
                params["jt"] = job_type_map[job_nature.lower()]
        
        # Experience is harder to filter via the API
        # Usually handled by the frontend search UI
        
        response = await self._make_request("get", self.api_url, params=params)
        
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse Indeed API response")
                return []
        
        jobs = []
        for result in response.get("results", []):
            job = Job(
                job_title=result.get("jobtitle", ""),
                company=result.get("company", ""),
                experience="Not specified",  # Not directly available in API
                jobNature=job_nature or self._infer_job_nature(result),
                location=result.get("formattedLocation", result.get("city", "")),
                salary=result.get("formattedRelativeTime", "Not specified"),
                apply_link=result.get("url", ""),
                description=result.get("snippet", "")[:500] + "...",
                source="Indeed"
            )
            jobs.append(job)
        
        return jobs
    
    def _infer_job_nature(self, job_data: Dict[str, Any]) -> str:
        """Infer job nature from Indeed job data"""
        job_type = job_data.get("jobType", "")
        if "FULLTIME" in job_type:
            return "Onsite"  # Most full-time jobs are onsite
        if "PARTTIME" in job_type:
            return "Hybrid"  # Assumption that part-time might be hybrid
        
        snippet = job_data.get("snippet", "").lower()
        if "remote" in snippet:
            return "Remote"
        if "hybrid" in snippet:
            return "Hybrid"
        if "on-site" in snippet or "onsite" in snippet or "in office" in snippet:
            return "Onsite"
        
        return "Not specified"
    
    async def _search_jobs_scraping(self, position: str, location: Optional[str], job_nature: Optional[str]) -> List[Job]:
        """Search for jobs using web scraping"""
        jobs = []
        
        query_params = {
            "q": position,
            "l": location or "",
        }
        
        # Add job type filter
        if job_nature:
            job_type_map = {
                "remote": "remotejob",
                "hybrid": "hybridjob", 
            }
            if job_nature.lower() in job_type_map:
                query_params["sc"] = "0kf:" + job_type_map[job_nature.lower()] + ";"
        
        search_url = f"{self.base_url}?{urlencode(query_params)}"
        
        try:
            resp = await self.client.get(search_url, headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            job_cards = soup.select('div.job_seen_beacon')
            
            for card in job_cards[:10]:  # Limit to 10 results
                try:
                    title_elem = card.select_one('h2.jobTitle span[title]')
                    company_elem = card.select_one('span.companyName')
                    location_elem = card.select_one('div.companyLocation')
                    
                    if not all([title_elem, company_elem, location_elem]):
                        continue
                    
                    job_id = card.get('data-jk', '')
                    if not job_id:
                        continue
                    
                    salary_elem = card.select_one('div.salary-snippet-container')
                    salary = salary_elem.text.strip() if salary_elem else "Not specified"
                    
                    # Get snippet
                    snippet_elem = card.select_one('div.job-snippet')
                    snippet = snippet_elem.text.strip() if snippet_elem else "No description available"
                    
                    job = Job(
                        job_title=title_elem.get('title', title_elem.text.strip()),
                        company=company_elem.text.strip(),
                        experience="Not specified",
                        jobNature=job_nature or self._extract_job_nature_from_card(card),
                        location=location_elem.text.strip(),
                        salary=salary,
                        apply_link=f"https://www.indeed.com/viewjob?jk={job_id}",
                        description=snippet,
            source="Indeed"
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing Indeed job card: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in Indeed scraping: {e}")
        
        return jobs
    
    def _extract_job_nature_from_card(self, card) -> str:
        """Extract job nature from Indeed job card"""
        try:
            job_type_elem = card.select_one('div.attribute_snippet')
            if job_type_elem:
                job_type = job_type_elem.text.strip().lower()
                if "remote" in job_type:
                    return "Remote"
                if "hybrid" in job_type:
                    return "Hybrid"
                if "in-person" in job_type or "on-site" in job_type:
                    return "Onsite"
        except Exception:
            pass
        
        return "Not specified"

    async def _search_jobs_mobile(self, position: str, location: Optional[str], job_nature: Optional[str]) -> List[Job]:
        """
        Search Indeed jobs using mobile site (often less restricted)
        """
        # Mobile site has different structure and sometimes fewer restrictions
        url = "https://indeed.com/m/jobs"
        params = {
            "q": position,
            "l": location or "",
        }
        
        # Handle job nature
        if job_nature:
            if job_nature.lower() == "remote":
                params["remotejob"] = "032b3046-06a3-4876-8dfd-474eb5e7ed11"
            
        try:
            response = await self._make_request("get", url, params=params, 
                                               headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"})
            
            if isinstance(response, dict):
                return []
            
            # Parse mobile site HTML
            soup = BeautifulSoup(response, 'html.parser')
            job_cards = soup.select('.jobsearch-ResultsList > li')
            
            jobs = []
            for card in job_cards[:10]:  # Limit to 10 results
                try:
                    title_elem = card.select_one('h2.jobTitle')
                    company_elem = card.select_one('span.companyName') 
                    location_elem = card.select_one('div.companyLocation')
                    
                    if not title_elem:
                        continue
                        
                    job_id = card.get('data-jk', '')
                    if not job_id:
                        # Try to extract from links
                        link_elem = card.select_one('a[href*="clk"]')
                        if link_elem:
                            href = link_elem.get('href', '')
                            job_id_match = re.search(r'jk=([^&]+)', href)
                            if job_id_match:
                                job_id = job_id_match.group(1)
                    
                    if not job_id:
                        continue
                    
                    job = Job(
                        job_title=title_elem.text.strip(),
                        company=company_elem.text.strip() if company_elem else "Unknown Company",
                        experience="Not specified",
                        jobNature="Not specified",  # Will be standardized later
                        location=location_elem.text.strip() if location_elem else (location or "Not specified"),
                        salary="Not specified",
                        apply_link=f"https://www.indeed.com/viewjob?jk={job_id}",
                        description="View job details for full description",
                        source="Indeed"
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing Indeed mobile job card: {e}")
                
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error in Indeed mobile scraping: {e}")
            return []
