from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from shared.database import get_db
from shared.schemas import BatchAnalytics, DepartmentAnalytics
from services.management.service import ManagementService
from gateway.routes.auth import get_current_user
from shared.models import User

router = APIRouter()

def require_management_role(current_user: User):
    """Ensure user has management or admin role"""
    if current_user.role not in ["dept_admin", "management"]:
        raise HTTPException(status_code=403, detail="Management access required")
    return current_user

@router.get("/overview")
def get_college_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall college analytics"""
    current_user = require_management_role(current_user)
    
    if not current_user.college_id:
        raise HTTPException(status_code=400, detail="User not associated with a college")
    
    overview = ManagementService.get_college_overview(db, current_user.college_id)
    return overview

@router.get("/batch/{batch_year}")
def get_batch_analytics(
    batch_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for a specific batch"""
    current_user = require_management_role(current_user)
    
    if not current_user.college_id:
        raise HTTPException(status_code=400, detail="User not associated with a college")
    
    analytics = ManagementService.get_batch_analytics(db, current_user.college_id, batch_year)
    return analytics

@router.get("/department/{department}")
def get_department_analytics(
    department: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for a specific department"""
    current_user = require_management_role(current_user)
    
    if not current_user.college_id:
        raise HTTPException(status_code=400, detail="User not associated with a college")
    
    analytics = ManagementService.get_department_analytics(db, current_user.college_id, department)
    return analytics

@router.get("/inactive-students")
def get_inactive_students(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get students who haven't been active in specified days"""
    current_user = require_management_role(current_user)
    
    if not current_user.college_id:
        raise HTTPException(status_code=400, detail="User not associated with a college")
    
    students = ManagementService.get_inactive_students(db, current_user.college_id, days)
    return students

@router.get("/placement-readiness/{batch_year}")
def get_placement_readiness(
    batch_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get placement readiness metrics for a batch"""
    current_user = require_management_role(current_user)
    
    if not current_user.college_id:
        raise HTTPException(status_code=400, detail="User not associated with a college")
    
    readiness = ManagementService.get_placement_readiness(db, current_user.college_id, batch_year)
    return readiness

@router.post("/assign-batch-mentor")
def assign_batch_mentor(
    mentor_id: int,
    batch_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a mentor to all students in a batch"""
    current_user = require_management_role(current_user)
    
    if not current_user.college_id:
        raise HTTPException(status_code=400, detail="User not associated with a college")
    
    count = ManagementService.assign_batch_mentor(
        db, mentor_id, batch_year, current_user.college_id, current_user.id
    )
    return {"message": f"Assigned mentor to {count} students", "count": count}
