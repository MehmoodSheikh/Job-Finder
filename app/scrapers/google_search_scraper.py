"""
Google Search based job scraper - an alternative approach
"""
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.models.job import Job
from app.scrapers.base_scraper import BaseScraper


class GoogleSearchScraper(BaseScraper):
    """
    Scraper that uses Google Search to find jobs for any platform
    """
    
    def __init__(self, platform_name="Google", use_proxy=False):
        super().__init__()  # Removed use_proxy parameter as it's not in the base class
        self.platform_name = platform_name
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
        Search for jobs using Google Search
        """
        try:
            # Construct search query 
            query = f"{position} jobs"
            
            # Add location if provided
            if location:
                query += f" in {location}"
            
            # Add job nature if provided
            if job_nature:
                query += f" {job_nature}"
            
            # Add platform name
            if self.platform_name != "Google":
                query += f" site:{self.platform_name.lower()}.com"
            
            # Add experience if provided
            if experience:
                query += f" {experience} experience"
            
            # Add job-specific keywords
            query += " apply career"
            
            # Encode query for URL
            encoded_query = quote_plus(query)
            
            # Construct search URL
            search_url = f"{self.base_url}?q={encoded_query}&num=20"
            
            # Make request
            response = await self._make_request("get", search_url, headers=self.headers)
            
            if isinstance(response, dict):
                self.logger.error("Unexpected JSON response from Google Search")
                return []
            
            # Parse search results
            return await self._parse_search_results(response, position, location, job_nature, experience)  # Pass experience to the parsing function
            
        except Exception as e:
            self.logger.error(f"Error in Google Search scraping: {e}")
            return []
    
    async def _parse_search_results(self, html: str, position: str, location: Optional[str], 
                                  job_nature: Optional[str], job_experience: Optional[str] = None) -> List[Job]:
        """Parse Google Search results for job listings"""
        jobs = []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all search result items
        result_divs = soup.select('div.g')
        
        for i, div in enumerate(result_divs[:10]):  # Process up to 10 results
            try:
                # Extract link and title
                link_elem = div.select_one('a')
                title_elem = div.select_one('h3')
                
                if not link_elem or not title_elem:
                    continue
                
                link = link_elem.get('href', '')
                title = title_elem.text.strip()
                
                # Skip non-job results
                job_keywords = ['job', 'career', 'position', 'hiring', 'vacancy', 'opening']
                if not any(keyword in title.lower() for keyword in job_keywords):
                    continue
                
                # Extract description
                snippet_elem = div.select_one('div.VwiC3b') or div.select_one('span.aCOpRe')
                description = snippet_elem.text.strip() if snippet_elem else "No description available"
                
                # Attempt to extract company name
                company = self.platform_name
                company_patterns = [
                    r'at\s+([A-Za-z0-9\s]+?)\s+in',
                    r'([A-Za-z0-9\s]+?)\s+is\s+hiring',
                    r'([A-Za-z0-9\s]+?)\s+careers',
                ]
                
                for pattern in company_patterns:
                    company_match = re.search(pattern, title + " " + description)
                    if company_match:
                        company = company_match.group(1).strip()
                        break
                
                # Infer job nature from title and description
                inferred_nature = job_nature or "Not specified"
                combined_text = (title + " " + description).lower()
                
                if "remote" in combined_text or "work from home" in combined_text:
                    inferred_nature = "Remote"
                elif "hybrid" in combined_text:
                    inferred_nature = "Hybrid"
                elif "on-site" in combined_text or "onsite" in combined_text or "in office" in combined_text:
                    inferred_nature = "Onsite"
                
                # Create job object
                job = Job(
                    job_title=title,
                    company=company,
                    experience=job_experience or "Not specified",  # Use the parameter passed to this function
                    jobNature=inferred_nature,
                    location=location or "Not specified",
                    salary="Not specified",
                    apply_link=link,
                    description=description,
                    source=self.platform_name
                )
                
                # Standardize the job nature based on title and description
                self.standardize_job_nature(job)
                
                jobs.append(job)
                
            except Exception as e:
                self.logger.error(f"Error parsing Google Search result: {e}")
        
        return jobs 