from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

class ProblemData(BaseModel):
    problem_id: str
    title: str
    difficulty: str
    topics: List[str]
    solved_at: Optional[datetime] = None
    submission_count: int = 1

class ContestData(BaseModel):
    contest_id: str
    contest_name: str
    rating: Optional[int] = None
    rank: Optional[int] = None
    problems_solved: int
    contest_date: datetime

class ProfileData(BaseModel):
    username: str
    user_id: Optional[str] = None
    rating: Optional[int] = None
    rank: Optional[int] = None
    total_solved: int
    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0

class BaseConnector(ABC):
    """Base connector interface for all platform integrations"""
    
    def __init__(self, username: str, credentials: Optional[Dict] = None):
        self.username = username
        self.credentials = credentials or {}
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform if needed"""
        pass
    
    @abstractmethod
    async def fetch_profile(self) -> ProfileData:
        """Fetch user profile data"""
        pass
    
    @abstractmethod
    async def fetch_problem_stats(self) -> List[ProblemData]:
        """Fetch solved problems"""
        pass
    
    @abstractmethod
    async def fetch_contest_stats(self) -> List[ContestData]:
        """Fetch contest participation data"""
        pass
    
    @abstractmethod
    async def fetch_activity(self, days: int = 30) -> List[Dict]:
        """Fetch recent activity"""
        pass
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return platform name"""
        pass
