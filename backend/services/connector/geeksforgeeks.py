import httpx
from typing import Dict, List, Optional
from datetime import datetime
from services.connector.base import BaseConnector, ProblemData, ContestData, ProfileData
import re

class GeeksforGeeksConnector(BaseConnector):
    """GeeksforGeeks platform connector using web scraping"""
    
    BASE_URL = "https://auth.geeksforgeeks.org"
    
    @property
    def platform_name(self) -> str:
        return "geeksforgeeks"
    
    async def authenticate(self) -> bool:
        # GeeksforGeeks doesn't have a public API, using web scraping
        return True
    
    async def fetch_profile(self) -> ProfileData:
        async with httpx.AsyncClient() as client:
            try:
                # Fetch user profile page
                response = await client.get(
                    f"https://auth.geeksforgeeks.org/user/{self.username}/",
                    timeout=10.0,
                    headers={"User-Agent": "Mozilla/5.0"},
                    follow_redirects=True
                )
                
                html = response.text
                
                # Extract problem count using regex
                total_solved = 0
                
                # Look for problem count patterns
                problem_match = re.search(r'Total Problems Solved.*?(\d+)', html, re.IGNORECASE)
                if problem_match:
                    total_solved = int(problem_match.group(1))
                else:
                    # Alternative pattern
                    problem_match = re.search(r'(\d+)\s*Problems?\s*Solved', html, re.IGNORECASE)
                    if problem_match:
                        total_solved = int(problem_match.group(1))
                
                # Extract difficulty breakdown if available
                easy = medium = hard = 0
                easy_match = re.search(r'Easy.*?(\d+)', html)
                medium_match = re.search(r'Medium.*?(\d+)', html)
                hard_match = re.search(r'Hard.*?(\d+)', html)
                
                if easy_match:
                    easy = int(easy_match.group(1))
                if medium_match:
                    medium = int(medium_match.group(1))
                if hard_match:
                    hard = int(hard_match.group(1))
                
                return ProfileData(
                    username=self.username,
                    total_solved=total_solved or (easy + medium + hard),
                    easy_solved=easy,
                    medium_solved=medium,
                    hard_solved=hard
                )
            except Exception:
                # Fallback with minimal data
                return ProfileData(
                    username=self.username,
                    total_solved=0,
                    easy_solved=0,
                    medium_solved=0,
                    hard_solved=0
                )
    
    async def fetch_problem_stats(self) -> List[ProblemData]:
        # GeeksforGeeks doesn't provide detailed problem list via public API
        # Would require authentication and more complex scraping
        return []
    
    async def fetch_contest_stats(self) -> List[ContestData]:
        # GeeksforGeeks contest data not easily accessible
        return []
    
    async def fetch_activity(self, days: int = 30) -> List[Dict]:
        # Activity data not easily accessible without authentication
        return []
