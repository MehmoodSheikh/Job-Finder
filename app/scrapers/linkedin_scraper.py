"""
LinkedIn job scraper implementation
"""
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

import httpx
from bs4 import BeautifulSoup

from app.models.job import Job
from app.scrapers.base_scraper import BaseScraper


class LinkedInScraper(BaseScraper):
    """
    Scraper for LinkedIn jobs
    
    Notes:
        LinkedIn has a partner API program, but it requires application approval:
        https://developer.linkedin.com/product-catalog
        
        This implementation uses web scraping as a fallback approach.
    """
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.api_base_url = "https://www.linkedin.com/voyager/api/search/hits"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept": "application/vnd.linkedin.normalized+json+2.1",
            "Accept-Language": "en-US,en;q=0.9",
            "csrf-token": "",  # Will need to be populated from cookies
            "Referer": "https://www.linkedin.com/jobs/search/",
        }
        
    async def _get_csrf_token(self):
        """
        Get CSRF token and cookies from LinkedIn
        
        Returns:
            Updated headers with CSRF token
        """
        try:
            response = await self.client.get("https://www.linkedin.com/")
            cookies = response.cookies
            
            if 'JSESSIONID' in cookies:
                jsession_id = cookies['JSESSIONID']
                # LinkedIn stores the CSRF token in the JSESSIONID cookie
                csrf_token = jsession_id.replace('"', '')
                self.headers["csrf-token"] = csrf_token
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error getting CSRF token: {e}")
            return False
    
    async def search_jobs(self, 
                    position: str,
                    location: Optional[str] = None,
                    experience: Optional[str] = None,
                    job_nature: Optional[str] = None,
                    **kwargs) -> List[Job]:
        """
        Search for jobs on LinkedIn based on the provided criteria
        """
        try:
            # Try API first
            if await self._get_csrf_token():
                try:
                    jobs = await self._search_via_api(position, location, experience, job_nature)
                    if jobs:
                        # Standardize job nature based on title and description
                        for job in jobs:
                            self.standardize_job_nature(job)
                        return jobs
                except Exception as e:
                    self.logger.error(f"LinkedIn API search failed: {e}")
                
            # Try direct HTML scraping next
            try:
                self.logger.info("Falling back to LinkedIn HTML scraping")
                jobs = await self._search_jobs_simple(position, location, job_nature)
                if jobs:
                    # Standardize job nature based on title and description
                    for job in jobs:
                        self.standardize_job_nature(job)
                    return jobs
            except Exception as e:
                self.logger.error(f"LinkedIn HTML scraping failed: {e}")
            
            # Try RSS feed as a last resort
            try:
                self.logger.info("Trying LinkedIn RSS feed method")
                jobs = await self._search_jobs_rss(position, location)
                if jobs:
                    # Standardize job nature based on title and description
                    for job in jobs:
                        self.standardize_job_nature(job)
                    return jobs
            except Exception as e:
                self.logger.error(f"LinkedIn RSS scraping failed: {e}")
            
            return []
        
        except Exception as e:
            self.logger.error(f"All LinkedIn scraping methods failed: {e}")
            return []
    
    async def _search_via_api(self, position: str, location: Optional[str], 
                           experience: Optional[str], job_nature: Optional[str]) -> List[Job]:
        """LinkedIn API search implementation"""
        # Build API parameters
        params = {
            "keywords": position,
            "locationUnion": location or "",
            "origin": "JOB_SEARCH_PAGE",
            "start": 0,
            "count": 25,
        }
        
        # Add filters
        if job_nature:
            # Map job nature to LinkedIn's work type filter
            job_type_map = {
                "remote": "1",
                "onsite": "2", 
                "hybrid": "3"
            }
            if job_nature.lower() in job_type_map:
                params["f_WT"] = job_type_map[job_nature.lower()]
        
        if experience:
            exp_level = self._map_experience_to_linkedin_filter(experience)
            if exp_level:
                params["f_E"] = exp_level
        
        # Make API request
        data = await self._make_request(
            "get", 
            self.api_base_url,
            params=params,
            headers=self.headers
        )
        
        # Parse response
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return []
        
        return self._parse_api_response(data)
    
    def _map_experience_to_linkedin_filter(self, experience: str) -> Optional[str]:
        """Map experience string to LinkedIn filter codes"""
        if re.search(r'0|entry|intern|junior', experience.lower()):
            return "1"  # Internship or Entry level
        elif re.search(r'1|2|3|associate|mid', experience.lower()):
            return "2"  # Associate or Mid-Senior level
        elif re.search(r'4|5|6|7|senior', experience.lower()):
            return "3"  # Senior level
        elif re.search(r'8|9|10|director', experience.lower()):
            return "4"  # Director level
        elif re.search(r'executive|ceo|cto|cfo|vp', experience.lower()):
            return "5"  # Executive level
        return None
    
    def _parse_api_response(self, data: Dict[str, Any]) -> List[Job]:
        """Parse LinkedIn API response into Job objects"""
        jobs = []
        
        try:
            if 'elements' in data:
                for element in data['elements']:
                    if 'jobPosting' not in element:
                        continue
                    
                    job_data = element['jobPosting']
                    
                    job = Job(
                        job_title=job_data.get('title', ''),
                        company=job_data.get('companyName', ''),
                        experience="Not specified",  # LinkedIn doesn't always provide this directly
                        jobNature=self._extract_job_nature(job_data),
                        location=job_data.get('location', ''),
                        salary=job_data.get('salary', 'Not specified'),
                        apply_link=f"https://www.linkedin.com/jobs/view/{job_data.get('id', '')}",
                        description=job_data.get('description', '')[:500] + '...',
            source="LinkedIn"
                    )
                    jobs.append(job)
        except Exception as e:
            self.logger.error(f"Error parsing LinkedIn API response: {e}")
        
        return jobs
    
    def _extract_job_nature(self, job_data: Dict[str, Any]) -> str:
        """Extract job nature from LinkedIn job data"""
        try:
            if 'workRemoteAllowed' in job_data and job_data['workRemoteAllowed']:
                return "Remote"
            
            # Try to extract from title or description
            for field in ['title', 'description']:
                if field in job_data:
                    text = job_data[field].lower()
                    if 'remote' in text:
                        return "Remote"
                    if 'hybrid' in text:
                        return "Hybrid"
                    if 'on-site' in text or 'onsite' in text or 'in office' in text:
                        return "Onsite"
        except Exception:
            pass
        
        return "Not specified"
    
    async def _search_jobs_simple(self, position: str, location: Optional[str], job_nature: Optional[str]) -> List[Job]:
        """Simple web scraping fallback method for LinkedIn jobs"""
        jobs = []
        
        query_params = {
            "keywords": position,
            "location": location or "",
            "f_AL": "true",  # All LinkedIn
        }
        
        # Add work type filter if specified
        if job_nature:
            job_type_map = {
                "remote": "1",
                "onsite": "2", 
                "hybrid": "3"
            }
            if job_nature.lower() in job_type_map:
                query_params["f_WT"] = job_type_map[job_nature.lower()]
        
        search_url = f"{self.base_url}?{urlencode(query_params)}"
        
        try:
            resp = await self.client.get(search_url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            job_cards = soup.select('div.job-search-card')
            
            for card in job_cards[:10]:  # Limit to 10 results
                try:
                    title_elem = card.select_one('h3.base-search-card__title')
                    company_elem = card.select_one('h4.base-search-card__subtitle')
                    location_elem = card.select_one('span.job-search-card__location')
                    link_elem = card.select_one('a.base-card__full-link')
                    
                    if not all([title_elem, company_elem, location_elem, link_elem]):
                        continue
                    
                    job_id = link_elem.get('href', '').split('/')[-1].split('?')[0]
                    
                    job_nature = "Not specified"
                    if "remote" in title_elem.text.lower() or "work from home" in title_elem.text.lower():
                        job_nature = "Remote"
                    elif "hybrid" in title_elem.text.lower():
                        job_nature = "Hybrid"
                    elif "onsite" in title_elem.text.lower() or "on-site" in title_elem.text.lower():
                        job_nature = "Onsite"
                    else:
                        # Try to infer from description
                        description_lower = title_elem.text.lower()
                        if "remote" in description_lower or "work from home" in description_lower:
                            job_nature = "Remote"
                        elif "hybrid" in description_lower:
                            job_nature = "Hybrid"
                        elif "onsite" in description_lower or "on-site" in description_lower or "in office" in description_lower:
                            job_nature = "Onsite"
                    
                    job = Job(
                        job_title=title_elem.text.strip(),
                        company=company_elem.text.strip(),
                        experience="Not specified",
                        jobNature=job_nature,
                        location=location_elem.text.strip(),
                        salary="Not specified",
                        apply_link=f"https://www.linkedin.com/jobs/view/{job_id}",
                        description=await self._fetch_job_description(job_id),
            source="LinkedIn"
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing LinkedIn job card: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in LinkedIn simple search: {e}")
        
        return jobs
    
    async def _fetch_job_description(self, job_id: str) -> str:
        """Fetch job description from LinkedIn job page"""
        try:
            url = f"https://www.linkedin.com/jobs/view/{job_id}"
            resp = await self.client.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            description_elem = soup.select_one('div.description__text')
            if description_elem:
                return self._clean_text(description_elem.text)[:500] + '...'
        except Exception as e:
            self.logger.error(f"Error fetching job description: {e}")
        
        return "No description available"

    async def _search_jobs_rss(self, position: str, location: Optional[str] = None) -> List[Job]:
        """
        Search LinkedIn jobs using their RSS feeds (more reliable than API/HTML)
        """
        query = position.replace(" ", "+")
        location_param = f"+{location.replace(' ', '+')}" if location else ""
        
        url = f"https://www.linkedin.com/jobs/search/rss?keywords={query}{location_param}"
        
        try:
            response = await self._make_request("get", url)
            if isinstance(response, dict):
                return []
            
            # Parse RSS feed with BeautifulSoup
            soup = BeautifulSoup(response, 'xml')  # Use XML parser for RSS
            items = soup.find_all('item')
            
            jobs = []
            for item in items:
                title = item.find('title').text if item.find('title') else ""
                link = item.find('link').text if item.find('link') else ""
                description = item.find('description').text if item.find('description') else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') else ""
                
                # Basic parsing to extract company and location
                company = "LinkedIn Company"
                job_location = location or "Not specified"
                
                if "at " in title and " in " in title:
                    title_parts = title.split("at ")
                    if len(title_parts) > 1:
                        title = title_parts[0].strip()
                        company_loc = title_parts[1].strip()
                        if " in " in company_loc:
                            company_parts = company_loc.split(" in ")
                            company = company_parts[0].strip()
                            job_location = company_parts[1].strip()
                
                job_nature = "Not specified"
                if "remote" in title.lower() or "work from home" in title.lower():
                    job_nature = "Remote"
                elif "hybrid" in title.lower():
                    job_nature = "Hybrid"
                elif "onsite" in title.lower() or "on-site" in title.lower():
                    job_nature = "Onsite"
                else:
                    # Try to infer from description
                    description_lower = description.lower()
                    if "remote" in description_lower or "work from home" in description_lower:
                        job_nature = "Remote"
                    elif "hybrid" in description_lower:
                        job_nature = "Hybrid"
                    elif "onsite" in description_lower or "on-site" in description_lower or "in office" in description_lower:
                        job_nature = "Onsite"
                
                job = Job(
                    job_title=title,
                    company=company,
                    experience="Not specified",
                    jobNature=job_nature,
                    location=job_location,
                    salary="Not specified",
                    apply_link=link,
                    description=description,
                    source="LinkedIn"
                )
                jobs.append(job)
            
            return jobs
        
        except Exception as e:
            self.logger.error(f"Error in LinkedIn RSS scraping: {e}")
            return []
