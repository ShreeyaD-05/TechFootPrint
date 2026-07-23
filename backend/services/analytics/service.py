from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict
from shared.models import User, ProblemStats, ContestStats, Analytics, PlatformAccount, PlatformProfileStats

class AnalyticsService:
    @staticmethod
    def calculate_user_analytics(db: Session, user_id: int) -> Analytics:
        """Calculate comprehensive analytics for a user"""
        
        # Get all platform accounts
        accounts = db.query(PlatformAccount).filter(
            PlatformAccount.user_id == user_id
        ).all()
        
        account_ids = [acc.id for acc in accounts]
        
        # Get all problems from database
        problems = db.query(ProblemStats).filter(
            ProblemStats.platform_account_id.in_(account_ids),
            ProblemStats.is_solved == True
        ).all()
        
        # Difficulty distribution from stored problems (case-insensitive)
        easy_from_db = sum(1 for p in problems if p.difficulty and p.difficulty.lower() == "easy")
        medium_from_db = sum(1 for p in problems if p.difficulty and p.difficulty.lower() == "medium")
        hard_from_db = sum(1 for p in problems if p.difficulty and p.difficulty.lower() == "hard")
        total_from_db = len(problems)
        
        # Check if we have profile stats that show more accurate counts
        # This is important for platforms like LeetCode where API limits prevent fetching all problems
        total_from_profile = 0
        easy_from_profile = 0
        medium_from_profile = 0
        hard_from_profile = 0
        
        for account in accounts:
            # Get the most recent profile stats from the dedicated table
            latest_stats = db.query(PlatformProfileStats).filter(
                PlatformProfileStats.platform_account_id == account.id
            ).order_by(PlatformProfileStats.fetched_at.desc()).first()
            
            if latest_stats:
                total_from_profile += latest_stats.total_solved
                easy_from_profile += latest_stats.easy_solved
                medium_from_profile += latest_stats.medium_solved
                hard_from_profile += latest_stats.hard_solved
            elif account.profile_stats:
                # Fallback to JSON column if table entry doesn't exist yet
                stats = account.profile_stats
                total_from_profile += stats.get("total_solved", 0)
                easy_from_profile += stats.get("easy_solved", 0)
                medium_from_profile += stats.get("medium_solved", 0)
                hard_from_profile += stats.get("hard_solved", 0)
        
        # Use profile stats if they show more problems than we have in DB
        if total_from_profile > total_from_db:
            total_solved = total_from_profile
            easy = easy_from_profile
            medium = medium_from_profile
            hard = hard_from_profile
        else:
            total_solved = total_from_db
            easy = easy_from_db
            medium = medium_from_db
            hard = hard_from_db
        
        # Topic distribution (from stored problems only)
        topic_count = {}
        for problem in problems:
            if problem.topics:
                for topic in problem.topics:
                    topic_count[topic] = topic_count.get(topic, 0) + 1
        
        # Platform distribution (use profile stats if available, otherwise DB count)
        platform_count = {}
        for account in accounts:
            platform_name = account.platform_name
            
            # Try to get count from profile stats table first
            latest_stats = db.query(PlatformProfileStats).filter(
                PlatformProfileStats.platform_account_id == account.id
            ).order_by(PlatformProfileStats.fetched_at.desc()).first()
            
            if latest_stats and latest_stats.total_solved > 0:
                count = latest_stats.total_solved
            elif account.profile_stats and account.profile_stats.get("total_solved", 0) > 0:
                # Fallback to JSON column
                count = account.profile_stats.get("total_solved", 0)
            else:
                # Fall back to DB count
                count = db.query(ProblemStats).filter(
                    ProblemStats.platform_account_id == account.id,
                    ProblemStats.is_solved == True
                ).count()
            
            if count > 0:  # Only include platforms with problems
                platform_count[platform_name] = count
        
        # Calculate streaks (from stored problems only)
        current_streak, longest_streak = AnalyticsService._calculate_streaks(problems)
        
        # Update or create analytics record
        analytics = db.query(Analytics).filter(Analytics.user_id == user_id).first()
        
        if not analytics:
            analytics = Analytics(user_id=user_id)
            db.add(analytics)
        
        analytics.total_problems_solved = total_solved
        analytics.easy_solved = easy
        analytics.medium_solved = medium
        analytics.hard_solved = hard
        analytics.current_streak = current_streak
        analytics.longest_streak = longest_streak
        analytics.topic_distribution = topic_count
        analytics.platform_distribution = platform_count
        analytics.last_calculated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(analytics)

        return analytics
    
    @staticmethod
    def _calculate_streaks(problems: list) -> tuple:
        """Calculate current and longest coding streaks"""
        if not problems:
            return 0, 0
        
        # Sort by solved date
        sorted_problems = sorted(
            [p for p in problems if p.solved_at],
            key=lambda x: x.solved_at
        )
        
        if not sorted_problems:
            return 0, 0
        
        # Get unique dates
        dates = list(set(p.solved_at.date() for p in sorted_problems))
        dates.sort()
        
        current_streak = 1
        longest_streak = 1
        temp_streak = 1
        
        for i in range(1, len(dates)):
            diff = (dates[i] - dates[i-1]).days
            if diff == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        # Check if current streak is active
        if dates and (datetime.now().date() - dates[-1]).days <= 1:
            # Count backwards from today
            today = datetime.now().date()
            current_streak = 0
            for date in reversed(dates):
                if (today - date).days == current_streak:
                    current_streak += 1
                else:
                    break
        else:
            current_streak = 0
        
        return current_streak, longest_streak
    
    @staticmethod
    def get_activity_heatmap(db: Session, user_id: int, days: int = 365) -> Dict:
        """Generate activity heatmap data — delegates to ActivityService"""
        from services.activity.service import ActivityService
        return ActivityService.get_activity_heatmap(db, user_id, days)
