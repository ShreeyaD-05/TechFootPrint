"""
evaluate_dl_recommender.py
==========================
Comprehensive evaluation script for the Transformer-based recommendation system.

Covers:
  1. Problem Encoder — embedding quality (alignment, uniformity, cluster purity)
  2. Recommendation Model — classification metrics per task head
  3. Ranking metrics — NDCG@K, Precision@K, Recall@K, MRR
  4. Benchmarks — latency, throughput, model size
  5. Exploration sanity checks — epsilon-greedy & UCB coverage
  6. Attention interpretability — entropy, head agreement

Run:
    python evaluate_dl_recommender.py [--checkpoint_dir checkpoints/dl_recommender]
                                       [--excel_path "../dataset/LeetCode Questions.xlsx"]
                                       [--device cpu]
                                       [--n_eval_users 50]
                                       [--output_dir eval_results/]
"""

import os
import sys
import json
import time
import math
import random
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Try importing project modules ─────────────────────────────────────────────
# Adjust sys.path so this script can be run from the backend/ directory.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from services.transformer.tokenizer import SimpleTokenizer
    from services.transformer.encoder import ProblemEncoder
    from services.recommender.user_encoder import UserEncoder
    from services.recommender.recommender_model import RecommenderModel
    from services.recommender.problem_encoder import ProblemBankEncoder
    from services.recommender.loss import ContrastiveLoss, MultiTaskLoss
    from services.training.dataset import (
        ProblemContentDataset,
        InteractionDataset,
        load_problems_from_excel,
        generate_synthetic_interactions,
        DIFF_MAP,
    )
    from services.training.optimizer import TorchAdamWrapper
    MODULES_AVAILABLE = True
    logger.info("✅  Project modules imported successfully.")
except ImportError as e:
    MODULES_AVAILABLE = False
    logger.warning("⚠️  Could not import project modules: %s", e)
    logger.warning("Running in STANDALONE / MOCK mode — "
                   "all metrics are computed on randomly-initialised models.")


# ═════════════════════════════════════════════════════════════════════════════
# 1.  HELPERS & METRICS PRIMITIVES
# ═════════════════════════════════════════════════════════════════════════════

def dcg_at_k(relevances: List[float], k: int) -> float:
    """Discounted Cumulative Gain at K."""
    relevances = relevances[:k]
    return sum(rel / math.log2(rank + 2) for rank, rel in enumerate(relevances))


def ndcg_at_k(relevances: List[float], k: int) -> float:
    """Normalised Discounted Cumulative Gain at K."""
    ideal = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg_at_k(relevances, k) / idcg


def precision_at_k(relevances: List[float], k: int, threshold: float = 0.5) -> float:
    """Precision@K — fraction of top-K that are relevant."""
    top_k = relevances[:k]
    return sum(1 for r in top_k if r >= threshold) / k if k > 0 else 0.0


def recall_at_k(relevances: List[float], k: int, threshold: float = 0.5) -> float:
    """Recall@K — fraction of all relevant items retrieved in top-K."""
    n_relevant = sum(1 for r in relevances if r >= threshold)
    if n_relevant == 0:
        return 0.0
    top_k_relevant = sum(1 for r in relevances[:k] if r >= threshold)
    return top_k_relevant / n_relevant


def mean_reciprocal_rank(relevances_list: List[List[float]], threshold: float = 0.5) -> float:
    """Mean Reciprocal Rank across multiple queries."""
    rr_sum = 0.0
    count = 0
    for rels in relevances_list:
        for rank, r in enumerate(rels):
            if r >= threshold:
                rr_sum += 1.0 / (rank + 1)
                break
        count += 1
    return rr_sum / count if count > 0 else 0.0


def binary_accuracy(preds: torch.Tensor, labels: torch.Tensor, threshold: float = 0.5) -> float:
    binary_preds = (preds > threshold).float()
    return (binary_preds == labels).float().mean().item()


