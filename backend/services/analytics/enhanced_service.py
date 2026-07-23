from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from shared.models import (
    User, Analytics, ProblemStats, PlatformAccount,
    Submission, MentorFeedback, CodingGoal, ActivityLog
)
from services.activity.service import ActivityService

class EnhancedAnalyticsService:
    @staticmethod
    def get_student_dashboard_data(db: Session, user_id: int) -> Dict:
        """Get comprehensive dashboard data for students"""
        
        # Basic analytics
        analytics = db.query(Analytics).filter(Analytics.user_id == user_id).first()
        
        # Platform accounts
        platforms = db.query(PlatformAccount).filter(
            PlatformAccount.user_id == user_id
        ).all()
        
        # Activity stats
        activity_stats = ActivityService.get_activity_stats(db, user_id, days=30)
        streak_data = ActivityService.get_streak_data(db, user_id)
        recent_activities = ActivityService.get_recent_activities(db, user_id, limit=10)
        
        # Mentor feedback
        unread_feedback = db.query(func.count(MentorFeedback.id)).filter(
            and_(
                MentorFeedback.student_id == user_id,
                MentorFeedback.is_read == False
            )
        ).scalar()
        
        # Active goals
        active_goals = db.query(CodingGoal).filter(
            and_(
                CodingGoal.target_id == user_id,
                CodingGoal.is_active == True
            )
        ).all()
        
        # Recent submissions
        recent_submissions = EnhancedAnalyticsService._get_recent_submissions(db, user_id, limit=5)
        
        # Topic mastery
        topic_mastery = EnhancedAnalyticsService._calculate_topic_mastery(db, user_id)
        
        return {
            "overview": {
                "total_problems": analytics.total_problems_solved if analytics else 0,
                "easy_solved": analytics.easy_solved if analytics else 0,
                "medium_solved": analytics.medium_solved if analytics else 0,
                "hard_solved": analytics.hard_solved if analytics else 0,
                "current_streak": streak_data["current_streak"],
                "longest_streak": streak_data["longest_streak"]
            },
            "platforms": [
                {
                    "id": p.id,
                    "name": p.platform_name,
                    "username": p.platform_username,
                    "is_verified": p.is_verified,
                    "last_synced": p.last_synced_at,
                    "sync_enabled": p.sync_enabled
                } for p in platforms
            ],
            "activity": {
                "stats": activity_stats,
                "recent": recent_activities,
                "streak": streak_data
            },
            "feedback": {
                "unread_count": unread_feedback
            },
            "goals": [
                {
                    "id": g.id,
                    "type": g.goal_type,
                    "target": g.target_value,
                    "deadline": g.deadline,
                    "description": g.description
                } for g in active_goals
            ],
            "recent_submissions": recent_submissions,
            "topic_mastery": topic_mastery,
            "difficulty_distribution": {
                "easy": analytics.easy_solved if analytics else 0,
                "medium": analytics.medium_solved if analytics else 0,
                "hard": analytics.hard_solved if analytics else 0
            }
        }
    
    @staticmethod
    def get_faculty_dashboard_data(db: Session, faculty_id: int) -> Dict:
        """Get comprehensive dashboard data for faculty"""
        from shared.models import MentorAssignment, ActivityLog

        assignments = db.query(MentorAssignment).filter(
            and_(
                MentorAssignment.mentor_id == faculty_id,
                MentorAssignment.is_active == True
            )
        ).all()

        student_ids = [a.student_id for a in assignments]

        if not student_ids:
            return {
                "overview": {
                    "total_students": 0,
                    "active_students": 0,
                    "avg_problems": 0,
                    "students_needing_attention": 0
                },
                "students": [],
                "performance": {},
                "alerts": []
            }

        # Fetch all students and analytics in bulk
        students = db.query(User).filter(User.id.in_(student_ids)).all()
        analytics_map = {
            a.user_id: a
            for a in db.query(Analytics).filter(Analytics.user_id.in_(student_ids)).all()
        }

        # Last activity per student in one query
        week_ago = datetime.utcnow() - timedelta(days=7)
        last_activity_rows = db.query(
            ActivityLog.user_id,
            func.max(ActivityLog.activity_date).label("last_active")
        ).filter(
            ActivityLog.user_id.in_(student_ids)
        ).group_by(ActivityLog.user_id).all()
        last_activity_map = {row.user_id: row.last_active for row in last_activity_rows}

        students_data = []
        total_problems = 0
        active_count = 0

        for student in students:
            analytics = analytics_map.get(student.id)
            last_active = last_activity_map.get(student.id)
            is_active = last_active is not None and last_active >= week_ago
            if is_active:
                active_count += 1

            problems_solved = analytics.total_problems_solved if analytics else 0
            total_problems += problems_solved
            current_streak = analytics.current_streak if analytics else 0

            students_data.append({
                "id": student.id,
                "username": student.username,
                "full_name": student.full_name,
                "email": student.email,
                "problems_solved": problems_solved,
                "current_streak": current_streak,
                "last_active": last_active,
                "is_active": is_active,
                "needs_attention": not is_active or current_streak == 0
            })

        students_data.sort(key=lambda x: x["problems_solved"], reverse=True)
        alerts = [s for s in students_data if s["needs_attention"]]

        performance_trends = EnhancedAnalyticsService._get_faculty_performance_trends(
            db, student_ids
        )

        return {
            "overview": {
                "total_students": len(student_ids),
                "active_students": active_count,
                "avg_problems": total_problems / len(student_ids) if student_ids else 0,
                "students_needing_attention": len(alerts)
            },
            "students": students_data,
            "performance": performance_trends,
            "alerts": alerts[:10]
        }
    
    @staticmethod
    def get_management_dashboard_data(db: Session, college_id: int) -> Dict:
        """Get comprehensive dashboard data for management"""
        
        # Get all students in college
        students = db.query(User).filter(
            and_(
                User.college_id == college_id,
                User.role == "student"
            )
        ).all()
        
        student_ids = [s.id for s in students]
        
        if not student_ids:
            return {
                "overview": {},
                "batches": {},
                "departments": {},
                "trends": {}
            }
        
        # Overview stats
        total_problems = db.query(func.sum(Analytics.total_problems_solved)).filter(
            Analytics.user_id.in_(student_ids)
        ).scalar() or 0
        
        # Active students (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_count = db.query(func.count(func.distinct(ActivityLog.user_id))).filter(
            and_(
                ActivityLog.user_id.in_(student_ids),
                ActivityLog.activity_date >= week_ago
            )
        ).scalar()
        
        # Batch distribution
        batch_stats = db.query(
            User.batch_year,
            func.count(User.id).label('count'),
            func.avg(Analytics.total_problems_solved).label('avg_problems')
        ).join(
            Analytics, Analytics.user_id == User.id, isouter=True
        ).filter(
            and_(
                User.college_id == college_id,
                User.role == "student",
                User.batch_year.isnot(None)
            )
        ).group_by(User.batch_year).all()
        
        # Department distribution
        dept_stats = db.query(
            User.department,
            func.count(User.id).label('count'),
            func.avg(Analytics.total_problems_solved).label('avg_problems')
        ).join(
            Analytics, Analytics.user_id == User.id, isouter=True
        ).filter(
            and_(
                User.college_id == college_id,
                User.role == "student",
                User.department.isnot(None)
            )
        ).group_by(User.department).all()
        
        return {
            "overview": {
                "total_students": len(student_ids),
                "active_students": active_count,
                "total_problems_solved": total_problems,
                "activity_rate": (active_count / len(student_ids) * 100) if student_ids else 0
            },
            "batches": [
                {
                    "year": b.batch_year,
                    "students": b.count,
                    "avg_problems": round(b.avg_problems or 0, 2)
                } for b in batch_stats
            ],
            "departments": [
                {
                    "name": d.department,
                    "students": d.count,
                    "avg_problems": round(d.avg_problems or 0, 2)
                } for d in dept_stats
            ],
            "trends": EnhancedAnalyticsService._get_management_trends(db, student_ids)
        }
    
    @staticmethod
    def _get_recent_submissions(db: Session, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent submissions for a user"""
        platform_ids = db.query(PlatformAccount.id).filter(
            PlatformAccount.user_id == user_id
        ).all()
        platform_ids = [p[0] for p in platform_ids]
        
        if not platform_ids:
            return []
        
        submissions = db.query(Submission).filter(
            Submission.platform_account_id.in_(platform_ids)
        ).order_by(desc(Submission.submitted_at)).limit(limit).all()
        
        return [
            {
                "id": s.id,
                "status": s.status,
                "language": s.language,
                "runtime": s.runtime,
                "memory": s.memory,
                "submitted_at": s.submitted_at
            } for s in submissions
        ]
    
    @staticmethod
    def _calculate_topic_mastery(db: Session, user_id: int) -> Dict:
        """Calculate topic mastery scores"""
        platform_ids = db.query(PlatformAccount.id).filter(
            PlatformAccount.user_id == user_id
        ).all()
        platform_ids = [p[0] for p in platform_ids]
        
        if not platform_ids:
            return {}
        
        # Get all solved problems with topics
        problems = db.query(ProblemStats).filter(
            and_(
                ProblemStats.platform_account_id.in_(platform_ids),
                ProblemStats.is_solved == True,
                ProblemStats.topics.isnot(None)
            )
        ).all()
        
        topic_counts = {}
        for problem in problems:
            if problem.topics:
                for topic in problem.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Calculate mastery score (0-100)
        max_count = max(topic_counts.values()) if topic_counts else 1
        topic_mastery = {
            topic: round((count / max_count) * 100, 2)
            for topic, count in topic_counts.items()
        }
        
        return topic_mastery
    
    @staticmethod
    def _get_faculty_performance_trends(db: Session, student_ids: List[int]) -> Dict:
        """Get performance trends for faculty dashboard — single query, no loop subqueries"""
        if not student_ids:
            return {"weekly_progress": []}

        # Get all platform account IDs for these students in one shot
        platform_ids = [
            r[0] for r in db.query(PlatformAccount.id).filter(
                PlatformAccount.user_id.in_(student_ids)
            ).all()
        ]

        if not platform_ids:
            return {"weekly_progress": [{"week": f"Week {i+1}", "problems": 0} for i in range(4)]}

        now = datetime.utcnow()
        weeks_data = []
        for week in range(4):
            start_date = now - timedelta(days=(week + 1) * 7)
            end_date = now - timedelta(days=week * 7)
            count = db.query(func.count(ProblemStats.id)).filter(
                ProblemStats.platform_account_id.in_(platform_ids),
                ProblemStats.solved_at >= start_date,
                ProblemStats.solved_at < end_date,
            ).scalar() or 0
            weeks_data.append({"week": f"Week {4 - week}", "problems": count})

        return {"weekly_progress": weeks_data}
    
    @staticmethod
    def _get_management_trends(db: Session, student_ids: List[int]) -> Dict:
        """Get trends for management dashboard — single platform_ids lookup, no loop subqueries"""
        if not student_ids:
            return {"monthly_growth": []}

        platform_ids = [
            r[0] for r in db.query(PlatformAccount.id).filter(
                PlatformAccount.user_id.in_(student_ids)
            ).all()
        ]

        if not platform_ids:
            return {"monthly_growth": []}

        now = datetime.utcnow()
        months_data = []
        for month in range(6):
            start_date = now - timedelta(days=(month + 1) * 30)
            end_date = now - timedelta(days=month * 30)
            count = db.query(func.count(ProblemStats.id)).filter(
                ProblemStats.platform_account_id.in_(platform_ids),
                ProblemStats.solved_at >= start_date,
                ProblemStats.solved_at < end_date,
            ).scalar() or 0
            months_data.append({"month": start_date.strftime("%b %Y"), "problems": count})

        return {"monthly_growth": list(reversed(months_data))}
