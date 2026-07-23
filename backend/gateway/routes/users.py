from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.schemas import ProfileCreate, ProfileResponse
from shared.models import Profile
from gateway.routes.auth import get_current_user

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        # Auto-create profile on first access
        profile = Profile(
            user_id=current_user.id,
            portfolio_slug=current_user.username.lower(),
            is_public=True,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile: ProfileCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for key, value in profile.dict(exclude_unset=True).items():
        setattr(db_profile, key, value)

    db.commit()
    db.refresh(db_profile)
    return db_profile