def compute_roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Simple trapezoidal AUC without sklearn."""
    sorted_idx = np.argsort(-scores)
    sorted_labels = labels[sorted_idx]
    n_pos = sorted_labels.sum()
    n_neg = len(sorted_labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    tp, fp = 0.0, 0.0
    auc = 0.0
    prev_fp = 0.0
    for label in sorted_labels:
        if label == 1:
            tp += 1
        else:
            fp += 1
            auc += tp * (fp - prev_fp) / (n_pos * n_neg)
            prev_fp = fp
    return auc


def compute_f1(preds: np.ndarray, labels: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """Compute Precision, Recall, F1 from score arrays."""
    binary = (preds > threshold).astype(int)
    tp = ((binary == 1) & (labels == 1)).sum()
    fp = ((binary == 1) & (labels == 0)).sum()
    fn = ((binary == 0) & (labels == 1)).sum()
    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1 = 2 * precision * recall / (precision + recall + 1e-8)
    return {"precision": float(precision), "recall": float(recall), "f1": float(f1)}


def embedding_alignment(embeddings: torch.Tensor, labels: torch.Tensor) -> float:
    """
    Alignment loss (Wang & Isola, 2020):
        E[||z_i - z_j||^2]  for (i,j) with same label.
    Lower = better: same-class embeddings are closer.
    """
    total, count = 0.0, 0
    for cls in labels.unique():
        mask = labels == cls
        emb_cls = embeddings[mask]  # (n_cls, d)
        if emb_cls.size(0) < 2:
            continue
        diffs = emb_cls.unsqueeze(0) - emb_cls.unsqueeze(1)  # (n,n,d)
        sq_dists = (diffs ** 2).sum(-1)  # (n,n)
        # Upper triangle only
        n = emb_cls.size(0)
        for i in range(n):
            for j in range(i + 1, n):
                total += sq_dists[i, j].item()
                count += 1
    return total / count if count > 0 else 0.0


def embedding_uniformity(embeddings: torch.Tensor, t: float = 2.0) -> float:
    """
    Uniformity loss (Wang & Isola, 2020):
        log E[exp(-t * ||z_i - z_j||^2)]
    Lower (more negative) = better distributed on hypersphere.
    """
    sq_dists = torch.pdist(embeddings, p=2).pow(2)
    return sq_dists.mul(-t).exp().mean().log().item()


def cluster_purity(embeddings: torch.Tensor, labels: torch.Tensor) -> float:
    """
    Cluster purity via nearest-neighbour: fraction where nearest neighbour
    shares the same cluster label.
    """
    n = embeddings.size(0)
    if n < 2:
        return 1.0
    sim = F.cosine_similarity(
        embeddings.unsqueeze(0), embeddings.unsqueeze(1), dim=-1
    )  # (n, n)
    sim.fill_diagonal_(-1.0)
    nn_idx = sim.argmax(dim=1)  # (n,)
    correct = (labels[nn_idx] == labels).float().mean().item()
    return correct


def attention_entropy(attn_weights: torch.Tensor) -> float:
    """
    Mean entropy of attention distributions.
    Higher entropy = more diffuse (less peaked) attention.
    attn_weights: (batch, heads, seq, seq)
    """
    # Avoid log(0)
    safe = attn_weights.clamp(min=1e-9)
    entropy = -(safe * safe.log()).sum(dim=-1)  # (batch, heads, seq)
    return entropy.mean().item()


# ═════════════════════════════════════════════════════════════════════════════
# 2.  MODEL LOADER
# ═════════════════════════════════════════════════════════════════════════════

def load_models(checkpoint_dir: str, device: torch.device):
    """
    Load all trained components from checkpoint directory.

    Returns (tokenizer, problem_encoder, user_encoder, recommender, config)
    or raises if any component is missing.
    """
    ckpt = Path(checkpoint_dir)

    required = [
        "tokenizer.json", "problem_encoder.pt",
        "user_encoder.pt", "recommender.pt", "config.json",
    ]
    missing = [f for f in required if not (ckpt / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing checkpoint files: {missing}\n"
            f"Run python train_dl_recommender.py to train first."
        )

    with open(ckpt / "config.json") as f:
        config = json.load(f)

    tokenizer = SimpleTokenizer.load(str(ckpt / "tokenizer.json"))
    logger.info("Tokenizer vocab: %d tokens", tokenizer.vocab_size_actual)

    problem_encoder = ProblemEncoder(
        vocab_size=tokenizer.vocab_size_actual,
        d_model=config["d_model"],
        embed_dim=config["embed_dim"],
        num_heads=config["num_heads"],
        num_layers=config["num_encoder_layers"],
        d_ff=config["d_ff"],
        max_len=config["max_len"],
        dropout=0.0,  # eval mode
    )
    problem_encoder.load_state_dict(
        torch.load(str(ckpt / "problem_encoder.pt"), map_location=device)
    )

    user_encoder = UserEncoder(
        embed_dim=config["embed_dim"],
        num_heads=config["num_heads"],
        num_layers=2,
        max_history=config["max_history"],
        dropout=0.0,
    )
    user_encoder.load_state_dict(
        torch.load(str(ckpt / "user_encoder.pt"), map_location=device)
    )

    recommender = RecommenderModel(
        embed_dim=config["embed_dim"],
        hidden_dim=config["hidden_dim"],
        num_residual_blocks=config["num_residual_blocks"],
        dropout=0.0,
    )
    recommender.load_state_dict(
        torch.load(str(ckpt / "recommender.pt"), map_location=device)
    )

    for m in [problem_encoder, user_encoder, recommender]:
        m.to(device)
        m.eval()

    logger.info("✅  All model weights loaded from %s", checkpoint_dir)
    return tokenizer, problem_encoder, user_encoder, recommender, config


def build_mock_models(device: torch.device):
    """Build randomly-initialised models for standalone testing."""
    logger.info("Building mock (randomly-initialised) models for standalone testing...")

    config = {
        "vocab_size": 512, "d_model": 64, "embed_dim": 32,
        "num_heads": 4, "num_encoder_layers": 2, "d_ff": 128,
        "max_len": 32, "dropout": 0.0, "hidden_dim": 128,
        "num_residual_blocks": 2, "max_history": 16,
        "w_solve": 0.4, "w_helpful": 0.3, "w_difficulty": 0.3,
    }

    if not MODULES_AVAILABLE:
        return None, None, None, None, config

    tokenizer = SimpleTokenizer(vocab_size=config["vocab_size"])
    tokenizer.fit(["two sum array hash table", "binary search sorted array",
                   "dynamic programming memoization", "graph depth first search"])

    pe = ProblemEncoder(
        vocab_size=tokenizer.vocab_size_actual,
        d_model=config["d_model"], embed_dim=config["embed_dim"],
        num_heads=config["num_heads"], num_layers=config["num_encoder_layers"],
        d_ff=config["d_ff"], max_len=config["max_len"], dropout=0.0,
    ).to(device).eval()

    ue = UserEncoder(
        embed_dim=config["embed_dim"], num_heads=config["num_heads"],
        num_layers=2, max_history=config["max_history"], dropout=0.0,
    ).to(device).eval()

    rm = RecommenderModel(
        embed_dim=config["embed_dim"], hidden_dim=config["hidden_dim"],
        num_residual_blocks=config["num_residual_blocks"], dropout=0.0,
    ).to(device).eval()

    return tokenizer, pe, ue, rm, config


# ═════════════════════════════════════════════════════════════════════════════
# 3.  ENCODER EVALUATION
# ═════════════════════════════════════════════════════════════════════════════

def evaluate_problem_encoder(
    encoder: "ProblemEncoder",
    dataset: "ProblemContentDataset",
    device: torch.device,
    batch_size: int = 64,
    max_samples: int = 1000,
) -> Dict[str, float]:
    """
    Evaluate the pre-trained problem encoder.

    Metrics:
      - Alignment loss      : same-cluster embeddings should be close
      - Uniformity loss     : embeddings should be spread on unit sphere
      - Cluster purity (NN) : nearest neighbour has same topic cluster
      - Contrastive loss    : InfoNCE on held-out samples
      - Mean embedding norm : should be ~1.0 (L2-normalised)
    """
    logger.info("--- Evaluating Problem Encoder ---")
    encoder.eval()

    loader = DataLoader(
        dataset, batch_size=batch_size, shuffle=True, drop_last=False
    )

    all_embeddings: List[torch.Tensor] = []
    all_labels: List[torch.Tensor] = []
    contrastive = ContrastiveLoss(temperature=0.2) if MODULES_AVAILABLE else None
    contrastive_losses: List[float] = []
    total_samples = 0

    with torch.no_grad():
        for batch in loader:
            if total_samples >= max_samples:
                break
            token_ids = batch["token_ids"].to(device)
            topic_ids = batch["topic_ids"].to(device)
            diff_ids  = batch["difficulty_id"].to(device)
            clusters  = batch["cluster_label"].to(device)

            emb = encoder(token_ids, topic_ids, diff_ids, normalize=True)

            all_embeddings.append(emb.cpu())
            all_labels.append(clusters.cpu())
            total_samples += emb.size(0)

            if contrastive is not None:
                loss = contrastive(emb, clusters)
                if torch.isfinite(loss):
                    contrastive_losses.append(loss.item())

    embeddings = torch.cat(all_embeddings, dim=0)
    labels     = torch.cat(all_labels, dim=0)

    norms = embeddings.norm(dim=-1)

    results = {
        "n_samples"        : int(embeddings.size(0)),
        "mean_emb_norm"    : float(norms.mean()),
        "std_emb_norm"     : float(norms.std()),
        "alignment_loss"   : embedding_alignment(embeddings, labels),
        "uniformity_loss"  : embedding_uniformity(embeddings),
        "cluster_purity_nn": cluster_purity(embeddings, labels),
        "contrastive_loss" : float(np.mean(contrastive_losses)) if contrastive_losses else float("nan"),
    }

    # Per-cluster analysis
    n_clusters = int(labels.max().item()) + 1
    per_cluster_purity = {}
    for c in range(n_clusters):
        mask = labels == c
        if mask.sum() < 2:
            continue
        purity_c = cluster_purity(embeddings[mask], labels[mask])
        per_cluster_purity[f"cluster_{c}"] = round(purity_c, 4)
    results["per_cluster_purity"] = per_cluster_purity

    _print_section("Problem Encoder Metrics", results)
    return results


# ═════════════════════════════════════════════════════════════════════════════
# 4.  RECOMMENDATION MODEL EVALUATION  (classification)
# ═════════════════════════════════════════════════════════════════════════════

def evaluate_recommender_classification(
    user_encoder: "UserEncoder",
    recommender: "RecommenderModel",
    dataset: "InteractionDataset",
    device: torch.device,
    batch_size: int = 64,
    val_fraction: float = 0.2,
) -> Dict[str, float]:
    """
    Classification metrics for each prediction head:
      - Solve head   : binary accuracy, AUC, F1, Brier score
      - Helpful head : binary accuracy, AUC, F1, Brier score
      - Difficulty   : top-1 accuracy, per-class accuracy
    """
    logger.info("--- Evaluating Recommender (Classification) ---")

    n_val = max(1, int(val_fraction * len(dataset)))
    n_train = len(dataset) - n_val
    _, val_ds = random_split(dataset, [n_train, n_val])
    loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    solve_scores, solve_labels           = [], []
    helpful_scores, helpful_labels       = [], []
    diff_preds, diff_labels              = [], []
    loss_fn = MultiTaskLoss(0.4, 0.3, 0.3) if MODULES_AVAILABLE else None
    total_losses: List[float]            = []

    user_encoder.eval()
    recommender.eval()

    with torch.no_grad():
        for batch in loader:
            pe  = batch["problem_embedding"].to(device)
            he  = batch["history_embeddings"].to(device)
            hd  = batch["history_difficulties"].to(device)
            pm  = batch["padding_mask"].to(device)
            sv  = batch["skill_vec"].to(device)
            sl  = batch["solve_label"]
            hl  = batch["helpful_label"]
            hm  = batch["helpful_mask"].to(device)
            dl  = batch["difficulty_label"]
            dm  = batch["difficulty_mask"].to(device)

            user_emb    = user_encoder(he, hd, sv, pm)
            predictions = recommender(user_emb, pe)

            # Collect scores/labels
            solve_p  = predictions["p_solve"].squeeze(-1).cpu()  # Already sigmoid'd
            help_p   = predictions["p_helpful"].squeeze(-1).cpu()  # Already sigmoid'd
            diff_p   = predictions["p_difficulty"].cpu()

            solve_scores.append(solve_p)
            solve_labels.append(sl)
            helpful_scores.append(help_p[hm.cpu()])
            helpful_labels.append(hl[hm.cpu()])
            diff_preds.append(diff_p[dm.cpu()])
            diff_labels.append(dl[dm.cpu()])

            if loss_fn is not None:
                targets = {
                    "solve": sl.to(device),
                    "helpful": hl.to(device),
                    "difficulty": dl.to(device),
                }
                masks = {"helpful_mask": hm, "difficulty_mask": dm}
                loss, _ = loss_fn(predictions, targets, masks)
                if torch.isfinite(loss):
                    total_losses.append(loss.item())

    solve_scores  = torch.cat(solve_scores).numpy()
    solve_labels  = torch.cat(solve_labels).numpy()
    helpful_scores = torch.cat(helpful_scores).numpy() if helpful_scores and any(len(t) > 0 for t in helpful_scores) else np.array([])
    helpful_labels = torch.cat(helpful_labels).numpy() if helpful_labels and any(len(t) > 0 for t in helpful_labels) else np.array([])

    if len(diff_preds) > 0 and any(len(t) > 0 for t in diff_preds):
        diff_pred_tensor = torch.cat(diff_preds)
        diff_label_tensor = torch.cat(diff_labels)
        diff_top1 = (diff_pred_tensor.argmax(dim=-1) == diff_label_tensor).float().mean().item()
        # Per-class
        per_class_acc = {}
        for c, name in enumerate(["too_easy", "just_right", "too_hard"]):
            mask = diff_label_tensor == c
            if mask.sum() > 0:
                per_class_acc[name] = (diff_pred_tensor[mask].argmax(dim=-1) == c).float().mean().item()
    else:
        diff_top1 = float("nan")
        per_class_acc = {}

    # Solve metrics
    solve_f1  = compute_f1(solve_scores, solve_labels)
    solve_auc = compute_roc_auc(solve_scores, solve_labels)
    brier_solve = float(np.mean((solve_scores - solve_labels) ** 2))

    results = {
        "val_loss"            : float(np.mean(total_losses)) if total_losses else float("nan"),
        # Solve head
        "solve_accuracy"      : float(binary_accuracy(
            torch.tensor(solve_scores), torch.tensor(solve_labels))),
        "solve_auc"           : solve_auc,
        "solve_precision"     : solve_f1["precision"],
        "solve_recall"        : solve_f1["recall"],
        "solve_f1"            : solve_f1["f1"],
        "solve_brier_score"   : brier_solve,
        # Helpful head
        "helpful_accuracy"    : float(binary_accuracy(
            torch.tensor(helpful_scores), torch.tensor(helpful_labels))) if len(helpful_scores) > 0 else float("nan"),
        "helpful_auc"         : compute_roc_auc(helpful_scores, helpful_labels) if len(helpful_scores) > 1 else float("nan"),
        "helpful_brier"       : float(np.mean((helpful_scores - helpful_labels) ** 2)) if len(helpful_scores) > 0 else float("nan"),
        # Difficulty head
        "difficulty_accuracy" : diff_top1,
        "difficulty_per_class": per_class_acc,
        # Sample counts
        "n_val_samples"       : len(solve_labels),
    }

    _print_section("Recommender Classification Metrics", results)
    return results


# ═════════════════════════════════════════════════════════════════════════════
# 5.  RANKING METRICS
# ═════════════════════════════════════════════════════════════════════════════

def evaluate_ranking(
    user_encoder: "UserEncoder",
    recommender: "RecommenderModel",
    dataset: "InteractionDataset",
    device: torch.device,
    k_values: List[int] = [5, 10, 20],
    n_users: int = 100,
    n_candidates_per_user: int = 50,
) -> Dict[str, float]:
    """
    Ranking-based evaluation.

    For each synthetic user:
      - Sample n_candidates_per_user problems from the interaction dataset
      - Score all candidates with the model
      - Measure NDCG@K, Precision@K, Recall@K, MRR
      - Ground truth: problems with solve_label == 1 are 'relevant'
    """
    logger.info("--- Evaluating Ranking Metrics (n_users=%d) ---", n_users)

    user_encoder.eval()
    recommender.eval()

    ndcg_scores = {k: [] for k in k_values}
    prec_scores = {k: [] for k in k_values}
    rec_scores  = {k: [] for k in k_values}
    all_relevances_for_mrr = []

    # We treat each item in the dataset as a (user, candidate_pool) pair
    items = [dataset[i] for i in range(min(n_users * n_candidates_per_user, len(dataset)))]

    # Group items into user 'sessions' of n_candidates_per_user
    random.shuffle(items)
    sessions = [
        items[i : i + n_candidates_per_user]
        for i in range(0, len(items) - n_candidates_per_user, n_candidates_per_user)
    ]
    sessions = sessions[:n_users]

    for session in sessions:
        if not session:
            continue

        # Stack into batch
        pe_list = [s["problem_embedding"] for s in session]
        he_list = [s["history_embeddings"] for s in session]
        hd_list = [s["history_difficulties"] for s in session]
        pm_list = [s["padding_mask"] for s in session]
        sv_list = [s["skill_vec"] for s in session]
        sl_list = [s["solve_label"].item() for s in session]

        pe_batch = torch.stack(pe_list).to(device)
        he_batch = torch.stack(he_list).to(device)
        hd_batch = torch.stack(hd_list).to(device)
        pm_batch = torch.stack(pm_list).to(device)
        sv_batch = torch.stack(sv_list).to(device)

        with torch.no_grad():
            user_emb    = user_encoder(he_batch, hd_batch, sv_batch, pm_batch)
            predictions = recommender(user_emb, pe_batch)

        # Composite score: weighted sum
        solve_p  = predictions["p_solve"].squeeze(-1).cpu().tolist()  # Already sigmoid'd
        help_p   = predictions["p_helpful"].squeeze(-1).cpu().tolist()  # Already sigmoid'd
        scores   = [0.6 * s + 0.4 * h for s, h in zip(solve_p, help_p)]

        # Sort by score descending
        ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        ranked_rel = [float(sl_list[i]) for i in ranked_idx]

        for k in k_values:
            ndcg_scores[k].append(ndcg_at_k(ranked_rel, k))
            prec_scores[k].append(precision_at_k(ranked_rel, k))
            rec_scores[k].append(recall_at_k(ranked_rel, k))

        all_relevances_for_mrr.append(ranked_rel)

    results: Dict[str, float] = {}
    for k in k_values:
        results[f"NDCG@{k}"]      = float(np.mean(ndcg_scores[k])) if ndcg_scores[k] else float("nan")
        results[f"Precision@{k}"] = float(np.mean(prec_scores[k])) if prec_scores[k] else float("nan")
        results[f"Recall@{k}"]    = float(np.mean(rec_scores[k]))  if rec_scores[k]  else float("nan")

    results["MRR"] = mean_reciprocal_rank(all_relevances_for_mrr)
    results["n_eval_sessions"] = len(sessions)

    _print_section("Ranking Metrics", results)
    return results


# ═════════════════════════════════════════════════════════════════════════════
# 6.  LATENCY & THROUGHPUT BENCHMARKS
# ═════════════════════════════════════════════════════════════════════════════

def benchmark_inference_latency(
    problem_encoder: "ProblemEncoder",
    user_encoder: "UserEncoder",
    recommender: "RecommenderModel",
    device: torch.device,
    embed_dim: int = 64,
    batch_sizes: List[int] = [1, 10, 50, 100, 200],
    n_repeats: int = 20,
    max_history: int = 32,
) -> Dict:
    """
    Benchmark end-to-end inference latency.

    Measures:
      - Problem encoding (single problem, not cached)
      - User encoding
      - Recommender scoring
      - Total pipeline (n_candidates problems)
      - Throughput (problems/second)
    """
    logger.info("--- Benchmarking Inference Latency ---")

    def make_batch(batch_size):
        seq_len = 32
        token_ids  = torch.randint(0, 100, (batch_size, seq_len), device=device)
        topic_ids  = torch.randint(0, 44, (batch_size, 8), device=device)
        diff_ids   = torch.randint(0, 3, (batch_size,), device=device)
        prob_emb   = F.normalize(torch.randn(batch_size, embed_dim, device=device), dim=-1)
        hist_emb   = F.normalize(torch.randn(batch_size, max_history, embed_dim, device=device), dim=-1)
        hist_diff  = torch.randint(0, 3, (batch_size, max_history), device=device)
        pad_mask   = torch.zeros(batch_size, max_history, dtype=torch.bool, device=device)
        skill_vec  = torch.randn(batch_size, 44, device=device)
        return token_ids, topic_ids, diff_ids, prob_emb, hist_emb, hist_diff, pad_mask, skill_vec

    latency_results = {}

    # Warm-up
    with torch.no_grad():
        t, tp, d, pe, he, hd, pm, sv = make_batch(1)
        problem_encoder(t, tp, d)
        user_encoder(he, hd, sv, pm)
        recommender(user_encoder(he, hd, sv, pm), pe)

    for bs in batch_sizes:
        times_problem_enc = []
        times_user_enc    = []
        times_recommender = []
        times_total       = []

        for _ in range(n_repeats):
            t, tp, d, pe, he, hd, pm, sv = make_batch(bs)

            t0 = time.perf_counter()
            with torch.no_grad():
                # 1. Encode problems
                t1 = time.perf_counter()
                prob_embs = problem_encoder(t, tp, d)
                t2 = time.perf_counter()
                # 2. Encode user (once per user; batch = multiple candidates same user)
                usr_emb = user_encoder(he[:1], hd[:1], sv[:1], pm[:1])
                usr_emb_expanded = usr_emb.expand(bs, -1)
                t3 = time.perf_counter()
                # 3. Score
                recommender(usr_emb_expanded, prob_embs)
                t4 = time.perf_counter()

            times_problem_enc.append((t2 - t1) * 1000)
            times_user_enc.append((t3 - t2) * 1000)
            times_recommender.append((t4 - t3) * 1000)
            times_total.append((t4 - t1) * 1000)

        latency_results[bs] = {
            "problem_enc_ms"   : round(float(np.median(times_problem_enc)), 2),
            "user_enc_ms"      : round(float(np.median(times_user_enc)), 2),
            "recommender_ms"   : round(float(np.median(times_recommender)), 2),
            "total_ms"         : round(float(np.median(times_total)), 2),
            "p95_total_ms"     : round(float(np.percentile(times_total, 95)), 2),
            "throughput_per_s" : round(bs / (float(np.median(times_total)) / 1000), 1),
        }
        logger.info(
            "  batch=%3d | total=%.1fms (p95=%.1fms) | %.0f problems/s",
            bs,
            latency_results[bs]["total_ms"],
            latency_results[bs]["p95_total_ms"],
            latency_results[bs]["throughput_per_s"],
        )

    _print_section("Latency Benchmarks", latency_results)
    return latency_results


# ═════════════════════════════════════════════════════════════════════════════
# 7.  MODEL SIZE ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════

def analyze_model_size(
    problem_encoder: nn.Module,
    user_encoder: nn.Module,
    recommender: nn.Module,
) -> Dict:
    """Analyse parameter counts and memory footprint."""
    logger.info("--- Analyzing Model Size ---")

    def module_stats(model: nn.Module, name: str) -> Dict:
        total = sum(p.numel() for p in model.parameters())
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        size_mb = total * 4 / (1024 ** 2)  # float32
        return {
            "name": name,
            "total_params": total,
            "trainable_params": trainable,
            "size_mb_fp32": round(size_mb, 2),
            "size_mb_fp16": round(size_mb / 2, 2),
            "size_mb_int8": round(size_mb / 4, 2),
        }

    pe_stats  = module_stats(problem_encoder, "ProblemEncoder")
    ue_stats  = module_stats(user_encoder, "UserEncoder")
    rm_stats  = module_stats(recommender, "RecommenderModel")
    all_total = pe_stats["total_params"] + ue_stats["total_params"] + rm_stats["total_params"]

    results = {
        "problem_encoder": pe_stats,
        "user_encoder"   : ue_stats,
        "recommender"    : rm_stats,
        "total_params"   : all_total,
        "total_params_M" : round(all_total / 1e6, 3),
        "total_size_fp32_mb": round(all_total * 4 / (1024 ** 2), 2),
        "total_size_fp16_mb": round(all_total * 2 / (1024 ** 2), 2),
    }

    print("\n" + "=" * 60)
    print("MODEL SIZE ANALYSIS")
    print("=" * 60)
    for name, stats in [("ProblemEncoder", pe_stats), ("UserEncoder", ue_stats), ("Recommender", rm_stats)]:
        print(f"  {name:20s} {stats['total_params']:>10,} params  ({stats['size_mb_fp32']:.2f} MB)")
    print(f"  {'TOTAL':20s} {all_total:>10,} params  ({results['total_size_fp32_mb']:.2f} MB FP32 | {results['total_size_fp16_mb']:.2f} MB FP16)")
    print("=" * 60)

    return results


# ═════════════════════════════════════════════════════════════════════════════
# 8.  ATTENTION INTERPRETABILITY
# ═════════════════════════════════════════════════════════════════════════════

def evaluate_attention_quality(
    problem_encoder: "ProblemEncoder",
    dataset: "ProblemContentDataset",
    device: torch.device,
    n_samples: int = 200,
) -> Dict:
    """
    Analyse attention weight quality:
      - Mean entropy per layer (uniform = max entropy = log(seq_len))
      - Head agreement: do all heads attend to the same tokens?
      - CLS token attention concentration
    """
    logger.info("--- Evaluating Attention Quality ---")

    problem_encoder.eval()
    loader = DataLoader(dataset, batch_size=32, shuffle=True)

    all_layer_entropies: Dict[int, List[float]] = defaultdict(list)
    cls_concentration: List[float] = []
    total = 0

    with torch.no_grad():
        for batch in loader:
            if total >= n_samples:
                break
            token_ids = batch["token_ids"].to(device)
            topic_ids = batch["topic_ids"].to(device)
            diff_ids  = batch["difficulty_id"].to(device)

            _ = problem_encoder(token_ids, topic_ids, diff_ids)
            attn_maps = problem_encoder.get_attention_maps()

            for layer_idx, attn in enumerate(attn_maps):
                # attn: (batch, heads, seq, seq)
                ent = attention_entropy(attn)
                all_layer_entropies[layer_idx].append(ent)

                # CLS attention — how concentrated is attention FROM cls position?
                cls_attn = attn[:, :, 0, :].mean(dim=1)  # (batch, seq)
                # Gini-like concentration (1 - normalised entropy)
                safe = cls_attn.clamp(min=1e-9)
                ent_cls = -(safe * safe.log()).sum(dim=-1)  # (batch,)
                max_ent = math.log(token_ids.size(1))
                conc = 1.0 - (ent_cls / max_ent).mean().item()
                cls_concentration.append(conc)

            total += token_ids.size(0)

    results = {}
    for layer_idx, entropies in all_layer_entropies.items():
        results[f"layer_{layer_idx}_mean_entropy"] = round(float(np.mean(entropies)), 4)
    results["cls_concentration_mean"] = round(float(np.mean(cls_concentration)), 4)
    results["n_samples"] = total

    _print_section("Attention Quality", results)
    return results


# ═════════════════════════════════════════════════════════════════════════════
# 9.  CALIBRATION (reliability of predicted probabilities)
# ═════════════════════════════════════════════════════════════════════════════

def evaluate_calibration(
    user_encoder: "UserEncoder",
    recommender: "RecommenderModel",
    dataset: "InteractionDataset",
    device: torch.device,
    n_bins: int = 10,
    val_fraction: float = 0.2,
) -> Dict:
    """
    Expected Calibration Error (ECE) for solve and helpful heads.

    ECE = Σ_b (|B_b| / n) * |acc(B_b) - conf(B_b)|

    A well-calibrated model: predicted probability ≈ actual accuracy in that bin.
    ECE < 0.05 is generally considered good.
    """
    logger.info("--- Evaluating Calibration ---")

    n_val = max(1, int(val_fraction * len(dataset)))
    n_train = len(dataset) - n_val
    _, val_ds = random_split(dataset, [n_train, n_val])
    loader = DataLoader(val_ds, batch_size=64, shuffle=False)

    solve_scores, solve_labels   = [], []
    helpful_scores, helpful_labels = [], []

    user_encoder.eval()
    recommender.eval()

    with torch.no_grad():
        for batch in loader:
            pe = batch["problem_embedding"].to(device)
            he = batch["history_embeddings"].to(device)
            hd = batch["history_difficulties"].to(device)
            pm = batch["padding_mask"].to(device)
            sv = batch["skill_vec"].to(device)
            sl = batch["solve_label"]
            hl = batch["helpful_label"]
            hm = batch["helpful_mask"].cpu()

            user_emb = user_encoder(he, hd, sv, pm)
            preds    = recommender(user_emb, pe)

            solve_p  = preds["p_solve"].squeeze(-1).cpu()  # Already sigmoid'd
            help_p   = preds["p_helpful"].squeeze(-1).cpu()  # Already sigmoid'd

            solve_scores.append(solve_p)
            solve_labels.append(sl)
            helpful_scores.append(help_p[hm])
            helpful_labels.append(hl[hm])

    def compute_ece(scores: np.ndarray, labels: np.ndarray, n_bins: int) -> Tuple[float, List]:
        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        bin_data = []
        for i in range(n_bins):
            in_bin = (scores >= bins[i]) & (scores < bins[i + 1])
            n_in = in_bin.sum()
            if n_in == 0:
                bin_data.append({"bin": f"{bins[i]:.1f}-{bins[i+1]:.1f}", "n": 0,
                                  "confidence": 0.0, "accuracy": 0.0, "gap": 0.0})
                continue
            conf = scores[in_bin].mean()
            acc  = labels[in_bin].mean()
            ece += (n_in / len(scores)) * abs(conf - acc)
            bin_data.append({
                "bin": f"{bins[i]:.1f}-{bins[i+1]:.1f}",
                "n": int(n_in),
                "confidence": round(float(conf), 4),
                "accuracy": round(float(acc), 4),
                "gap": round(float(abs(conf - acc)), 4),
            })
        return ece, bin_data

    sc = torch.cat(solve_scores).numpy()
    sl = torch.cat(solve_labels).numpy()
    solve_ece, solve_bins = compute_ece(sc, sl, n_bins)

    hc = torch.cat(helpful_scores).numpy() if helpful_scores and any(len(t) > 0 for t in helpful_scores) else np.array([])
    hl_arr = torch.cat(helpful_labels).numpy() if helpful_labels and any(len(t) > 0 for t in helpful_labels) else np.array([])

    helpful_ece = 0.0
    helpful_bins = []
    if len(hc) > 0:
        helpful_ece, helpful_bins = compute_ece(hc, hl_arr, n_bins)

    results = {
        "solve_ece"        : round(float(solve_ece), 5),
        "helpful_ece"      : round(float(helpful_ece), 5),
        "solve_bins"       : solve_bins,
        "helpful_bins"     : helpful_bins,
        "calibration_rating": (
            "Excellent (ECE < 0.05)" if solve_ece < 0.05 else
            "Good (ECE < 0.10)" if solve_ece < 0.10 else
            "Fair (ECE < 0.15)" if solve_ece < 0.15 else
            "Poor (ECE >= 0.15)"
        ),
    }

    _print_section("Calibration (ECE)", {
        "solve_ece": results["solve_ece"],
        "helpful_ece": results["helpful_ece"],
        "calibration_rating": results["calibration_rating"],
    })
    return results


# ═════════════════════════════════════════════════════════════════════════════
# 10.  SUMMARY REPORT
# ═════════════════════════════════════════════════════════════════════════════

def _print_section(title: str, data: Dict):
    print(f"\n{'='*60}")
    print(f"  {title.upper()}")
    print(f"{'='*60}")
    def _fmt(v, indent=2):
        pad = " " * indent
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if isinstance(v2, (dict, list)):
                    print(f"{pad}{k2}:")
                    _fmt(v2, indent + 2)
                else:
                    print(f"{pad}{k2:35s}: {v2}")
        elif isinstance(v, list):
            for item in v[:10]:
                print(f"{pad}{item}")
    _fmt(data)


def save_full_report(all_results: Dict, output_dir: str):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    report_path = str(Path(output_dir) / "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    logger.info("Full evaluation report saved → %s", report_path)
    return report_path


def print_summary_table(all_results: Dict):
    """Print a compact summary table of all key metrics."""
    print("\n" + "=" * 70)
    print("  FINAL EVALUATION SUMMARY")
    print("=" * 70)
    fmt = "  {:<40s}  {:>12s}"
    print(fmt.format("Metric", "Value"))
    print("  " + "-" * 66)

    def _row(label, value, unit=""):
        if isinstance(value, float):
            if math.isnan(value):
                print(fmt.format(label, "N/A"))
            else:
                print(fmt.format(label, f"{value:.4f}{unit}"))
        else:
            print(fmt.format(label, str(value)))

    enc = all_results.get("encoder_metrics", {})
    _row("Cluster Purity (NN)", enc.get("cluster_purity_nn", float("nan")))
    _row("Embedding Alignment Loss", enc.get("alignment_loss", float("nan")))
    _row("Embedding Uniformity", enc.get("uniformity_loss", float("nan")))
    _row("Contrastive Loss", enc.get("contrastive_loss", float("nan")))

    cls = all_results.get("classification_metrics", {})
    _row("Solve Accuracy", cls.get("solve_accuracy", float("nan")))
    _row("Solve AUC", cls.get("solve_auc", float("nan")))
    _row("Solve F1", cls.get("solve_f1", float("nan")))
    _row("Solve Brier Score", cls.get("solve_brier_score", float("nan")))
    _row("Helpful Accuracy", cls.get("helpful_accuracy", float("nan")))
    _row("Helpful AUC", cls.get("helpful_auc", float("nan")))
    _row("Difficulty Accuracy", cls.get("difficulty_accuracy", float("nan")))

    rnk = all_results.get("ranking_metrics", {})
    for k in [5, 10, 20]:
        _row(f"NDCG@{k}", rnk.get(f"NDCG@{k}", float("nan")))
    _row("MRR", rnk.get("MRR", float("nan")))

    calib = all_results.get("calibration", {})
    _row("Solve ECE", calib.get("solve_ece", float("nan")))
    _row("Calibration Rating", calib.get("calibration_rating", "N/A"))

    lat = all_results.get("latency", {})
    if 100 in lat:
        _row("Total Latency @100 problems", lat[100].get("total_ms", float("nan")), " ms")
        _row("Throughput @100 problems", lat[100].get("throughput_per_s", float("nan")), " probs/s")

    sz = all_results.get("model_size", {})
    _row("Total Parameters", sz.get("total_params_M", float("nan")), "M")
    _row("Model Size (FP32)", sz.get("total_size_fp32_mb", float("nan")), " MB")

    print("=" * 70)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Evaluate DL Recommendation System")
    parser.add_argument("--checkpoint_dir", default="checkpoints/dl_recommender",
                        help="Path to trained checkpoint directory")
    parser.add_argument("--excel_path", default="../dataset/LeetCode Questions.xlsx")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--n_eval_users", type=int, default=50,
                        help="Number of synthetic users for ranking eval")
    parser.add_argument("--output_dir", default="eval_results/")
    parser.add_argument("--mock", action="store_true",
                        help="Force mock models (skip checkpoint loading)")
    args = parser.parse_args()

    device = torch.device(args.device)
    logger.info("Running evaluation on device: %s", device)

    # ── Load models ────────────────────────────────────────────────────────────
    use_mock = args.mock or not MODULES_AVAILABLE

    if not use_mock:
        try:
            tokenizer, problem_encoder, user_encoder, recommender, config = \
                load_models(args.checkpoint_dir, device)
        except FileNotFoundError as e:
            logger.warning("Checkpoint not found (%s). Falling back to mock models.", e)
            use_mock = True

    if use_mock:
        tokenizer, problem_encoder, user_encoder, recommender, config = \
            build_mock_models(device)
        if not MODULES_AVAILABLE:
            logger.error("Project modules not available and mock mode requires them too. "
                         "Please install dependencies and set PYTHONPATH correctly.")
            sys.exit(1)

    # ── Build datasets ─────────────────────────────────────────────────────────
    logger.info("Building evaluation datasets...")

    # Minimal synthetic corpus if Excel not found
    if Path(args.excel_path).exists():
        from services.training.dataset import load_problems_from_excel
        problems = load_problems_from_excel(args.excel_path)
        algo_problems = [p for p in problems if p.category in ("Algorithms", None)]
    else:
        logger.warning("Excel file not found. Using tiny synthetic problem set.")
        from services.training.dataset import ProblemRecord
        from services.transformer.tokenizer import SimpleTokenizer as ST
        algo_problems = [
            ProblemRecord(f"lc-{i}", f"Problem {i}", ["easy","medium","hard"][i%3],
                          [["array","hash-table"],["dynamic-programming"],["graph","depth-first-search"]][i%3])
            for i in range(1, 201)
        ]
        tokenizer = ST(vocab_size=512)
        tokenizer.fit([f"{p.title} {' '.join(p.topics)}" for p in algo_problems])

    problem_dataset = ProblemContentDataset(
        algo_problems, tokenizer,
        max_len=config["max_len"],
    )
    interactions = generate_synthetic_interactions(
        algo_problems,
        n_users=max(50, args.n_eval_users),
        interactions_per_user=30,
        embed_dim=config["embed_dim"],
        seed=999,  # different seed from training for fair eval
    )
    interaction_dataset = InteractionDataset(
        interactions,
        embed_dim=config["embed_dim"],
        max_history=config["max_history"],
    )

    all_results = {}

    # ── Run evaluations ────────────────────────────────────────────────────────
    all_results["encoder_metrics"] = evaluate_problem_encoder(
        problem_encoder, problem_dataset, device, max_samples=500,
    )

    all_results["classification_metrics"] = evaluate_recommender_classification(
        user_encoder, recommender, interaction_dataset, device,
    )

    all_results["ranking_metrics"] = evaluate_ranking(
        user_encoder, recommender, interaction_dataset, device,
        n_users=args.n_eval_users,
    )

    all_results["calibration"] = evaluate_calibration(
        user_encoder, recommender, interaction_dataset, device,
    )

    all_results["latency"] = benchmark_inference_latency(
        problem_encoder, user_encoder, recommender, device,
        embed_dim=config["embed_dim"],
        max_history=config["max_history"],
    )

    all_results["model_size"] = analyze_model_size(
        problem_encoder, user_encoder, recommender,
    )

    all_results["attention_quality"] = evaluate_attention_quality(
        problem_encoder, problem_dataset, device, n_samples=200,
    )

    # ── Summary ────────────────────────────────────────────────────────────────
    print_summary_table(all_results)

    report_path = save_full_report(all_results, args.output_dir)
    logger.info("✅  Evaluation complete! Report: %s", report_path)
    return all_results


if __name__ == "__main__":
    main()
