"""
My College Routes — for faculty, dept_admin, management, and super_admin.
Provides a self-service view of the college they belong to.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from typing import Optional

from shared.database import get_db
from gateway.routes.auth import get_current_user
from shared.models import User, College, MentorAssignment, Analytics

router = APIRouter()

COLLEGE_ROLES = {"faculty", "dept_admin", "management", "super_admin"}


def _get_college_for_user(db: Session, user: User, college_id: Optional[int] = None) -> College:
    """Resolve college: super_admin can pass ?college_id, others use their own."""
    if user.role == "super_admin":
        cid = college_id or user.college_id
        if not cid:
            raise HTTPException(status_code=400, detail="Provide ?college_id")
    else:
        cid = user.college_id
        if not cid:
            raise HTTPException(status_code=400, detail="You are not associated with a college")

    college = db.query(College).filter(College.id == cid).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    return college


@router.get("/overview")
def get_my_college_overview(
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full overview of the college: info, stats, departments, batches, faculty list.
    """
    if current_user.role not in COLLEGE_ROLES:
        raise HTTPException(status_code=403, detail="Access denied")

    college = _get_college_for_user(db, current_user, college_id)

    # ── User counts by role ───────────────────────────────────────────────────
    role_counts = db.query(
        User.role,
        func.count(User.id).label("cnt"),
    ).filter(
        User.college_id == college.id,
        User.is_active == True,
    ).group_by(User.role).all()

    counts = {r.role: r.cnt for r in role_counts}
    total_students = counts.get("student", 0)
    total_faculty = sum(counts.get(r, 0) for r in ["faculty", "dept_admin", "management"])

    # ── Department breakdown ──────────────────────────────────────────────────
    dept_rows = db.query(
        User.department,
        func.count(User.id).label("cnt"),
    ).filter(
        User.college_id == college.id,
        User.role == "student",
        User.is_active == True,
        User.department.isnot(None),
    ).group_by(User.department).order_by(func.count(User.id).desc()).all()

    departments = [{"name": r.department, "student_count": r.cnt} for r in dept_rows]

    # ── Batch breakdown ───────────────────────────────────────────────────────
    batch_rows = db.query(
        User.batch_year,
        func.count(User.id).label("cnt"),
    ).filter(
        User.college_id == college.id,
        User.role == "student",
        User.is_active == True,
        User.batch_year.isnot(None),
    ).group_by(User.batch_year).order_by(User.batch_year.desc()).all()

    batches = [{"year": r.batch_year, "student_count": r.cnt} for r in batch_rows]

    # ── Faculty list with their assigned student count ────────────────────────
    faculty_users = db.query(User).filter(
        User.college_id == college.id,
        User.role.in_(["faculty", "dept_admin", "management"]),
        User.is_active == True,
    ).order_by(User.full_name).all()

    # Count active assignments per mentor in one query
    assignment_counts = dict(
        db.query(
            MentorAssignment.mentor_id,
            func.count(MentorAssignment.id).label("cnt"),
        ).filter(
            MentorAssignment.is_active == True,
            MentorAssignment.mentor_id.in_([f.id for f in faculty_users]),
        ).group_by(MentorAssignment.mentor_id).all()
    )

    faculty_list = [
        {
            "id": f.id,
            "username": f.username,
            "full_name": f.full_name,
            "role": f.role,
            "department": f.department,
            "email": f.email,
            "assigned_students": assignment_counts.get(f.id, 0),
        }
        for f in faculty_users
    ]

    # ── Unassigned students count ─────────────────────────────────────────────
    assigned_student_ids = db.query(MentorAssignment.student_id).filter(
        MentorAssignment.is_active == True,
    ).subquery()

    unassigned_count = db.query(func.count(User.id)).filter(
        User.college_id == college.id,
        User.role == "student",
        User.is_active == True,
        ~User.id.in_(assigned_student_ids),
    ).scalar()

    # ── Analytics summary ─────────────────────────────────────────────────────
    student_ids = [
        r.id for r in db.query(User.id).filter(
            User.college_id == college.id,
            User.role == "student",
            User.is_active == True,
        ).all()
    ]

    analytics_rows = db.query(Analytics).filter(
        Analytics.user_id.in_(student_ids)
    ).all() if student_ids else []

    total_problems = sum(a.total_problems_solved or 0 for a in analytics_rows)
    avg_problems = round(total_problems / max(len(analytics_rows), 1), 1)
    avg_streak = round(
        sum(a.current_streak or 0 for a in analytics_rows) / max(len(analytics_rows), 1), 1
    )

    return {
        "college": {
            "id": college.id,
            "name": college.name,
            "code": college.code,
            "location": college.location,
            "subscription_tier": college.subscription_tier,
            "max_students": college.max_students,
            "is_active": college.is_active,
            "created_at": college.created_at,
        },
        "stats": {
            "total_students": total_students,
            "total_faculty": total_faculty,
            "unassigned_students": unassigned_count,
            "total_problems_solved": total_problems,
            "avg_problems_per_student": avg_problems,
            "avg_streak": avg_streak,
        },
        "departments": departments,
        "batches": batches,
        "faculty": faculty_list,
    }


@router.get("/assignments-summary")
def get_assignments_summary(
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Per-faculty assignment summary: how many students each faculty has.
    """
    if current_user.role not in COLLEGE_ROLES:
        raise HTTPException(status_code=403, detail="Access denied")

    college = _get_college_for_user(db, current_user, college_id)

    faculty_users = db.query(User).filter(
        User.college_id == college.id,
        User.role.in_(["faculty", "dept_admin", "management"]),
        User.is_active == True,
    ).all()

    faculty_ids = [f.id for f in faculty_users]

    assignment_counts = dict(
        db.query(
            MentorAssignment.mentor_id,
            func.count(MentorAssignment.id).label("cnt"),
        ).filter(
            MentorAssignment.is_active == True,
            MentorAssignment.mentor_id.in_(faculty_ids),
        ).group_by(MentorAssignment.mentor_id).all()
    )

    return [
        {
            "faculty_id": f.id,
            "faculty_name": f.full_name or f.username,
            "role": f.role,
            "department": f.department,
            "assigned_count": assignment_counts.get(f.id, 0),
        }
        for f in faculty_users
    ]
