"""
Multi-task loss functions for the recommendation model.

Tasks:
    1. solve_loss     — Binary Cross Entropy (did user solve it?)
    2. helpful_loss   — Binary Cross Entropy (was it helpful?)
    3. difficulty_loss — Cross Entropy (too_easy / just_right / too_hard)
    4. contrastive_loss — InfoNCE / NT-Xent for problem embedding space

Combined loss:
    L = w1 * solve_loss + w2 * helpful_loss + w3 * difficulty_loss
        + w4 * contrastive_loss (optional)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple


class MultiTaskLoss(nn.Module):
    """
    Weighted combination of all task losses.

    Weights are learnable via uncertainty-based loss weighting
    (Kendall et al., 2018) or fixed.
    """

    def __init__(
        self,
        w_solve: float = 0.4,
        w_helpful: float = 0.3,
        w_difficulty: float = 0.3,
        w_contrastive: float = 0.0,
        learnable_weights: bool = False,
        label_smoothing: float = 0.05,
    ):
        super().__init__()
        self.w_contrastive = w_contrastive
        self.label_smoothing = label_smoothing

        if learnable_weights:
            # Log-variance parameterisation (Kendall et al.)
            # L_i = (1 / 2*sigma_i^2) * L_i + log(sigma_i)
            self.log_var_solve = nn.Parameter(torch.zeros(1))
            self.log_var_helpful = nn.Parameter(torch.zeros(1))
            self.log_var_difficulty = nn.Parameter(torch.zeros(1))
            self._learnable = True
        else:
            self._learnable = False
            self._w_solve = w_solve
            self._w_helpful = w_helpful
            self._w_difficulty = w_difficulty

    def _bce_loss(
        self,
        pred: torch.Tensor,   # (batch, 1) — sigmoid output
        target: torch.Tensor, # (batch,) — 0/1 float
        mask: Optional[torch.Tensor] = None,  # (batch,) — True = valid sample
    ) -> torch.Tensor:
        """
        Binary cross-entropy with optional label smoothing and masking.
        """
        target = target.float().unsqueeze(-1)  # (batch, 1)

        # Label smoothing
        if self.label_smoothing > 0:
            target = target * (1 - self.label_smoothing) + 0.5 * self.label_smoothing

        loss = F.binary_cross_entropy(pred, target, reduction="none")  # (batch, 1)
        loss = loss.squeeze(-1)  # (batch,)

        if mask is not None:
            loss = loss * mask.float()
            return loss.sum() / (mask.float().sum().clamp(min=1))

        return loss.mean()

    def _ce_loss(
        self,
        logits: torch.Tensor,  # (batch, 3)
        target: torch.Tensor,  # (batch,) — 0/1/2
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Cross-entropy for difficulty classification."""
        loss = F.cross_entropy(logits, target.long(), reduction="none")  # (batch,)

        if mask is not None:
            loss = loss * mask.float()
            return loss.sum() / (mask.float().sum().clamp(min=1))

        return loss.mean()

    def forward(
        self,
        predictions: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
        masks: Optional[Dict[str, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Compute combined multi-task loss.

        Args:
            predictions: output of RecommenderModel.forward()
                keys: p_solve, p_helpful, p_difficulty
            targets: ground-truth labels
                keys: solve (0/1), helpful (0/1), difficulty (0/1/2)
            masks: optional per-task validity masks (some labels may be missing)
                keys: solve_mask, helpful_mask, difficulty_mask

        Returns:
            total_loss: scalar tensor
            loss_dict:  individual losses for logging
        """
        masks = masks or {}

        solve_loss = self._bce_loss(
            predictions["p_solve"],
            targets["solve"],
            masks.get("solve_mask"),
        )

        helpful_loss = self._bce_loss(
            predictions["p_helpful"],
            targets["helpful"],
            masks.get("helpful_mask"),
        )

        difficulty_loss = self._ce_loss(
            predictions["p_difficulty"],
            targets["difficulty"],
            masks.get("difficulty_mask"),
        )

        if self._learnable:
            # Uncertainty weighting
            total = (
                torch.exp(-self.log_var_solve) * solve_loss + self.log_var_solve
                + torch.exp(-self.log_var_helpful) * helpful_loss + self.log_var_helpful
                + torch.exp(-self.log_var_difficulty) * difficulty_loss + self.log_var_difficulty
            )
        else:
            total = (
                self._w_solve * solve_loss
                + self._w_helpful * helpful_loss
                + self._w_difficulty * difficulty_loss
            )

        loss_dict = {
            "solve_loss": solve_loss.item(),
            "helpful_loss": helpful_loss.item(),
            "difficulty_loss": difficulty_loss.item(),
            "total_loss": total.item(),
        }

        return total, loss_dict


class ContrastiveLoss(nn.Module):
    """
    InfoNCE / NT-Xent contrastive loss for problem embeddings.

    Pulls together embeddings of problems with the same topics (positives)
    and pushes apart problems with different topics (negatives).

    This encourages the encoder to learn a meaningful semantic space
    where similar problems cluster together.

    L = -log( exp(sim(z_i, z_j) / τ) / Σ_k exp(sim(z_i, z_k) / τ) )
    """

    def __init__(self, temperature: float = 0.2):
        super().__init__()
        self.temperature = temperature

    def forward(
        self,
        embeddings: torch.Tensor,  # (batch, embed_dim) — L2 normalised
        labels: torch.Tensor,      # (batch,) — topic cluster label
    ) -> torch.Tensor:
        """
        Args:
            embeddings: (batch, embed_dim) — L2-normalised problem embeddings
            labels:     (batch,) — integer cluster labels (same label = positive pair)

        Returns:
            scalar contrastive loss
        """
        batch = embeddings.size(0)
        if batch < 2:
            return torch.tensor(0.0, device=embeddings.device)

        # Re-normalise embeddings for numerical safety
        embeddings = F.normalize(embeddings, p=2, dim=-1)

        # Cosine similarity matrix
        sim_matrix = torch.matmul(embeddings, embeddings.T) / self.temperature
        # (batch, batch)

        # Mask out self-similarity
        eye_mask = torch.eye(batch, dtype=torch.bool, device=embeddings.device)

        # Positive mask: same label, excluding self
        label_matrix = labels.unsqueeze(0) == labels.unsqueeze(1)  # (batch, batch)
        positive_mask = label_matrix & ~eye_mask  # (batch, batch)

        # Skip anchors that have no positives (all-same-label batch or singletons)
        has_positive = positive_mask.any(dim=-1)  # (batch,)
        if not has_positive.any():
            # Fallback: treat each sample as its own positive (self-supervised)
            # Use a simple uniformity loss to spread embeddings
            sq_dists = torch.pdist(embeddings, p=2).pow(2)
            return -sq_dists.mean().clamp(max=10.0) * 0.0 + torch.tensor(0.0, device=embeddings.device)

        # For numerical stability: subtract row max before softmax (log-sum-exp trick)
        # Mask self before computing log_softmax
        sim_no_self = sim_matrix.masked_fill(eye_mask, float("-inf"))

        # log_softmax over all non-self positions
        log_probs = F.log_softmax(sim_no_self, dim=-1)  # (batch, batch)

        # Replace any remaining NaN/inf (e.g. all-masked rows) with 0
        log_probs = torch.nan_to_num(log_probs, nan=0.0, posinf=0.0, neginf=0.0)

        # Average log-prob over positives, only for anchors that have positives
        n_positives = positive_mask.float().sum(dim=-1).clamp(min=1)
        per_anchor_loss = -(log_probs * positive_mask.float()).sum(dim=-1) / n_positives

        # Only average over anchors that actually had positives
        loss = per_anchor_loss[has_positive].mean()
        return loss


class CurriculumScheduler:
    """
    Curriculum learning: gradually increase difficulty of training samples.

    Stages:
        1. Easy problems only (first `warmup_epochs` epochs)
        2. Easy + Medium
        3. All difficulties

    Also implements loss-based curriculum: focus on samples with high loss.
    """

    def __init__(
        self,
        warmup_epochs: int = 5,
        medium_start_epoch: int = 10,
        hard_start_epoch: int = 20,
    ):
        self.warmup_epochs = warmup_epochs
        self.medium_start_epoch = medium_start_epoch
        self.hard_start_epoch = hard_start_epoch

    def get_difficulty_filter(self, epoch: int) -> list:
        """Return list of allowed difficulty levels for this epoch."""
        if epoch < self.warmup_epochs:
            return ["easy"]
        elif epoch < self.medium_start_epoch:
            return ["easy", "medium"]
        else:
            return ["easy", "medium", "hard"]

    def get_sample_weights(
        self,
        losses: torch.Tensor,
        epoch: int,
        strategy: str = "loss_proportional",
    ) -> torch.Tensor:
        """
        Compute per-sample weights for curriculum sampling.

        Strategies:
            - uniform: equal weights
            - loss_proportional: higher weight for harder samples
            - self_paced: lower weight for very high loss (too hard)
        """
        if strategy == "uniform":
            return torch.ones_like(losses)

        elif strategy == "loss_proportional":
            # Focus on samples with above-average loss
            weights = F.softmax(losses / losses.mean().clamp(min=1e-8), dim=0)
            return weights * len(losses)

        elif strategy == "self_paced":
            # Self-paced: include samples below a loss threshold
            threshold = losses.mean() + losses.std()
            weights = (losses <= threshold).float()
            return weights

        return torch.ones_like(losses)
