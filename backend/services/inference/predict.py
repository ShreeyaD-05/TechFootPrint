"""
Inference engine — production-ready recommendation serving.

Responsibilities:
    - Load trained models from checkpoints
    - Encode user from DB profile + interaction history
    - Score all candidate problems
    - Apply exploration strategy
    - Generate human-readable explanations
    - Visualise attention weights
    - Benchmark against rule-based system

Thread-safe: models are loaded once and reused across requests.
"""

import os
import json
import math
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

import torch
import torch.nn as nn
import numpy as np

from services.transformer.tokenizer import SimpleTokenizer
from services.transformer.encoder import ProblemEncoder
from services.recommender.user_encoder import UserEncoder, InteractionRecord
from services.recommender.recommender_model import RecommenderModel, ExplorationStrategy
from services.recommender.problem_encoder import ProblemBankEncoder
from services.training.train import DEFAULT_CONFIG, load_checkpoint
from services.training.dataset import (
    load_problems_from_excel,
    DIFF_MAP,
    _encode_topics,
    _topic_cluster_label,
)

logger = logging.getLogger(__name__)

# ── Singleton model registry ───────────────────────────────────────────────────

_MODEL_REGISTRY: Dict[str, object] = {}


def _get_registry() -> Dict:
    return _MODEL_REGISTRY


# ── Model loader ───────────────────────────────────────────────────────────────

