"""
Training pipeline for the deep recommendation system.

Stages:
    1. Pre-train problem encoder with contrastive learning on Excel dataset
    2. Train full recommendation model on interaction data
    3. Fine-tune with real feedback from DB

Self-implemented:
    - Training loop with manual forward/backward
    - Gradient clipping
    - Checkpoint saving/loading
    - Metrics tracking
    - Curriculum learning integration
"""

import os
import json
import time
import logging
import math
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

from services.transformer.tokenizer import SimpleTokenizer
from services.transformer.encoder import ProblemEncoder
from services.recommender.user_encoder import UserEncoder
from services.recommender.recommender_model import RecommenderModel
from services.recommender.loss import MultiTaskLoss, ContrastiveLoss, CurriculumScheduler
from services.recommender.problem_encoder import ProblemBankEncoder
from services.training.dataset import (
    ProblemContentDataset,
    InteractionDataset,
    load_problems_from_excel,
    generate_synthetic_interactions,
)
from services.training.optimizer import TorchAdamWrapper, WarmupCosineScheduler

logger = logging.getLogger(__name__)

# ── Default hyperparameters ────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    # Model architecture
    "vocab_size": 4096,
    "d_model": 128,
    "embed_dim": 64,
    "num_heads": 4,
    "num_encoder_layers": 3,
    "d_ff": 512,
    "max_len": 64,
    "dropout": 0.1,
    "hidden_dim": 256,
    "num_residual_blocks": 3,
    "max_history": 32,
    # Training
    "pretrain_epochs": 10,
    "train_epochs": 30,
    "batch_size": 32,
    "lr": 3e-4,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    "warmup_ratio": 0.1,
    # Loss weights
    "w_solve": 0.4,
    "w_helpful": 0.3,
    "w_difficulty": 0.3,
    "w_contrastive": 0.1,
    # Curriculum
    "curriculum_warmup_epochs": 3,
    "curriculum_medium_start": 8,
    "curriculum_hard_start": 15,
    # Paths
    "checkpoint_dir": "checkpoints/dl_recommender",
    "excel_path": "../dataset/LeetCode Questions.xlsx",
}


# ── Metrics tracker ────────────────────────────────────────────────────────────

class MetricsTracker:
    """Tracks training metrics across epochs."""

    def __init__(self):
        self.history: Dict[str, List[float]] = {}
        self._current: Dict[str, List[float]] = {}

    def update(self, **kwargs):
        for k, v in kwargs.items():
            self._current.setdefault(k, []).append(float(v))

    def epoch_end(self) -> Dict[str, float]:
        epoch_metrics = {}
        for k, vals in self._current.items():
            avg = sum(vals) / len(vals)
            epoch_metrics[k] = avg
            self.history.setdefault(k, []).append(avg)
        self._current = {}
        return epoch_metrics

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.history, f, indent=2)


# ── Pre-training: problem encoder ─────────────────────────────────────────────

