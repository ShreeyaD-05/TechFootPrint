"""
Tokenizer — character-level BPE-inspired subword tokenizer.

Built from scratch: no HuggingFace, no SentencePiece.
Supports:
  - Vocabulary building from a corpus
  - Encode / decode
  - Special tokens: [PAD], [UNK], [CLS], [SEP]
  - Save / load vocabulary
"""

import re
import json
import os
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional


# ── Special token constants ────────────────────────────────────────────────────
PAD_TOKEN = "[PAD]"
UNK_TOKEN = "[UNK]"
CLS_TOKEN = "[CLS]"
SEP_TOKEN = "[SEP]"
SPECIAL_TOKENS = [PAD_TOKEN, UNK_TOKEN, CLS_TOKEN, SEP_TOKEN]

PAD_ID = 0
UNK_ID = 1
CLS_ID = 2
SEP_ID = 3


def _basic_tokenize(text: str) -> List[str]:
    """
    Lowercase, strip punctuation, split on whitespace.
    Returns a list of word-level tokens.
    """
    text = text.lower()
    # Keep alphanumeric and hyphens (important for topic names like 'depth-first-search')
    text = re.sub(r"[^a-z0-9\-\s]", " ", text)
    return text.split()


class BPETokenizer:
    """
    Lightweight Byte-Pair Encoding tokenizer built from scratch.

    Training:
        1. Start with character-level vocabulary (each word split into chars + </w>)
        2. Iteratively merge the most frequent adjacent pair
        3. Stop after `num_merges` iterations or when vocab reaches `vocab_size`

    Encoding:
        Apply learned merge rules greedily left-to-right.
    """

    def __init__(self, vocab_size: int = 4096, num_merges: int = 2000):
        self.vocab_size = vocab_size
        self.num_merges = num_merges

        # token → id
        self.token2id: Dict[str, int] = {}
        # id → token
        self.id2token: Dict[int, str] = {}
        # ordered list of merge rules: (a, b) → "a b"
        self.merges: List[Tuple[str, str]] = []
        self._merge_set: Dict[Tuple[str, str], int] = {}  # for O(1) lookup

        self._init_special_tokens()

    # ── Initialisation ─────────────────────────────────────────────────────────

    def _init_special_tokens(self):
        for tok in SPECIAL_TOKENS:
            idx = len(self.token2id)
            self.token2id[tok] = idx
            self.id2token[idx] = tok

    # ── Training ───────────────────────────────────────────────────────────────

    def _word_to_chars(self, word: str) -> Tuple[str, ...]:
        """Split word into characters, appending </w> to mark word boundary."""
        return tuple(list(word) + ["</w>"])

    def _get_pair_counts(
        self, vocab: Dict[Tuple[str, ...], int]
    ) -> Counter:
        pairs: Counter = Counter()
        for word_chars, freq in vocab.items():
            for i in range(len(word_chars) - 1):
                pairs[(word_chars[i], word_chars[i + 1])] += freq
        return pairs

    def _merge_vocab(
        self,
        pair: Tuple[str, str],
        vocab: Dict[Tuple[str, ...], int],
    ) -> Dict[Tuple[str, ...], int]:
        """Replace all occurrences of `pair` in vocab with merged token."""
        merged = pair[0] + pair[1]
        new_vocab: Dict[Tuple[str, ...], int] = {}
        for word_chars, freq in vocab.items():
            new_chars: List[str] = []
            i = 0
            while i < len(word_chars):
                if (
                    i < len(word_chars) - 1
                    and word_chars[i] == pair[0]
                    and word_chars[i + 1] == pair[1]
                ):
                    new_chars.append(merged)
                    i += 2
                else:
                    new_chars.append(word_chars[i])
                    i += 1
            new_vocab[tuple(new_chars)] = freq
        return new_vocab

    def fit(self, corpus: List[str]) -> "BPETokenizer":
        """
        Train BPE on a list of text strings.

        Args:
            corpus: list of raw text strings (titles, descriptions, tags)
        Returns:
            self (for chaining)
        """
        # Build word frequency table
        word_freq: Counter = Counter()
        for text in corpus:
            for word in _basic_tokenize(text):
                word_freq[word] += 1

        # Initialise character-level vocab
        vocab: Dict[Tuple[str, ...], int] = {
            self._word_to_chars(word): freq
            for word, freq in word_freq.items()
        }

        # Collect all unique characters as base tokens
        char_set: set = set()
        for word_chars in vocab:
            char_set.update(word_chars)

        for ch in sorted(char_set):
            if ch not in self.token2id:
                idx = len(self.token2id)
                self.token2id[ch] = idx
                self.id2token[idx] = ch

        # BPE merge loop
        for merge_idx in range(self.num_merges):
            if len(self.token2id) >= self.vocab_size:
                break

            pair_counts = self._get_pair_counts(vocab)
            if not pair_counts:
                break

            best_pair = pair_counts.most_common(1)[0][0]
            self.merges.append(best_pair)
            self._merge_set[best_pair] = merge_idx

            # Add merged token to vocabulary
            merged_token = best_pair[0] + best_pair[1]
            if merged_token not in self.token2id:
                idx = len(self.token2id)
                self.token2id[merged_token] = idx
                self.id2token[idx] = merged_token

            vocab = self._merge_vocab(best_pair, vocab)

        return self

    # ── Encoding ───────────────────────────────────────────────────────────────

    def _tokenize_word(self, word: str) -> List[str]:
        """Apply BPE merges to a single word."""
        chars = list(self._word_to_chars(word))

        # Apply merges greedily
        for pair in self.merges:
            i = 0
            new_chars: List[str] = []
            while i < len(chars):
                if (
                    i < len(chars) - 1
                    and chars[i] == pair[0]
                    and chars[i + 1] == pair[1]
                ):
                    new_chars.append(pair[0] + pair[1])
                    i += 2
                else:
                    new_chars.append(chars[i])
                    i += 1
            chars = new_chars

        return chars

    def encode(
        self,
        text: str,
        max_length: int = 128,
        add_special_tokens: bool = True,
    ) -> List[int]:
        """
        Encode text to token IDs.

        Args:
            text: raw input string
            max_length: truncate/pad to this length
            add_special_tokens: prepend [CLS], append [SEP]
        Returns:
            list of integer token IDs, length == max_length
        """
        words = _basic_tokenize(text)
        tokens: List[str] = []

        if add_special_tokens:
            tokens.append(CLS_TOKEN)

        for word in words:
            tokens.extend(self._tokenize_word(word))

        if add_special_tokens:
            tokens.append(SEP_TOKEN)

        # Convert to IDs
        ids = [self.token2id.get(t, UNK_ID) for t in tokens]

        # Truncate
        if len(ids) > max_length:
            if add_special_tokens:
                ids = ids[: max_length - 1] + [SEP_ID]
            else:
                ids = ids[:max_length]

        # Pad
        ids += [PAD_ID] * (max_length - len(ids))
        return ids

    def decode(self, ids: List[int]) -> str:
        """Decode token IDs back to a string (best-effort)."""
        tokens = [self.id2token.get(i, UNK_TOKEN) for i in ids]
        # Remove special tokens
        tokens = [t for t in tokens if t not in SPECIAL_TOKENS]
        # Merge </w> markers
        text = " ".join(tokens).replace(" </w>", "").replace("</w>", "")
        return text

    @property
    def vocab_size_actual(self) -> int:
        return len(self.token2id)

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self, path: str):
        """Save tokenizer state to a JSON file."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        state = {
            "vocab_size": self.vocab_size,
            "num_merges": self.num_merges,
            "token2id": self.token2id,
            "merges": self.merges,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "BPETokenizer":
        """Load tokenizer from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)

        tok = cls(vocab_size=state["vocab_size"], num_merges=state["num_merges"])
        tok.token2id = state["token2id"]
        tok.id2token = {int(k) if k.isdigit() else k: v for k, v in {}}
        # Rebuild id2token
        tok.id2token = {v: k for k, v in tok.token2id.items()}
        tok.merges = [tuple(m) for m in state["merges"]]
        tok._merge_set = {tuple(m): i for i, m in enumerate(tok.merges)}
        return tok