class DeepRecommenderEngine:
    """
    Production inference engine for the deep recommendation system.

    Usage:
        engine = DeepRecommenderEngine.load(checkpoint_dir)
        results = engine.recommend(user_profile, candidate_problems, n=10)
    """

    def __init__(
        self,
        problem_encoder: ProblemEncoder,
        user_encoder: UserEncoder,
        recommender: RecommenderModel,
        tokenizer: SimpleTokenizer,
        bank_encoder: ProblemBankEncoder,
        config: Dict,
        device: torch.device,
        exploration: ExplorationStrategy,
    ):
        self.problem_encoder = problem_encoder
        self.user_encoder = user_encoder
        self.recommender = recommender
        self.tokenizer = tokenizer
        self.bank_encoder = bank_encoder
        self.config = config
        self.device = device
        self.exploration = exploration

        # Set all models to eval mode
        for m in [problem_encoder, user_encoder, recommender]:
            m.eval()

    @classmethod
    def load(
        cls,
        checkpoint_dir: str,
        excel_path: Optional[str] = None,
        device_str: str = "cpu",
        exploration_strategy: str = "epsilon_greedy",
        epsilon: float = 0.15,
    ) -> "DeepRecommenderEngine":
        """
        Load a trained engine from a checkpoint directory.

        Args:
            checkpoint_dir: directory containing model weights + config
            excel_path: path to LeetCode Questions.xlsx (for problem bank)
            device_str: "cpu" or "cuda"
        """
        ckpt_dir = Path(checkpoint_dir)
        device = torch.device(device_str)

        # Load config
        config_path = ckpt_dir / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
        else:
            config = DEFAULT_CONFIG.copy()

        # Load tokenizer
        tokenizer = SimpleTokenizer.load(str(ckpt_dir / "tokenizer.json"))
        logger.info("Tokenizer loaded: %d tokens", tokenizer.vocab_size_actual)

        # Build models
        problem_encoder = ProblemEncoder(
            vocab_size=tokenizer.vocab_size_actual,
            d_model=config["d_model"],
            embed_dim=config["embed_dim"],
            num_heads=config["num_heads"],
            num_layers=config["num_encoder_layers"],
            d_ff=config["d_ff"],
            max_len=config["max_len"],
            dropout=0.0,  # no dropout at inference
        )

        user_encoder = UserEncoder(
            embed_dim=config["embed_dim"],
            num_heads=config["num_heads"],
            num_layers=2,
            max_history=config["max_history"],
            dropout=0.0,
        )

        recommender = RecommenderModel(
            embed_dim=config["embed_dim"],
            hidden_dim=config["hidden_dim"],
            num_residual_blocks=config["num_residual_blocks"],
            dropout=0.0,
        )

        # Load weights
        pe_path = ckpt_dir / "problem_encoder.pt"
        ue_path = ckpt_dir / "user_encoder.pt"
        rec_path = ckpt_dir / "recommender.pt"

        if pe_path.exists():
            problem_encoder.load_state_dict(torch.load(pe_path, map_location=device))
            logger.info("Problem encoder weights loaded.")
        if ue_path.exists():
            user_encoder.load_state_dict(torch.load(ue_path, map_location=device))
            logger.info("User encoder weights loaded.")
        if rec_path.exists():
            recommender.load_state_dict(torch.load(rec_path, map_location=device))
            logger.info("Recommender weights loaded.")

        problem_encoder = problem_encoder.to(device)
        user_encoder = user_encoder.to(device)
        recommender = recommender.to(device)

        # Build problem bank encoder
        bank_encoder = ProblemBankEncoder(
            model=problem_encoder,
            tokenizer=tokenizer,
            device=device,
            max_len=config["max_len"],
        )

        # Load cached embeddings if available
        emb_cache_path = ckpt_dir / "problem_embeddings.pt"
        if emb_cache_path.exists():
            cache = torch.load(emb_cache_path, map_location="cpu")
            for pid, emb in zip(cache["ids"], cache["embeddings"]):
                bank_encoder._cache[pid] = emb
            logger.info("Loaded %d cached problem embeddings.", len(bank_encoder._cache))
        elif excel_path:
            problems = load_problems_from_excel(excel_path)
            bank_encoder.build_cache([p.to_dict() for p in problems])

        exploration = ExplorationStrategy(
            strategy=exploration_strategy,
            epsilon=epsilon,
        )

        return cls(
            problem_encoder=problem_encoder,
            user_encoder=user_encoder,
            recommender=recommender,
            tokenizer=tokenizer,
            bank_encoder=bank_encoder,
            config=config,
            device=device,
            exploration=exploration,
        )

    # ── Core recommendation ────────────────────────────────────────────────────

    def recommend(
        self,
        user_profile,           # UserProfile from suggestions/model.py
        candidate_problems: List[Dict],
        n: int = 10,
        strategy: str = "balanced",
        use_exploration: bool = True,
    ) -> List[Dict]:
        """
        Generate top-N recommendations for a user.

        Args:
            user_profile: UserProfile dataclass
            candidate_problems: list of problem dicts (unsolved candidates)
            n: number of recommendations
            strategy: balanced | gap_fill | progression | contest_prep
            use_exploration: apply epsilon-greedy/UCB exploration

        Returns:
            list of recommendation dicts with scores and explanations
        """
        if not candidate_problems:
            return []

        # ── Encode user ────────────────────────────────────────────────────────
        user_emb = self._encode_user(user_profile)  # (1, embed_dim)

        # ── Score all candidates ───────────────────────────────────────────────
        scores = []
        problem_ids = []

        for p in candidate_problems:
            pid = p.get("id") or p.get("problem_id")
            prob_emb = self.bank_encoder.get_embedding(pid)

            if prob_emb is None:
                # Encode on-the-fly
                prob_emb = self.bank_encoder.encode_single(p)

            prob_emb = prob_emb.unsqueeze(0).to(self.device)

            with torch.no_grad():
                score = self.recommender.score(user_emb, prob_emb)

            scores.append(score.item())
            problem_ids.append(pid)

        scores_arr = np.array(scores)

        # ── Apply strategy adjustments ─────────────────────────────────────────
        scores_arr = self._apply_strategy(
            scores_arr, candidate_problems, user_profile, strategy
        )

        # ── Exploration ────────────────────────────────────────────────────────
        if use_exploration:
            selected_indices = self.exploration.select(problem_ids, scores_arr, n=n * 2)
        else:
            selected_indices = list(np.argsort(scores_arr)[::-1][: n * 2])

        # ── Diversify and build output ─────────────────────────────────────────
        results = self._build_results(
            selected_indices, candidate_problems, scores_arr,
            user_profile, strategy, n
        )

        return results

    def _encode_user(self, user_profile) -> torch.Tensor:
        """Encode user profile into embedding vector."""
        from services.suggestions.model import SkillVector

        # Skill vector
        skill_vec = SkillVector.encode(user_profile)
        skill_tensor = torch.tensor(skill_vec, dtype=torch.float32).unsqueeze(0).to(self.device)

        # History: use zeros if no history available (cold start)
        # In production, pass actual solved problem embeddings
        max_history = self.config["max_history"]
        embed_dim = self.config["embed_dim"]

        hist_emb = torch.zeros(1, max_history, embed_dim, device=self.device)
        hist_diff = torch.ones(1, max_history, dtype=torch.long, device=self.device)
        pad_mask = torch.ones(1, max_history, dtype=torch.bool, device=self.device)

        with torch.no_grad():
            user_emb = self.user_encoder(hist_emb, hist_diff, skill_tensor, pad_mask)

        return user_emb  # (1, embed_dim)

    def _encode_user_with_history(
        self,
        user_profile,
        solved_problem_ids: List[str],
        solved_difficulties: List[str],
    ) -> torch.Tensor:
        """
        Encode user with actual problem history.
        More accurate than skill-vector-only encoding.
        """
        from services.suggestions.model import SkillVector

        skill_vec = SkillVector.encode(user_profile)
        skill_tensor = torch.tensor(skill_vec, dtype=torch.float32).unsqueeze(0).to(self.device)

        max_history = self.config["max_history"]
        embed_dim = self.config["embed_dim"]

        # Get embeddings for solved problems
        hist_embeds = []
        hist_diffs = []
        for pid, diff in zip(solved_problem_ids[-max_history:], solved_difficulties[-max_history:]):
            emb = self.bank_encoder.get_embedding(pid)
            if emb is not None:
                hist_embeds.append(emb)
                hist_diffs.append(DIFF_MAP.get(diff.lower() if diff else "medium", 1))

        n = len(hist_embeds)
        if n > 0:
            hist_tensor = torch.stack(hist_embeds).unsqueeze(0).to(self.device)
            diff_tensor = torch.tensor(hist_diffs, dtype=torch.long).unsqueeze(0).to(self.device)
            pad_mask = torch.zeros(1, n, dtype=torch.bool, device=self.device)

            # Pad to max_history
            if n < max_history:
                pad_len = max_history - n
                pad_emb = torch.zeros(1, pad_len, embed_dim, device=self.device)
                pad_diff = torch.ones(1, pad_len, dtype=torch.long, device=self.device)
                pad_m = torch.ones(1, pad_len, dtype=torch.bool, device=self.device)
                hist_tensor = torch.cat([hist_tensor, pad_emb], dim=1)
                diff_tensor = torch.cat([diff_tensor, pad_diff], dim=1)
                pad_mask = torch.cat([pad_mask, pad_m], dim=1)
        else:
            hist_tensor = torch.zeros(1, max_history, embed_dim, device=self.device)
            diff_tensor = torch.ones(1, max_history, dtype=torch.long, device=self.device)
            pad_mask = torch.ones(1, max_history, dtype=torch.bool, device=self.device)

        with torch.no_grad():
            user_emb = self.user_encoder(hist_tensor, diff_tensor, skill_tensor, pad_mask)

        return user_emb

    def _apply_strategy(
        self,
        scores: np.ndarray,
        problems: List[Dict],
        user_profile,
        strategy: str,
    ) -> np.ndarray:
        """Apply strategy-specific score adjustments."""
        from services.suggestions.model import (
            DifficultyProgressionEngine, TopicGapAnalyzer, UserProfile
        )

        target_diff, _ = DifficultyProgressionEngine.get_target_difficulty(user_profile)
        weak_topics = {
            w["topic"] for w in TopicGapAnalyzer.find_weak_topics(user_profile)
        }

        adjusted = scores.copy()
        for i, p in enumerate(problems):
            diff = (p.get("difficulty") or "medium").lower()
            topics = [t.lower().replace(" ", "-") for t in p.get("topics", [])]

            # Difficulty alignment bonus
            if diff == target_diff:
                adjusted[i] += 0.1
            elif strategy == "progression" and diff == {"easy": "medium", "medium": "hard"}.get(target_diff):
                adjusted[i] += 0.08

            # Gap fill bonus
            if strategy in ("balanced", "gap_fill"):
                overlap = len(set(topics) & weak_topics)
                adjusted[i] += min(overlap * 0.05, 0.15)

            # Contest prep bonus
            if strategy == "contest_prep":
                contest_topics = {"dynamic-programming", "greedy", "graph", "math", "binary-search"}
                if set(topics) & contest_topics:
                    adjusted[i] += 0.1

        return adjusted

    def _build_results(
        self,
        indices: List[int],
        problems: List[Dict],
        scores: np.ndarray,
        user_profile,
        strategy: str,
        n: int,
    ) -> List[Dict]:
        """Build final recommendation list with diversity and explanations."""
        from services.suggestions.model import TopicGapAnalyzer, DifficultyProgressionEngine

        weak_topics = {
            w["topic"] for w in TopicGapAnalyzer.find_weak_topics(user_profile)
        }
        target_diff, _ = DifficultyProgressionEngine.get_target_difficulty(user_profile)

        selected = []
        covered_topics = set()

        for idx in indices:
            if len(selected) >= n:
                break
            p = problems[idx]
            topics = set(t.lower().replace(" ", "-") for t in p.get("topics", []))

            # Diversity: allow if covers new topics or we need more
            if len(selected) < n // 2 or not topics.issubset(covered_topics):
                pid = p.get("id") or p.get("problem_id")
                explanation = self._generate_explanation(
                    p, user_profile, weak_topics, target_diff, strategy
                )

                selected.append({
                    "rank": len(selected) + 1,
                    "problem_id": pid,
                    "title": p.get("title", ""),
                    "difficulty": p.get("difficulty", "medium"),
                    "platform": p.get("platform", "leetcode"),
                    "topics": p.get("topics", []),
                    "url": p.get("url", "#"),
                    "dl_score": round(float(scores[idx]), 4),
                    "explanation": explanation,
                    "fills_gap": bool(topics & weak_topics),
                    "target_topics": list(topics & weak_topics),
                })
                covered_topics.update(topics)

        # Fill remaining slots without diversity constraint
        for idx in indices:
            if len(selected) >= n:
                break
            p = problems[idx]
            pid = p.get("id") or p.get("problem_id")
            if not any(r["problem_id"] == pid for r in selected):
                topics = set(t.lower().replace(" ", "-") for t in p.get("topics", []))
                explanation = self._generate_explanation(
                    p, user_profile, weak_topics, target_diff, strategy
                )
                selected.append({
                    "rank": len(selected) + 1,
                    "problem_id": pid,
                    "title": p.get("title", ""),
                    "difficulty": p.get("difficulty", "medium"),
                    "platform": p.get("platform", "leetcode"),
                    "topics": p.get("topics", []),
                    "url": p.get("url", "#"),
                    "dl_score": round(float(scores[idx]), 4),
                    "explanation": explanation,
                    "fills_gap": bool(topics & weak_topics),
                    "target_topics": list(topics & weak_topics),
                })

        return selected[:n]

    def _generate_explanation(
        self,
        problem: Dict,
        user_profile,
        weak_topics: set,
        target_diff: str,
        strategy: str,
    ) -> str:
        """
        Generate a human-readable explanation for a recommendation.

        Examples:
            "Recommended because you are weak in Graphs and recently solved DP problems"
            "Perfect difficulty match for your current level (medium)"
        """
        topics = [t.lower().replace(" ", "-") for t in problem.get("topics", [])]
        gap_topics = [t for t in topics if t in weak_topics]
        diff = (problem.get("difficulty") or "medium").lower()

        if gap_topics:
            topic_str = gap_topics[0].replace("-", " ").title()
            recent = user_profile.recent_topics[:2] if user_profile.recent_topics else []
            if recent:
                recent_str = " and ".join(t.replace("-", " ").title() for t in recent[:2])
                return (
                    f"Recommended because you are weak in {topic_str} "
                    f"and recently solved {recent_str} problems"
                )
            return f"Strengthen your {topic_str} skills — identified as a growth area"

        if diff == target_diff:
            return f"Perfect difficulty match for your current level ({diff})"

        if strategy == "progression":
            return f"Challenges you to the next level — step up from {target_diff} to {diff}"

        if strategy == "contest_prep":
            return "High-frequency contest pattern — great for competitive programming"

        if user_profile.streak > 7:
            return f"Keep your {user_profile.streak}-day streak going with this {diff} challenge"

        return (
            f"Recommended based on your {user_profile.total_solved} solved problems "
            f"and topic profile"
        )

    # ── Attention visualisation ────────────────────────────────────────────────

    def visualize_attention(
        self,
        problem: Dict,
        tokens: Optional[List[str]] = None,
    ) -> Dict:
        """
        Compute attention weights for a problem and return visualisation data.

        Returns:
            dict with:
                tokens: list of token strings
                attention_maps: list of (heads, seq, seq) arrays per layer
                token_importance: (seq,) importance scores
        """
        text = f"{problem.get('title', '')} {' '.join(problem.get('topics', []))}"
        token_ids = self.tokenizer.encode(text, max_length=self.config["max_len"])

        # Decode tokens for display
        if tokens is None:
            tokens = [
                self.tokenizer.id2token.get(tid, "[UNK]")
                for tid in token_ids
                if tid != 0  # skip padding
            ]

        topics = problem.get("topics", [])
        difficulty = problem.get("difficulty", "medium")

        token_tensor = torch.tensor([token_ids], dtype=torch.long, device=self.device)
        topic_ids = _encode_topics(topics)
        topic_tensor = torch.tensor([topic_ids], dtype=torch.long, device=self.device)
        diff_tensor = torch.tensor(
            [DIFF_MAP.get(difficulty.lower(), 1)], dtype=torch.long, device=self.device
        )

        with torch.no_grad():
            _ = self.problem_encoder(token_tensor, topic_tensor, diff_tensor)

        attn_maps = self.problem_encoder.get_attention_maps()
        token_importance = self.problem_encoder.get_token_importance(layer_idx=-1)

        return {
            "tokens": tokens,
            "attention_maps": [a.cpu().numpy().tolist() for a in attn_maps],
            "token_importance": token_importance[0].cpu().numpy().tolist(),
            "n_layers": len(attn_maps),
            "n_heads": attn_maps[0].shape[1] if attn_maps else 0,
        }

    # ── Benchmark vs rule-based ────────────────────────────────────────────────

    def benchmark_vs_rule_based(
        self,
        user_profile,
        candidate_problems: List[Dict],
        n: int = 10,
    ) -> Dict:
        """
        Compare DL recommendations against the rule-based system.

        Returns:
            dict with both recommendation lists and comparison metrics
        """
        from services.suggestions.model import (
            suggestion_engine, ProblemFeature
        )

        # DL recommendations
        t0 = time.time()
        dl_recs = self.recommend(user_profile, candidate_problems, n=n)
        dl_time = time.time() - t0

        # Rule-based recommendations
        t0 = time.time()
        candidates_pf = [
            ProblemFeature(
                problem_id=p.get("id", ""),
                title=p.get("title", ""),
                difficulty=p.get("difficulty", "medium"),
                topics=p.get("topics", []),
                platform=p.get("platform", "leetcode"),
            )
            for p in candidate_problems
        ]
        rb_recs = suggestion_engine.generate_suggestions(
            user_profile, candidates_pf, n_suggestions=n
        )
        rb_time = time.time() - t0

        # Overlap analysis
        dl_ids = {r["problem_id"] for r in dl_recs}
        rb_ids = {r["problem_id"] for r in rb_recs}
        overlap = dl_ids & rb_ids
        overlap_pct = len(overlap) / n * 100

        # Topic diversity
        dl_topics = set()
        rb_topics = set()
        for r in dl_recs:
            dl_topics.update(t.lower() for t in r.get("topics", []))
        for r in rb_recs:
            rb_topics.update(t.lower() for t in r.get("topics", []))

        return {
            "dl_recommendations": dl_recs,
            "rule_based_recommendations": rb_recs,
            "comparison": {
                "overlap_count": len(overlap),
                "overlap_pct": round(overlap_pct, 1),
                "dl_topic_diversity": len(dl_topics),
                "rb_topic_diversity": len(rb_topics),
                "dl_latency_ms": round(dl_time * 1000, 2),
                "rb_latency_ms": round(rb_time * 1000, 2),
                "dl_unique_recs": list(dl_ids - rb_ids),
                "rb_unique_recs": list(rb_ids - dl_ids),
            },
        }


# ── Singleton loader ───────────────────────────────────────────────────────────

_engine_instance: Optional[DeepRecommenderEngine] = None


def get_engine(
    checkpoint_dir: str = "checkpoints/dl_recommender",
    excel_path: Optional[str] = None,
    device_str: str = "cpu",
    force_reload: bool = False,
) -> Optional[DeepRecommenderEngine]:
    """
    Get or create the singleton DeepRecommenderEngine.

    Returns None if checkpoints don't exist yet (model not trained).
    """
    global _engine_instance

    if _engine_instance is not None and not force_reload:
        return _engine_instance

    ckpt_dir = Path(checkpoint_dir)
    if not (ckpt_dir / "tokenizer.json").exists():
        logger.warning(
            "DL model not trained yet. Checkpoint not found at %s. "
            "Run training first with: python -m services.training.train",
            checkpoint_dir,
        )
        return None

    try:
        _engine_instance = DeepRecommenderEngine.load(
            checkpoint_dir=checkpoint_dir,
            excel_path=excel_path,
            device_str=device_str,
        )
        logger.info("DeepRecommenderEngine loaded successfully.")
    except Exception as e:
        logger.error("Failed to load DeepRecommenderEngine: %s", e)
        return None

    return _engine_instance
