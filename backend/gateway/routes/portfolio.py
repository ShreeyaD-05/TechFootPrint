from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from shared.database import get_db
from shared.models import Profile, Analytics, PlatformAccount, User
from gateway.routes.auth import get_current_user

router = APIRouter()

@router.get("/{portfolio_slug}")
async def get_public_portfolio(portfolio_slug: str, db: Session = Depends(get_db)):
    """Get public portfolio by slug"""
    result = (
        db.query(Profile, User)
        .join(User, Profile.user_id == User.id)
        .filter(Profile.portfolio_slug == portfolio_slug, Profile.is_public == True)
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    profile, user = result

    # Get analytics and platforms in parallel queries
    analytics = db.query(Analytics).filter(Analytics.user_id == profile.user_id).first()
    platforms = db.query(PlatformAccount).filter(PlatformAccount.user_id == profile.user_id).all()

    return {
        "profile": {
            "username": user.username,
            "full_name": user.full_name,
            "bio": profile.bio,
            "avatar_url": profile.avatar_url,
            "location": profile.location,
            "website": profile.website,
            "github_username": profile.github_username,
            "linkedin_url": profile.linkedin_url,
        },
        "analytics": {
            "total_problems_solved": analytics.total_problems_solved if analytics else 0,
            "easy_solved": analytics.easy_solved if analytics else 0,
            "medium_solved": analytics.medium_solved if analytics else 0,
            "hard_solved": analytics.hard_solved if analytics else 0,
            "current_streak": analytics.current_streak if analytics else 0,
            "longest_streak": analytics.longest_streak if analytics else 0,
            "topic_distribution": analytics.topic_distribution if analytics else {},
            "platform_distribution": analytics.platform_distribution if analytics else {},
        },
        "platforms": [
            {
                "name": p.platform_name,
                "username": p.platform_username,
                "last_synced": p.last_synced_at,
            }
            for p in platforms
        ],
    }

@router.post("/generate")
async def generate_portfolio(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate/update portfolio data"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create profile first.")
    
    # Generate slug if not exists
    if not profile.portfolio_slug:
        profile.portfolio_slug = current_user.username.lower()
        db.commit()
    
    return {
        "message": "Portfolio generated",
        "portfolio_url": f"/portfolio/{profile.portfolio_slug}"
    }
