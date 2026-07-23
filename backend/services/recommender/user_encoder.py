"""
User Encoder — learns a dense user representation from interaction history.

Two modes:
  1. AggregationEncoder  — weighted mean-pool of solved problem embeddings
                           (recency × difficulty × success weighting)
  2. SequentialEncoder   — Transformer over the user's problem-solving sequence
                           (captures temporal patterns)

Both output a (batch, embed_dim) user embedding.
"""

import math
import torch
import torch.nn as nn
from typing import List, Optional, Tuple

from services.transformer.attention import TransformerEncoderLayer


# ── Interaction record ─────────────────────────────────────────────────────────

class InteractionRecord:
    """
    Represents a single user–problem interaction.

    Attributes:
        problem_embedding: (embed_dim,) tensor — pre-computed problem embedding
        difficulty:        0=easy, 1=medium, 2=hard
        was_solved:        True/False
        was_helpful:       True/False/None
        days_ago:          how many days ago this was solved (for recency decay)
    """

    DIFFICULTY_WEIGHTS = {0: 1.0, 1: 2.5, 2: 5.0}

    def __init__(
        self,
        problem_embedding: torch.Tensor,
        difficulty: int = 1,
        was_solved: bool = True,
        was_helpful: Optional[bool] = None,
        days_ago: float = 0.0,
    ):
        self.problem_embedding = problem_embedding
        self.difficulty = difficulty
        self.was_solved = was_solved
        self.was_helpful = was_helpful
        self.days_ago = days_ago

    def compute_weight(self, recency_halflife: float = 30.0) -> float:
        """
        Composite interaction weight:
            recency_decay × difficulty_weight × success_bonus
        """
        # Exponential recency decay: halves every `recency_halflife` days
        recency = math.exp(-math.log(2) * self.days_ago / recency_halflife)

        # Difficulty weight
        diff_w = self.DIFFICULTY_WEIGHTS.get(self.difficulty, 1.0)

        # Success bonus: solved problems contribute more
        success = 1.2 if self.was_solved else 0.6

        # Helpfulness bonus
        helpful = 1.1 if self.was_helpful else (0.9 if self.was_helpful is False else 1.0)

        return recency * diff_w * success * helpful


# ── Aggregation Encoder ────────────────────────────────────────────────────────

class AggregationUserEncoder(nn.Module):
    """
    Weighted mean-pool of solved problem embeddings.

    Simple but effective: captures topic coverage and difficulty profile.
    No sequential structure — order doesn't matter.

    Architecture:
        weighted_mean(problem_embeddings) → MLP → user_embedding
    """

    def __init__(self, embed_dim: int, hidden_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.embed_dim = embed_dim

        # MLP to transform pooled embedding into user representation
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, embed_dim),
            nn.LayerNorm(embed_dim),
        )

        for layer in self.mlp:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)

    def forward(
        self,
        problem_embeddings: torch.Tensor,  # (batch, n_problems, embed_dim)
        weights: torch.Tensor,             # (batch, n_problems) — interaction weights
    ) -> torch.Tensor:
        """
        Args:
            problem_embeddings: (batch, n_problems, embed_dim)
            weights:            (batch, n_problems) — non-negative interaction weights

        Returns:
            user_embedding: (batch, embed_dim)
        """
        # Normalise weights to sum to 1
        w = weights / (weights.sum(dim=-1, keepdim=True).clamp(min=1e-8))
        w = w.unsqueeze(-1)  # (batch, n_problems, 1)

        # Weighted mean pool
        pooled = (problem_embeddings * w).sum(dim=1)  # (batch, embed_dim)

        return self.mlp(pooled)

    def encode_from_interactions(
        self,
        interactions: List[InteractionRecord],
        device: torch.device = torch.device("cpu"),
    ) -> torch.Tensor:
        """
        Convenience method: encode a single user from a list of interactions.

        Returns:
            (1, embed_dim) user embedding
        """
        if not interactions:
            return torch.zeros(1, self.embed_dim, device=device)

        embeds = torch.stack([r.problem_embedding for r in interactions]).to(device)
        weights = torch.tensor(
            [r.compute_weight() for r in interactions],
            dtype=torch.float32,
            device=device,
        )

        return self.forward(embeds.unsqueeze(0), weights.unsqueeze(0))


# ── Sequential Encoder ─────────────────────────────────────────────────────────

