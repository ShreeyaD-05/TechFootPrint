"""
Deep Recommendation Model — combines user and problem embeddings.

Architecture:
    user_embedding (embed_dim)
    problem_embedding (embed_dim)
        ↓
    Interaction layer (element-wise product + concat)
        ↓
    3-layer MLP with residual connections
        ↓
    Multi-task output heads:
        p_solve      — probability user solves this problem
        p_helpful    — probability user finds it helpful
        p_difficulty — predicted difficulty match (3-class)

Exploration:
    Epsilon-greedy and UCB strategies for recommendation diversity.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional, List
import numpy as np


class InteractionLayer(nn.Module):
    """
    Combines user and problem embeddings via:
        1. Element-wise product (captures feature interactions)
        2. Concatenation (preserves individual signals)
        3. Difference (captures gap/mismatch)

    Output: (batch, 3 * embed_dim)
    """

    def __init__(self, embed_dim: int):
        super().__init__()
        self.embed_dim = embed_dim

    def forward(
        self,
        user_emb: torch.Tensor,    # (batch, embed_dim)
        problem_emb: torch.Tensor, # (batch, embed_dim)
    ) -> torch.Tensor:
        product = user_emb * problem_emb                    # element-wise product
        diff = torch.abs(user_emb - problem_emb)            # absolute difference
        concat = torch.cat([user_emb, problem_emb, product, diff], dim=-1)
        return concat  # (batch, 4 * embed_dim)


class ResidualBlock(nn.Module):
    """
    MLP residual block: Linear → GELU → Dropout → Linear + skip connection.
    """

    def __init__(self, dim: int, dropout: float = 0.1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(dim, dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
        )
        self.norm = nn.LayerNorm(dim)
        for layer in self.block:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.norm(x + self.block(x))


class RecommenderModel(nn.Module):
    """
    Multi-task deep recommendation model.

    Predicts three signals simultaneously:
        p_solve:      P(user solves this problem)       — binary
        p_helpful:    P(user finds it helpful)          — binary
        p_difficulty: P(difficulty match)               — 3-class (too_easy/just_right/too_hard)

    These are trained jointly with a weighted combined loss.
    """

    def __init__(
        self,
        embed_dim: int = 64,
        hidden_dim: int = 256,
        num_residual_blocks: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.embed_dim = embed_dim

        # Interaction layer: 4 * embed_dim input
        self.interaction = InteractionLayer(embed_dim)
        interaction_dim = 4 * embed_dim

        # Input projection
        self.input_proj = nn.Sequential(
            nn.Linear(interaction_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        nn.init.xavier_uniform_(self.input_proj[0].weight)

        # Residual blocks
        self.residual_blocks = nn.ModuleList([
            ResidualBlock(hidden_dim, dropout)
            for _ in range(num_residual_blocks)
        ])

        # ── Multi-task output heads ────────────────────────────────────────────

        # Head 1: P(solve) — binary classification
        self.solve_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.GELU(),
            nn.Linear(64, 1),
        )

        # Head 2: P(helpful) — binary classification
        self.helpful_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.GELU(),
            nn.Linear(64, 1),
        )

        # Head 3: difficulty match — 3-class (too_easy=0, just_right=1, too_hard=2)
        self.difficulty_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.GELU(),
            nn.Linear(64, 3),
        )

        for head in [self.solve_head, self.helpful_head, self.difficulty_head]:
            for layer in head:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    nn.init.zeros_(layer.bias)

        # UCB exploration: per-problem visit counts and reward sums
        # These are maintained externally (see ExplorationStrategy)

    def forward(
        self,
        user_emb: torch.Tensor,    # (batch, embed_dim)
        problem_emb: torch.Tensor, # (batch, embed_dim)
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            user_emb:    (batch, embed_dim) — L2-normalised user embedding
            problem_emb: (batch, embed_dim) — L2-normalised problem embedding

        Returns:
            dict with keys:
                p_solve:      (batch, 1) — sigmoid probability
                p_helpful:    (batch, 1) — sigmoid probability
                p_difficulty: (batch, 3) — softmax logits
                hidden:       (batch, hidden_dim) — shared representation
        """
        # Interaction
        interaction = self.interaction(user_emb, problem_emb)

        # Shared representation
        h = self.input_proj(interaction)
        for block in self.residual_blocks:
            h = block(h)

        # Multi-task heads
        p_solve = torch.sigmoid(self.solve_head(h))
        p_helpful = torch.sigmoid(self.helpful_head(h))
        p_difficulty = self.difficulty_head(h)  # raw logits for CE loss

        return {
            "p_solve": p_solve,
            "p_helpful": p_helpful,
            "p_difficulty": p_difficulty,
            "hidden": h,
        }

    def score(
        self,
        user_emb: torch.Tensor,
        problem_emb: torch.Tensor,
        weights: Tuple[float, float, float] = (0.5, 0.3, 0.2),
    ) -> torch.Tensor:
        """
        Compute a single composite recommendation score.

        score = w_solve * p_solve + w_helpful * p_helpful + w_diff * p_just_right

        Args:
            weights: (w_solve, w_helpful, w_difficulty)
        Returns:
            (batch,) score in [0, 1]
        """
        out = self.forward(user_emb, problem_emb)
        p_just_right = F.softmax(out["p_difficulty"], dim=-1)[:, 1]  # class 1 = just_right

        score = (
            weights[0] * out["p_solve"].squeeze(-1)
            + weights[1] * out["p_helpful"].squeeze(-1)
            + weights[2] * p_just_right
        )
        return score


