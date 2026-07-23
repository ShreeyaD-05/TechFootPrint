"""
Dataset loaders for the recommendation system.

Sources:
    1. Excel dataset (LeetCode Questions.xlsx) — problem content
    2. Database (SuggestionFeedback, ProblemStats) — user interactions

Provides:
    - ProblemDataset: problem content for encoder pre-training
    - InteractionDataset: user–problem interactions for recommendation training
    - DataLoader: custom batch generator (no PyTorch DataLoader dependency)
"""

import re
import math
import random
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader as TorchDataLoader
from typing import List, Dict, Optional, Tuple, Iterator
from datetime import datetime, timedelta
import logging

from services.transformer.embeddings import TagEmbedding
from services.transformer.tokenizer import SimpleTokenizer

logger = logging.getLogger(__name__)

# ── Difficulty mapping ─────────────────────────────────────────────────────────
DIFF_MAP = {"easy": 0, "medium": 1, "hard": 2}
DIFF_FELT_MAP = {"too_easy": 0, "just_right": 1, "too_hard": 2}
MAX_TOPICS = 8


def _parse_topics(raw: str) -> List[str]:
    """Parse comma-separated topic string into a list."""
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _encode_topics(topics: List[str], max_topics: int = MAX_TOPICS) -> List[int]:
    """Convert topic names to padded index list."""
    ids = []
    for t in topics:
        key = t.lower().replace(" ", "-")
        idx = TagEmbedding.TOPIC2ID.get(key, TagEmbedding.NUM_TOPICS)
        ids.append(idx)
    ids = ids[:max_topics]
    ids += [TagEmbedding.NUM_TOPICS] * (max_topics - len(ids))
    return ids


def _topic_cluster_label(topics: List[str]) -> int:
    """
    Assign a cluster label based on primary topic.
    Used for contrastive learning.
    """
    primary_clusters = {
        "dynamic-programming": 0, "memoization": 0,
        "graph": 1, "depth-first-search": 1, "breadth-first-search": 1,
        "topological-sort": 1, "shortest-path": 1, "union-find": 1,
        "tree": 2, "binary-tree": 2, "trie": 2, "segment-tree": 2,
        "array": 3, "matrix": 3, "prefix-sum": 3,
        "string": 4, "sliding-window": 4,
        "math": 5, "number-theory": 5, "combinatorics": 5,
        "sorting": 6, "binary-search": 6,
        "stack": 7, "queue": 7, "monotonic-stack": 7, "heap": 7,
        "linked-list": 8, "two-pointers": 8,
        "backtracking": 9, "recursion": 9, "divide-and-conquer": 9,
    }
    for t in topics:
        key = t.lower().replace(" ", "-")
        if key in primary_clusters:
            return primary_clusters[key]
    return 10  # misc


# ── Excel Problem Dataset ──────────────────────────────────────────────────────

class ProblemRecord:
    """Parsed problem from the Excel dataset."""

    def __init__(
        self,
        problem_id: str,
        title: str,
        difficulty: str,
        topics: List[str],
        acceptance_rate: float = 0.5,
        category: str = "Algorithms",
    ):
        self.problem_id = problem_id
        self.title = title
        self.difficulty = difficulty.lower() if difficulty else "medium"
        self.topics = topics
        self.acceptance_rate = acceptance_rate
        self.category = category

    def to_dict(self) -> Dict:
        return {
            "id": self.problem_id,
            "title": self.title,
            "difficulty": self.difficulty,
            "topics": self.topics,
            "acceptance_rate": self.acceptance_rate,
            "platform": "leetcode",
        }


