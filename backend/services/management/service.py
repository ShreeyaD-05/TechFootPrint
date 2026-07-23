from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from shared.models import (
    User, College, Analytics, ProblemStats, PlatformAccount,
    MentorAssignment, ActivityLog
)

class ManagementService:
    @staticmethod
    def get_batch_analytics(db: Session, college_id: int, batch_year: int) -> dict:
        """Get analytics for a specific batch"""
        students = db.query(User).filter(
            and_(
                User.college_id == college_id,
                User.batch_year == batch_year,
                User.role == "student"
            )
        ).all()
        
        student_ids = [s.id for s in students]
        total_students = len(student_ids)
        
        if total_students == 0:
            return {
                "batch_year": batch_year,
                "total_students": 0,
                "active_students": 0,
                "total_problems_solved": 0,
                "avg_problems_per_student": 0,
                "top_performers": []
            }
        
        # Get analytics for all students
        analytics_list = db.query(Analytics).filter(Analytics.user_id.in_(student_ids)).all()
        
        total_problems = sum(a.total_problems_solved for a in analytics_list)
        avg_problems = total_problems / total_students if total_students > 0 else 0
        
        # Active students (solved at least 1 problem in last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_count = db.query(func.count(func.distinct(ProblemStats.platform_account_id))).filter(
            and_(
                ProblemStats.platform_account_id.in_(
                    db.query(PlatformAccount.id).filter(PlatformAccount.user_id.in_(student_ids))
                ),
                ProblemStats.solved_at >= week_ago
            )
        ).scalar()
        
        # Top performers — sort analytics first, then join with student data
        analytics_sorted = sorted(analytics_list, key=lambda a: a.total_problems_solved, reverse=True)
        student_map = {s.id: s for s in students}
        top_performers = []
        for a in analytics_sorted[:10]:
            student = student_map.get(a.user_id)
            if student:
                top_performers.append({
                    "user_id": student.id,
                    "username": student.username,
                    "full_name": student.full_name,
                    "total_problems": a.total_problems_solved,
                    "current_streak": a.current_streak,
                })
        
        return {
            "batch_year": batch_year,
            "total_students": total_students,
            "active_students": active_count,
            "total_problems_solved": total_problems,
            "avg_problems_per_student": round(avg_problems, 2),
            "top_performers": top_performers[:10]
        }
    
    @staticmethod
    def get_department_analytics(db: Session, college_id: int, department: str) -> dict:
        """Get analytics for a specific department"""
        students = db.query(User).filter(
            and_(
                User.college_id == college_id,
                User.department == department,
                User.role == "student"
            )
        ).all()
        
        student_ids = [s.id for s in students]
        total_students = len(student_ids)
        
        if total_students == 0:
            return {
                "department": department,
                "total_students": 0,
                "total_problems_solved": 0,
                "avg_streak": 0,
                "platform_distribution": {}
            }
        
        analytics_list = db.query(Analytics).filter(Analytics.user_id.in_(student_ids)).all()
        
        total_problems = sum(a.total_problems_solved for a in analytics_list)
        avg_streak = sum(a.current_streak for a in analytics_list) / total_students if total_students > 0 else 0
        
        # Platform distribution
        platform_dist = {}
        for analytics in analytics_list:
            if analytics.platform_distribution:
                for platform, count in analytics.platform_distribution.items():
                    platform_dist[platform] = platform_dist.get(platform, 0) + count
        
        return {
            "department": department,
            "total_students": total_students,
            "total_problems_solved": total_problems,
            "avg_streak": round(avg_streak, 2),
            "platform_distribution": platform_dist
        }
    
    @staticmethod
    def get_college_overview(db: Session, college_id: int) -> dict:
        """Get overall college analytics"""
        students = db.query(User).filter(
            and_(
                User.college_id == college_id,
                User.role == "student"
            )
        ).all()
        
        student_ids = [s.id for s in students]
        total_students = len(student_ids)
        
        # Connected platforms count
        platform_count = db.query(func.count(PlatformAccount.id)).filter(
            PlatformAccount.user_id.in_(student_ids)
        ).scalar()
        
        # Total problems solved
        analytics_list = db.query(Analytics).filter(Analytics.user_id.in_(student_ids)).all()
        total_problems = sum(a.total_problems_solved for a in analytics_list)
        
        # Active students (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_count = db.query(func.count(func.distinct(ProblemStats.platform_account_id))).filter(
            and_(
                ProblemStats.platform_account_id.in_(
                    db.query(PlatformAccount.id).filter(PlatformAccount.user_id.in_(student_ids))
                ),
                ProblemStats.solved_at >= week_ago
            )
        ).scalar()
        
        # Batch distribution
        batch_dist = db.query(
            User.batch_year,
            func.count(User.id)
        ).filter(
            and_(
                User.college_id == college_id,
                User.role == "student",
                User.batch_year.isnot(None)
            )
        ).group_by(User.batch_year).all()
        
        # Department distribution
        dept_dist = db.query(
            User.department,
            func.count(User.id)
        ).filter(
            and_(
                User.college_id == college_id,
                User.role == "student",
                User.department.isnot(None)
            )
        ).group_by(User.department).all()
        
        return {
            "total_students": total_students,
            "active_students": active_count,
            "total_problems_solved": total_problems,
            "platform_connections": platform_count,
            "batch_distribution": {str(year): count for year, count in batch_dist},
            "department_distribution": {dept: count for dept, count in dept_dist}
        }
    
    @staticmethod
    def get_inactive_students(db: Session, college_id: int, days: int = 7) -> List[Dict]:
        """Get students who haven't been active in specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        students = db.query(User).filter(
            and_(
                User.college_id == college_id,
                User.role == "student"
            )
        ).all()

        if not students:
            return []

        student_ids = [s.id for s in students]

        # Get last activity per student in one query
        last_activity_rows = db.query(
            PlatformAccount.user_id,
            func.max(ProblemStats.solved_at).label("last_active")
        ).join(
            ProblemStats, ProblemStats.platform_account_id == PlatformAccount.id
        ).filter(
            PlatformAccount.user_id.in_(student_ids)
        ).group_by(PlatformAccount.user_id).all()

        last_activity_map = {row.user_id: row.last_active for row in last_activity_rows}

        inactive_students = []
        for student in students:
            last_active = last_activity_map.get(student.id)
            if not last_active or last_active < cutoff_date:
                inactive_students.append({
                    "user_id": student.id,
                    "username": student.username,
                    "full_name": student.full_name,
                    "batch_year": student.batch_year,
                    "department": student.department,
                    "last_active": last_active
                })

        return inactive_students
    
    @staticmethod
    def get_placement_readiness(db: Session, college_id: int, batch_year: int) -> dict:
        """Calculate placement readiness metrics for a batch"""
        students = db.query(User).filter(
            and_(
                User.college_id == college_id,
                User.batch_year == batch_year,
                User.role == "student"
            )
        ).all()
        
        student_ids = [s.id for s in students]
        analytics_list = db.query(Analytics).filter(Analytics.user_id.in_(student_ids)).all()
        
        # Placement readiness criteria
        ready_count = 0
        moderate_count = 0
        needs_improvement = 0
        
        for analytics in analytics_list:
            total = analytics.total_problems_solved
            if total >= 300:  # Ready
                ready_count += 1
            elif total >= 150:  # Moderate
                moderate_count += 1
            else:  # Needs improvement
                needs_improvement += 1
        
        return {
            "batch_year": batch_year,
            "total_students": len(student_ids),
            "placement_ready": ready_count,
            "moderate_readiness": moderate_count,
            "needs_improvement": needs_improvement,
            "readiness_percentage": round((ready_count / len(student_ids) * 100), 2) if student_ids else 0
        }
    
    @staticmethod
    def assign_batch_mentor(db: Session, mentor_id: int, batch_year: int, college_id: int, assigned_by_id: int) -> int:
        """Assign a mentor to all students in a batch"""
        students = db.query(User).filter(
            and_(
                User.college_id == college_id,
                User.batch_year == batch_year,
                User.role == "student"
            )
        ).all()

        if not students:
            return 0

        student_ids = [s.id for s in students]

        # Fetch already-assigned student IDs in one query
        already_assigned = {
            row.student_id
            for row in db.query(MentorAssignment.student_id).filter(
                and_(
                    MentorAssignment.mentor_id == mentor_id,
                    MentorAssignment.student_id.in_(student_ids),
                    MentorAssignment.is_active == True,
                )
            ).all()
        }

        count = 0
        for student in students:
            if student.id not in already_assigned:
                db.add(MentorAssignment(
                    mentor_id=mentor_id,
                    student_id=student.id,
                    assigned_by=assigned_by_id,
                ))
                count += 1

        db.commit()
        return count
