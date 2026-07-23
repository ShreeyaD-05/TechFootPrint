"""
Transformer module public API.

Import from here to avoid deep path dependencies.
"""

from services.transformer.tokenizer import BPETokenizer, SimpleTokenizer, PAD_ID, UNK_ID, CLS_ID, SEP_ID
from services.transformer.embeddings import (
    TokenEmbedding,
    SinusoidalPositionalEncoding,
    LearnablePositionalEncoding,
    TagEmbedding,
    ProblemInputEmbedding,
)
from services.transformer.attention import (
    scaled_dot_product_attention,
    MultiHeadAttention,
    FeedForwardNetwork,
    TransformerEncoderLayer,
)
from services.transformer.encoder import TransformerEncoder, ProblemEncoder

__all__ = [
    "BPETokenizer",
    "SimpleTokenizer",
    "PAD_ID",
    "UNK_ID",
    "CLS_ID",
    "SEP_ID",
    "TokenEmbedding",
    "SinusoidalPositionalEncoding",
    "LearnablePositionalEncoding",
    "TagEmbedding",
    "ProblemInputEmbedding",
    "scaled_dot_product_attention",
    "MultiHeadAttention",
    "FeedForwardNetwork",
    "TransformerEncoderLayer",
    "TransformerEncoder",
    "ProblemEncoder",
]