def pretrain_problem_encoder(
    encoder: ProblemEncoder,
    dataset: ProblemContentDataset,
    config: Dict,
    device: torch.device,
) -> ProblemEncoder:
    """
    Pre-train the problem encoder using contrastive learning.

    Objective: problems with the same topic cluster should have similar embeddings.
    Loss: InfoNCE / NT-Xent contrastive loss.
    """
    logger.info("=== Pre-training Problem Encoder ===")

    encoder = encoder.to(device)
    contrastive_loss = ContrastiveLoss(temperature=0.2)

    # Split train/val
    n_val = max(1, int(0.1 * len(dataset)))
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(
        train_ds,
        batch_size=config["batch_size"],
        shuffle=True,
        drop_last=True,
    )
    val_loader = DataLoader(val_ds, batch_size=config["batch_size"])

    optimizer = TorchAdamWrapper(
        encoder.parameters(),
        lr=config["lr"],
        weight_decay=config["weight_decay"],
    )

    total_steps = config["pretrain_epochs"] * len(train_loader)
    warmup_steps = int(total_steps * config["warmup_ratio"])
    scheduler = WarmupCosineScheduler(
        optimizer,
        warmup_steps=warmup_steps,
        total_steps=total_steps,
        lr_max=config["lr"],
        lr_min=config["lr"] * 0.01,
    )

    metrics = MetricsTracker()
    best_val_loss = float("inf")

    for epoch in range(config["pretrain_epochs"]):
        encoder.train()
        for batch in train_loader:
            token_ids = batch["token_ids"].to(device)
            topic_ids = batch["topic_ids"].to(device)
            diff_ids = batch["difficulty_id"].to(device)
            cluster_labels = batch["cluster_label"].to(device)

            optimizer.zero_grad()

            # Forward pass
            embeddings = encoder(token_ids, topic_ids, diff_ids, normalize=True)

            # Contrastive loss
            loss = contrastive_loss(embeddings, cluster_labels)

            # Skip NaN/zero loss batches
            if not torch.isfinite(loss) or loss.item() == 0.0:
                continue

            # Backward pass
            loss.backward()
            optimizer.clip_grad_norm(config["max_grad_norm"])
            optimizer.step()
            scheduler.step()

            metrics.update(pretrain_loss=loss.item())

        # Validation
        encoder.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                token_ids = batch["token_ids"].to(device)
                topic_ids = batch["topic_ids"].to(device)
                diff_ids = batch["difficulty_id"].to(device)
                cluster_labels = batch["cluster_label"].to(device)

                embeddings = encoder(token_ids, topic_ids, diff_ids, normalize=True)
                loss = contrastive_loss(embeddings, cluster_labels)
                if torch.isfinite(loss) and loss.item() > 0.0:
                    val_losses.append(loss.item())

        val_loss = sum(val_losses) / len(val_losses) if val_losses else float("inf")
        epoch_metrics = metrics.epoch_end()
        epoch_metrics["val_pretrain_loss"] = val_loss

        logger.info(
            "Pretrain Epoch %d/%d | train_loss=%.4f | val_loss=%.4f | lr=%.6f",
            epoch + 1,
            config["pretrain_epochs"],
            epoch_metrics.get("pretrain_loss", 0),
            val_loss,
            scheduler.get_lr(),
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            _save_checkpoint(encoder, optimizer, epoch, epoch_metrics, config, "pretrain_best")

    logger.info("Pre-training complete. Best val loss: %.4f", best_val_loss)
    return encoder


# ── Main training loop ─────────────────────────────────────────────────────────

def train_recommender(
    problem_encoder: ProblemEncoder,
    user_encoder: UserEncoder,
    recommender: RecommenderModel,
    dataset: InteractionDataset,
    config: Dict,
    device: torch.device,
) -> Dict:
    """
    Train the full recommendation model.

    Self-implemented training loop:
        for each epoch:
            for each batch:
                1. Forward pass through user encoder + recommender
                2. Compute multi-task loss
                3. Backward pass (loss.backward())
                4. Gradient clipping
                5. Optimizer step
                6. LR scheduler step
    """
    logger.info("=== Training Recommendation Model ===")

    user_encoder = user_encoder.to(device)
    recommender = recommender.to(device)

    # Freeze problem encoder (already pre-trained)
    for p in problem_encoder.parameters():
        p.requires_grad = False

    # Split train/val
    n_val = max(1, int(0.1 * len(dataset)))
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(
        train_ds,
        batch_size=config["batch_size"],
        shuffle=True,
        drop_last=False,
    )
    val_loader = DataLoader(val_ds, batch_size=config["batch_size"])

    # Combine parameters from user encoder + recommender
    all_params = list(user_encoder.parameters()) + list(recommender.parameters())
    optimizer = TorchAdamWrapper(
        all_params,
        lr=config["lr"],
        weight_decay=config["weight_decay"],
    )

    total_steps = config["train_epochs"] * len(train_loader)
    warmup_steps = int(total_steps * config["warmup_ratio"])
    scheduler = WarmupCosineScheduler(
        optimizer,
        warmup_steps=warmup_steps,
        total_steps=total_steps,
        lr_max=config["lr"],
        lr_min=config["lr"] * 0.01,
    )

    loss_fn = MultiTaskLoss(
        w_solve=config["w_solve"],
        w_helpful=config["w_helpful"],
        w_difficulty=config["w_difficulty"],
        label_smoothing=0.05,
    )

    curriculum = CurriculumScheduler(
        warmup_epochs=config["curriculum_warmup_epochs"],
        medium_start_epoch=config["curriculum_medium_start"],
        hard_start_epoch=config["curriculum_hard_start"],
    )

    metrics = MetricsTracker()
    best_val_loss = float("inf")
    training_history = []

    for epoch in range(config["train_epochs"]):
        user_encoder.train()
        recommender.train()

        for batch in train_loader:
            # Move to device
            prob_emb = batch["problem_embedding"].to(device)
            hist_emb = batch["history_embeddings"].to(device)
            hist_diff = batch["history_difficulties"].to(device)
            pad_mask = batch["padding_mask"].to(device)
            skill_vec = batch["skill_vec"].to(device)

            solve_label = batch["solve_label"].to(device)
            helpful_label = batch["helpful_label"].to(device)
            helpful_mask = batch["helpful_mask"].to(device)
            diff_label = batch["difficulty_label"].to(device)
            diff_mask = batch["difficulty_mask"].to(device)

            optimizer.zero_grad()

            # ── Forward pass ──────────────────────────────────────────────────

            # 1. Encode user
            user_emb = user_encoder(hist_emb, hist_diff, skill_vec, pad_mask)

            # 2. Recommend
            predictions = recommender(user_emb, prob_emb)

            # 3. Compute loss
            targets = {
                "solve": solve_label,
                "helpful": helpful_label,
                "difficulty": diff_label,
            }
            masks = {
                "helpful_mask": helpful_mask,
                "difficulty_mask": diff_mask,
            }

            total_loss, loss_dict = loss_fn(predictions, targets, masks)

            # ── Backward pass ─────────────────────────────────────────────────
            total_loss.backward()
            grad_norm = optimizer.clip_grad_norm(config["max_grad_norm"])
            optimizer.step()
            scheduler.step()

            metrics.update(
                train_loss=total_loss.item(),
                solve_loss=loss_dict["solve_loss"],
                helpful_loss=loss_dict["helpful_loss"],
                difficulty_loss=loss_dict["difficulty_loss"],
                grad_norm=grad_norm,
            )

        # ── Validation ────────────────────────────────────────────────────────
        val_metrics = _validate(user_encoder, recommender, loss_fn, val_loader, device)
        epoch_metrics = metrics.epoch_end()
        epoch_metrics.update(val_metrics)
        training_history.append(epoch_metrics)

        logger.info(
            "Epoch %d/%d | train=%.4f | val=%.4f | solve=%.4f | helpful=%.4f | diff=%.4f | lr=%.6f",
            epoch + 1,
            config["train_epochs"],
            epoch_metrics.get("train_loss", 0),
            epoch_metrics.get("val_loss", 0),
            epoch_metrics.get("solve_loss", 0),
            epoch_metrics.get("helpful_loss", 0),
            epoch_metrics.get("difficulty_loss", 0),
            scheduler.get_lr(),
        )

        # Save best checkpoint
        if epoch_metrics.get("val_loss", float("inf")) < best_val_loss:
            best_val_loss = epoch_metrics["val_loss"]
            _save_checkpoint(
                {"user_encoder": user_encoder, "recommender": recommender},
                optimizer,
                epoch,
                epoch_metrics,
                config,
                "best",
            )

        # Save periodic checkpoint
        if (epoch + 1) % 10 == 0:
            _save_checkpoint(
                {"user_encoder": user_encoder, "recommender": recommender},
                optimizer,
                epoch,
                epoch_metrics,
                config,
                f"epoch_{epoch+1}",
            )

    logger.info("Training complete. Best val loss: %.4f", best_val_loss)
    return {"history": training_history, "best_val_loss": best_val_loss}


def _validate(
    user_encoder: UserEncoder,
    recommender: RecommenderModel,
    loss_fn: MultiTaskLoss,
    val_loader: DataLoader,
    device: torch.device,
) -> Dict[str, float]:
    """Run validation loop and return metrics."""
    user_encoder.eval()
    recommender.eval()

    total_losses = []
    solve_accs = []

    with torch.no_grad():
        for batch in val_loader:
            prob_emb = batch["problem_embedding"].to(device)
            hist_emb = batch["history_embeddings"].to(device)
            hist_diff = batch["history_difficulties"].to(device)
            pad_mask = batch["padding_mask"].to(device)
            skill_vec = batch["skill_vec"].to(device)

            solve_label = batch["solve_label"].to(device)
            helpful_label = batch["helpful_label"].to(device)
            helpful_mask = batch["helpful_mask"].to(device)
            diff_label = batch["difficulty_label"].to(device)
            diff_mask = batch["difficulty_mask"].to(device)

            user_emb = user_encoder(hist_emb, hist_diff, skill_vec, pad_mask)
            predictions = recommender(user_emb, prob_emb)

            targets = {"solve": solve_label, "helpful": helpful_label, "difficulty": diff_label}
            masks = {"helpful_mask": helpful_mask, "difficulty_mask": diff_mask}

            total_loss, _ = loss_fn(predictions, targets, masks)
            total_losses.append(total_loss.item())

            # Solve accuracy
            pred_solve = (predictions["p_solve"].squeeze(-1) > 0.5).float()
            acc = (pred_solve == solve_label).float().mean().item()
            solve_accs.append(acc)

    return {
        "val_loss": sum(total_losses) / len(total_losses),
        "val_solve_acc": sum(solve_accs) / len(solve_accs),
    }


# ── Checkpoint utilities ───────────────────────────────────────────────────────

def _save_checkpoint(models, optimizer, epoch: int, metrics: Dict, config: Dict, tag: str):
    """Save model checkpoint."""
    ckpt_dir = Path(config["checkpoint_dir"])
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    path = ckpt_dir / f"checkpoint_{tag}.pt"

    if isinstance(models, dict):
        state_dicts = {k: v.state_dict() for k, v in models.items()}
    else:
        state_dicts = {"model": models.state_dict()}

    torch.save(
        {
            "epoch": epoch,
            "models": state_dicts,
            "optimizer": optimizer.state_dict(),
            "metrics": metrics,
            "config": config,
        },
        path,
    )
    logger.info("Checkpoint saved: %s", path)


def load_checkpoint(path: str, models: Dict[str, nn.Module], optimizer=None) -> Dict:
    """Load a checkpoint and restore model weights."""
    ckpt = torch.load(path, map_location="cpu")

    for name, model in models.items():
        if name in ckpt["models"]:
            model.load_state_dict(ckpt["models"][name])
            logger.info("Loaded weights for: %s", name)

    if optimizer is not None and "optimizer" in ckpt:
        optimizer.load_state_dict(ckpt["optimizer"])

    return ckpt


# ── Online learning (partial_fit) ─────────────────────────────────────────────

class OnlineLearner:
    """
    Supports real-time model updates from new user feedback.

    partial_fit() takes a single interaction and performs one gradient step.
    Uses a small replay buffer to prevent catastrophic forgetting.
    """

    def __init__(
        self,
        user_encoder: UserEncoder,
        recommender: RecommenderModel,
        config: Dict,
        device: torch.device,
        replay_buffer_size: int = 512,
    ):
        self.user_encoder = user_encoder.to(device)
        self.recommender = recommender.to(device)
        self.device = device
        self.config = config
        self.replay_buffer: List[Dict] = []
        self.replay_buffer_size = replay_buffer_size

        all_params = list(user_encoder.parameters()) + list(recommender.parameters())
        self.optimizer = TorchAdamWrapper(
            all_params,
            lr=config.get("online_lr", 1e-4),
            weight_decay=config.get("weight_decay", 0.01),
        )
        self.loss_fn = MultiTaskLoss(
            w_solve=config["w_solve"],
            w_helpful=config["w_helpful"],
            w_difficulty=config["w_difficulty"],
        )

    def partial_fit(self, sample: Dict) -> Dict[str, float]:
        """
        Perform one gradient step on a new interaction sample.

        Args:
            sample: dict with keys matching InteractionDataset.__getitem__

        Returns:
            loss_dict
        """
        # Add to replay buffer
        self.replay_buffer.append(sample)
        if len(self.replay_buffer) > self.replay_buffer_size:
            self.replay_buffer.pop(0)

        # Sample a mini-batch from replay buffer (+ current sample)
        batch_size = min(8, len(self.replay_buffer))
        replay_batch = random.sample(self.replay_buffer, batch_size)

        self.user_encoder.train()
        self.recommender.train()
        self.optimizer.zero_grad()

        total_loss_val = 0.0
        for s in replay_batch:
            prob_emb = s["problem_embedding"].unsqueeze(0).to(self.device)
            hist_emb = s["history_embeddings"].unsqueeze(0).to(self.device)
            hist_diff = s["history_difficulties"].unsqueeze(0).to(self.device)
            pad_mask = s["padding_mask"].unsqueeze(0).to(self.device)
            skill_vec = s["skill_vec"].unsqueeze(0).to(self.device)

            user_emb = self.user_encoder(hist_emb, hist_diff, skill_vec, pad_mask)
            predictions = self.recommender(user_emb, prob_emb)

            targets = {
                "solve": s["solve_label"].unsqueeze(0).to(self.device),
                "helpful": s["helpful_label"].unsqueeze(0).to(self.device),
                "difficulty": s["difficulty_label"].unsqueeze(0).to(self.device),
            }
            masks = {
                "helpful_mask": s["helpful_mask"].unsqueeze(0).to(self.device),
                "difficulty_mask": s["difficulty_mask"].unsqueeze(0).to(self.device),
            }

            loss, loss_dict = self.loss_fn(predictions, targets, masks)
            (loss / batch_size).backward()
            total_loss_val += loss.item()

        self.optimizer.clip_grad_norm(self.config["max_grad_norm"])
        self.optimizer.step()

        return {"online_loss": total_loss_val / batch_size}


# ── Full training entry point ──────────────────────────────────────────────────

def run_full_training(
    excel_path: Optional[str] = None,
    config: Optional[Dict] = None,
    db=None,
    device_str: str = "cpu",
) -> Dict:
    """
    End-to-end training pipeline.

    1. Load problems from Excel
    2. Build tokenizer
    3. Pre-train problem encoder (contrastive)
    4. Build problem embedding cache
    5. Load/generate interaction data
    6. Train recommendation model
    7. Save all weights

    Args:
        excel_path: path to LeetCode Questions.xlsx
        config: hyperparameter dict (defaults to DEFAULT_CONFIG)
        db: SQLAlchemy session (optional, for real interaction data)
        device_str: "cpu" or "cuda"

    Returns:
        training results dict
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    if excel_path:
        cfg["excel_path"] = excel_path

    device = torch.device(device_str if torch.cuda.is_available() or device_str == "cpu" else "cpu")
    logger.info("Training on device: %s", device)

    # ── 1. Load problems ───────────────────────────────────────────────────────
    problems = load_problems_from_excel(cfg["excel_path"])
    # Filter to Algorithms category only for recommendation
    algo_problems = [p for p in problems if p.category in ("Algorithms", None)]
    logger.info("Using %d algorithm problems.", len(algo_problems))

    # ── 2. Build tokenizer ─────────────────────────────────────────────────────
    corpus = [f"{p.title} {' '.join(p.topics)}" for p in algo_problems]
    tokenizer = SimpleTokenizer(vocab_size=cfg["vocab_size"])
    tokenizer.fit(corpus)
    logger.info("Tokenizer vocab size: %d", tokenizer.vocab_size_actual)

    # Save tokenizer
    ckpt_dir = Path(cfg["checkpoint_dir"])
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(ckpt_dir / "tokenizer.json"))

    # ── 3. Build models ────────────────────────────────────────────────────────
    problem_encoder = ProblemEncoder(
        vocab_size=tokenizer.vocab_size_actual,
        d_model=cfg["d_model"],
        embed_dim=cfg["embed_dim"],
        num_heads=cfg["num_heads"],
        num_layers=cfg["num_encoder_layers"],
        d_ff=cfg["d_ff"],
        max_len=cfg["max_len"],
        dropout=cfg["dropout"],
    )

    user_encoder = UserEncoder(
        embed_dim=cfg["embed_dim"],
        num_heads=cfg["num_heads"],
        num_layers=2,
        max_history=cfg["max_history"],
        dropout=cfg["dropout"],
    )

    recommender = RecommenderModel(
        embed_dim=cfg["embed_dim"],
        hidden_dim=cfg["hidden_dim"],
        num_residual_blocks=cfg["num_residual_blocks"],
        dropout=cfg["dropout"],
    )

    total_params = sum(p.numel() for p in problem_encoder.parameters()) + \
                   sum(p.numel() for p in user_encoder.parameters()) + \
                   sum(p.numel() for p in recommender.parameters())
    logger.info("Total parameters: %d (%.1fM)", total_params, total_params / 1e6)

    # ── 4. Pre-train problem encoder ───────────────────────────────────────────
    problem_dataset = ProblemContentDataset(
        algo_problems, tokenizer, max_len=cfg["max_len"]
    )
    problem_encoder = pretrain_problem_encoder(
        problem_encoder, problem_dataset, cfg, device
    )

    # ── 5. Build problem embedding cache ──────────────────────────────────────
    bank_encoder = ProblemBankEncoder(
        model=problem_encoder,
        tokenizer=tokenizer,
        device=device,
        max_len=cfg["max_len"],
    )
    bank_encoder.build_cache([p.to_dict() for p in algo_problems])

    # Save problem embeddings
    ids, embeddings = bank_encoder.get_all_embeddings()
    torch.save(
        {"ids": ids, "embeddings": embeddings},
        str(ckpt_dir / "problem_embeddings.pt"),
    )

    # ── 6. Load interaction data ───────────────────────────────────────────────
    if db is not None:
        from services.training.dataset import load_interactions_from_db
        interactions = load_interactions_from_db(db, bank_encoder, cfg["embed_dim"])

    if not db or not interactions:
        logger.info("Generating synthetic interaction data...")
        interactions = generate_synthetic_interactions(
            algo_problems,
            n_users=300,
            interactions_per_user=40,
            embed_dim=cfg["embed_dim"],
        )

    interaction_dataset = InteractionDataset(
        interactions,
        embed_dim=cfg["embed_dim"],
        max_history=cfg["max_history"],
    )

    # ── 7. Train recommendation model ─────────────────────────────────────────
    results = train_recommender(
        problem_encoder, user_encoder, recommender,
        interaction_dataset, cfg, device,
    )

    # ── 8. Save final weights ──────────────────────────────────────────────────
    torch.save(problem_encoder.state_dict(), str(ckpt_dir / "problem_encoder.pt"))
    torch.save(user_encoder.state_dict(), str(ckpt_dir / "user_encoder.pt"))
    torch.save(recommender.state_dict(), str(ckpt_dir / "recommender.pt"))

    # Save config
    with open(str(ckpt_dir / "config.json"), "w") as f:
        json.dump(cfg, f, indent=2)

    logger.info("All weights saved to %s", ckpt_dir)
    return results
