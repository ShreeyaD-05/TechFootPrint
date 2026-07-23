"""
Problem Encoder — wraps the Transformer encoder with a problem bank cache.

Responsibilities:
  - Batch-encode problems from the dataset
  - Cache embeddings to avoid re-encoding on every request
  - Provide tag-only fast encoding (no text) for cold-start
"""

import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

from services.transformer.encoder import ProblemEncoder as TransformerProblemEncoder
from services.transformer.embeddings import TagEmbedding
from services.transformer.tokenizer import SimpleTokenizer

logger = logging.getLogger(__name__)


class ProblemBankEncoder:
    """
    Manages problem embeddings for the full problem bank.

    Usage:
        encoder = ProblemBankEncoder(model, tokenizer)
        encoder.build_cache(problems)          # one-time
        emb = encoder.get_embedding("lc-1")   # O(1) lookup
    """

    def __init__(
        self,
        model: TransformerProblemEncoder,
        tokenizer: SimpleTokenizer,
        device: torch.device = torch.device("cpu"),
        max_topics: int = 8,
        max_len: int = 64,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.max_topics = max_topics
        self.max_len = max_len

        # problem_id → embedding tensor (embed_dim,)
        self._cache: Dict[str, torch.Tensor] = {}
        # problem_id → metadata
        self._meta: Dict[str, Dict] = {}

    # ── Encoding helpers ───────────────────────────────────────────────────────

    def _encode_topics(self, topics: List[str]) -> List[int]:
        """Convert topic names to padded index list."""
        ids = []
        for t in topics:
            key = t.lower().replace(" ", "-")
            idx = TagEmbedding.TOPIC2ID.get(key, TagEmbedding.NUM_TOPICS)
            ids.append(idx)
        # Pad / truncate
        ids = ids[: self.max_topics]
        ids += [TagEmbedding.NUM_TOPICS] * (self.max_topics - len(ids))
        return ids

    def _encode_difficulty(self, difficulty: str) -> int:
        return {"easy": 0, "medium": 1, "hard": 2}.get(
            difficulty.lower() if difficulty else "medium", 1
        )

    def _problem_to_text(self, problem: Dict) -> str:
        """Concatenate title + topics into a single text string."""
        title = problem.get("title", "")
        topics = " ".join(problem.get("topics", []))
        desc = problem.get("description", "")[:200]  # truncate long descriptions
        return f"{title} {topics} {desc}".strip()

    def _batch_encode(self, problems: List[Dict]) -> torch.Tensor:
        """
        Encode a batch of problem dicts.

        Returns:
            (batch, embed_dim) tensor
        """
        token_ids_list = []
        topic_ids_list = []
        diff_ids_list = []

        for p in problems:
            text = self._problem_to_text(p)
            token_ids_list.append(self.tokenizer.encode(text, max_length=self.max_len))
            topic_ids_list.append(self._encode_topics(p.get("topics", [])))
            diff_ids_list.append(self._encode_difficulty(p.get("difficulty", "medium")))

        token_ids = torch.tensor(token_ids_list, dtype=torch.long, device=self.device)
        topic_ids = torch.tensor(topic_ids_list, dtype=torch.long, device=self.device)
        diff_ids = torch.tensor(diff_ids_list, dtype=torch.long, device=self.device)

        self.model.eval()
        with torch.no_grad():
            embeddings = self.model(token_ids, topic_ids, diff_ids, normalize=True)

        return embeddings  # (batch, embed_dim)

    # ── Cache management ───────────────────────────────────────────────────────

    def build_cache(self, problems: List[Dict], batch_size: int = 64):
        """
        Pre-compute and cache embeddings for all problems.

        Args:
            problems: list of dicts with keys: id, title, difficulty, topics, [description]
            batch_size: encoding batch size
        """
        logger.info("Building problem embedding cache for %d problems...", len(problems))

        for i in range(0, len(problems), batch_size):
            batch = problems[i : i + batch_size]
            embeddings = self._batch_encode(batch)

            for j, p in enumerate(batch):
                pid = p.get("id") or p.get("problem_id")
                self._cache[pid] = embeddings[j].cpu()
                self._meta[pid] = {
                    "title": p.get("title", ""),
                    "difficulty": p.get("difficulty", "medium"),
                    "topics": p.get("topics", []),
                    "platform": p.get("platform", "leetcode"),
                }

        logger.info("Cache built: %d problems encoded.", len(self._cache))

    def get_embedding(self, problem_id: str) -> Optional[torch.Tensor]:
        """Return cached embedding for a problem ID, or None if not cached."""
        return self._cache.get(problem_id)

    def get_all_embeddings(self) -> Tuple[List[str], torch.Tensor]:
        """
        Return all cached embeddings as a matrix.

        Returns:
            ids:        list of problem IDs (length N)
            embeddings: (N, embed_dim) tensor
        """
        ids = list(self._cache.keys())
        if not ids:
            return [], torch.empty(0)
        embeddings = torch.stack([self._cache[pid] for pid in ids])
        return ids, embeddings

    def encode_single(self, problem: Dict) -> torch.Tensor:
        """Encode a single problem dict on-the-fly (no caching)."""
        return self._batch_encode([problem])[0]

    def get_metadata(self, problem_id: str) -> Optional[Dict]:
        return self._meta.get(problem_id)

    def __len__(self) -> int:
        return len(self._cache)

    # ── Tag-only fast encoder (no text, for cold-start) ────────────────────────

    def encode_tag_only(self, topics: List[str], difficulty: str) -> torch.Tensor:
        """
        Fast encoding using only tags (no text tokenisation).
        Useful when description is unavailable.

        Returns:
            (embed_dim,) tensor
        """
        topic_ids = torch.tensor(
            [self._encode_topics(topics)], dtype=torch.long, device=self.device
        )
        diff_id = torch.tensor(
            [self._encode_difficulty(difficulty)], dtype=torch.long, device=self.device
        )

        # Use zero token IDs (just [PAD]) — tag embedding carries the signal
        token_ids = torch.zeros(1, self.max_len, dtype=torch.long, device=self.device)
        token_ids[0, 0] = 2  # [CLS]

        self.model.eval()
        with torch.no_grad():
            emb = self.model(token_ids, topic_ids, diff_id, normalize=True)

        return emb[0].cpu()