# ── Exploration Strategies ─────────────────────────────────────────────────────

class ExplorationStrategy:
    """
    Balances exploitation (recommend best-scoring problems) with
    exploration (try less-seen problems to gather more signal).

    Supports:
        - Epsilon-greedy: with probability ε, pick a random problem
        - UCB (Upper Confidence Bound): score + c * sqrt(log(N) / n_i)
    """

    def __init__(
        self,
        strategy: str = "epsilon_greedy",
        epsilon: float = 0.15,
        ucb_c: float = 1.0,
    ):
        assert strategy in ("epsilon_greedy", "ucb", "greedy")
        self.strategy = strategy
        self.epsilon = epsilon
        self.ucb_c = ucb_c

        # Per-problem statistics (problem_id → count, reward_sum)
        self._counts: Dict[str, int] = {}
        self._rewards: Dict[str, float] = {}
        self._total_pulls: int = 0

    def select(
        self,
        problem_ids: List[str],
        scores: np.ndarray,
        n: int = 10,
    ) -> List[int]:
        """
        Select `n` problem indices from `problem_ids` using the exploration strategy.

        Args:
            problem_ids: list of candidate problem IDs
            scores:      (len(problem_ids),) numpy array of model scores
            n:           number to select

        Returns:
            list of selected indices into problem_ids
        """
        if self.strategy == "greedy":
            return self._greedy(scores, n)
        elif self.strategy == "epsilon_greedy":
            return self._epsilon_greedy(problem_ids, scores, n)
        else:
            return self._ucb(problem_ids, scores, n)

    def _greedy(self, scores: np.ndarray, n: int) -> List[int]:
        return list(np.argsort(scores)[::-1][:n])

    def _epsilon_greedy(
        self, problem_ids: List[str], scores: np.ndarray, n: int
    ) -> List[int]:
        selected = []
        remaining = list(range(len(problem_ids)))

        for _ in range(min(n, len(remaining))):
            if np.random.random() < self.epsilon:
                # Explore: random pick
                idx = np.random.choice(remaining)
            else:
                # Exploit: best score among remaining
                remaining_scores = [(i, scores[i]) for i in remaining]
                idx = max(remaining_scores, key=lambda x: x[1])[0]

            selected.append(idx)
            remaining.remove(idx)

        return selected

    def _ucb(
        self, problem_ids: List[str], scores: np.ndarray, n: int
    ) -> List[int]:
        """UCB1: score + c * sqrt(log(N+1) / (n_i + 1))"""
        N = self._total_pulls + 1
        ucb_scores = []

        for i, pid in enumerate(problem_ids):
            n_i = self._counts.get(pid, 0)
            bonus = self.ucb_c * math.sqrt(math.log(N) / (n_i + 1))
            ucb_scores.append(scores[i] + bonus)

        ucb_arr = np.array(ucb_scores)
        return list(np.argsort(ucb_arr)[::-1][:n])

    def update(self, problem_id: str, reward: float):
        """
        Update statistics after observing a reward (e.g., user solved = 1.0).

        Args:
            problem_id: the problem that was recommended
            reward:     observed reward (0.0 – 1.0)
        """
        self._counts[problem_id] = self._counts.get(problem_id, 0) + 1
        self._rewards[problem_id] = self._rewards.get(problem_id, 0.0) + reward
        self._total_pulls += 1

    def get_stats(self, problem_id: str) -> Dict:
        n = self._counts.get(problem_id, 0)
        r = self._rewards.get(problem_id, 0.0)
        return {
            "pulls": n,
            "total_reward": r,
            "avg_reward": r / n if n > 0 else 0.0,
        }
