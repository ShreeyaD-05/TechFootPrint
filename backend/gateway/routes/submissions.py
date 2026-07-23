from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from gateway.routes.auth import get_current_user
from shared.models import User
from services.submissions.service import SubmissionService
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("/submissions")
def get_submissions(
    platform: Optional[str] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user submissions with filters"""
    # Parse dates
    date_from_dt = datetime.fromisoformat(date_from) if date_from else None
    date_to_dt = datetime.fromisoformat(date_to) if date_to else None
    
    result = SubmissionService.get_user_submissions(
        db,
        user_id=current_user.id,
        platform=platform,
        difficulty=difficulty,
        status=status,
        date_from=date_from_dt,
        date_to=date_to_dt,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return result


@router.get("/submissions/stats")
def get_submission_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get submission statistics"""
    stats = SubmissionService.get_submission_stats(db, current_user.id, days)
    return stats


@router.get("/submissions/problem/{platform}/{problem_id}")
def get_problem_submissions(
    platform: str,
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all submissions for a specific problem"""
    submissions = SubmissionService.get_problem_submissions(
        db,
        current_user.id,
        problem_id,
        platform
    )
    return {"submissions": submissions}


@router.get("/submissions/platforms/summary")
def get_platform_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of submissions by platform"""
    summary = SubmissionService.get_platform_summary(db, current_user.id)
    return summary
