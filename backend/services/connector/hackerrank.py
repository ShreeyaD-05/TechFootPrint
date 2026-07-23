import httpx
from typing import Dict, List, Optional
from datetime import datetime
from services.connector.base import BaseConnector, ProblemData, ContestData, ProfileData
import re
import json
from bs4 import BeautifulSoup

class HackerRankConnector(BaseConnector):
    """HackerRank platform connector using GraphQL API"""
    
    GRAPHQL_URL = "https://www.hackerrank.com/graphql"
    
    @property
    def platform_name(self) -> str:
        return "hackerrank"
    
    async def authenticate(self) -> bool:
        return True
    
    async def fetch_profile(self) -> ProfileData:
        """Fetch profile by scraping the profile page HTML"""
        async with httpx.AsyncClient() as client:
            try:
                # Scrape the profile page
                response = await client.get(
                    f"https://www.hackerrank.com/profile/{self.username}",
                    timeout=15.0,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    print(f"HackerRank profile page returned status {response.status_code}")
                    raise Exception(f"Failed to fetch profile: HTTP {response.status_code}")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for embedded JSON data in script tags
                total_solved = 0
                certificates_found = set()  # Use set to avoid duplicates
                
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # Look for certificate names in URL-encoded format
                        # Pattern: %22Python%20(Basic)%22
                        url_cert_pattern = r'%22([A-Z][a-z]+(?:%20|\s)\([A-Za-z]+\))%22'
                        url_certs = re.findall(url_cert_pattern, script.string)
                        
                        for cert in url_certs:
                            import urllib.parse
                            decoded = urllib.parse.unquote(cert)
                            certificates_found.add(decoded)
                        
                        # Also look for plain text certificates
                        plain_cert_pattern = r'"([A-Z][a-z]+\s*\([A-Za-z]+\))"'
                        plain_certs = re.findall(plain_cert_pattern, script.string)
                        for cert in plain_certs:
                            certificates_found.add(cert)
                
                certificates_count = len(certificates_found)
                
                # If we found certificates, estimate problems based on certificates
                # Each certificate typically requires 2-5 problems to earn
                if certificates_count > 0:
                    estimated_problems = certificates_count * 3  # Conservative estimate: 3 problems per cert
                    total_solved = estimated_problems
                    print(f"HackerRank profile: {certificates_count} certificates found ({', '.join(sorted(certificates_found))}), estimated {total_solved} problems")
                else:
                    print(f"HackerRank profile: No certificates or problems found")
                
                # Estimate difficulty distribution
                if total_solved > 0:
                    easy = int(total_solved * 0.3)
                    medium = int(total_solved * 0.5)
                    hard = total_solved - easy - medium
                else:
                    easy = medium = hard = 0
                
                return ProfileData(
                    username=self.username,
                    total_solved=total_solved,
                    easy_solved=easy,
                    medium_solved=medium,
                    hard_solved=hard
                )
                
            except Exception as e:
                print(f"HackerRank scraping error: {e}")
                return ProfileData(
                    username=self.username,
                    total_solved=0,
                    easy_solved=0,
                    medium_solved=0,
                    hard_solved=0
                )
    
    async def fetch_problem_stats(self) -> List[ProblemData]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://www.hackerrank.com/rest/hackers/{self.username}/recent_challenges",
                    timeout=15.0,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    print(f"HackerRank problems fetch returned status {response.status_code}")
                    return []
                
                data = response.json()
                problems = []
                models = data.get("models", [])
                
                for problem in models:
                    try:
                        solved_at = None
                        if problem.get("solved_at"):
                            try:
                                solved_at = datetime.fromisoformat(
                                    problem.get("solved_at").replace("Z", "+00:00")
                                )
                            except:
                                pass
                        
                        problems.append(ProblemData(
                            problem_id=problem.get("slug", problem.get("id", "")),
                            title=problem.get("name", "Unknown"),
                            difficulty=problem.get("difficulty_name", "Medium"),
                            topics=[problem.get("track", {}).get("name", "General")] if problem.get("track") else [],
                            solved_at=solved_at
                        ))
                    except Exception as e:
                        print(f"Error parsing problem: {e}")
                        continue
                
                return problems
            except Exception as e:
                print(f"Error fetching HackerRank problems: {e}")
                return []
    
    async def fetch_contest_stats(self) -> List[ContestData]:
        # HackerRank contest API is not publicly available
        return []
    
    async def fetch_activity(self, days: int = 30) -> List[Dict]:
        problems = await self.fetch_problem_stats()
        return [
            {
                "type": "problem_solved",
                "title": p.title,
                "date": p.solved_at or datetime.now()
            }
            for p in problems[:days]
        ]