def load_problems_from_excel(path: str) -> List[ProblemRecord]:
    """
    Load problems from the LeetCode Questions Excel file.

    Expected columns:
        ID, Problem Name, Likes, Dislikes, Like Ratio, Topics,
        Difficulty, Accepted, Submissions, Accept Rate, Free?, Solution?,
        Video Solution?, Category
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is required: pip install openpyxl")

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    problems = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:  # skip empty rows
            continue

        problem_id = str(row[0])
        # Title may be a HYPERLINK formula — extract display text
        raw_title = str(row[1]) if row[1] else ""
        title_match = re.search(r'"([^"]+)"\s*\)', raw_title)
        title = title_match.group(1) if title_match else raw_title

        topics = _parse_topics(str(row[5]) if row[5] else "")
        difficulty = str(row[6]) if row[6] else "Medium"

        # Accept rate: column 9 (0-indexed)
        try:
            accept_rate = float(row[9]) if row[9] else 0.5
        except (ValueError, TypeError):
            accept_rate = 0.5

        category = str(row[13]) if row[13] else "Algorithms"

        problems.append(ProblemRecord(
            problem_id=f"lc-{problem_id}",
            title=title,
            difficulty=difficulty,
            topics=topics,
            acceptance_rate=accept_rate,
            category=category,
        ))

    logger.info("Loaded %d problems from Excel.", len(problems))
    return problems


# ── Problem Content Dataset (for encoder pre-training) ────────────────────────

class ProblemContentDataset(Dataset):
    """
    Dataset for pre-training the problem encoder.

    Each sample is a problem with its text, topics, and difficulty.
    Used for:
        - Masked language modelling (optional)
        - Contrastive learning between similar problems
    """

    def __init__(
        self,
        problems: List[ProblemRecord],
        tokenizer: SimpleTokenizer,
        max_len: int = 64,
        max_topics: int = MAX_TOPICS,
    ):
        self.problems = problems
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.max_topics = max_topics

    def __len__(self) -> int:
        return len(self.problems)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        p = self.problems[idx]
        text = f"{p.title} {' '.join(p.topics)}"

        token_ids = self.tokenizer.encode(text, max_length=self.max_len)
        topic_ids = _encode_topics(p.topics, self.max_topics)
        diff_id = DIFF_MAP.get(p.difficulty, 1)
        cluster = _topic_cluster_label(p.topics)

        return {
            "token_ids": torch.tensor(token_ids, dtype=torch.long),
            "topic_ids": torch.tensor(topic_ids, dtype=torch.long),
            "difficulty_id": torch.tensor(diff_id, dtype=torch.long),
            "cluster_label": torch.tensor(cluster, dtype=torch.long),
            "problem_id": p.problem_id,
        }


# ── Interaction Dataset (for recommendation training) ─────────────────────────

class InteractionSample:
    """A single user–problem interaction training sample."""

    def __init__(
        self,
        user_id: int,
        problem_id: str,
        problem_embedding: Optional[torch.Tensor],
        user_skill_vec: np.ndarray,
        history_embeddings: List[torch.Tensor],
        history_difficulties: List[int],
        was_solved: bool,
        was_helpful: Optional[bool],
        difficulty_felt: Optional[str],
        days_ago: float = 0.0,
    ):
        self.user_id = user_id
        self.problem_id = problem_id
        self.problem_embedding = problem_embedding
        self.user_skill_vec = user_skill_vec
        self.history_embeddings = history_embeddings
        self.history_difficulties = history_difficulties
        self.was_solved = was_solved
        self.was_helpful = was_helpful
        self.difficulty_felt = difficulty_felt
        self.days_ago = days_ago


class InteractionDataset(Dataset):
    """
    Dataset of user–problem interactions for training the recommender.

    Samples come from the SuggestionFeedback table in the database.
    Falls back to synthetic data generation if the DB is empty.
    """

    def __init__(
        self,
        samples: List[InteractionSample],
        embed_dim: int = 64,
        max_history: int = 32,
    ):
        self.samples = samples
        self.embed_dim = embed_dim
        self.max_history = max_history

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        s = self.samples[idx]

        # Problem embedding (use zeros if not yet computed)
        if s.problem_embedding is not None:
            prob_emb = s.problem_embedding
        else:
            prob_emb = torch.zeros(self.embed_dim)

        # History: pad/truncate to max_history
        hist = s.history_embeddings[-self.max_history :]
        hist_diffs = s.history_difficulties[-self.max_history :]

        n = len(hist)
        if n > 0:
            hist_tensor = torch.stack(hist)  # (n, embed_dim)
        else:
            hist_tensor = torch.zeros(1, self.embed_dim)
            hist_diffs = [1]
            n = 1

        # Pad to max_history
        pad_len = self.max_history - n
        if pad_len > 0:
            pad = torch.zeros(pad_len, self.embed_dim)
            hist_tensor = torch.cat([hist_tensor, pad], dim=0)
            hist_diffs = hist_diffs + [0] * pad_len

        padding_mask = torch.tensor(
            [False] * n + [True] * (self.max_history - n), dtype=torch.bool
        )

        # Skill vector
        skill_vec = torch.tensor(s.user_skill_vec, dtype=torch.float32)

        # Labels
        solve_label = torch.tensor(float(s.was_solved), dtype=torch.float32)
        helpful_label = torch.tensor(
            float(s.was_helpful) if s.was_helpful is not None else 0.5,
            dtype=torch.float32,
        )
        helpful_mask = torch.tensor(s.was_helpful is not None, dtype=torch.bool)

        diff_felt = DIFF_FELT_MAP.get(s.difficulty_felt or "just_right", 1)
        diff_label = torch.tensor(diff_felt, dtype=torch.long)
        diff_mask = torch.tensor(s.difficulty_felt is not None, dtype=torch.bool)

        return {
            "problem_embedding": prob_emb,
            "history_embeddings": hist_tensor,
            "history_difficulties": torch.tensor(hist_diffs, dtype=torch.long),
            "padding_mask": padding_mask,
            "skill_vec": skill_vec,
            "solve_label": solve_label,
            "helpful_label": helpful_label,
            "helpful_mask": helpful_mask,
            "difficulty_label": diff_label,
            "difficulty_mask": diff_mask,
        }


# ── Synthetic data generator (for cold-start / testing) ───────────────────────

def generate_synthetic_interactions(
    problems: List[ProblemRecord],
    n_users: int = 200,
    interactions_per_user: int = 50,
    embed_dim: int = 64,
    seed: int = 42,
) -> List[InteractionSample]:
    """
    Generate synthetic user–problem interactions for initial training.

    Simulates realistic user behaviour:
        - Beginners solve mostly easy problems
        - Advanced users solve harder problems
        - Users have topic preferences
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    samples = []
    skill_levels = ["beginner", "intermediate", "advanced"]

    for user_id in range(n_users):
        skill = rng.choice(skill_levels)
        # Topic preference: each user prefers 2-3 topics
        preferred_topics = rng.sample(list(TagEmbedding.TOPIC2ID.keys()), k=3)

        # Build history
        history_embeddings = []
        history_difficulties = []
        history_problems = rng.sample(problems, k=min(interactions_per_user, len(problems)))

        for p in history_problems:
            # Simulate solve probability based on skill and difficulty
            diff_id = DIFF_MAP.get(p.difficulty, 1)
            if skill == "beginner":
                solve_prob = [0.8, 0.4, 0.1][diff_id]
            elif skill == "intermediate":
                solve_prob = [0.95, 0.7, 0.3][diff_id]
            else:
                solve_prob = [0.99, 0.9, 0.6][diff_id]

            was_solved = rng.random() < solve_prob
            was_helpful = rng.random() < (0.7 if was_solved else 0.3)

            # Difficulty felt (random.choices supports weights; rng is random.Random)
            if diff_id == 0:
                felt = random.choices(["too_easy", "just_right"], weights=[0.6, 0.4], k=1)[0]
            elif diff_id == 1:
                felt = random.choices(["too_easy", "just_right", "too_hard"], weights=[0.2, 0.6, 0.2], k=1)[0]
            else:
                felt = random.choices(["just_right", "too_hard"], weights=[0.3, 0.7], k=1)[0]

            # Fake problem embedding (in real training, use ProblemBankEncoder)
            prob_emb = torch.randn(embed_dim) * 0.1
            prob_emb = torch.nn.functional.normalize(prob_emb, dim=0)

            history_embeddings.append(prob_emb)
            history_difficulties.append(diff_id)

            # Skill vector (simplified)
            skill_vec = np.zeros(44)  # 40 topics + 4 difficulty features
            for t in preferred_topics:
                idx = TagEmbedding.TOPIC2ID.get(t, 0)
                if idx < 40:  # only set if within topic range
                    skill_vec[idx] = rng.uniform(0.3, 1.0)

            if skill == "beginner":
                skill_vec[40:44] = [0.7, 0.2, 0.05, 0.1]
            elif skill == "intermediate":
                skill_vec[40:44] = [0.3, 0.5, 0.15, 0.3]
            else:
                skill_vec[40:44] = [0.1, 0.4, 0.4, 0.5]

            samples.append(InteractionSample(
                user_id=user_id,
                problem_id=p.problem_id,
                problem_embedding=prob_emb,
                user_skill_vec=skill_vec,
                history_embeddings=history_embeddings[:-1],  # exclude current
                history_difficulties=history_difficulties[:-1],
                was_solved=was_solved,
                was_helpful=was_helpful,
                difficulty_felt=felt,
                days_ago=rng.uniform(0, 90),
            ))

    logger.info("Generated %d synthetic interaction samples.", len(samples))
    return samples


