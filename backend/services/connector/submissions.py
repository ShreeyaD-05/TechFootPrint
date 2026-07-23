"""Helper module for fetching detailed submission data"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class SubmissionData(BaseModel):
    submission_id: str
    problem_id: str
    status: str
    language: Optional[str] = None
    runtime: Optional[str] = None
    memory: Optional[str] = None
    submitted_at: datetime
    code: Optional[str] = None
