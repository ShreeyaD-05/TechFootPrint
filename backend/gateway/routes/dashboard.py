from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from shared.database import get_db
from gateway.routes.auth import get_current_user
from shared.models import User, MentorAssignment
from services.analytics.enhanced_service import EnhancedAnalyticsService
from services.activity.service import ActivityService
from services.submissions.service import SubmissionService
from services.discussion.service import DiscussionService

router = APIRouter()

# Student Dashboard Endpoints
@router.get("/student/overview")
def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive student dashboard data"""
    if current_user.role not in ["student", "faculty", "dept_admin", "management", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    data = EnhancedAnalyticsService.get_student_dashboard_data(db, current_user.id)
    return data

@router.get("/student/activity")
def get_student_activity(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student activity history"""
    activities = ActivityService.get_user_activity(db, current_user.id, days=days)
    return {
        "activities": [
            {
                "id": a.id,
                "type": a.activity_type,
                "platform": a.platform,
                "data": a.activity_data,
                "date": a.activity_date
            } for a in activities
        ]
    }

@router.get("/student/heatmap")
def get_student_heatmap(
    days: int = 365,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity heatmap data"""
    heatmap = ActivityService.get_activity_heatmap(db, current_user.id, days=days)
    return {"heatmap": heatmap}

@router.get("/student/streak")
def get_student_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get streak information"""
    streak = ActivityService.get_streak_data(db, current_user.id)
    return streak

# Faculty Dashboard Endpoints
@router.get("/faculty/overview")
def get_faculty_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive faculty dashboard data"""
    if current_user.role not in ["faculty", "dept_admin", "management", "super_admin"]:
        raise HTTPException(status_code=403, detail="Faculty access required")
    
    data = EnhancedAnalyticsService.get_faculty_dashboard_data(db, current_user.id)
    return data

@router.get("/faculty/student/{student_id}")
def get_student_details(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed view of a specific student"""
    if current_user.role not in ["faculty", "dept_admin", "management", "super_admin"]:
        raise HTTPException(status_code=403, detail="Faculty access required")
    
    # Verify faculty has access to this student
    if current_user.role == "faculty":
        assignment = db.query(MentorAssignment).filter(
            and_(
                MentorAssignment.mentor_id == current_user.id,
                MentorAssignment.student_id == student_id,
                MentorAssignment.is_active == True
            )
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="Not assigned to this student")
    
    data = EnhancedAnalyticsService.get_student_dashboard_data(db, student_id)
    return data

# Management Dashboard Endpoints
@router.get("/management/overview")
def get_management_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive management dashboard data"""
    if current_user.role not in ["dept_admin", "management", "super_admin"]:
        raise HTTPException(status_code=403, detail="Management access required")
    
    if not current_user.college_id and current_user.role != "super_admin":
        raise HTTPException(status_code=400, detail="User not associated with a college")
    
    data = EnhancedAnalyticsService.get_management_dashboard_data(db, current_user.college_id)
    return data

@router.get("/management/batch/{batch_year}")
def get_batch_details(
    batch_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed batch analytics"""
    if current_user.role not in ["dept_admin", "management", "super_admin"]:
        raise HTTPException(status_code=403, detail="Management access required")
    
    from services.management.service import ManagementService
    data = ManagementService.get_batch_analytics(db, current_user.college_id, batch_year)
    return data

@router.get("/management/department/{department}")
def get_department_details(
    department: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed department analytics"""
    if current_user.role not in ["dept_admin", "management", "super_admin"]:
        raise HTTPException(status_code=403, detail="Management access required")
    
    from services.management.service import ManagementService
    data = ManagementService.get_department_analytics(db, current_user.college_id, department)
    return data

# Activity Logging Endpoint
@router.post("/activity/log")
def log_activity(
    activity_type: str,
    platform: str = None,
    activity_data: dict = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log user activity"""
    activity = ActivityService.log_activity(
        db, 
        current_user.id, 
        activity_type, 
        platform, 
        activity_data
    )
    return {"success": True, "activity_id": activity.id}


# Enhanced Student Dashboard Endpoints
@router.get("/student/submissions/overview")
def get_student_submissions_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student submissions overview"""
    stats = SubmissionService.get_submission_stats(db, current_user.id, days=30)
    platform_summary = SubmissionService.get_platform_summary(db, current_user.id)
    
    return {
        "stats": stats,
        "platform_summary": platform_summary
    }

@router.get("/student/discussions/overview")
def get_student_discussions_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student discussions overview"""
    my_discussions = DiscussionService.get_discussions(
        db,
        user_id=current_user.id,
        limit=5,
        sort_by="recent"
    )
    
    recent_discussions = DiscussionService.get_discussions(
        db,
        limit=10,
        sort_by="recent"
    )
    
    popular_discussions = DiscussionService.get_discussions(
        db,
        limit=5,
        sort_by="popular"
    )
    
    return {
        "my_discussions": my_discussions,
        "recent_discussions": recent_discussions,
        "popular_discussions": popular_discussions
    }


# BI KPI Endpoints
@router.get("/kpi/college")
def get_college_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get college-level KPI metrics for BI dashboard"""
    if current_user.role not in ["dept_admin", "management", "super_admin"]:
        raise HTTPException(status_code=403, detail="Management access required")

    from sqlalchemy import func, distinct
    from shared.models import Analytics, PlatformAccount, ProblemStats
    from datetime import datetime, timedelta

    college_id = current_user.college_id

    # All student IDs for this college in one query
    student_ids = [
        u.id for u in db.query(User.id).filter(
            User.role == "student",
            User.college_id == college_id
        ).all()
    ]
    total_students = len(student_ids)

    if not student_ids:
        return {
            "total_students": 0,
            "active_7d": 0,
            "engagement_rate": 0,
            "total_problems_solved": 0,
            "avg_problems_per_student": 0,
            "avg_streak": 0,
            "platform_connections": 0,
            "placement_readiness": {"ready": 0, "moderate": 0, "needs_work": 0, "ready_pct": 0},
            "batch_kpis": []
        }

    # Analytics in one query
    analytics_rows = db.query(Analytics).filter(
        Analytics.user_id.in_(student_ids)
    ).all()

    # Active students (last 7 days) via Analytics.last_calculated
    active_7d = db.query(func.count(Analytics.id)).filter(
        Analytics.user_id.in_(student_ids),
        Analytics.last_calculated_at >= datetime.utcnow() - timedelta(days=7)
    ).scalar() or 0

    total_problems = sum(a.total_problems_solved or 0 for a in analytics_rows)
    avg_problems = round(total_problems / max(len(analytics_rows), 1), 1)
    avg_streak = round(sum(a.current_streak or 0 for a in analytics_rows) / max(len(analytics_rows), 1), 1)

    # Platform connections
    platform_count = db.query(func.count(PlatformAccount.id)).filter(
        PlatformAccount.user_id.in_(student_ids)
    ).scalar() or 0

    # Placement readiness
    ready = sum(1 for a in analytics_rows if (a.total_problems_solved or 0) >= 150)
    moderate = sum(1 for a in analytics_rows if 50 <= (a.total_problems_solved or 0) < 150)
    needs_work = sum(1 for a in analytics_rows if (a.total_problems_solved or 0) < 50)

    # Batch KPIs — single query grouped by batch_year
    batch_rows = db.query(
        User.batch_year,
        func.count(User.id).label("student_count"),
    ).filter(
        User.role == "student",
        User.college_id == college_id,
        User.batch_year.isnot(None)
    ).group_by(User.batch_year).all()

    # Build analytics lookup by user_id
    analytics_by_user = {a.user_id: a for a in analytics_rows}

    # Batch analytics lookup
    batch_user_map: dict = {}
    for u in db.query(User.id, User.batch_year).filter(
        User.role == "student",
        User.college_id == college_id,
        User.batch_year.isnot(None)
    ).all():
        batch_user_map.setdefault(u.batch_year, []).append(u.id)

    batch_kpis = []
    for row in batch_rows:
        if not row.batch_year:
            continue
        b_ids = batch_user_map.get(row.batch_year, [])
        b_analytics = [analytics_by_user[uid] for uid in b_ids if uid in analytics_by_user]
        b_total = sum(a.total_problems_solved or 0 for a in b_analytics)
        b_ready = sum(1 for a in b_analytics if (a.total_problems_solved or 0) >= 150)
        batch_kpis.append({
            "batch_year": row.batch_year,
            "student_count": row.student_count,
            "avg_problems": round(b_total / max(len(b_analytics), 1), 1),
            "ready_count": b_ready
        })

    return {
        "total_students": total_students,
        "active_7d": active_7d,
        "engagement_rate": round(active_7d / max(total_students, 1) * 100, 1),
        "total_problems_solved": total_problems,
        "avg_problems_per_student": avg_problems,
        "avg_streak": avg_streak,
        "platform_connections": platform_count,
        "placement_readiness": {
            "ready": ready,
            "moderate": moderate,
            "needs_work": needs_work,
            "ready_pct": round(ready / max(len(analytics_rows), 1) * 100, 1)
        },
        "batch_kpis": sorted(batch_kpis, key=lambda x: x["batch_year"], reverse=True)
    }