# ── Simple whitespace tokenizer (fast fallback) ───────────────────────────────

class SimpleTokenizer:
    """
    Word-level tokenizer with a fixed vocabulary.
    Faster than BPE; good for short problem titles and tags.
    """

    def __init__(self, vocab_size: int = 8192):
        self.vocab_size = vocab_size
        self.token2id: Dict[str, int] = {}
        self.id2token: Dict[int, str] = {}
        self._init_special_tokens()

    def _init_special_tokens(self):
        for tok in SPECIAL_TOKENS:
            idx = len(self.token2id)
            self.token2id[tok] = idx
            self.id2token[idx] = tok

    def fit(self, corpus: List[str]) -> "SimpleTokenizer":
        word_freq: Counter = Counter()
        for text in corpus:
            for word in _basic_tokenize(text):
                word_freq[word] += 1

        # Keep top (vocab_size - num_special) words
        top_words = word_freq.most_common(self.vocab_size - len(SPECIAL_TOKENS))
        for word, _ in top_words:
            if word not in self.token2id:
                idx = len(self.token2id)
                self.token2id[word] = idx
                self.id2token[idx] = word
        return self

    def encode(
        self,
        text: str,
        max_length: int = 64,
        add_special_tokens: bool = True,
    ) -> List[int]:
        words = _basic_tokenize(text)
        ids: List[int] = []

        if add_special_tokens:
            ids.append(CLS_ID)

        for word in words:
            ids.append(self.token2id.get(word, UNK_ID))

        if add_special_tokens:
            ids.append(SEP_ID)

        if len(ids) > max_length:
            ids = ids[: max_length - 1] + [SEP_ID]

        ids += [PAD_ID] * (max_length - len(ids))
        return ids

    def decode(self, ids: List[int]) -> str:
        tokens = [self.id2token.get(i, UNK_TOKEN) for i in ids]
        return " ".join(t for t in tokens if t not in SPECIAL_TOKENS)

    @property
    def vocab_size_actual(self) -> int:
        return len(self.token2id)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        state = {"vocab_size": self.vocab_size, "token2id": self.token2id}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "SimpleTokenizer":
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        tok = cls(vocab_size=state["vocab_size"])
        tok.token2id = state["token2id"]
        tok.id2token = {v: k for k, v in tok.token2id.items()}
        return tok
