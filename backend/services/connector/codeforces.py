import httpx
from typing import Dict, List, Optional
from datetime import datetime
from services.connector.base import BaseConnector, ProblemData, ContestData, ProfileData

class CodeforcesConnector(BaseConnector):
    """Codeforces platform connector using official API"""
    
    API_BASE = "https://codeforces.com/api"
    
    @property
    def platform_name(self) -> str:
        return "codeforces"
    
    async def authenticate(self) -> bool:
        # Codeforces public API doesn't require authentication
        return True
    
    async def fetch_profile(self) -> ProfileData:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/user.info?handles={self.username}")
            data = response.json()
            
            if data["status"] != "OK":
                raise Exception(f"Failed to fetch profile: {data.get('comment')}")
            
            user = data["result"][0]
            
            # Get submission stats
            submissions_response = await client.get(
                f"{self.API_BASE}/user.status?handle={self.username}"
            )
            submissions_data = submissions_response.json()
            
            solved_problems = {}
            easy = medium = hard = 0
            
            if submissions_data["status"] == "OK":
                for sub in submissions_data["result"]:
                    if sub["verdict"] == "OK":
                        problem = sub["problem"]
                        problem_id = f"{problem['contestId']}{problem['index']}"
                        
                        if problem_id not in solved_problems:
                            # Categorize by rating
                            if "rating" in problem:
                                rating = problem["rating"]
                                if rating < 1200:
                                    easy += 1
                                elif rating < 1800:
                                    medium += 1
                                else:
                                    hard += 1
                            solved_problems[problem_id] = True
            
            total = len(solved_problems)
            
            return ProfileData(
                username=self.username,
                rating=user.get("rating"),
                rank=user.get("rank"),
                total_solved=total,
                easy_solved=easy,
                medium_solved=medium,
                hard_solved=hard
            )
    
    async def fetch_problem_stats(self) -> List[ProblemData]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.API_BASE}/user.status?handle={self.username}")
            data = response.json()
            
            if data["status"] != "OK":
                return []
            
            solved_map = {}
            for sub in data["result"]:
                if sub["verdict"] == "OK":
                    problem = sub["problem"]
                    problem_id = f"{problem['contestId']}{problem['index']}"
                    
                    if problem_id not in solved_map:
                        difficulty = "Unknown"
                        if "rating" in problem:
                            rating = problem["rating"]
                            if rating < 1200:
                                difficulty = "Easy"
                            elif rating < 1800:
                                difficulty = "Medium"
                            else:
                                difficulty = "Hard"
                        
                        solved_map[problem_id] = ProblemData(
                            problem_id=problem_id,
                            title=problem["name"],
                            difficulty=difficulty,
                            topics=problem.get("tags", []),
                            solved_at=datetime.fromtimestamp(sub["creationTimeSeconds"])
                        )
            
            return list(solved_map.values())
    
    async def fetch_contest_stats(self) -> List[ContestData]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/user.rating?handle={self.username}"
            )
            data = response.json()
            
            if data["status"] != "OK":
                return []
            
            contests = []
            for contest in data["result"]:
                contests.append(ContestData(
                    contest_id=str(contest["contestId"]),
                    contest_name=contest["contestName"],
                    rating=contest["newRating"],
                    rank=contest["rank"],
                    problems_solved=0,  # Not directly available
                    contest_date=datetime.fromtimestamp(contest["ratingUpdateTimeSeconds"])
                ))
            
            return contests
    
    async def fetch_activity(self, days: int = 30) -> List[Dict]:
        problems = await self.fetch_problem_stats()
        cutoff = datetime.now().timestamp() - (days * 86400)
        
        return [
            {
                "type": "problem_solved",
                "title": p.title,
                "date": p.solved_at
            }
            for p in problems
            if p.solved_at and p.solved_at.timestamp() > cutoff
        ]
