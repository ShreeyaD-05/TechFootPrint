from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.schemas import AnalyticsResponse
from shared.models import Analytics
from gateway.routes.auth import get_current_user
from services.analytics.service import AnalyticsService

router = APIRouter()

@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user analytics"""
    analytics = db.query(Analytics).filter(Analytics.user_id == current_user.id).first()
    
    if not analytics:
        # Calculate if not exists
        analytics = AnalyticsService.calculate_user_analytics(db, current_user.id)
    
    return analytics

@router.post("/recalculate")
async def recalculate_analytics(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually recalculate analytics"""
    analytics = AnalyticsService.calculate_user_analytics(db, current_user.id)
    return {"message": "Analytics recalculated", "total_problems": analytics.total_problems_solved}

@router.get("/heatmap")
async def get_activity_heatmap(
    days: int = 365,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity heatmap data"""
    heatmap = AnalyticsService.get_activity_heatmap(db, current_user.id, days)
    return {"heatmap": heatmap}
