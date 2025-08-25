# backend/app/services/job_sourcing_engine.py
"""
Automated Job Sourcing Engine
Multi-source job discovery with intelligent filtering and real-time alerts
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import re
import hashlib
from abc import ABC, abstractmethod
import time
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobPosting:
    """Standardized job posting data structure"""
    external_id: str
    title: str
    company: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: str = "Full-time"
    remote_option: bool = False
    description: str = ""
    requirements: str = ""
    posted_date: datetime = None
    expires_date: Optional[datetime] = None
    application_url: str = ""
    source: str = ""
    source_url: str = ""
    benefits: str = ""
    company_size: Optional[str] = None
    industry: Optional[str] = None

@dataclass
class SearchCriteria:
    """Job search criteria for sourcing"""
    keywords: List[str]
    locations: List[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_types: List[str] = None  # full-time, part-time, contract
    remote_preference: str = "hybrid"  # remote, hybrid, onsite, any
    experience_levels: List[str] = None  # entry, mid, senior, executive
    company_sizes: List[str] = None  # startup, small, medium, large
    industries: List[str] = None
    exclude_companies: List[str] = None
    posted_within_days: int = 30

class JobSourcer(ABC):
    """Base class for job sourcing from different platforms"""
    
    def __init__(self, source_name: str, rate_limit_delay: float = 1.0):
        self.source_name = source_name
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
    async def rate_limit(self):
        """Implement rate limiting to be respectful to job boards"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
            
        self.last_request_time = time.time()
    
    @abstractmethod
    async def search_jobs(self, criteria: SearchCriteria, limit: int = 50) -> List[JobPosting]:
        """Search for jobs based on criteria"""
        pass
    
    def generate_job_id(self, title: str, company: str, location: str, source_url: str = "") -> str:
        """Generate unique job ID for deduplication"""
        unique_string = f"{title}_{company}_{location}_{source_url}_{self.source_name}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def clean_salary_text(self, salary_text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract salary range from text"""
        if not salary_text:
            return None, None
            
        # Remove currency symbols and normalize
        salary_text = salary_text.replace('$', '').replace(',', '').lower()
        
        # Look for ranges like "80k - 120k" or "80000 - 120000"
        range_pattern = r'(\d+)k?\s*-\s*(\d+)k?'
        match = re.search(range_pattern, salary_text)
        
        if match:
            min_sal = int(match.group(1))
            max_sal = int(match.group(2))
            
            # Convert k to thousands if needed
            if min_sal < 1000:
                min_sal *= 1000
            if max_sal < 1000:
                max_sal *= 1000
                
            return min_sal, max_sal
            
        # Look for single values like "100k" or "up to 150k"
        single_pattern = r'(?:up to )?(\d+)k?'
        match = re.search(single_pattern, salary_text)
        
        if match:
            salary = int(match.group(1))
            if salary < 1000:
                salary *= 1000
            return salary, salary
            
        return None, None

