"""
Google Jobs scraper implementation
"""
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote

from bs4 import BeautifulSoup

from app.models.job import Job
from app.scrapers.base_scraper import BaseScraper


class GoogleJobsScraper(BaseScraper):
    """
    Scraper for Google Jobs
    
    Google does not provide an official API for jobs search.
    This implementation uses web scraping to fetch job listings.
    """
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.google.com/search"
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
        Search for jobs on Google Jobs based on the provided criteria
        
        Args:
            position: Job title or position
            location: Job location
            experience: Required experience
            job_nature: Job nature (onsite, remote, hybrid)
            **kwargs: Additional search parameters
            
        Returns:
            List of Job objects
        """
        # Construct search query
        query = f"{position} jobs"
        if location:
            query += f" in {location}"
        if job_nature:
            query += f" {job_nature}"
        
        # Add experience to the query if provided
        if experience:
            query += f" {experience} experience"
        
        params = {
            "q": query,
            "ibp": "htl;jobs",  # This parameter helps target the jobs widget
            "uule": self._get_uule_parameter(location),  # Location encoding for Google
            "hl": "en",  # Language
            "gl": kwargs.get("country_code", "us"),  # Country code
        }
        
        search_url = f"{self.base_url}?{urlencode(params)}"
        
        try:
            resp = await self._make_request("get", search_url, headers=self.headers)
            if isinstance(resp, dict):
                self.logger.error("Unexpected JSON response from Google. Expected HTML.")
                return []
            
            return await self._parse_search_results(resp, position, location, job_nature)
            
        except Exception as e:
            self.logger.error(f"Error searching Google Jobs: {e}")
            return []
    
    def _get_uule_parameter(self, location: Optional[str]) -> Optional[str]:
        """
        Generate a UULE parameter for Google search based on location
        
        UULE is Google's location encoding for search
        
        Args:
            location: Location string
            
        Returns:
            UULE parameter or None
        """
        if not location:
            return None
            
        # This is a simplified version of UULE encoding
        # For a more accurate implementation, refer to:
        # https://moz.com/blog/how-to-track-local-google-search-results
        
        # Base64 encoding with padding characters removed
        # In real implementation, you'd want to properly encode this
        return f"w+CAIQICI{quote(location)}"
    
    async def _parse_search_results(self, html: str, position: str, location: Optional[str], job_nature: Optional[str]) -> List[Job]:
        """Parse Google Jobs search results"""
        jobs = []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # First, try to find the jobs widget
        job_widgets = soup.select('div.iFjolb')
        if not job_widgets:
            # If the default selector doesn't work, try alternative selectors
            # Google frequently changes its HTML structure
            job_widgets = soup.select('div.mnr-c') or soup.select('div.g') or soup.select('div.tF2Cxc')
        
        if not job_widgets:
            self.logger.warning("Could not find job listings in Google search results")
            return jobs
        
        for widget in job_widgets[:10]:  # Limit to 10 results
            try:
                # Try different possible selectors for job elements
                # These selectors may change as Google updates its UI
                title_elem = widget.select_one('div.BjJfJf') or widget.select_one('h3') or widget.select_one('a.jobtitle')
                company_elem = widget.select_one('div.vNEEBe') or widget.select_one('div.HnYYW') or widget.select_one('div.company')
                location_elem = widget.select_one('div.Qk80Jf') or widget.select_one('div.location') 
                
                if not title_elem:
                    continue
                
                # Extract job title
                job_title = title_elem.text.strip()
                
                # Extract company name
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                
                # Extract location
                job_location = location_elem.text.strip() if location_elem else location or "Location not specified"
                
                # Try to find a link element
                link_elem = title_elem.parent if title_elem.name == 'a' else title_elem.find('a')
                job_link = link_elem.get('href', '') if link_elem else ''
                
                # Clean up the link
                if job_link and not job_link.startswith('http'):
                    job_link = f"https://www.google.com{job_link}"
                
                # Try to extract description from search snippet
                description_elem = widget.select_one('div.yDiU8d') or widget.select_one('div.job-snippet')
                description = description_elem.text.strip() if description_elem else "No description available"
                
                # Try to extract salary information
                salary_elem = widget.select_one('div.SuWscb') or widget.select_one('div.salary')
                salary = salary_elem.text.strip() if salary_elem else "Not specified"
                
                # Create Job object
                job = Job(
                    job_title=job_title,
                    company=company,
                    experience="Not specified",  # Not directly available in search results
                    jobNature=job_nature or self._extract_job_nature(description),
                    location=job_location,
                    salary=salary,
                    apply_link=job_link,
                    description=description,
            source="Google Jobs"
                )
                
                jobs.append(job)
                
            except Exception as e:
                self.logger.error(f"Error parsing Google job listing: {e}")
        
        # If we couldn't extract job details using the main approach, try the secondary approach
        if not jobs:
            jobs = await self._parse_search_results_alternative(html, position, location, job_nature)
        
        return jobs
    
    async def _parse_search_results_alternative(self, html: str, position: str, location: Optional[str], job_nature: Optional[str]) -> List[Job]:
        """Alternative method to parse Google Jobs search results"""
        jobs = []
        
        # Look for structured job data in the page
        script_data = re.search(r'(\[{.*?"job_results".*?}\])', html)
        if script_data:
            try:
                # Extract and parse JSON data
                json_str = script_data.group(1)
                data = json.loads(json_str)
                
                # Find job results in the data
                for item in data:
                    if "job_results" in item:
                        job_results = item["job_results"].get("results", [])
                        
                        for job_data in job_results[:10]:  # Limit to 10 results
                            try:
                                title = job_data.get("title", "")
                                company = job_data.get("company_name", "")
                                job_location = job_data.get("location", location or "")
                                description = job_data.get("description", job_data.get("snippet", ""))
                                link = job_data.get("apply_link", job_data.get("job_url", ""))
                                salary = job_data.get("salary", "Not specified")
                                
                                if title:
                                    job = Job(
                                        job_title=title,
                                        company=company,
                                        experience="Not specified",
                                        jobNature=job_nature or self._extract_job_nature(description),
                                        location=job_location,
                                        salary=salary,
                                        apply_link=link,
                                        description=description[:500] + "..." if len(description) > 500 else description,
            source="Google Jobs"
                                    )
                                    jobs.append(job)
                            except Exception as e:
                                self.logger.error(f"Error parsing Google job data: {e}")
            except Exception as e:
                self.logger.error(f"Error parsing Google Jobs structured data: {e}")
        
        return jobs
    
    def _extract_job_nature(self, text: str) -> str:
        """Extract job nature from job description"""
        if not text:
            return "Not specified"
            
        text = text.lower()
        
        if "remote" in text:
            return "Remote"
        if "hybrid" in text:
            return "Hybrid"
        if "on-site" in text or "onsite" in text or "in office" in text or "in-person" in text:
            return "Onsite"
        
        return "Not specified"