class SequentialUserEncoder(nn.Module):
    """
    Transformer over the user's problem-solving sequence.

    Captures temporal patterns: e.g., "user recently shifted from DP to Graphs".
    Uses a learnable [USER] token (analogous to [CLS]) as the output.

    Architecture:
        [USER] + sequence of problem embeddings
            ↓
        N × TransformerEncoderLayer
            ↓
        [USER] token → user embedding
    """

    USER_TOKEN_IDX = 0  # position 0 is the [USER] token

    def __init__(
        self,
        embed_dim: int,
        num_heads: int = 4,
        num_layers: int = 2,
        d_ff: int = 256,
        max_history: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.max_history = max_history

        # Learnable [USER] token
        self.user_token = nn.Parameter(torch.randn(1, 1, embed_dim) * 0.02)

        # Learnable positional encoding for history sequence
        self.pos_embedding = nn.Embedding(max_history + 1, embed_dim)
        nn.init.normal_(self.pos_embedding.weight, std=0.02)

        # Difficulty embedding (injected into each problem position)
        self.diff_embedding = nn.Embedding(3, embed_dim)

        # Input projection (problem embed → model dim)
        self.input_proj = nn.Linear(embed_dim, embed_dim)

        # Transformer layers
        self.layers = nn.ModuleList([
            TransformerEncoderLayer(
                d_model=embed_dim,
                num_heads=num_heads,
                d_ff=d_ff,
                dropout=dropout,
            )
            for _ in range(num_layers)
        ])

        self.norm = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        problem_embeddings: torch.Tensor,  # (batch, seq_len, embed_dim)
        difficulty_ids: torch.Tensor,      # (batch, seq_len) — 0/1/2
        padding_mask: Optional[torch.Tensor] = None,  # (batch, seq_len) True=pad
    ) -> torch.Tensor:
        """
        Args:
            problem_embeddings: (batch, seq_len, embed_dim) — chronological order
            difficulty_ids:     (batch, seq_len)
            padding_mask:       (batch, seq_len) — True = padding position

        Returns:
            user_embedding: (batch, embed_dim)
        """
        batch = problem_embeddings.size(0)
        seq_len = problem_embeddings.size(1)

        # Project problem embeddings
        x = self.input_proj(problem_embeddings)  # (batch, seq_len, embed_dim)

        # Add difficulty embeddings
        x = x + self.diff_embedding(difficulty_ids)

        # Add positional embeddings (offset by 1 for [USER] token)
        positions = torch.arange(1, seq_len + 1, device=x.device).unsqueeze(0)
        x = x + self.pos_embedding(positions)

        # Prepend [USER] token
        user_tok = self.user_token.expand(batch, -1, -1)  # (batch, 1, embed_dim)
        x = torch.cat([user_tok, x], dim=1)  # (batch, seq_len+1, embed_dim)

        # Extend padding mask to include [USER] token (never masked)
        if padding_mask is not None:
            user_mask = torch.zeros(batch, 1, dtype=torch.bool, device=x.device)
            padding_mask = torch.cat([user_mask, padding_mask], dim=1)

        # Pass through Transformer layers
        for layer in self.layers:
            x, _ = layer(x, src_key_padding_mask=padding_mask)

        x = self.norm(x)

        # Return [USER] token representation
        return x[:, 0, :]  # (batch, embed_dim)

    def encode_from_interactions(
        self,
        interactions: List[InteractionRecord],
        device: torch.device = torch.device("cpu"),
    ) -> torch.Tensor:
        """
        Convenience method: encode a single user from a list of interactions.
        Truncates to max_history most recent interactions.

        Returns:
            (1, embed_dim) user embedding
        """
        if not interactions:
            return torch.zeros(1, self.embed_dim, device=device)

        # Take most recent max_history interactions
        recent = interactions[-self.max_history :]

        embeds = torch.stack([r.problem_embedding for r in recent]).to(device)
        diffs = torch.tensor(
            [r.difficulty for r in recent], dtype=torch.long, device=device
        )

        return self.forward(
            embeds.unsqueeze(0),
            diffs.unsqueeze(0),
        )


# ── Skill Profile Encoder ──────────────────────────────────────────────────────

class SkillProfileEncoder(nn.Module):
    """
    Encodes the structured skill profile (topic counts, difficulty distribution)
    into a dense vector that can be fused with the interaction-based user embedding.

    Input: raw skill feature vector (same as legacy SkillVector)
    Output: (batch, embed_dim) skill embedding
    """

    NUM_TOPICS = 40
    FEATURE_DIM = NUM_TOPICS + 4  # topics + easy/medium/hard ratios + streak

    def __init__(self, embed_dim: int, dropout: float = 0.1):
        super().__init__()
        self.embed_dim = embed_dim

        self.encoder = nn.Sequential(
            nn.Linear(self.FEATURE_DIM, 128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, embed_dim),
            nn.LayerNorm(embed_dim),
        )

        for layer in self.encoder:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)

    def forward(self, skill_vec: torch.Tensor) -> torch.Tensor:
        """
        Args:
            skill_vec: (batch, FEATURE_DIM) float tensor
        Returns:
            (batch, embed_dim)
        """
        return self.encoder(skill_vec)


# ── Combined User Encoder ──────────────────────────────────────────────────────

class UserEncoder(nn.Module):
    """
    Full user encoder combining:
        1. SequentialUserEncoder (interaction history)
        2. SkillProfileEncoder (structured skill features)

    Fuses both via a gated mechanism:
        gate = sigmoid(W [seq_emb; skill_emb])
        user_emb = gate * seq_emb + (1 - gate) * skill_emb
    """

    def __init__(
        self,
        embed_dim: int,
        num_heads: int = 4,
        num_layers: int = 2,
        max_history: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.embed_dim = embed_dim

        self.seq_encoder = SequentialUserEncoder(
            embed_dim=embed_dim,
            num_heads=num_heads,
            num_layers=num_layers,
            max_history=max_history,
            dropout=dropout,
        )

        self.skill_encoder = SkillProfileEncoder(embed_dim, dropout)

        # Gating network
        self.gate = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim),
            nn.Sigmoid(),
        )
        nn.init.xavier_uniform_(self.gate[0].weight)
        nn.init.zeros_(self.gate[0].bias)

        # Final projection
        self.output_proj = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.LayerNorm(embed_dim),
        )

    def forward(
        self,
        problem_embeddings: torch.Tensor,  # (batch, seq_len, embed_dim)
        difficulty_ids: torch.Tensor,      # (batch, seq_len)
        skill_vec: torch.Tensor,           # (batch, FEATURE_DIM)
        padding_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Returns:
            user_embedding: (batch, embed_dim) — L2 normalised
        """
        seq_emb = self.seq_encoder(problem_embeddings, difficulty_ids, padding_mask)
        skill_emb = self.skill_encoder(skill_vec)

        # Gated fusion
        combined = torch.cat([seq_emb, skill_emb], dim=-1)
        gate = self.gate(combined)
        fused = gate * seq_emb + (1 - gate) * skill_emb

        out = self.output_proj(fused)
        return nn.functional.normalize(out, p=2, dim=-1)
