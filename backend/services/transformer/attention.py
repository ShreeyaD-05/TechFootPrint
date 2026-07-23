"""
Multi-Head Self-Attention — implemented from scratch.

Implements:
  - Scaled Dot-Product Attention (with optional masking)
  - Multi-Head Attention (split heads, parallel attention, concat + project)
  - Attention weight extraction for interpretability

Reference: Vaswani et al., "Attention Is All You Need" (2017)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


def scaled_dot_product_attention(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    mask: Optional[torch.Tensor] = None,
    dropout: Optional[nn.Dropout] = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Compute scaled dot-product attention.

    Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V

    Args:
        query:  (batch, heads, seq_q, d_k)
        key:    (batch, heads, seq_k, d_k)
        value:  (batch, heads, seq_k, d_v)
        mask:   (batch, 1, 1, seq_k) or (batch, 1, seq_q, seq_k) — True = MASK OUT
        dropout: optional dropout module

    Returns:
        output:  (batch, heads, seq_q, d_v)
        weights: (batch, heads, seq_q, seq_k) — attention weights for visualisation
    """
    d_k = query.size(-1)
    # (batch, heads, seq_q, seq_k)
    scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(d_k)

    if mask is not None:
        # Fill masked positions with -inf so softmax → 0
        scores = scores.masked_fill(mask, float("-inf"))

    weights = F.softmax(scores, dim=-1)

    # Replace NaN (all-masked rows) with 0
    weights = torch.nan_to_num(weights, nan=0.0)

    if dropout is not None:
        weights = dropout(weights)

    output = torch.matmul(weights, value)
    return output, weights


class MultiHeadAttention(nn.Module):
    """
    Multi-Head Attention from scratch.

    Projects Q, K, V into `num_heads` subspaces, runs attention in parallel,
    then concatenates and projects back to d_model.

    d_k = d_v = d_model // num_heads
    """

    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % num_heads == 0, (
            f"d_model ({d_model}) must be divisible by num_heads ({num_heads})"
        )

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        # Linear projections for Q, K, V and output
        # We use a single matrix for all heads (more efficient than separate)
        self.W_q = nn.Linear(d_model, d_model, bias=False)
        self.W_k = nn.Linear(d_model, d_model, bias=False)
        self.W_v = nn.Linear(d_model, d_model, bias=False)
        self.W_o = nn.Linear(d_model, d_model, bias=False)

        # Initialise with Xavier uniform
        for layer in [self.W_q, self.W_k, self.W_v, self.W_o]:
            nn.init.xavier_uniform_(layer.weight)

        self.attn_dropout = nn.Dropout(p=dropout)

        # Store last attention weights for interpretability
        self._last_attn_weights: Optional[torch.Tensor] = None

    def _split_heads(self, x: torch.Tensor) -> torch.Tensor:
        """
        Reshape (batch, seq, d_model) → (batch, heads, seq, d_k)
        """
        batch, seq, _ = x.size()
        x = x.view(batch, seq, self.num_heads, self.d_k)
        return x.transpose(1, 2)  # (batch, heads, seq, d_k)

    def _merge_heads(self, x: torch.Tensor) -> torch.Tensor:
        """
        Reshape (batch, heads, seq, d_k) → (batch, seq, d_model)
        """
        batch, heads, seq, d_k = x.size()
        x = x.transpose(1, 2).contiguous()
        return x.view(batch, seq, heads * d_k)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            query: (batch, seq_q, d_model)
            key:   (batch, seq_k, d_model)
            value: (batch, seq_k, d_model)
            mask:  (batch, 1, 1, seq_k) boolean — True positions are masked

        Returns:
            output:  (batch, seq_q, d_model)
            weights: (batch, heads, seq_q, seq_k)
        """
        # Project
        Q = self._split_heads(self.W_q(query))  # (batch, heads, seq_q, d_k)
        K = self._split_heads(self.W_k(key))    # (batch, heads, seq_k, d_k)
        V = self._split_heads(self.W_v(value))  # (batch, heads, seq_k, d_k)

        # Attend
        attn_out, weights = scaled_dot_product_attention(
            Q, K, V, mask=mask, dropout=self.attn_dropout
        )

        # Store for visualisation
        self._last_attn_weights = weights.detach()

        # Merge heads and project
        merged = self._merge_heads(attn_out)   # (batch, seq_q, d_model)
        output = self.W_o(merged)              # (batch, seq_q, d_model)

        return output, weights

    def get_attention_weights(self) -> Optional[torch.Tensor]:
        """Return the last computed attention weights (for visualisation)."""
        return self._last_attn_weights


class FeedForwardNetwork(nn.Module):
    """
    Position-wise Feed-Forward Network.

    FFN(x) = max(0, x W_1 + b_1) W_2 + b_2

    The inner dimension is typically 4 * d_model.
    """

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(p=dropout)
        self.activation = nn.GELU()  # GELU slightly outperforms ReLU in practice

        nn.init.xavier_uniform_(self.linear1.weight)
        nn.init.xavier_uniform_(self.linear2.weight)
        nn.init.zeros_(self.linear1.bias)
        nn.init.zeros_(self.linear2.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq, d_model)
        Returns:
            (batch, seq, d_model)
        """
        return self.linear2(self.dropout(self.activation(self.linear1(x))))


class TransformerEncoderLayer(nn.Module):
    """
    Single Transformer encoder layer:
        x → LayerNorm → MultiHeadAttention → residual
          → LayerNorm → FFN → residual

    Uses Pre-LN (layer norm before sub-layer) for training stability.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int,
        d_ff: int,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.ffn = FeedForwardNetwork(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(p=dropout)

    def forward(
        self,
        x: torch.Tensor,
        src_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: (batch, seq, d_model)
            src_key_padding_mask: (batch, seq) bool — True = padding position

        Returns:
            x: (batch, seq, d_model)
            attn_weights: (batch, heads, seq, seq)
        """
        # Pre-LN self-attention with residual
        residual = x
        x_norm = self.norm1(x)

        # Expand mask for attention: (batch, 1, 1, seq)
        attn_mask = None
        if src_key_padding_mask is not None:
            attn_mask = src_key_padding_mask.unsqueeze(1).unsqueeze(2)

        attn_out, attn_weights = self.self_attn(x_norm, x_norm, x_norm, mask=attn_mask)
        x = residual + self.dropout(attn_out)

        # Pre-LN FFN with residual
        residual = x
        x = residual + self.dropout(self.ffn(self.norm2(x)))

        return x, attn_weights
