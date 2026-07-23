import asyncio
import logging
import traceback
from datetime import datetime

from workers.celery_app import celery_app
from shared.database import SessionLocal
from shared.models import (
    PlatformAccount, ProblemStats, ContestStats,
    ActivityLog, User, PlatformProfileStats
)
from services.connector.registry import ConnectorRegistry
from services.analytics.service import AnalyticsService

logger = logging.getLogger(__name__)


@celery_app.task
def sync_platform_data(platform_account_id: int):
    """Sync data for a specific platform account"""
    db = SessionLocal()
    try:
        account = db.query(PlatformAccount).filter(
            PlatformAccount.id == platform_account_id
        ).first()

        if not account or not account.sync_enabled:
            return {"status": "skipped", "reason": "account not found or sync disabled"}

        connector = ConnectorRegistry.get_connector(
            account.platform_name,
            account.platform_username,
            account.credentials
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        problems: list = []
        contests: list = []
        new_problems = 0
        new_contests = 0

        try:
            # Fetch and persist profile stats
            profile_data = loop.run_until_complete(connector.fetch_profile())
            account.is_verified = True
            account.platform_user_id = profile_data.user_id

            db.add(PlatformProfileStats(
                platform_account_id=account.id,
                total_solved=profile_data.total_solved,
                easy_solved=profile_data.easy_solved,
                medium_solved=profile_data.medium_solved,
                hard_solved=profile_data.hard_solved,
                rating=profile_data.rating,
                rank=profile_data.rank,
                fetched_at=datetime.utcnow()
            ))

            # Fetch and persist problem stats
            problems = loop.run_until_complete(connector.fetch_problem_stats())
            for problem in problems:
                exists = db.query(ProblemStats).filter(
                    ProblemStats.platform_account_id == account.id,
                    ProblemStats.problem_id == problem.problem_id
                ).first()

                if not exists:
                    new_problems += 1
                    db.add(ProblemStats(
                        platform_account_id=account.id,
                        problem_id=problem.problem_id,
                        problem_title=problem.title,
                        difficulty=problem.difficulty,
                        topics=problem.topics,
                        solved_at=problem.solved_at,
                        submission_count=problem.submission_count
                    ))
                    db.add(ActivityLog(
                        user_id=account.user_id,
                        activity_type="problem_solved",
                        platform=account.platform_name,
                        activity_data={
                            "problem_id": problem.problem_id,
                            "title": problem.title,
                            "difficulty": problem.difficulty
                        },
                        activity_date=problem.solved_at or datetime.utcnow()
                    ))

            # Fetch and persist contest stats
            contests = loop.run_until_complete(connector.fetch_contest_stats())
            for contest in contests:
                exists = db.query(ContestStats).filter(
                    ContestStats.platform_account_id == account.id,
                    ContestStats.contest_id == contest.contest_id
                ).first()

                if not exists:
                    new_contests += 1
                    db.add(ContestStats(
                        platform_account_id=account.id,
                        contest_id=contest.contest_id,
                        contest_name=contest.contest_name,
                        rating=contest.rating,
                        rank=contest.rank,
                        problems_solved=contest.problems_solved,
                        contest_date=contest.contest_date
                    ))

            account.last_synced_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.error("Sync error for account %d: %s\n%s",
                         platform_account_id, e, traceback.format_exc())
            raise
        finally:
            loop.close()

        # Recalculate analytics after successful sync
        AnalyticsService.calculate_user_analytics(db, account.user_id)

        return {
            "status": "success",
            "platform": account.platform_name,
            "problems_synced": len(problems),
            "new_problems": new_problems,
            "contests_synced": len(contests),
            "new_contests": new_contests
        }

    except Exception as e:
        db.rollback()
        logger.error("Sync failed for account %d: %s", platform_account_id, e)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task
def sync_all_platforms():
    """Queue sync for all enabled platform accounts"""
    db = SessionLocal()
    try:
        accounts = db.query(PlatformAccount).filter(
            PlatformAccount.sync_enabled == True
        ).all()
        for account in accounts:
            sync_platform_data.delay(account.id)
        return {"status": "success", "accounts_queued": len(accounts)}
    finally:
        db.close()


@celery_app.task
def recalculate_all_analytics():
    """Recalculate analytics for all active users"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            AnalyticsService.calculate_user_analytics(db, user.id)
        return {"status": "success", "users_processed": len(users)}
    finally:
        db.close()
