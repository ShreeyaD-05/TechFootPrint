"""
Embedding layers — implemented from scratch using PyTorch primitives.

Includes:
  - TokenEmbedding: learnable lookup table
  - PositionalEncoding: sinusoidal (fixed) or learnable
  - TagEmbedding: for discrete topic/difficulty tags
  - combined ProblemInputEmbedding
"""

import math
import torch
import torch.nn as nn
from typing import Optional


class TokenEmbedding(nn.Module):
    """
    Standard learnable token embedding.
    Maps integer token IDs → dense vectors of size `d_model`.
    Weights initialised with N(0, d_model^-0.5) following the original
    'Attention Is All You Need' paper.
    """

    def __init__(self, vocab_size: int, d_model: int, padding_idx: int = 0):
        super().__init__()
        self.d_model = d_model
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=padding_idx)
        # Scale init as in Vaswani et al.
        nn.init.normal_(self.embedding.weight, mean=0.0, std=d_model ** -0.5)
        # Zero out padding embedding
        with torch.no_grad():
            self.embedding.weight[padding_idx].fill_(0)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        Args:
            token_ids: (batch, seq_len) long tensor
        Returns:
            (batch, seq_len, d_model) float tensor, scaled by sqrt(d_model)
        """
        return self.embedding(token_ids) * math.sqrt(self.d_model)


class SinusoidalPositionalEncoding(nn.Module):
    """
    Fixed sinusoidal positional encoding from 'Attention Is All You Need'.

    PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

    This is NOT learned — it generalises to unseen sequence lengths.
    """

    def __init__(self, d_model: int, max_len: int = 512, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Build the encoding matrix once
        pe = torch.zeros(max_len, d_model)  # (max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)  # (max_len, 1)
        # Compute the division term in log-space for numerical stability
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float)
            * (-math.log(10000.0) / d_model)
        )  # (d_model/2,)

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        pe = pe.unsqueeze(0)  # (1, max_len, d_model) — broadcast over batch
        # Register as buffer so it moves with .to(device) but is not a parameter
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, d_model)
        Returns:
            (batch, seq_len, d_model) with positional encoding added
        """
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class LearnablePositionalEncoding(nn.Module):
    """
    Learnable positional encoding (used in BERT).
    Better for fixed-length inputs; less generalisable than sinusoidal.
    """

    def __init__(self, d_model: int, max_len: int = 512, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.pe = nn.Embedding(max_len, d_model)
        nn.init.normal_(self.pe.weight, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, d_model)
        Returns:
            (batch, seq_len, d_model)
        """
        seq_len = x.size(1)
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0)  # (1, seq_len)
        return self.dropout(x + self.pe(positions))


class TagEmbedding(nn.Module):
    """
    Embeds discrete topic tags and difficulty level.

    Topics are multi-hot: a problem can have multiple tags.
    We embed each tag separately and sum/mean-pool them.

    Difficulty is a single categorical label (easy=0, medium=1, hard=2).
    """

    TOPICS = [
        "array", "string", "hash-table", "dynamic-programming", "math",
        "sorting", "greedy", "depth-first-search", "binary-search", "database",
        "breadth-first-search", "tree", "matrix", "two-pointers", "bit-manipulation",
        "stack", "design", "graph", "simulation", "backtracking",
        "prefix-sum", "counting", "sliding-window", "linked-list", "union-find",
        "ordered-set", "monotonic-stack", "number-theory", "trie", "recursion",
        "divide-and-conquer", "heap", "binary-tree", "queue", "memoization",
        "geometry", "segment-tree", "topological-sort", "game-theory", "shortest-path",
        "number-theory", "combinatorics", "probability", "randomized", "interactive",
    ]
    TOPIC2ID = {t: i for i, t in enumerate(TOPICS)}
    NUM_TOPICS = len(TOPICS)
    NUM_DIFFICULTIES = 3  # easy, medium, hard

    def __init__(self, d_model: int):
        super().__init__()
        self.d_model = d_model
        # Each topic gets its own embedding vector
        self.topic_embedding = nn.Embedding(self.NUM_TOPICS + 1, d_model, padding_idx=self.NUM_TOPICS)
        # Difficulty embedding
        self.diff_embedding = nn.Embedding(self.NUM_DIFFICULTIES, d_model)
        # Projection to combine topic + difficulty
        self.proj = nn.Linear(d_model * 2, d_model)
        nn.init.xavier_uniform_(self.proj.weight)

    def encode_topics(self, topic_names: list) -> torch.Tensor:
        """
        Convert a list of topic name strings to a (d_model,) embedding vector.
        Returns a CPU tensor — move to device as needed.
        """
        ids = []
        for t in topic_names:
            key = t.lower().replace(" ", "-")
            ids.append(self.TOPIC2ID.get(key, self.NUM_TOPICS))  # unknown → padding

        if not ids:
            ids = [self.NUM_TOPICS]  # all-padding

        id_tensor = torch.tensor(ids, dtype=torch.long)
        embeds = self.topic_embedding(id_tensor)  # (n_topics, d_model)
        return embeds.mean(dim=0)  # (d_model,)

    def forward(
        self,
        topic_ids: torch.Tensor,   # (batch, max_topics) long, padded with NUM_TOPICS
        difficulty_ids: torch.Tensor,  # (batch,) long  0/1/2
    ) -> torch.Tensor:
        """
        Args:
            topic_ids: (batch, max_topics) — padded topic indices
            difficulty_ids: (batch,) — difficulty index
        Returns:
            (batch, d_model) tag embedding
        """
        # Mean-pool topic embeddings (ignoring padding)
        topic_embeds = self.topic_embedding(topic_ids)  # (batch, max_topics, d_model)
        # Mask padding
        mask = (topic_ids != self.NUM_TOPICS).float().unsqueeze(-1)  # (batch, max_topics, 1)
        topic_vec = (topic_embeds * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)  # (batch, d_model)

        diff_vec = self.diff_embedding(difficulty_ids)  # (batch, d_model)

        combined = torch.cat([topic_vec, diff_vec], dim=-1)  # (batch, 2*d_model)
        return self.proj(combined)  # (batch, d_model)


class ProblemInputEmbedding(nn.Module):
    """
    Full input embedding for a problem:
        token_embedding + positional_encoding + tag_embedding (added to [CLS])

    The tag embedding is added only to the [CLS] position so the Transformer
    can attend to both textual and structural features.
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int,
        max_len: int = 128,
        dropout: float = 0.1,
        use_learnable_pos: bool = False,
    ):
        super().__init__()
        self.token_emb = TokenEmbedding(vocab_size, d_model)
        if use_learnable_pos:
            self.pos_enc = LearnablePositionalEncoding(d_model, max_len, dropout)
        else:
            self.pos_enc = SinusoidalPositionalEncoding(d_model, max_len, dropout)
        self.tag_emb = TagEmbedding(d_model)
        self.layer_norm = nn.LayerNorm(d_model)

    def forward(
        self,
        token_ids: torch.Tensor,       # (batch, seq_len)
        topic_ids: torch.Tensor,       # (batch, max_topics)
        difficulty_ids: torch.Tensor,  # (batch,)
    ) -> torch.Tensor:
        """
        Returns:
            (batch, seq_len, d_model) embedding tensor
        """
        x = self.token_emb(token_ids)          # (batch, seq_len, d_model)
        x = self.pos_enc(x)                    # add positional encoding

        # Inject tag info into [CLS] token (position 0)
        tag_vec = self.tag_emb(topic_ids, difficulty_ids)  # (batch, d_model)
        x[:, 0, :] = x[:, 0, :] + tag_vec

        return self.layer_norm(x)
