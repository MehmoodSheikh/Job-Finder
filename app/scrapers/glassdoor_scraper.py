"""
Glassdoor job scraper implementation
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


class GlassdoorScraper(BaseScraper):
    """
    Scraper for Glassdoor jobs
    
    Glassdoor has an API but requires partner access:
    https://www.glassdoor.com/developer/index.htm
    
    This implementation uses web scraping as a fallback.
    """
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.glassdoor.com/Job/jobs.htm"
        self.api_url = "https://api.glassdoor.com/api/api.htm"
        self.partner_id = os.environ.get("GLASSDOOR_PARTNER_ID", "")
        self.partner_key = os.environ.get("GLASSDOOR_PARTNER_KEY", "")
        self.use_api = bool(self.partner_id and self.partner_key)
        
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
        Search for jobs on Glassdoor based on the provided criteria
        
        Args:
            position: Job title or position
            location: Job location
            experience: Required experience
            job_nature: Job nature (onsite, remote, hybrid)
            **kwargs: Additional search parameters
            
        Returns:
            List of Job objects
        """
        if self.use_api:
            try:
                return await self._search_jobs_api(position, location, experience, job_nature, **kwargs)
            except Exception as e:
                self.logger.error(f"Error using Glassdoor API: {e}")
                self.logger.info("Falling back to web scraping")
        
        # Fall back to web scraping
        return await self._search_jobs_scraping(position, location, job_nature)
    
    async def _search_jobs_api(self, position: str, location: Optional[str], 
                         experience: Optional[str], job_nature: Optional[str], **kwargs) -> List[Job]:
        """Search for jobs using Glassdoor API"""
        params = {
            "v": "1",
            "format": "json",
            "t.p": self.partner_id,
            "t.k": self.partner_key,
            "action": "jobs-prog",
            "keyword": position,
            "locId": location or "",
            "countryId": kwargs.get("country_id", "1"),  # Default to US
        }
        
        # Experience and job_nature are not directly supported by the API
        
        response = await self._make_request("get", self.api_url, params=params)
        
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse Glassdoor API response")
                return []
        
        jobs = []
        try:
            results = response.get("response", {}).get("jobListings", [])
            for result in results:
                job = Job(
                    job_title=result.get("jobTitle", ""),
                    company=result.get("employer", {}).get("name", ""),
                    experience="Not specified",
                    jobNature=job_nature or self._infer_job_nature(result),
                    location=result.get("location", ""),
                    salary=self._extract_salary(result),
                    apply_link=result.get("jobViewUrl", ""),
                    description=result.get("jobDescription", "")[:500] + "...",
                    source="Glassdoor"
                )
                jobs.append(job)
        except Exception as e:
            self.logger.error(f"Error parsing Glassdoor API response: {e}")
        
        return jobs
    
    def _infer_job_nature(self, job_data: Dict[str, Any]) -> str:
        """Infer job nature from Glassdoor job data"""
        if job_data.get("isRemote", False):
            return "Remote"
        
        description = job_data.get("jobDescription", "").lower()
        if "remote" in description:
            return "Remote"
        if "hybrid" in description:
            return "Hybrid"
        if "on-site" in description or "onsite" in description or "in office" in description:
            return "Onsite"
        
        return "Not specified"
    
    def _extract_salary(self, job_data: Dict[str, Any]) -> str:
        """Extract salary information from Glassdoor job data"""
        pay_info = job_data.get("salaryInfo", {})
        
        if pay_info:
            pay_period = pay_info.get("payPeriod", "")
            min_pay = pay_info.get("salaryLow", 0)
            max_pay = pay_info.get("salaryHigh", 0)
            
            if min_pay and max_pay:
                return f"${min_pay:,} - ${max_pay:,} {pay_period}"
            elif min_pay:
                return f"${min_pay:,} {pay_period}"
        
        return "Not specified"
    
    async def _search_jobs_scraping(self, position: str, location: Optional[str], job_nature: Optional[str]) -> List[Job]:
        """Search for jobs using web scraping"""
        jobs = []
        
        query_params = {
            "keyword": position,
            "locT": "N",
            "locId": "0",
        }
        
        if location:
            query_params["loc"] = location
        
        # Add job type filter if specified
        if job_nature:
            job_type_map = {
                "remote": "REMOTE",
                "onsite": "REGULAR",
                "hybrid": "HYBRID", 
            }
            if job_nature.lower() in job_type_map:
                query_params["jobType"] = job_type_map[job_nature.lower()]
        
        search_url = f"{self.base_url}?{urlencode(query_params)}"
        
        try:
            resp = await self.client.get(search_url, headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Glassdoor job listings typically use this CSS selector pattern
            job_cards = soup.select('li.react-job-listing')
            
            for card in job_cards[:10]:  # Limit to 10 results
                try:
                    # Extract job details
                    job_id = card.get('data-id', '')
                    if not job_id:
                        continue
                    
                    # Job title
                    title_elem = card.select_one('a.jobLink')
                    if not title_elem:
                        continue
                    job_title = title_elem.text.strip()
                    
                    # Company name
                    company_elem = card.select_one('div.css-1vg6q84 a')
                    company = company_elem.text.strip() if company_elem else "Unknown Company"
                    
                    # Location
                    location_elem = card.select_one('span.css-3g3psg')
                    job_location = location_elem.text.strip() if location_elem else "Location not specified"
                    
                    # Salary
                    salary_elem = card.select_one('span[data-test="detailSalary"]')
                    salary = salary_elem.text.strip() if salary_elem else "Not specified"
                    
                    # Job link
                    job_link = f"https://www.glassdoor.com/job-listing/{job_id}"
                    
                    # Get job description
                    description = await self._fetch_job_description(job_id)
                    
                    job = Job(
                        job_title=job_title,
                        company=company,
                        experience="Not specified",  # Not directly available in search results
                        jobNature=job_nature or self._extract_job_nature_from_card(card),
                        location=job_location,
                        salary=salary,
                        apply_link=job_link,
                        description=description,
            source="Glassdoor"
                    )
                    
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing Glassdoor job card: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in Glassdoor scraping: {e}")
        
        return jobs
    
    def _extract_job_nature_from_card(self, card) -> str:
        """Extract job nature from Glassdoor job card"""
        try:
            job_type_elem = card.select_one('span.css-1wh2kri')
            if job_type_elem:
                job_type = job_type_elem.text.strip().lower()
                if "remote" in job_type:
                    return "Remote"
                if "hybrid" in job_type:
                    return "Hybrid"
                if "in-person" in job_type or "on-site" in job_type or "full-time" in job_type:
                    return "Onsite"
        except Exception:
            pass
        
        return "Not specified"
    
    async def _fetch_job_description(self, job_id: str) -> str:
        """Fetch job description from Glassdoor job page"""
        try:
            url = f"https://www.glassdoor.com/job-listing/{job_id}"
            resp = await self.client.get(url, headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            description_elem = soup.select_one('div.jobDescriptionContent')
            if description_elem:
                return self._clean_text(description_elem.text)[:500] + "..."
        except Exception as e:
            self.logger.error(f"Error fetching Glassdoor job description: {e}")
        
        return "No description available"