class IndeedJobSourcer(JobSourcer):
    """Indeed job sourcing (using their Partner API when available, web scraping as fallback)"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("Indeed", rate_limit_delay=2.0)  # Respectful rate limiting
        self.api_key = api_key
        self.base_url = "https://indeed.com"
        
    async def search_jobs(self, criteria: SearchCriteria, limit: int = 50) -> List[JobPosting]:
        """Search Indeed for jobs"""
        jobs = []
        
        try:
            if self.api_key:
                # Use official API if available
                jobs = await self._search_with_api(criteria, limit)
            else:
                # Fallback to careful web scraping
                jobs = await self._search_with_scraping(criteria, limit)
                
        except Exception as e:
            logger.error(f"Indeed search failed: {e}")
            
        logger.info(f"Found {len(jobs)} jobs from Indeed")
        return jobs[:limit]
    
    async def _search_with_api(self, criteria: SearchCriteria, limit: int) -> List[JobPosting]:
        """Search using Indeed's official API (if available)"""
        # This would use the official Indeed API
        # For now, return empty list as API access is limited
        logger.info("Indeed API not implemented - using scraping fallback")
        return []
    
    async def _search_with_scraping(self, criteria: SearchCriteria, limit: int) -> List[JobPosting]:
        """Carefully scrape Indeed search results"""
        jobs = []
        
        # Build search URL
        keywords = " ".join(criteria.keywords) if criteria.keywords else ""
        location = criteria.locations[0] if criteria.locations else ""
        
        search_params = {
            'q': keywords,
            'l': location,
            'sort': 'date',  # Most recent first
            'limit': min(limit, 50)  # Respect their limits
        }
        
        if criteria.remote_preference == 'remote':
            search_params['remotejob'] = '1'
            
        search_url = f"{self.base_url}/jobs?" + urlencode(search_params)
        
        try:
            await self.rate_limit()
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Mozilla/5.0 (compatible; JobSearchBot/1.0)'}
            ) as session:
                async with session.get(search_url) as response:
                    if response.status != 200:
                        logger.error(f"Indeed returned status {response.status}")
                        return jobs
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Parse job cards (Indeed's structure may change)
                    job_cards = soup.find_all('div', class_='job_seen_beacon')
                    
                    for card in job_cards[:limit]:
                        try:
                            job = self._parse_indeed_job_card(card)
                            if job:
                                jobs.append(job)
                        except Exception as e:
                            logger.warning(f"Failed to parse Indeed job card: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Indeed scraping error: {e}")
            
        return jobs
    
    def _parse_indeed_job_card(self, card) -> Optional[JobPosting]:
        """Parse an Indeed job card"""
        try:
            # Extract title
            title_elem = card.find('h2', class_='jobTitle')
            if not title_elem:
                return None
                
            title_link = title_elem.find('a')
            title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
            
            # Extract company
            company_elem = card.find('span', class_='companyName')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract location
            location_elem = card.find('div', class_='companyLocation')
            location = location_elem.get_text(strip=True) if location_elem else "Unknown Location"
            
            # Extract salary if available
            salary_elem = card.find('span', class_='salary-snippet')
            salary_text = salary_elem.get_text(strip=True) if salary_elem else ""
            salary_min, salary_max = self.clean_salary_text(salary_text)
            
            # Extract job URL
            job_url = ""
            if title_link and title_link.get('href'):
                job_url = self.base_url + title_link.get('href')
            
            # Extract snippet/description
            snippet_elem = card.find('div', class_='summary')
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Check for remote indicators
            remote_option = bool(
                'remote' in title.lower() or 
                'remote' in snippet.lower() or
                'work from home' in snippet.lower()
            )
            
            # Generate unique ID
            external_id = self.generate_job_id(title, company, location, job_url)
            
            return JobPosting(
                external_id=external_id,
                title=title,
                company=company,
                location=location,
                salary_min=salary_min,
                salary_max=salary_max,
                description=snippet,
                remote_option=remote_option,
                application_url=job_url,
                source="Indeed",
                source_url=job_url,
                posted_date=datetime.now()  # Would extract actual date in production
            )
            
        except Exception as e:
            logger.warning(f"Error parsing Indeed job card: {e}")
            return None

class LinkedInJobSourcer(JobSourcer):
    """LinkedIn job sourcing"""
    
    def __init__(self, access_token: Optional[str] = None):
        super().__init__("LinkedIn", rate_limit_delay=3.0)  # More conservative
        self.access_token = access_token
        self.base_url = "https://www.linkedin.com"
        
    async def search_jobs(self, criteria: SearchCriteria, limit: int = 50) -> List[JobPosting]:
        """Search LinkedIn for jobs"""
        jobs = []
        
        try:
            # LinkedIn requires authentication for API access
            # For demo purposes, we'll simulate job results
            jobs = await self._simulate_linkedin_jobs(criteria, limit)
            
        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
            
        logger.info(f"Found {len(jobs)} jobs from LinkedIn")
        return jobs[:limit]
    
    async def _simulate_linkedin_jobs(self, criteria: SearchCriteria, limit: int) -> List[JobPosting]:
        """Simulate LinkedIn job results for demo"""
        await self.rate_limit()  # Respect rate limits even in simulation
        
        # Simulate realistic job data
        sample_jobs = [
            {
                'title': 'Senior Python Developer',
                'company': 'TechCorp Solutions', 
                'location': 'San Francisco, CA',
                'salary_min': 130000,
                'salary_max': 170000,
                'remote_option': True,
                'description': 'Join our team building scalable Python applications. 5+ years experience required.'
            },
            {
                'title': 'Full Stack Engineer',
                'company': 'InnovateNow Inc',
                'location': 'Remote',
                'salary_min': 110000,
                'salary_max': 150000, 
                'remote_option': True,
                'description': 'React + Node.js developer needed for fintech startup. Great benefits and equity.'
            },
            {
                'title': 'DevOps Engineer',
                'company': 'CloudFirst Systems',
                'location': 'Austin, TX',
                'salary_min': 120000,
                'salary_max': 160000,
                'remote_option': False,
                'description': 'AWS expert needed for infrastructure automation. Kubernetes and Docker required.'
            }
        ]
        
        jobs = []
        keywords_lower = [k.lower() for k in (criteria.keywords or [])]
        
        for i, job_data in enumerate(sample_jobs):
            if len(jobs) >= limit:
                break
                
            # Filter by keywords
            if keywords_lower:
                job_text = f"{job_data['title']} {job_data['description']}".lower()
                if not any(keyword in job_text for keyword in keywords_lower):
                    continue
            
            # Filter by remote preference
            if criteria.remote_preference == 'remote' and not job_data['remote_option']:
                continue
                
            external_id = self.generate_job_id(
                job_data['title'], 
                job_data['company'], 
                job_data['location'],
                f"linkedin_job_{i}"
            )
            
            jobs.append(JobPosting(
                external_id=external_id,
                title=job_data['title'],
                company=job_data['company'],
                location=job_data['location'],
                salary_min=job_data['salary_min'],
                salary_max=job_data['salary_max'],
                remote_option=job_data['remote_option'],
                description=job_data['description'],
                application_url=f"https://linkedin.com/jobs/view/12345{i}",
                source="LinkedIn",
                source_url=f"https://linkedin.com/jobs/view/12345{i}",
                posted_date=datetime.now() - timedelta(days=i)
            ))
        
        return jobs

class RemoteOKJobSourcer(JobSourcer):
    """RemoteOK job sourcing for remote positions"""
    
    def __init__(self):
        super().__init__("RemoteOK", rate_limit_delay=1.5)
        self.base_url = "https://remoteok.io"
        
    async def search_jobs(self, criteria: SearchCriteria, limit: int = 50) -> List[JobPosting]:
        """Search RemoteOK for remote jobs"""
        jobs = []
        
        try:
            jobs = await self._search_remoteok_api(criteria, limit)
        except Exception as e:
            logger.error(f"RemoteOK search failed: {e}")
            
        logger.info(f"Found {len(jobs)} jobs from RemoteOK")
        return jobs[:limit]
    
    async def _search_remoteok_api(self, criteria: SearchCriteria, limit: int) -> List[JobPosting]:
        """Search using RemoteOK's API"""
        jobs = []
        
        await self.rate_limit()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'JobSearch/1.0'}
            ) as session:
                
                # RemoteOK has a simple API endpoint
                api_url = f"{self.base_url}/api"
                
                async with session.get(api_url) as response:
                    if response.status != 200:
                        logger.error(f"RemoteOK API returned status {response.status}")
                        return jobs
                        
                    data = await response.json()
                    
                    # Filter and parse jobs
                    keywords_lower = [k.lower() for k in (criteria.keywords or [])]
                    
                    for job_data in data[:limit * 2]:  # Get extra to account for filtering
                        if len(jobs) >= limit:
                            break
                            
                        try:
                            # Basic filtering
                            if keywords_lower:
                                job_text = f"{job_data.get('position', '')} {job_data.get('description', '')}".lower()
                                if not any(keyword in job_text for keyword in keywords_lower):
                                    continue
                            
                            # Parse salary
                            salary_min, salary_max = None, None
                            if job_data.get('salary_min'):
                                salary_min = int(job_data['salary_min'])
                            if job_data.get('salary_max'):
                                salary_max = int(job_data['salary_max'])
                            
                            external_id = self.generate_job_id(
                                job_data.get('position', ''),
                                job_data.get('company', ''),
                                'Remote',
                                job_data.get('url', '')
                            )
                            
                            job = JobPosting(
                                external_id=external_id,
                                title=job_data.get('position', 'Unknown Position'),
                                company=job_data.get('company', 'Unknown Company'),
                                location='Remote',
                                salary_min=salary_min,
                                salary_max=salary_max,
                                job_type='Full-time',
                                remote_option=True,
                                description=job_data.get('description', ''),
                                application_url=job_data.get('url', ''),
                                source="RemoteOK",
                                source_url=job_data.get('url', ''),
                                posted_date=datetime.now()
                            )
                            
                            jobs.append(job)
                            
                        except Exception as e:
                            logger.warning(f"Error parsing RemoteOK job: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"RemoteOK API error: {e}")
            
        return jobs

class JobSourcingEngine:
    """
    Main job sourcing engine that coordinates multiple sources
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Initialize job sourcers
        self.sourcers = {
            'indeed': IndeedJobSourcer(self.config.get('indeed_api_key')),
            'linkedin': LinkedInJobSourcer(self.config.get('linkedin_access_token')),
            'remoteok': RemoteOKJobSourcer()
        }
        
        # Job deduplication cache
        self.seen_jobs = set()
        
        logger.info(f"Initialized Job Sourcing Engine with {len(self.sourcers)} sources")
    
    def create_search_criteria_from_user_profile(self, user_profile: Dict) -> SearchCriteria:
        """Create search criteria from user profile and preferences"""
        
        # Extract keywords from user skills and target roles
        keywords = []
        if user_profile.get('current_skills'):
            keywords.extend(user_profile['current_skills'][:5])  # Top 5 skills
        if user_profile.get('target_titles'):
            keywords.extend(user_profile['target_titles'])
        
        # Default search if no specific keywords
        if not keywords:
            keywords = ['software engineer', 'developer']
            
        return SearchCriteria(
            keywords=keywords,
            locations=user_profile.get('preferred_locations', ['Remote']),
            salary_min=user_profile.get('salary_expectation_min'),
            salary_max=user_profile.get('salary_expectation_max'),
            remote_preference=user_profile.get('remote_preference', 'hybrid'),
            experience_levels=[user_profile.get('current_role_level', 'mid')],
            company_sizes=user_profile.get('preferred_company_sizes'),
            industries=user_profile.get('preferred_industries'),
            exclude_companies=user_profile.get('blacklist_companies', []),
            posted_within_days=30
        )
    
    async def source_jobs_for_user(self, user_profile: Dict, sources: List[str] = None, 
                                 limit_per_source: int = 25) -> List[JobPosting]:
        """
        Source jobs for a specific user across multiple platforms
        """
        criteria = self.create_search_criteria_from_user_profile(user_profile)
        
        # Use specified sources or all available
        active_sourcers = sources or list(self.sourcers.keys())
        
        logger.info(f"Sourcing jobs with criteria: {len(criteria.keywords)} keywords, "
                   f"{len(criteria.locations) if criteria.locations else 0} locations")
        
        # Source jobs from all platforms concurrently
        sourcing_tasks = []
        for source_name in active_sourcers:
            if source_name in self.sourcers:
                task = self.sourcers[source_name].search_jobs(criteria, limit_per_source)
                sourcing_tasks.append((source_name, task))
        
        # Execute all sourcing tasks
        all_jobs = []
        results = await asyncio.gather(*[task for _, task in sourcing_tasks], return_exceptions=True)
        
        for (source_name, _), result in zip(sourcing_tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Sourcing from {source_name} failed: {result}")
                continue
                
            source_jobs = result
            logger.info(f"Sourced {len(source_jobs)} jobs from {source_name}")
            all_jobs.extend(source_jobs)
        
        # Deduplicate jobs
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        # Apply advanced filtering
        filtered_jobs = self._apply_advanced_filtering(unique_jobs, criteria)
        
        logger.info(f"Final result: {len(filtered_jobs)} unique, filtered jobs")
        return filtered_jobs
    
    def _deduplicate_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Remove duplicate jobs based on title, company, and location"""
        unique_jobs = []
        
        for job in jobs:
            # Create deduplication key
            dedup_key = f"{job.title.lower()}_{job.company.lower()}_{job.location.lower()}"
            
            if dedup_key not in self.seen_jobs:
                self.seen_jobs.add(dedup_key)
                unique_jobs.append(job)
        
        logger.info(f"Deduplicated {len(jobs)} -> {len(unique_jobs)} jobs")
        return unique_jobs
    
    def _apply_advanced_filtering(self, jobs: List[JobPosting], criteria: SearchCriteria) -> List[JobPosting]:
        """Apply advanced filtering beyond basic keyword matching"""
        filtered_jobs = []
        
        for job in jobs:
            # Salary filtering
            if criteria.salary_min and job.salary_max and job.salary_max < criteria.salary_min:
                continue
            if criteria.salary_max and job.salary_min and job.salary_min > criteria.salary_max:
                continue
                
            # Company blacklist
            if criteria.exclude_companies:
                if any(blocked.lower() in job.company.lower() 
                      for blocked in criteria.exclude_companies):
                    continue
            
            # Remote preference filtering
            if criteria.remote_preference == 'remote' and not job.remote_option:
                continue
            elif criteria.remote_preference == 'onsite' and job.remote_option and 'remote' in job.location.lower():
                continue
                
            # Job age filtering
            if criteria.posted_within_days and job.posted_date:
                age_days = (datetime.now() - job.posted_date).days
                if age_days > criteria.posted_within_days:
                    continue
            
            filtered_jobs.append(job)
        
        return filtered_jobs
    
    async def get_trending_keywords(self, industry: str = None) -> List[Dict[str, any]]:
        """Analyze trending keywords across job postings"""
        # In a real implementation, this would analyze job descriptions
        # For now, return mock trending data
        
        tech_keywords = [
            {'keyword': 'python', 'frequency': 450, 'growth': '+23%'},
            {'keyword': 'react', 'frequency': 380, 'growth': '+18%'},
            {'keyword': 'kubernetes', 'frequency': 220, 'growth': '+45%'},
            {'keyword': 'aws', 'frequency': 340, 'growth': '+31%'},
            {'keyword': 'machine learning', 'frequency': 180, 'growth': '+38%'}
        ]
        
        return tech_keywords[:5]
    
    async def monitor_new_jobs(self, user_profile: Dict, callback_function) -> None:
        """
        Background job monitoring for real-time alerts
        This would run as a background task
        """
        logger.info("Starting job monitoring for user")
        
        while True:
            try:
                # Source new jobs
                new_jobs = await self.source_jobs_for_user(user_profile, limit_per_source=10)
                
                # Filter for truly new jobs (not seen in last runs)
                fresh_jobs = [job for job in new_jobs if job.external_id not in self.seen_jobs]
                
                if fresh_jobs:
                    logger.info(f"Found {len(fresh_jobs)} new jobs")
                    await callback_function(fresh_jobs)
                
                # Sleep before next check (typically 1-6 hours)
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Job monitoring error: {e}")
                await asyncio.sleep(1800)  # 30 minute retry delay

# Testing and usage functions
async def test_job_sourcing():
    """Test the job sourcing engine"""
    
    engine = JobSourcingEngine()
    
    # Sample user profile
    user_profile = {
        'current_skills': ['Python', 'React', 'AWS'],
        'target_titles': ['Software Engineer', 'Full Stack Developer'],
        'preferred_locations': ['San Francisco', 'Remote'],
        'salary_expectation_min': 100000,
        'salary_expectation_max': 180000,
        'remote_preference': 'hybrid',
        'current_role_level': 'senior',
        'preferred_company_sizes': ['medium', 'large'],
        'blacklist_companies': ['BadCompany Inc']
    }
    
    print("🔍 Testing Job Sourcing Engine...")
    print("=" * 60)
    
    # Test job sourcing
    jobs = await engine.source_jobs_for_user(user_profile, limit_per_source=10)
    
    print(f"📊 Sourcing Results:")
    print(f"   Total Jobs Found: {len(jobs)}")
    print(f"   Sources Used: {list(engine.sourcers.keys())}")
    print()
    
    # Display sample jobs
    print("🎯 Sample Job Matches:")
    for i, job in enumerate(jobs[:5], 1):
        print(f"   {i}. {job.title} at {job.company}")
        print(f"      Location: {job.location}")
        if job.salary_min and job.salary_max:
            print(f"      Salary: ${job.salary_min:,} - ${job.salary_max:,}")
        print(f"      Remote: {'Yes' if job.remote_option else 'No'}")
        print(f"      Source: {job.source}")
        print()
    
    # Test trending keywords
    trending = await engine.get_trending_keywords('technology')
    print("📈 Trending Keywords:")
    for keyword in trending:
        print(f"   • {keyword['keyword']}: {keyword['frequency']} jobs ({keyword['growth']})")

if __name__ == "__main__":
    asyncio.run(test_job_sourcing())