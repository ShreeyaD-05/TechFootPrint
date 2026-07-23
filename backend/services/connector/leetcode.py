import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime
from services.connector.base import BaseConnector, ProblemData, ContestData, ProfileData

logger = logging.getLogger(__name__)

class LeetCodeConnector(BaseConnector):
    """LeetCode platform connector using GraphQL API"""
    
    GRAPHQL_URL = "https://leetcode.com/graphql"
    
    @property
    def platform_name(self) -> str:
        return "leetcode"
    
    async def authenticate(self) -> bool:
        # LeetCode public API doesn't require authentication for public profiles
        return True
    
    async def fetch_profile(self) -> ProfileData:
        query = """
        query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                username
                profile {
                    ranking
                    userAvatar
                }
                submitStats {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": {"username": self.username}}
            )
            data = response.json()
            
            user_data = data.get("data", {}).get("matchedUser", {})
            submit_stats = user_data.get("submitStats", {}).get("acSubmissionNum", [])
            
            easy = medium = hard = 0
            for stat in submit_stats:
                if stat["difficulty"] == "Easy":
                    easy = stat["count"]
                elif stat["difficulty"] == "Medium":
                    medium = stat["count"]
                elif stat["difficulty"] == "Hard":
                    hard = stat["count"]
            
            return ProfileData(
                username=self.username,
                rating=user_data.get("profile", {}).get("ranking"),
                total_solved=easy + medium + hard,
                easy_solved=easy,
                medium_solved=medium,
                hard_solved=hard
            )
    
    async def fetch_problem_stats(self) -> List[ProblemData]:
        """
        Fetch solved problems from LeetCode.
        Note: LeetCode's public API only provides the 20 most recent AC submissions.
        For a complete list, users would need to authenticate or use LeetCode Premium API.
        """
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get user's solved problem count by difficulty from profile
            profile_query = """
            query getUserProfile($username: String!) {
                matchedUser(username: $username) {
                    submitStatsGlobal {
                        acSubmissionNum {
                            difficulty
                            count
                        }
                    }
                }
            }
            """
            
            profile_response = await client.post(
                self.GRAPHQL_URL,
                json={"query": profile_query, "variables": {"username": self.username}}
            )
            profile_data = profile_response.json()
            
            matched_user = profile_data.get("data", {}).get("matchedUser", {})
            stats = matched_user.get("submitStatsGlobal", {}).get("acSubmissionNum", [])
            
            # Get counts by difficulty
            difficulty_counts = {}
            for stat in stats:
                difficulty_counts[stat["difficulty"]] = stat["count"]
            
            # Fetch recent submissions with details
            recent_query = """
            query getRecentSubmissions($username: String!, $limit: Int!) {
                recentAcSubmissionList(username: $username, limit: $limit) {
                    title
                    titleSlug
                    timestamp
                }
            }
            """
            
            response = await client.post(
                self.GRAPHQL_URL,
                json={"query": recent_query, "variables": {"username": self.username, "limit": 20}}
            )
            data = response.json()
            
            submissions = data.get("data", {}).get("recentAcSubmissionList", [])

            problems = []
            seen_problems = set()
            
            # Query to get problem details
            problem_query = """
            query questionData($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    questionId
                    title
                    titleSlug
                    difficulty
                    topicTags {
                        name
                    }
                }
            }
            """
            
            for sub in submissions:
                problem_slug = sub["titleSlug"]
                if problem_slug not in seen_problems:
                    seen_problems.add(problem_slug)
                    
                    try:
                        detail_response = await client.post(
                            self.GRAPHQL_URL,
                            json={"query": problem_query, "variables": {"titleSlug": problem_slug}},
                            timeout=10.0
                        )
                        detail_data = detail_response.json()
                        question = detail_data.get("data", {}).get("question", {})

                        if question:
                            difficulty = question.get("difficulty", "Medium")
                            title = question.get("title", sub["title"])
                            topics = [tag["name"] for tag in question.get("topicTags", [])]

                            problems.append(ProblemData(
                                problem_id=problem_slug,
                                title=title,
                                difficulty=difficulty,
                                topics=topics,
                                solved_at=datetime.fromtimestamp(int(sub["timestamp"]))
                            ))
                        else:
                            problems.append(ProblemData(
                                problem_id=problem_slug,
                                title=sub["title"],
                                difficulty="Medium",
                                topics=[],
                                solved_at=datetime.fromtimestamp(int(sub["timestamp"]))
                            ))
                    except Exception as e:
                        logger.warning("Error fetching details for %s: %s", problem_slug, e)
                        problems.append(ProblemData(
                            problem_id=problem_slug,
                            title=sub["title"],
                            difficulty="Medium",
                            topics=[],
                            solved_at=datetime.fromtimestamp(int(sub["timestamp"]))
                        ))
            
            return problems
    
    async def fetch_contest_stats(self) -> List[ContestData]:
        query = """
        query getUserContestRanking($username: String!) {
            userContestRanking(username: $username) {
                attendedContestsCount
                rating
                globalRanking
                topPercentage
            }
            userContestRankingHistory(username: $username) {
                contest {
                    title
                    startTime
                }
                rating
                ranking
                problemsSolved
            }
        }
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": {"username": self.username}}
            )
            data = response.json()
            
            history = data.get("data", {}).get("userContestRankingHistory", [])
            contests = []
            
            for contest in history:
                contests.append(ContestData(
                    contest_id=contest["contest"]["title"],
                    contest_name=contest["contest"]["title"],
                    rating=int(contest["rating"]),
                    rank=contest["ranking"],
                    problems_solved=contest["problemsSolved"],
                    contest_date=datetime.fromtimestamp(contest["contest"]["startTime"])
                ))
            
            return contests
    
    async def fetch_activity(self, days: int = 30) -> List[Dict]:
        # Fetch recent submissions as activity
        problems = await self.fetch_problem_stats()
        return [
            {
                "type": "problem_solved",
                "title": p.title,
                "date": p.solved_at
            }
            for p in problems[:days]
        ]
