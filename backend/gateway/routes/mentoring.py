from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from shared.database import get_db
from shared.schemas import (
    MentorAssignmentCreate, MentorAssignmentResponse,
    MentorFeedbackCreate, MentorFeedbackResponse,
    CodingGoalCreate, CodingGoalResponse,
    ProblemNoteCreate, ProblemNoteResponse,
    UserWithRoleResponse, StudentProgressSummary
)
from services.mentoring.service import MentoringService
from gateway.routes.auth import get_current_user
from shared.models import User

router = APIRouter()

@router.post("/assignments", response_model=MentorAssignmentResponse)
def assign_mentor(
    assignment: MentorAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a mentor to a student (requires faculty/admin role)"""
    if current_user.role not in ["faculty", "dept_admin", "management"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = MentoringService.assign_mentor(db, assignment, current_user.id)
    return result

@router.get("/my-students", response_model=List[UserWithRoleResponse])
def get_my_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all students assigned to current mentor"""
    if current_user.role not in ["faculty", "dept_admin", "management"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    students = MentoringService.get_mentor_students(db, current_user.id)
    return students

@router.get("/my-mentor", response_model=UserWithRoleResponse)
def get_my_mentor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the mentor assigned to current student"""
    mentor = MentoringService.get_student_mentor(db, current_user.id)
    if not mentor:
        raise HTTPException(status_code=404, detail="No mentor assigned")
    return mentor

@router.post("/feedback", response_model=MentorFeedbackResponse)
def create_feedback(
    feedback: MentorFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create feedback for a student (mentor only)"""
    if current_user.role not in ["faculty", "dept_admin", "management"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = MentoringService.create_feedback(db, current_user.id, feedback)
    return result

@router.get("/feedback", response_model=List[MentorFeedbackResponse])
def get_my_feedback(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feedback for current student"""
    feedback = MentoringService.get_student_feedback(db, current_user.id, unread_only)
    return feedback

@router.put("/feedback/{feedback_id}/read", response_model=MentorFeedbackResponse)
def mark_feedback_read(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark feedback as read"""
    result = MentoringService.mark_feedback_read(db, feedback_id)
    if not result:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return result

@router.post("/goals", response_model=CodingGoalResponse)
def create_goal(
    goal: CodingGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a coding goal (faculty/admin only)"""
    if current_user.role not in ["faculty", "dept_admin", "management"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = MentoringService.create_goal(db, current_user.id, goal)
    return result

@router.get("/goals", response_model=List[CodingGoalResponse])
def get_my_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get goals for current student"""
    goals = MentoringService.get_student_goals(db, current_user.id)
    return goals

@router.post("/notes", response_model=ProblemNoteResponse)
def create_problem_note(
    note: ProblemNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a note for a problem"""
    result = MentoringService.create_problem_note(db, current_user.id, note)
    return result

@router.get("/notes", response_model=List[ProblemNoteResponse])
def get_my_notes(
    problem_stat_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notes for problems"""
    notes = MentoringService.get_problem_notes(db, current_user.id, problem_stat_id)
    return notes

@router.get("/students/{student_id}/progress")
def get_student_progress(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get progress summary for a student (mentor only)"""
    if current_user.role not in ["faculty", "dept_admin", "management"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    progress = MentoringService.get_student_progress_summary(db, student_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Student not found")
    return progress
