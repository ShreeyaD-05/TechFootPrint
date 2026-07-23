from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, case
from shared.models import Submission, ProblemStats, PlatformAccount
from typing import List, Optional, Dict
from datetime import datetime, timedelta


class SubmissionService:

    @staticmethod
    def _base_query(db: Session, user_id: int):
        """Base query joining Submission → PlatformAccount → ProblemStats for a user."""
        return (
            db.query(
                Submission,
                PlatformAccount.platform_name.label("platform"),
                ProblemStats.problem_title.label("problem_title"),
                ProblemStats.difficulty.label("difficulty"),
                ProblemStats.problem_id.label("problem_id_str"),
            )
            .join(PlatformAccount, Submission.platform_account_id == PlatformAccount.id)
            .outerjoin(ProblemStats, Submission.problem_stat_id == ProblemStats.id)
            .filter(PlatformAccount.user_id == user_id)
        )

    @staticmethod
    def _row_to_dict(row) -> Dict:
        sub, platform, problem_title, difficulty, problem_id_str = row
        return {
            "id": sub.id,
            "problem_id": problem_id_str or sub.submission_id,
            "problem_title": problem_title,
            "platform": platform,
            "difficulty": difficulty,
            "status": sub.status,
            "language": sub.language,
            "submission_time": sub.submitted_at,
            "runtime": sub.runtime,
            "memory": sub.memory,
            "submission_url": None,
        }

    @staticmethod
    def get_user_submissions(
        db: Session,
        user_id: int,
        platform: Optional[str] = None,
        difficulty: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict:
        query = SubmissionService._base_query(db, user_id)

        if platform:
            query = query.filter(PlatformAccount.platform_name == platform)
        if difficulty:
            query = query.filter(ProblemStats.difficulty == difficulty)
        if status:
            query = query.filter(Submission.status == status)
        if date_from:
            query = query.filter(Submission.submitted_at >= date_from)
        if date_to:
            query = query.filter(Submission.submitted_at <= date_to)
        if search:
            query = query.filter(
                or_(
                    ProblemStats.problem_title.ilike(f"%{search}%"),
                    ProblemStats.problem_id.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        rows = query.order_by(desc(Submission.submitted_at)).offset(skip).limit(limit).all()

        return {
            "total": total,
            "page": (skip // limit) + 1,
            "limit": limit,
            "submissions": [SubmissionService._row_to_dict(r) for r in rows],
        }

    @staticmethod
    def get_submission_stats(db: Session, user_id: int, days: int = 30) -> Dict:
        date_from = datetime.utcnow() - timedelta(days=days)

        rows = (
            SubmissionService._base_query(db, user_id)
            .filter(Submission.submitted_at >= date_from)
            .all()
        )

        total = len(rows)
        accepted = sum(1 for r in rows if (r[0].status or "").lower() == "accepted")
        wrong_answer = sum(1 for r in rows if "wrong" in (r[0].status or "").lower())
        tle = sum(1 for r in rows if "time" in (r[0].status or "").lower())
        runtime_error = sum(1 for r in rows if "runtime" in (r[0].status or "").lower())

        by_platform: Dict[str, int] = {}
        by_difficulty: Dict[str, int] = {}
        by_language: Dict[str, int] = {}

        for row in rows:
            sub, platform, _, difficulty, _ = row
            if platform:
                by_platform[platform] = by_platform.get(platform, 0) + 1
            if difficulty:
                by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1
            if sub.language:
                by_language[sub.language] = by_language.get(sub.language, 0) + 1

        recent_rows = (
            SubmissionService._base_query(db, user_id)
            .order_by(desc(Submission.submitted_at))
            .limit(10)
            .all()
        )

        return {
            "total_submissions": total,
            "accepted": accepted,
            "wrong_answer": wrong_answer,
            "time_limit_exceeded": tle,
            "runtime_error": runtime_error,
            "by_platform": by_platform,
            "by_difficulty": by_difficulty,
            "by_language": by_language,
            "recent_submissions": [SubmissionService._row_to_dict(r) for r in recent_rows],
        }

    @staticmethod
    def get_problem_submissions(db: Session, user_id: int, problem_id: str, platform: str) -> List[Dict]:
        rows = (
            SubmissionService._base_query(db, user_id)
            .filter(
                PlatformAccount.platform_name == platform,
                ProblemStats.problem_id == problem_id,
            )
            .order_by(desc(Submission.submitted_at))
            .all()
        )
        return [SubmissionService._row_to_dict(r) for r in rows]

    @staticmethod
    def get_platform_summary(db: Session, user_id: int) -> Dict:
        rows = (
            db.query(
                PlatformAccount.platform_name,
                func.count(Submission.id).label("total"),
                func.sum(
                    case((func.lower(Submission.status) == "accepted", 1), else_=0)
                ).label("accepted"),
            )
            .join(Submission, Submission.platform_account_id == PlatformAccount.id)
            .filter(PlatformAccount.user_id == user_id)
            .group_by(PlatformAccount.platform_name)
            .all()
        )

        return {
            platform: {
                "total": total,
                "accepted": int(accepted or 0),
                "acceptance_rate": round((int(accepted or 0) / total * 100), 2) if total > 0 else 0,
            }
            for platform, total, accepted in rows
        }
