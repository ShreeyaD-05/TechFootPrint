from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from gateway.routes.auth import get_current_user
from shared.models import User
from shared.schemas import (
    DiscussionCreate,
    DiscussionUpdate,
    DiscussionReplyCreate,
    DiscussionVoteCreate,
)
from services.discussion.service import DiscussionService
from typing import Optional

router = APIRouter()


@router.post("/discussions")
def create_discussion(
    discussion: DiscussionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_discussion = DiscussionService.create_discussion(
        db,
        user_id=current_user.id,
        title=discussion.title,
        content=discussion.content,
        problem_stat_id=discussion.problem_stat_id,
        tags=discussion.tags,
    )
    return {"success": True, "discussion_id": new_discussion.id}


# NOTE: /my/posts MUST come before /{discussion_id} to avoid route shadowing
@router.get("/discussions/my/posts")
def get_my_discussions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    discussions = DiscussionService.get_discussions(
        db, skip=skip, limit=limit, user_id=current_user.id, sort_by="recent"
    )
    return {"discussions": discussions, "page": (skip // limit) + 1, "limit": limit}


@router.get("/discussions")
def get_discussions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tags: Optional[str] = None,
    problem_stat_id: Optional[int] = None,
    user_id: Optional[int] = None,
    is_solved: Optional[bool] = None,
    sort_by: str = Query("recent"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if sort_by not in ("recent", "popular", "replies"):
        sort_by = "recent"
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    discussions = DiscussionService.get_discussions(
        db,
        skip=skip,
        limit=limit,
        search=search,
        tags=tag_list,
        problem_stat_id=problem_stat_id,
        user_id=user_id,
        is_solved=is_solved,
        sort_by=sort_by,
    )
    return {"discussions": discussions, "page": (skip // limit) + 1, "limit": limit}


@router.get("/discussions/{discussion_id}")
def get_discussion_detail(
    discussion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    discussion = DiscussionService.get_discussion_detail(db, discussion_id, current_user.id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return discussion


@router.put("/discussions/{discussion_id}")
def update_discussion(
    discussion_id: int,
    discussion_update: DiscussionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = DiscussionService.update_discussion(
        db,
        discussion_id,
        current_user.id,
        title=discussion_update.title,
        content=discussion_update.content,
        tags=discussion_update.tags,
        is_solved=discussion_update.is_solved,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Discussion not found or unauthorized")
    return {"success": True, "message": "Discussion updated"}


@router.delete("/discussions/{discussion_id}")
def delete_discussion(
    discussion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = DiscussionService.delete_discussion(db, discussion_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Discussion not found or unauthorized")
    return {"success": True, "message": "Discussion deleted"}


@router.post("/discussions/{discussion_id}/replies")
def add_reply(
    discussion_id: int,
    reply: DiscussionReplyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_reply = DiscussionService.add_reply(
        db, discussion_id, current_user.id, reply.content, reply.is_solution
    )
    return {"success": True, "reply_id": new_reply.id}


@router.post("/discussions/{discussion_id}/vote")
def vote_discussion(
    discussion_id: int,
    vote: DiscussionVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if vote.vote_type not in ("upvote", "downvote"):
        raise HTTPException(status_code=400, detail="Invalid vote type")
    return DiscussionService.vote_discussion(db, discussion_id, current_user.id, vote.vote_type)


@router.post("/discussions/replies/{reply_id}/vote")
def vote_reply(
    reply_id: int,
    vote: DiscussionVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if vote.vote_type not in ("upvote", "downvote"):
        raise HTTPException(status_code=400, detail="Invalid vote type")
    return DiscussionService.vote_reply(db, reply_id, current_user.id, vote.vote_type)
