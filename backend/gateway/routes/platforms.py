from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from shared.database import get_db
from shared.schemas import PlatformAccountCreate, PlatformAccountResponse
from shared.models import PlatformAccount, ProblemStats, Submission
from gateway.routes.auth import get_current_user
from services.connector.registry import ConnectorRegistry
from workers.tasks import sync_platform_data

router = APIRouter()

@router.get("/available")
async def list_available_platforms():
    """List all available platforms"""
    return {"platforms": ConnectorRegistry.list_platforms()}

@router.post("/connect", response_model=PlatformAccountResponse)
async def connect_platform(
    account: PlatformAccountCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect a new platform account"""
    # Check if already connected
    existing = db.query(PlatformAccount).filter(
        PlatformAccount.user_id == current_user.id,
        PlatformAccount.platform_name == account.platform_name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Platform already connected")
    
    # Verify platform exists
    if account.platform_name not in ConnectorRegistry.list_platforms():
        raise HTTPException(status_code=400, detail="Unknown platform")
    
    db_account = PlatformAccount(
        user_id=current_user.id,
        platform_name=account.platform_name,
        platform_username=account.platform_username,
        is_verified=False
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    # Trigger background sync
    background_tasks.add_task(sync_platform_data, db_account.id)
    
    return db_account

@router.get("/connected", response_model=List[PlatformAccountResponse])
async def list_connected_platforms(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all connected platforms"""
    accounts = db.query(PlatformAccount).filter(
        PlatformAccount.user_id == current_user.id
    ).all()
    return accounts

@router.get("/{platform_id}/problems")
async def get_platform_problems(
    platform_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all problems solved on a platform"""
    account = db.query(PlatformAccount).filter(
        PlatformAccount.id == platform_id,
        PlatformAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Platform account not found")
    
    problems = db.query(ProblemStats).filter(
        ProblemStats.platform_account_id == platform_id
    ).order_by(ProblemStats.solved_at.desc()).all()
    
    return problems

@router.get("/{platform_id}/problems/{problem_id}/submissions")
async def get_problem_submissions(
    platform_id: int,
    problem_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all submissions for a specific problem"""
    account = db.query(PlatformAccount).filter(
        PlatformAccount.id == platform_id,
        PlatformAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Platform account not found")
    
    problem = db.query(ProblemStats).filter(
        ProblemStats.id == problem_id,
        ProblemStats.platform_account_id == platform_id
    ).first()
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    submissions = db.query(Submission).filter(
        Submission.problem_stat_id == problem_id
    ).order_by(Submission.submitted_at.desc()).all()
    
    return {
        "problem": {
            "id": problem.id,
            "title": problem.problem_title,
            "difficulty": problem.difficulty,
            "topics": problem.topics,
            "solved_at": problem.solved_at
        },
        "submissions": submissions
    }

@router.post("/sync/{platform_id}")
async def sync_platform(
    platform_id: int,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger platform sync"""
    account = db.query(PlatformAccount).filter(
        PlatformAccount.id == platform_id,
        PlatformAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Platform account not found")
    
    background_tasks.add_task(sync_platform_data, platform_id)
    
    return {"message": "Sync initiated", "platform": account.platform_name}

@router.delete("/{platform_id}")
async def disconnect_platform(
    platform_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect a platform"""
    account = db.query(PlatformAccount).filter(
        PlatformAccount.id == platform_id,
        PlatformAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Platform account not found")
    
    db.delete(account)
    db.commit()
    
    return {"message": "Platform disconnected"}
