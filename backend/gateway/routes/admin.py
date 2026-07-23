from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from shared.database import get_db
from shared.schemas import (
    CollegeCreate, CollegeUpdate, CollegeResponse, CollegeWithStats,
    UserCreateByAdmin, UserUpdateByAdmin, UserWithRoleResponse,
    SystemStatsResponse, FacultyCreate, FacultyUpdate, FacultyResponse,
    ResetPasswordResponse,
)
from services.admin.service import AdminService
from services.email.service import EmailService
from gateway.routes.auth import get_current_user
from shared.models import User, College

router = APIRouter()

def require_super_admin(current_user: User):
    """Ensure user has super_admin role"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user

@router.get("/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system-wide statistics (super admin only)"""
    current_user = require_super_admin(current_user)
    stats = AdminService.get_system_stats(db)
    return stats

@router.get("/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get admin dashboard data"""
    current_user = require_super_admin(current_user)
    
    stats = AdminService.get_system_stats(db)
    colleges = AdminService.get_all_colleges(db, include_stats=True)
    recent_users = AdminService.get_recent_users(db, limit=10)
    
    # Count by role
    from shared.models import User as UserModel
    total_students = db.query(UserModel).filter(UserModel.role == "student").count()
    total_faculty = db.query(UserModel).filter(
        UserModel.role.in_(["faculty", "dept_admin", "management"])
    ).count()
    
    return {
        **stats,
        "total_students": total_students,
        "total_faculty": total_faculty,
        "colleges_list": colleges,
        "recent_users": recent_users
    }

# College Management
@router.get("/colleges", response_model=List[CollegeWithStats])
def get_all_colleges(
    include_stats: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all colleges"""
    current_user = require_super_admin(current_user)
    colleges = AdminService.get_all_colleges(db, include_stats=include_stats)
    return colleges

@router.post("/colleges", response_model=CollegeResponse)
def create_college(
    college: CollegeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new college"""
    current_user = require_super_admin(current_user)
    
    # Check if code already exists
    from shared.models import College
    existing = db.query(College).filter(College.code == college.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="College code already exists")
    
    new_college = AdminService.create_college(db, college)
    return new_college

@router.put("/colleges/{college_id}", response_model=CollegeResponse)
def update_college(
    college_id: int,
    college_update: CollegeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update college information"""
    current_user = require_super_admin(current_user)
    
    updated_college = AdminService.update_college(db, college_id, college_update)
    if not updated_college:
        raise HTTPException(status_code=404, detail="College not found")
    
    return updated_college

@router.delete("/colleges/{college_id}")
def delete_college(
    college_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (deactivate) a college"""
    current_user = require_super_admin(current_user)
    
    success = AdminService.delete_college(db, college_id)
    if not success:
        raise HTTPException(status_code=404, detail="College not found")
    
    return {"message": "College deactivated successfully"}

# User Management
@router.get("/users", response_model=List[UserWithRoleResponse])
def get_all_users(
    college_id: Optional[int] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users with optional filters"""
    current_user = require_super_admin(current_user)
    users = AdminService.get_all_users(db, college_id=college_id, role=role)
    return users

@router.post("/users", response_model=UserWithRoleResponse)
def create_user(
    user_data: UserCreateByAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user"""
    current_user = require_super_admin(current_user)
    
    try:
        new_user = AdminService.create_user(db, user_data)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/users/{user_id}", response_model=UserWithRoleResponse)
def update_user(
    user_id: int,
    user_update: UserUpdateByAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information"""
    current_user = require_super_admin(current_user)
    
    updated_user = AdminService.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (deactivate) a user"""
    current_user = require_super_admin(current_user)
    
    # Prevent deleting super admins
    user = AdminService.get_user_by_id(db, user_id)
    if user and user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot delete super admin users")
    
    success = AdminService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deactivated successfully"}

@router.get("/users/search")
def search_users(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search users by username, email, or name"""
    current_user = require_super_admin(current_user)
    users = AdminService.search_users(db, q)
    return users

@router.get("/users/{user_id}", response_model=UserWithRoleResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    current_user = require_super_admin(current_user)
    user = AdminService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Faculty Management (super_admin only) ─────────────────────────────────────

@router.get("/faculty", response_model=List[FacultyResponse])
def get_all_faculty(
    college_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all faculty members, optionally filtered by college."""
    require_super_admin(current_user)
    users = AdminService.get_all_faculty(db, college_id=college_id)

    # Enrich with college name
    college_map: dict = {}
    result = []
    for u in users:
        if u.college_id and u.college_id not in college_map:
            college = db.query(College).filter(College.id == u.college_id).first()
            college_map[u.college_id] = college.name if college else None
        result.append({
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "college_id": u.college_id,
            "college_name": college_map.get(u.college_id),
            "department": u.department,
            "is_active": u.is_active,
            "created_at": u.created_at,
        })
    return result


@router.post("/faculty", response_model=FacultyResponse, status_code=201)
def create_faculty(
    faculty_data: FacultyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a faculty account and send welcome email with credentials."""
    require_super_admin(current_user)

    # Validate college exists
    college = db.query(College).filter(College.id == faculty_data.college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    try:
        user, temp_password = AdminService.create_faculty(db, faculty_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Send welcome email
    EmailService.send_welcome_faculty(
        to_email=user.email,
        full_name=user.full_name or user.username,
        username=user.username,
        temp_password=temp_password,
        college_name=college.name,
    )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "college_id": user.college_id,
        "college_name": college.name,
        "department": user.department,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.put("/faculty/{faculty_id}", response_model=FacultyResponse)
def update_faculty(
    faculty_id: int,
    update_data: FacultyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a faculty member's details."""
    require_super_admin(current_user)

    user = AdminService.update_faculty(db, faculty_id, update_data)
    if not user:
        raise HTTPException(status_code=404, detail="Faculty member not found")

    college_name = None
    if user.college_id:
        college = db.query(College).filter(College.id == user.college_id).first()
        college_name = college.name if college else None

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "college_id": user.college_id,
        "college_name": college_name,
        "department": user.department,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.delete("/faculty/{faculty_id}")
def delete_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate a faculty member."""
    require_super_admin(current_user)
    success = AdminService.delete_faculty(db, faculty_id)
    if not success:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    return {"message": "Faculty member deactivated successfully"}


@router.post("/faculty/{faculty_id}/reset-password", response_model=ResetPasswordResponse)
def reset_faculty_password(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset a faculty member's password and send new credentials via email."""
    require_super_admin(current_user)
    user, temp_password = AdminService.reset_user_password(db, faculty_id)
    if not user:
        raise HTTPException(status_code=404, detail="Faculty member not found")

    email_sent = EmailService.send_password_reset(
        to_email=user.email,
        full_name=user.full_name or user.username,
        new_password=temp_password,
    )
    return {"message": "Password reset successfully", "email_sent": email_sent}