# ── DB Interaction Loader ──────────────────────────────────────────────────────

def load_interactions_from_db(
    db,
    problem_bank_encoder,
    embed_dim: int = 64,
    max_history: int = 32,
) -> List[InteractionSample]:
    """
    Load real interaction data from the SuggestionFeedback table.

    Args:
        db: SQLAlchemy session
        problem_bank_encoder: ProblemBankEncoder with cached embeddings
        embed_dim: embedding dimension
        max_history: max history length per user

    Returns:
        list of InteractionSample
    """
    from shared.models import SuggestionFeedback, ProblemStats, PlatformAccount, Analytics
    from services.suggestions.model import SkillVector, UserProfile
    import math

    feedbacks = db.query(SuggestionFeedback).order_by(
        SuggestionFeedback.user_id, SuggestionFeedback.created_at
    ).all()

    if not feedbacks:
        logger.warning("No feedback data in DB. Using synthetic data.")
        return []

    # Group by user
    user_feedbacks: Dict[int, List] = {}
    for fb in feedbacks:
        user_feedbacks.setdefault(fb.user_id, []).append(fb)

    samples = []
    now = datetime.utcnow()

    for user_id, fbs in user_feedbacks.items():
        # Build history from solved problems
        accounts = db.query(PlatformAccount).filter(
            PlatformAccount.user_id == user_id
        ).all()
        account_ids = [a.id for a in accounts]

        solved = db.query(ProblemStats).filter(
            ProblemStats.platform_account_id.in_(account_ids),
            ProblemStats.is_solved == True,
        ).order_by(ProblemStats.solved_at).all()

        history_embeddings = []
        history_difficulties = []
        for ps in solved[-max_history:]:
            emb = problem_bank_encoder.get_embedding(f"lc-{ps.problem_id}")
            if emb is None:
                emb = torch.zeros(embed_dim)
            history_embeddings.append(emb)
            history_difficulties.append(DIFF_MAP.get(
                (ps.difficulty or "medium").lower(), 1
            ))

        # Build skill vector
        analytics = db.query(Analytics).filter(Analytics.user_id == user_id).first()
        topic_counts: Dict[str, int] = {}
        for ps in solved:
            if ps.topics:
                for t in ps.topics:
                    key = t.lower().replace(" ", "-")
                    topic_counts[key] = topic_counts.get(key, 0) + 1

        profile = UserProfile(
            user_id=user_id,
            total_solved=analytics.total_problems_solved if analytics else len(solved),
            easy_solved=analytics.easy_solved if analytics else 0,
            medium_solved=analytics.medium_solved if analytics else 0,
            hard_solved=analytics.hard_solved if analytics else 0,
            topics=topic_counts,
            platforms=[a.platform_name for a in accounts],
            streak=analytics.current_streak if analytics else 0,
            recent_topics=[],
        )
        skill_vec = SkillVector.encode(profile)

        for fb in fbs:
            days_ago = (now - fb.created_at).total_seconds() / 86400

            prob_emb = problem_bank_encoder.get_embedding(fb.problem_id)
            if prob_emb is None:
                prob_emb = torch.zeros(embed_dim)

            samples.append(InteractionSample(
                user_id=user_id,
                problem_id=fb.problem_id,
                problem_embedding=prob_emb,
                user_skill_vec=skill_vec,
                history_embeddings=list(history_embeddings),
                history_difficulties=list(history_difficulties),
                was_solved=bool(fb.was_solved) if fb.was_solved is not None else False,
                was_helpful=fb.was_helpful,
                difficulty_felt=fb.difficulty_felt,
                days_ago=days_ago,
            ))

    logger.info("Loaded %d interaction samples from DB.", len(samples))
    return samples
