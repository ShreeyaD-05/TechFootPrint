from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging
from shared.database import get_db
from gateway.routes.auth import get_current_user
from shared.models import User, SuggestionFeedback
from shared.schemas import SuggestionFeedbackCreate
from services.suggestions.service import SuggestionService, PROBLEM_BANK
from services.inference.predict import get_engine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/suggestions")
def get_suggestions(
    strategy: str = Query("balanced", description="balanced|gap_fill|progression|contest_prep"),
    n: int = Query(10, ge=1, le=20),
    difficulty: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    use_dl: bool = Query(True, description="Use DL model if available, fallback to rule-based"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered personalized problem suggestions.
    
    Tries DL model first (if trained), falls back to rule-based system.
    
    Query Parameters:
    - strategy: balanced (default) | gap_fill | progression | contest_prep
    - n: number of recommendations (1-20, default 10)
    - difficulty: filter by easy/medium/hard
    - platform: filter by platform (leetcode/codeforces/etc)
    - topic: filter by topic
    - use_dl: use DL model if available (default true)
    """
    
    # Try DL model first
    if use_dl:
        try:
            engine = get_engine(device_str="cpu")
            if engine is not None:
                logger.info(f"Using DL model for user {current_user.id}")
                
                # Build user profile from DB
                profile = SuggestionService._build_user_profile(db, current_user.id)
                if profile is None:
                    raise HTTPException(status_code=404, detail="User profile not found")
                
                # Get solved problem IDs
                solved_ids = SuggestionService._get_solved_ids(db, current_user.id)
                
                # Get candidate problems
                candidates = []
                for p in PROBLEM_BANK:
                    if p["id"] in solved_ids:
                        continue
                    if difficulty and p["difficulty"].lower() != difficulty.lower():
                        continue
                    if platform and p["platform"].lower() != platform.lower():
                        continue
                    if topic:
                        topic_lower = topic.lower()
                        if not any(topic_lower in t.lower() for t in p["topics"]):
                            continue
                    candidates.append(p)
                
                if not candidates:
                    logger.warning(f"No candidate problems for user {current_user.id}")
                    return {"suggestions": [], "skill_analysis": {}, "source": "dl", "message": "No unsolved problems matching filters"}
                
                # Get DL recommendations
                dl_recommendations = engine.recommend(
                    user_profile=profile,
                    candidate_problems=candidates,
                    n=n,
                    strategy=strategy,
                    use_exploration=True
                )
                
                # Get skill analysis
                skill_analysis = SuggestionService.get_skill_analysis(db, current_user.id)
                
                return {
                    "suggestions": dl_recommendations,
                    "skill_analysis": skill_analysis,
                    "profile_summary": {
                        "total_solved": profile.total_solved,
                        "easy": profile.easy_solved,
                        "medium": profile.medium_solved,
                        "hard": profile.hard_solved,
                        "platforms": profile.platforms,
                        "streak": profile.streak,
                    },
                    "source": "dl_model"
                }
        except Exception as e:
            logger.warning(f"DL model failed for user {current_user.id}: {e}. Falling back to rule-based.")
    
    # Fallback to rule-based system
    logger.info(f"Using rule-based system for user {current_user.id}")
    return {
        **SuggestionService.get_suggestions(
            db, current_user.id,
            strategy=strategy, n=n,
            difficulty_filter=difficulty,
            platform_filter=platform,
            topic_filter=topic
        ),
        "source": "rule_based"
    }


@router.get("/suggestions/skill-analysis")
def get_skill_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed skill gap analysis for the current user"""
    return SuggestionService.get_skill_analysis(db, current_user.id)


@router.get("/suggestions/dl-benchmark")
def get_dl_benchmark(
    n: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare DL recommendations against rule-based system.
    
    Returns both recommendation lists and comparison metrics:
    - overlap_pct: percentage of recommendations that match
    - dl_latency_ms: DL model inference time
    - rb_latency_ms: rule-based system time
    - dl_unique_recs: recommendations only from DL
    - rb_unique_recs: recommendations only from rule-based
    """
    try:
        engine = get_engine(device_str="cpu")
        if engine is None:
            raise HTTPException(status_code=503, detail="DL model not trained yet")
        
        # Build user profile
        profile = SuggestionService._build_user_profile(db, current_user.id)
        if profile is None:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Get candidates
        solved_ids = SuggestionService._get_solved_ids(db, current_user.id)
        candidates = [p for p in PROBLEM_BANK if p["id"] not in solved_ids]
        
        if not candidates:
            return {"message": "No unsolved problems available"}
        
        # Benchmark
        return engine.benchmark_vs_rule_based(profile, candidates, n=n)
    
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/dl-attention/{problem_id}")
def get_dl_attention(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get attention visualization for a specific problem.
    
    Returns:
    - tokens: list of tokenized problem content
    - attention_maps: attention weights from all layers
    - token_importance: per-token importance scores
    - n_layers: number of transformer layers
    - n_heads: number of attention heads
    """
    try:
        engine = get_engine(device_str="cpu")
        if engine is None:
            raise HTTPException(status_code=503, detail="DL model not trained yet")
        
        # Find problem in bank
        problem = None
        for p in PROBLEM_BANK:
            if p["id"] == problem_id:
                problem = p
                break
        
        if problem is None:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        # Get attention visualization
        return engine.visualize_attention(problem)
    
    except Exception as e:
        logger.error(f"Attention visualization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/batch-readiness")
def get_batch_readiness(
    batch_year: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get placement readiness for a batch (faculty/management only)"""
    if current_user.role not in ["faculty", "dept_admin", "management", "super_admin"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(User).filter(User.role == "student")
    if batch_year:
        query = query.filter(User.batch_year == batch_year)
    if department:
        query = query.filter(User.department == department)

    user_ids = [u.id for u in query.all()]
    return {"readiness": SuggestionService.get_batch_readiness(db, user_ids)}


@router.post("/suggestions/feedback")
def submit_suggestion_feedback(
    feedback: SuggestionFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback on a suggestion to improve the model.
    
    This feedback is used to:
    1. Train the DL model (offline fine-tuning)
    2. Update online learning (real-time model updates)
    3. Evaluate recommendation quality
    
    Feedback fields:
    - problem_id: the recommended problem
    - platform: platform (leetcode, codeforces, etc)
    - strategy: recommendation strategy used
    - was_helpful: whether user found it helpful
    - was_solved: whether user solved it
    - difficulty_felt: too_easy | just_right | too_hard
    - suggestion_score: user's rating (0-1)
    """
    try:
        record = SuggestionFeedback(
            user_id=current_user.id,
            **feedback.model_dump()
        )
        db.add(record)
        db.commit()
        
        # Try to update online learning model
        try:
            from services.training.train import OnlineLearner
            from services.recommender.problem_encoder import ProblemBankEncoder
            from services.training.dataset import InteractionSample
            import torch
            
            engine = get_engine(device_str="cpu")
            if engine is not None:
                # Build interaction sample from feedback
                profile = SuggestionService._build_user_profile(db, current_user.id)
                if profile is not None:
                    # Get problem embedding
                    prob_emb = engine.bank_encoder.get_embedding(feedback.problem_id)
                    if prob_emb is None:
                        prob_emb = torch.zeros(engine.config["embed_dim"])
                    
                    # Get user history
                    solved_ids = SuggestionService._get_solved_ids(db, current_user.id)
                    history_embeds = []
                    history_diffs = []
                    for pid in list(solved_ids)[-32:]:  # last 32 solved
                        emb = engine.bank_encoder.get_embedding(pid)
                        if emb is not None:
                            history_embeds.append(emb)
                            history_diffs.append(1)  # default to medium
                    
                    # Create sample
                    from services.suggestions.model import SkillVector
                    skill_vec = SkillVector.encode(profile)
                    
                    sample = InteractionSample(
                        user_id=current_user.id,
                        problem_id=feedback.problem_id,
                        problem_embedding=prob_emb,
                        user_skill_vec=skill_vec,
                        history_embeddings=history_embeds,
                        history_difficulties=history_diffs,
                        was_solved=feedback.was_solved or False,
                        was_helpful=feedback.was_helpful,
                        difficulty_felt=feedback.difficulty_felt,
                        days_ago=0.0
                    )
                    
                    # Online learning update
                    learner = OnlineLearner(
                        engine.user_encoder,
                        engine.recommender,
                        engine.config,
                        engine.device
                    )
                    loss_dict = learner.partial_fit(sample.__dict__)
                    logger.info(f"Online learning update for user {current_user.id}: {loss_dict}")
        
        except Exception as e:
            logger.warning(f"Online learning update failed: {e}. Feedback still recorded.")
        
        return {"success": True, "message": "Feedback recorded and model updated"}
    
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
