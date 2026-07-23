from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from shared.models import PeerDiscussion, DiscussionReply, DiscussionVote, User, ProblemStats
from typing import List, Optional, Dict
from datetime import datetime


class DiscussionService:
    
    @staticmethod
    def create_discussion(
        db: Session,
        user_id: int,
        title: str,
        content: str,
        problem_stat_id: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> PeerDiscussion:
        """Create a new discussion"""
        discussion = PeerDiscussion(
            user_id=user_id,
            title=title,
            content=content,
            problem_stat_id=problem_stat_id,
            tags=tags or []
        )
        db.add(discussion)
        db.commit()
        db.refresh(discussion)
        return discussion
    
    @staticmethod
    def get_discussions(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        problem_stat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        is_solved: Optional[bool] = None,
        sort_by: str = "recent"
    ) -> List[Dict]:
        """Get discussions with filters"""
        query = db.query(
            PeerDiscussion,
            User.username,
            User.full_name,
            ProblemStats.problem_title,
            func.count(DiscussionReply.id).label('reply_count')
        ).join(
            User, PeerDiscussion.user_id == User.id
        ).outerjoin(
            ProblemStats, PeerDiscussion.problem_stat_id == ProblemStats.id
        ).outerjoin(
            DiscussionReply, PeerDiscussion.id == DiscussionReply.discussion_id
        )
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    PeerDiscussion.title.ilike(f"%{search}%"),
                    PeerDiscussion.content.ilike(f"%{search}%")
                )
            )
        
        if tags:
            for tag in tags:
                query = query.filter(PeerDiscussion.tags.contains([tag]))
        
        if problem_stat_id:
            query = query.filter(PeerDiscussion.problem_stat_id == problem_stat_id)
        
        if user_id:
            query = query.filter(PeerDiscussion.user_id == user_id)
        
        if is_solved is not None:
            query = query.filter(PeerDiscussion.is_solved == is_solved)
        
        # Group by for count
        query = query.group_by(
            PeerDiscussion.id,
            User.username,
            User.full_name,
            ProblemStats.problem_title
        )
        
        # Sorting
        if sort_by == "popular":
            query = query.order_by(desc(PeerDiscussion.upvotes))
        elif sort_by == "recent":
            query = query.order_by(desc(PeerDiscussion.created_at))
        elif sort_by == "replies":
            query = query.order_by(desc('reply_count'))
        
        results = query.offset(skip).limit(limit).all()
        
        return [
            {
                "id": disc.id,
                "user_id": disc.user_id,
                "username": username,
                "full_name": full_name,
                "problem_stat_id": disc.problem_stat_id,
                "problem_title": problem_title,
                "title": disc.title,
                "content": disc.content,
                "tags": disc.tags,
                "upvotes": disc.upvotes,
                "is_solved": disc.is_solved,
                "reply_count": reply_count,
                "created_at": disc.created_at,
                "updated_at": disc.updated_at
            }
            for disc, username, full_name, problem_title, reply_count in results
        ]
    
    @staticmethod
    def get_discussion_detail(db: Session, discussion_id: int, current_user_id: Optional[int] = None) -> Optional[Dict]:
        """Get discussion with replies"""
        discussion = db.query(
            PeerDiscussion,
            User.username,
            User.full_name,
            ProblemStats.problem_title
        ).join(
            User, PeerDiscussion.user_id == User.id
        ).outerjoin(
            ProblemStats, PeerDiscussion.problem_stat_id == ProblemStats.id
        ).filter(
            PeerDiscussion.id == discussion_id
        ).first()
        
        if not discussion:
            return None
        
        disc, username, full_name, problem_title = discussion
        
        # Get replies
        replies = db.query(
            DiscussionReply,
            User.username,
            User.full_name
        ).join(
            User, DiscussionReply.user_id == User.id
        ).filter(
            DiscussionReply.discussion_id == discussion_id
        ).order_by(
            desc(DiscussionReply.is_solution),
            desc(DiscussionReply.upvotes),
            DiscussionReply.created_at
        ).all()
        
        # Check if user voted
        user_voted = None
        if current_user_id:
            vote = db.query(DiscussionVote).filter(
                and_(
                    DiscussionVote.user_id == current_user_id,
                    DiscussionVote.discussion_id == discussion_id
                )
            ).first()
            if vote:
                user_voted = vote.vote_type
        
        return {
            "id": disc.id,
            "user_id": disc.user_id,
            "username": username,
            "full_name": full_name,
            "problem_stat_id": disc.problem_stat_id,
            "problem_title": problem_title,
            "title": disc.title,
            "content": disc.content,
            "tags": disc.tags,
            "upvotes": disc.upvotes,
            "is_solved": disc.is_solved,
            "reply_count": len(replies),
            "created_at": disc.created_at,
            "updated_at": disc.updated_at,
            "user_voted": user_voted,
            "replies": [
                {
                    "id": reply.id,
                    "discussion_id": reply.discussion_id,
                    "user_id": reply.user_id,
                    "username": reply_username,
                    "full_name": reply_full_name,
                    "content": reply.content,
                    "upvotes": reply.upvotes,
                    "is_solution": reply.is_solution,
                    "created_at": reply.created_at,
                    "updated_at": reply.updated_at
                }
                for reply, reply_username, reply_full_name in replies
            ]
        }
    
    @staticmethod
    def add_reply(db: Session, discussion_id: int, user_id: int, content: str, is_solution: bool = False) -> DiscussionReply:
        """Add a reply to discussion"""
        reply = DiscussionReply(
            discussion_id=discussion_id,
            user_id=user_id,
            content=content,
            is_solution=is_solution
        )
        db.add(reply)
        
        # Mark discussion as solved if this is a solution
        if is_solution:
            discussion = db.query(PeerDiscussion).filter(PeerDiscussion.id == discussion_id).first()
            if discussion:
                discussion.is_solved = True
        
        db.commit()
        db.refresh(reply)
        return reply
    
    @staticmethod
    def vote_discussion(db: Session, discussion_id: int, user_id: int, vote_type: str) -> Dict:
        """Vote on a discussion"""
        # Check existing vote
        existing_vote = db.query(DiscussionVote).filter(
            and_(
                DiscussionVote.user_id == user_id,
                DiscussionVote.discussion_id == discussion_id
            )
        ).first()
        
        discussion = db.query(PeerDiscussion).filter(PeerDiscussion.id == discussion_id).first()
        if not discussion:
            return {"success": False, "message": "Discussion not found"}
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Remove vote
                db.delete(existing_vote)
                discussion.upvotes -= 1 if vote_type == "upvote" else 0
                db.commit()
                return {"success": True, "action": "removed", "upvotes": discussion.upvotes}
            else:
                # Change vote
                existing_vote.vote_type = vote_type
                discussion.upvotes += 2 if vote_type == "upvote" else -2
                db.commit()
                return {"success": True, "action": "changed", "upvotes": discussion.upvotes}
        else:
            # New vote
            vote = DiscussionVote(
                user_id=user_id,
                discussion_id=discussion_id,
                vote_type=vote_type
            )
            db.add(vote)
            discussion.upvotes += 1 if vote_type == "upvote" else 0
            db.commit()
            return {"success": True, "action": "added", "upvotes": discussion.upvotes}
    
    @staticmethod
    def vote_reply(db: Session, reply_id: int, user_id: int, vote_type: str) -> Dict:
        """Vote on a reply"""
        existing_vote = db.query(DiscussionVote).filter(
            and_(
                DiscussionVote.user_id == user_id,
                DiscussionVote.reply_id == reply_id
            )
        ).first()
        
        reply = db.query(DiscussionReply).filter(DiscussionReply.id == reply_id).first()
        if not reply:
            return {"success": False, "message": "Reply not found"}
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                db.delete(existing_vote)
                reply.upvotes -= 1 if vote_type == "upvote" else 0
                db.commit()
                return {"success": True, "action": "removed", "upvotes": reply.upvotes}
            else:
                existing_vote.vote_type = vote_type
                reply.upvotes += 2 if vote_type == "upvote" else -2
                db.commit()
                return {"success": True, "action": "changed", "upvotes": reply.upvotes}
        else:
            vote = DiscussionVote(
                user_id=user_id,
                reply_id=reply_id,
                vote_type=vote_type
            )
            db.add(vote)
            reply.upvotes += 1 if vote_type == "upvote" else 0
            db.commit()
            return {"success": True, "action": "added", "upvotes": reply.upvotes}
    
    @staticmethod
    def update_discussion(db: Session, discussion_id: int, user_id: int, **kwargs) -> Optional[PeerDiscussion]:
        """Update discussion (only by owner)"""
        discussion = db.query(PeerDiscussion).filter(
            and_(
                PeerDiscussion.id == discussion_id,
                PeerDiscussion.user_id == user_id
            )
        ).first()
        
        if not discussion:
            return None
        
        for key, value in kwargs.items():
            if value is not None and hasattr(discussion, key):
                setattr(discussion, key, value)
        
        discussion.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(discussion)
        return discussion
    
    @staticmethod
    def delete_discussion(db: Session, discussion_id: int, user_id: int) -> bool:
        """Delete discussion (only by owner)"""
        discussion = db.query(PeerDiscussion).filter(
            and_(
                PeerDiscussion.id == discussion_id,
                PeerDiscussion.user_id == user_id
            )
        ).first()
        
        if not discussion:
            return False
        
        db.delete(discussion)
        db.commit()
        return True
