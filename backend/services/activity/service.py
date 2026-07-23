from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from shared.models import ActivityLog, User

class ActivityService:
    @staticmethod
    def log_activity(
        db: Session, 
        user_id: int, 
        activity_type: str, 
        platform: Optional[str] = None,
        activity_data: Optional[Dict] = None
    ) -> ActivityLog:
        """
        Log user activity
        
        Activity Types:
        - login: User login
        - problem_solved: Problem completion
        - platform_sync: Platform data sync
        - feedback_read: Mentor feedback read
        - goal_completed: Goal achievement
        - note_created: Problem note added
        - profile_updated: Profile modification
        """
        activity = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            platform=platform,
            activity_data=activity_data or {},
            activity_date=datetime.utcnow()
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    
    @staticmethod
    def get_user_activity(
        db: Session, 
        user_id: int, 
        days: int = 30,
        activity_type: Optional[str] = None
    ) -> List[ActivityLog]:
        """Get user activity history"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(ActivityLog).filter(
            and_(
                ActivityLog.user_id == user_id,
                ActivityLog.activity_date >= cutoff_date
            )
        )
        
        if activity_type:
            query = query.filter(ActivityLog.activity_type == activity_type)
        
        return query.order_by(desc(ActivityLog.activity_date)).all()
    
    @staticmethod
    def get_activity_heatmap(db: Session, user_id: int, days: int = 365) -> Dict:
        """
        Generate activity heatmap data (GitHub-style)
        Returns: {date: count} for each day
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        activities = db.query(
            func.date(ActivityLog.activity_date).label('date'),
            func.count(ActivityLog.id).label('count')
        ).filter(
            and_(
                ActivityLog.user_id == user_id,
                ActivityLog.activity_date >= cutoff_date
            )
        ).group_by(func.date(ActivityLog.activity_date)).all()
        
        # Convert to dict
        heatmap = {}
        for activity in activities:
            heatmap[activity.date.isoformat()] = activity.count
        
        return heatmap
    
    @staticmethod
    def get_activity_stats(db: Session, user_id: int, days: int = 30) -> Dict:
        """Get activity statistics for a user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total activities
        total = db.query(func.count(ActivityLog.id)).filter(
            and_(
                ActivityLog.user_id == user_id,
                ActivityLog.activity_date >= cutoff_date
            )
        ).scalar()
        
        # Activities by type
        by_type = db.query(
            ActivityLog.activity_type,
            func.count(ActivityLog.id).label('count')
        ).filter(
            and_(
                ActivityLog.user_id == user_id,
                ActivityLog.activity_date >= cutoff_date
            )
        ).group_by(ActivityLog.activity_type).all()
        
        type_counts = {item.activity_type: item.count for item in by_type}
        
        # Most active day
        most_active = db.query(
            func.date(ActivityLog.activity_date).label('date'),
            func.count(ActivityLog.id).label('count')
        ).filter(
            and_(
                ActivityLog.user_id == user_id,
                ActivityLog.activity_date >= cutoff_date
            )
        ).group_by(func.date(ActivityLog.activity_date)
        ).order_by(desc('count')).first()
        
        return {
            "total_activities": total,
            "by_type": type_counts,
            "most_active_day": {
                "date": most_active.date.isoformat() if most_active else None,
                "count": most_active.count if most_active else 0
            },
            "period_days": days
        }
    
    @staticmethod
    def get_recent_activities(
        db: Session, 
        user_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Get recent activities with formatted data"""
        activities = db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id
        ).order_by(desc(ActivityLog.activity_date)).limit(limit).all()
        
        formatted = []
        for activity in activities:
            formatted.append({
                "id": activity.id,
                "type": activity.activity_type,
                "platform": activity.platform,
                "data": activity.activity_data,
                "date": activity.activity_date,
                "description": ActivityService._format_activity_description(activity)
            })
        
        return formatted
    
    @staticmethod
    def _format_activity_description(activity: ActivityLog) -> str:
        """Format activity into human-readable description"""
        type_map = {
            "login": "Logged in",
            "problem_solved": f"Solved problem: {activity.activity_data.get('problem_title', 'Unknown')}",
            "platform_sync": f"Synced {activity.platform} data",
            "feedback_read": "Read mentor feedback",
            "goal_completed": f"Completed goal: {activity.activity_data.get('goal_name', 'Unknown')}",
            "note_created": "Added problem note",
            "profile_updated": "Updated profile"
        }
        
        return type_map.get(activity.activity_type, activity.activity_type)
    
    @staticmethod
    def get_streak_data(db: Session, user_id: int) -> Dict:
        """Calculate current and longest streak"""
        # Get all activity dates (distinct)
        activities = db.query(
            func.date(ActivityLog.activity_date).label('date')
        ).filter(
            ActivityLog.user_id == user_id
        ).distinct().order_by(desc('date')).all()
        
        if not activities:
            return {"current_streak": 0, "longest_streak": 0}
        
        dates = [activity.date for activity in activities]
        
        # Calculate current streak
        current_streak = 0
        today = datetime.utcnow().date()
        
        for i, date in enumerate(dates):
            expected_date = today - timedelta(days=i)
            if date == expected_date:
                current_streak += 1
            else:
                break
        
        # Calculate longest streak
        longest_streak = 0
        temp_streak = 1
        
        for i in range(len(dates) - 1):
            diff = (dates[i] - dates[i + 1]).days
            if diff == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity": dates[0].isoformat() if dates else None
        }
