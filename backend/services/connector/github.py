import httpx
from typing import Dict, List, Optional
from datetime import datetime
from services.connector.base import BaseConnector, ProblemData, ContestData, ProfileData

class GitHubConnector(BaseConnector):
    """GitHub platform connector using REST API"""
    
    API_BASE = "https://api.github.com"
    
    @property
    def platform_name(self) -> str:
        return "github"
    
    async def authenticate(self) -> bool:
        # GitHub public API works without authentication for public data
        # Can add token support for private repos
        return True
    
    async def fetch_profile(self) -> ProfileData:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/users/{self.username}")
            data = response.json()
            
            # Get repository stats
            repos_response = await client.get(f"{self.API_BASE}/users/{self.username}/repos")
            repos = repos_response.json()
            
            return ProfileData(
                username=self.username,
                user_id=str(data.get("id")),
                total_solved=len(repos),  # Using repo count as metric
                easy_solved=0,
                medium_solved=0,
                hard_solved=0
            )
    
    async def fetch_problem_stats(self) -> List[ProblemData]:
        # GitHub doesn't have "problems" in the traditional sense
        # We can track repositories as projects
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/users/{self.username}/repos")
            repos = response.json()
            
            problems = []
            for repo in repos:
                problems.append(ProblemData(
                    problem_id=str(repo["id"]),
                    title=repo["name"],
                    difficulty="Unknown",
                    topics=repo.get("topics", []),
                    solved_at=datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
                ))
            
            return problems
    
    async def fetch_contest_stats(self) -> List[ContestData]:
        # GitHub doesn't have contests
        return []
    
    async def fetch_activity(self, days: int = 30) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/users/{self.username}/events/public")
            events = response.json()
            
            activities = []
            for event in events[:days]:
                activities.append({
                    "type": event["type"],
                    "repo": event.get("repo", {}).get("name"),
                    "date": datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
                })
            
            return activities
