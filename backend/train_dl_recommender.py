"""
Standalone training script for the DL recommendation system.

Run from backend/ directory:
    python train_dl_recommender.py

Trains on the LeetCode Questions.xlsx dataset using synthetic interaction
data (no DB required). Saves all weights to checkpoints/dl_recommender/.
"""

import sys
import os
import logging

# Make sure backend/ is on the path
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_dl_recommender")

from services.training.train import run_full_training, DEFAULT_CONFIG

if __name__ == "__main__":
    config = {
        **DEFAULT_CONFIG,
        # ── Architecture (lightweight for CPU) ─────────────────────────────
        "vocab_size":           4096,
        "d_model":              128,
        "embed_dim":            64,
        "num_heads":            4,
        "num_encoder_layers":   3,
        "d_ff":                 512,
        "max_len":              64,
        "dropout":              0.1,
        "hidden_dim":           256,
        "num_residual_blocks":  3,
        "max_history":          32,
        # ── Training schedule ──────────────────────────────────────────────
        "pretrain_epochs":      15,
        "train_epochs":         30,
        "batch_size":           64,
        "lr":                   3e-4,
        "weight_decay":         0.01,
        "max_grad_norm":        1.0,
        "warmup_ratio":         0.1,
        # ── Loss weights ───────────────────────────────────────────────────
        "w_solve":              0.4,
        "w_helpful":            0.3,
        "w_difficulty":         0.3,
        "w_contrastive":        0.1,
        # ── Curriculum ─────────────────────────────────────────────────────
        "curriculum_warmup_epochs":  3,
        "curriculum_medium_start":   8,
        "curriculum_hard_start":     15,
        # ── Paths ──────────────────────────────────────────────────────────
        "checkpoint_dir":       "checkpoints/dl_recommender",
        "excel_path":           "../dataset/LeetCode Questions.xlsx",
    }

    logger.info("Starting DL Recommender training...")
    logger.info("Config: pretrain=%d epochs, train=%d epochs, batch=%d, lr=%g",
                config["pretrain_epochs"], config["train_epochs"],
                config["batch_size"], config["lr"])

    results = run_full_training(
        excel_path=config["excel_path"],
        config=config,
        db=None,           # no DB — uses synthetic interaction data
        device_str="cpu",
    )

    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info("Best validation loss: %.4f", results.get("best_val_loss", 0))
    logger.info("Checkpoints saved to: %s", config["checkpoint_dir"])
    logger.info("=" * 60)
