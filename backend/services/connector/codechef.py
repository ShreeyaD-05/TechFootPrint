import httpx
from typing import Dict, List, Optional
from datetime import datetime
from services.connector.base import BaseConnector, ProblemData, ContestData, ProfileData
import re

class CodeChefConnector(BaseConnector):
    """CodeChef platform connector using web scraping (API has rate limits)"""
    
    @property
    def platform_name(self) -> str:
        return "codechef"
    
    async def authenticate(self) -> bool:
        return True
    
    async def fetch_profile(self) -> ProfileData:
        async with httpx.AsyncClient() as client:
            try:
                # Try the unofficial API first
                response = await client.get(
                    f"https://codechef-api.vercel.app/handle/{self.username}",
                    timeout=15.0,
                    follow_redirects=True
                )
                
                # If API returns 402 (payment required) or fails, scrape the profile page
                if response.status_code == 402 or response.status_code >= 400:
                    print(f"CodeChef API unavailable (status {response.status_code}), trying web scraping...")
                    return await self._scrape_profile(client)
                
                data = response.json()
                
                if not data.get("success", True):
                    print("CodeChef API returned success=false, trying web scraping...")
                    return await self._scrape_profile(client)
                
                # Extract stats from API
                total_solved = data.get("totalProblemsSolved", 0)
                easy = data.get("easySolved", 0)
                medium = data.get("mediumSolved", 0)
                hard = data.get("hardSolved", 0)
                
                # If no difficulty breakdown, estimate
                if easy == 0 and medium == 0 and hard == 0 and total_solved > 0:
                    easy = int(total_solved * 0.4)
                    medium = int(total_solved * 0.4)
                    hard = total_solved - easy - medium
                
                return ProfileData(
                    username=self.username,
                    rating=data.get("currentRating", 0),
                    rank=str(data.get("globalRank", 0)) if data.get("globalRank") else None,
                    total_solved=total_solved,
                    easy_solved=easy,
                    medium_solved=medium,
                    hard_solved=hard
                )
            except Exception as e:
                print(f"CodeChef API error: {e}, trying web scraping...")
                return await self._scrape_profile(client)
    
    async def _scrape_profile(self, client: httpx.AsyncClient) -> ProfileData:
        """Scrape CodeChef profile page as fallback"""
        try:
            response = await client.get(
                f"https://www.codechef.com/users/{self.username}",
                timeout=15.0,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                follow_redirects=True
            )
            
            if response.status_code != 200:
                print(f"CodeChef profile page returned status {response.status_code}")
                raise Exception(f"Failed to fetch profile: HTTP {response.status_code}")
            
            html = response.text
            
            # Debug: Save HTML to see structure
            # with open('codechef_debug.html', 'w', encoding='utf-8') as f:
            #     f.write(html)
            
            # Extract total problems solved - try multiple patterns
            total_solved = 0
            
            # Pattern 1: Look for "Fully Solved" with number
            patterns = [
                r'<h3[^>]*>(\d+)</h3>\s*<[^>]*>Fully\s*Solved',
                r'Fully\s*Solved[^>]*>(\d+)',
                r'<div[^>]*class="[^"]*problems-solved[^"]*"[^>]*>(\d+)',
                r'Problems\s*Solved[^>]*>(\d+)',
                r'<section[^>]*>\s*<h3>(\d+)</h3>\s*<p>Fully Solved</p>',
                r'<div[^>]*>\s*<h3>(\d+)</h3>\s*<p>Fully Solved</p>',
                r'"problemsFullySolved"\s*:\s*(\d+)',
                r'"problemsSolved"\s*:\s*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    total_solved = int(match.group(1))
                    print(f"Found {total_solved} problems using pattern: {pattern[:50]}...")
                    break
            
            # Extract rating - try multiple patterns
            rating = 0
            rating_patterns = [
                r'<div[^>]*class="[^"]*rating-number[^"]*"[^>]*>(\d+)</div>',
                r'"rating"\s*:\s*(\d+)',
                r'Rating[^>]*>(\d+)',
                r'<div[^>]*rating[^>]*>(\d+)</div>',
            ]
            
            for pattern in rating_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    rating = int(match.group(1))
                    print(f"Found rating {rating}")
                    break
            
            # If still no data found, check if profile exists
            if total_solved == 0 and 'User not found' in html:
                print(f"CodeChef user '{self.username}' not found")
                raise Exception(f"CodeChef user '{self.username}' does not exist")
            
            # Estimate difficulty breakdown (CodeChef doesn't show this on profile)
            if total_solved > 0:
                easy = int(total_solved * 0.4)
                medium = int(total_solved * 0.4)
                hard = total_solved - easy - medium
            else:
                easy = medium = hard = 0
            
            print(f"Scraped CodeChef profile: {total_solved} problems, rating {rating}")
            
            return ProfileData(
                username=self.username,
                rating=rating if rating > 0 else None,
                total_solved=total_solved,
                easy_solved=easy,
                medium_solved=medium,
                hard_solved=hard
            )
        except Exception as e:
            print(f"Error scraping CodeChef profile: {e}")
            # Return minimal data instead of failing
            return ProfileData(
                username=self.username,
                total_solved=0,
                easy_solved=0,
                medium_solved=0,
                hard_solved=0
            )
    
    async def fetch_problem_stats(self) -> List[ProblemData]:
        # CodeChef doesn't provide detailed problem list easily
        # Would require authentication or complex scraping
        return []
    
    async def fetch_contest_stats(self) -> List[ContestData]:
        # Contest data not easily accessible without API
        return []
    
    async def fetch_activity(self, days: int = 30) -> List[Dict]:
        return []
