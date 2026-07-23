"""
Transformer Encoder — stacks N TransformerEncoderLayers.

Input:  token IDs + topic tags + difficulty
Output: fixed-size problem embedding (CLS token representation)

Architecture:
  ProblemInputEmbedding
      ↓
  N × TransformerEncoderLayer
      ↓
  LayerNorm
      ↓
  CLS token → problem embedding (d_model,)
"""

import torch
import torch.nn as nn
from typing import Optional, List, Tuple, Dict

from services.transformer.embeddings import ProblemInputEmbedding, TagEmbedding
from services.transformer.attention import TransformerEncoderLayer


class TransformerEncoder(nn.Module):
    """
    Mini Transformer encoder for problem content understanding.

    Hyperparameters (defaults are lightweight for CPU/small GPU):
        vocab_size:  tokenizer vocabulary size
        d_model:     embedding dimension (128 or 256)
        num_heads:   attention heads (4 or 8)
        num_layers:  encoder depth (2–4)
        d_ff:        feed-forward inner dim (4 * d_model)
        max_len:     max token sequence length
        dropout:     dropout rate
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        num_heads: int = 4,
        num_layers: int = 3,
        d_ff: int = 512,
        max_len: int = 128,
        dropout: float = 0.1,
        use_learnable_pos: bool = False,
    ):
        super().__init__()
        self.d_model = d_model
        self.num_layers = num_layers

        # Input embedding (token + positional + tag)
        self.input_embedding = ProblemInputEmbedding(
            vocab_size=vocab_size,
            d_model=d_model,
            max_len=max_len,
            dropout=dropout,
            use_learnable_pos=use_learnable_pos,
        )

        # Stack of encoder layers
        self.layers = nn.ModuleList([
            TransformerEncoderLayer(
                d_model=d_model,
                num_heads=num_heads,
                d_ff=d_ff,
                dropout=dropout,
            )
            for _ in range(num_layers)
        ])

        # Final layer norm
        self.norm = nn.LayerNorm(d_model)

        # Store attention weights from all layers for interpretability
        self._all_attn_weights: List[torch.Tensor] = []

    def forward(
        self,
        token_ids: torch.Tensor,       # (batch, seq_len)
        topic_ids: torch.Tensor,       # (batch, max_topics)
        difficulty_ids: torch.Tensor,  # (batch,)
        return_all_hidden: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            token_ids:       (batch, seq_len) — padded token IDs
            topic_ids:       (batch, max_topics) — padded topic indices
            difficulty_ids:  (batch,) — difficulty 0/1/2
            return_all_hidden: if True, also return all layer outputs

        Returns:
            cls_embedding: (batch, d_model) — [CLS] token representation
            sequence_out:  (batch, seq_len, d_model) — full sequence output
        """
        # Build padding mask: True where token_id == 0 (PAD)
        padding_mask = (token_ids == 0)  # (batch, seq_len)

        # Embed
        x = self.input_embedding(token_ids, topic_ids, difficulty_ids)

        # Pass through encoder layers
        self._all_attn_weights = []
        all_hidden = []

        for layer in self.layers:
            x, attn_w = layer(x, src_key_padding_mask=padding_mask)
            self._all_attn_weights.append(attn_w)
            if return_all_hidden:
                all_hidden.append(x)

        x = self.norm(x)

        # CLS token is at position 0
        cls_embedding = x[:, 0, :]  # (batch, d_model)

        return cls_embedding, x

    def get_attention_maps(self) -> List[torch.Tensor]:
        """
        Return attention weight tensors from all layers.
        Shape per layer: (batch, heads, seq, seq)
        Useful for attention visualisation.
        """
        return self._all_attn_weights

    def get_token_importance(self, layer_idx: int = -1) -> torch.Tensor:
        """
        Compute per-token importance by averaging attention weights
        from the [CLS] token across all heads in a given layer.

        Args:
            layer_idx: which layer to use (-1 = last)
        Returns:
            (batch, seq_len) importance scores
        """
        if not self._all_attn_weights:
            raise RuntimeError("No attention weights stored. Run forward() first.")

        attn = self._all_attn_weights[layer_idx]  # (batch, heads, seq, seq)
        # Average over heads, take CLS row (position 0)
        cls_attn = attn.mean(dim=1)[:, 0, :]  # (batch, seq)
        return cls_attn


class ProblemEncoder(nn.Module):
    """
    Full problem encoder: Transformer + projection head.

    Adds a 2-layer MLP projection on top of the CLS embedding to produce
    a normalised problem embedding suitable for similarity computation.

    Output embedding is L2-normalised for cosine similarity.
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        embed_dim: int = 64,
        num_heads: int = 4,
        num_layers: int = 3,
        d_ff: int = 512,
        max_len: int = 128,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.transformer = TransformerEncoder(
            vocab_size=vocab_size,
            d_model=d_model,
            num_heads=num_heads,
            num_layers=num_layers,
            d_ff=d_ff,
            max_len=max_len,
            dropout=dropout,
        )

        # Projection head: d_model → embed_dim
        self.projection = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, embed_dim),
        )

        for layer in self.projection:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)

        self.embed_dim = embed_dim

    def forward(
        self,
        token_ids: torch.Tensor,
        topic_ids: torch.Tensor,
        difficulty_ids: torch.Tensor,
        normalize: bool = True,
    ) -> torch.Tensor:
        """
        Args:
            token_ids:      (batch, seq_len)
            topic_ids:      (batch, max_topics)
            difficulty_ids: (batch,)
            normalize:      L2-normalise output for cosine similarity

        Returns:
            (batch, embed_dim) problem embedding
        """
        cls_emb, _ = self.transformer(token_ids, topic_ids, difficulty_ids)
        proj = self.projection(cls_emb)  # (batch, embed_dim)

        if normalize:
            proj = nn.functional.normalize(proj, p=2, dim=-1)

        return proj

    def get_attention_maps(self) -> List[torch.Tensor]:
        return self.transformer.get_attention_maps()

    def get_token_importance(self, layer_idx: int = -1) -> torch.Tensor:
        return self.transformer.get_token_importance(layer_idx)
