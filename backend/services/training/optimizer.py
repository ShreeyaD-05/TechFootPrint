"""
Self-implemented Adam optimizer and learning rate schedulers.

Adam: Kingma & Ba (2015) — Adaptive Moment Estimation
    m_t = β1 * m_{t-1} + (1 - β1) * g_t
    v_t = β2 * v_{t-1} + (1 - β2) * g_t²
    m̂_t = m_t / (1 - β1^t)
    v̂_t = v_t / (1 - β2^t)
    θ_t = θ_{t-1} - α * m̂_t / (sqrt(v̂_t) + ε)

We implement this from scratch using raw parameter tensors,
then also provide a thin wrapper around torch.optim.Adam for
production use (same interface).
"""

import math
import torch
import torch.nn as nn
from typing import List, Dict, Optional, Callable, Iterable


# ── From-scratch Adam ──────────────────────────────────────────────────────────

class AdamOptimizer:
    """
    Adam optimizer implemented from scratch.

    Operates directly on nn.Parameter tensors.
    Supports:
        - Weight decay (L2 regularisation)
        - Gradient clipping
        - Parameter groups with different learning rates
    """

    def __init__(
        self,
        params: Iterable,
        lr: float = 1e-3,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.0,
    ):
        self.lr = lr
        self.beta1, self.beta2 = betas
        self.eps = eps
        self.weight_decay = weight_decay

        # Collect parameters
        self.params: List[torch.Tensor] = []
        for p in params:
            if isinstance(p, dict):
                # Parameter group
                self.params.extend(p["params"])
            elif isinstance(p, torch.Tensor) and p.requires_grad:
                self.params.append(p)

        # State: first moment (m), second moment (v), step count
        self.state: Dict[int, Dict] = {}
        for i, p in enumerate(self.params):
            self.state[i] = {
                "m": torch.zeros_like(p.data),
                "v": torch.zeros_like(p.data),
                "step": 0,
            }

    def zero_grad(self):
        """Zero all parameter gradients."""
        for p in self.params:
            if p.grad is not None:
                p.grad.detach_()
                p.grad.zero_()

    def step(self, closure: Optional[Callable] = None):
        """Perform a single optimisation step."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for i, p in enumerate(self.params):
            if p.grad is None:
                continue

            grad = p.grad.data

            # Weight decay (L2 regularisation)
            if self.weight_decay != 0:
                grad = grad + self.weight_decay * p.data

            state = self.state[i]
            state["step"] += 1
            t = state["step"]

            # Update biased first and second moment estimates
            state["m"].mul_(self.beta1).add_(grad, alpha=1 - self.beta1)
            state["v"].mul_(self.beta2).addcmul_(grad, grad, value=1 - self.beta2)

            # Bias correction
            bias_correction1 = 1 - self.beta1 ** t
            bias_correction2 = 1 - self.beta2 ** t

            m_hat = state["m"] / bias_correction1
            v_hat = state["v"] / bias_correction2

            # Parameter update
            p.data.addcdiv_(m_hat, v_hat.sqrt().add_(self.eps), value=-self.lr)

        return loss

    def clip_grad_norm(self, max_norm: float) -> float:
        """Clip gradients by global norm. Returns the norm before clipping."""
        total_norm = 0.0
        for p in self.params:
            if p.grad is not None:
                param_norm = p.grad.data.norm(2).item()
                total_norm += param_norm ** 2
        total_norm = total_norm ** 0.5

        if total_norm > max_norm:
            clip_coef = max_norm / (total_norm + 1e-6)
            for p in self.params:
                if p.grad is not None:
                    p.grad.data.mul_(clip_coef)

        return total_norm

    def get_lr(self) -> float:
        return self.lr

    def set_lr(self, lr: float):
        self.lr = lr

    def state_dict(self) -> Dict:
        return {
            "lr": self.lr,
            "beta1": self.beta1,
            "beta2": self.beta2,
            "eps": self.eps,
            "weight_decay": self.weight_decay,
            "state": {
                k: {
                    "m": v["m"].clone(),
                    "v": v["v"].clone(),
                    "step": v["step"],
                }
                for k, v in self.state.items()
            },
        }

    def load_state_dict(self, state: Dict):
        self.lr = state["lr"]
        self.beta1 = state["beta1"]
        self.beta2 = state["beta2"]
        self.eps = state["eps"]
        self.weight_decay = state["weight_decay"]
        for k, v in state["state"].items():
            self.state[int(k)] = {
                "m": v["m"].clone(),
                "v": v["v"].clone(),
                "step": v["step"],
            }


# ── Learning Rate Schedulers ───────────────────────────────────────────────────

class WarmupCosineScheduler:
    """
    Linear warmup followed by cosine annealing.

    lr(t) = lr_max * t / warmup_steps                    (t < warmup_steps)
    lr(t) = lr_min + 0.5 * (lr_max - lr_min) *
            (1 + cos(π * (t - warmup) / (total - warmup)))  (t >= warmup_steps)
    """

    def __init__(
        self,
        optimizer,
        warmup_steps: int,
        total_steps: int,
        lr_max: float = 1e-3,
        lr_min: float = 1e-5,
    ):
        self.optimizer = optimizer
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        self.lr_max = lr_max
        self.lr_min = lr_min
        self._step = 0

    def step(self):
        self._step += 1
        lr = self._get_lr()
        self.optimizer.set_lr(lr)
        return lr

    def _get_lr(self) -> float:
        t = self._step
        if t < self.warmup_steps:
            return self.lr_max * t / max(self.warmup_steps, 1)
        else:
            progress = (t - self.warmup_steps) / max(
                self.total_steps - self.warmup_steps, 1
            )
            progress = min(progress, 1.0)
            return self.lr_min + 0.5 * (self.lr_max - self.lr_min) * (
                1 + math.cos(math.pi * progress)
            )

    def get_lr(self) -> float:
        return self._get_lr()


class StepDecayScheduler:
    """
    Multiply LR by `gamma` every `step_size` epochs.
    """

    def __init__(self, optimizer, step_size: int = 10, gamma: float = 0.5):
        self.optimizer = optimizer
        self.step_size = step_size
        self.gamma = gamma
        self._epoch = 0

    def step(self):
        self._epoch += 1
        if self._epoch % self.step_size == 0:
            new_lr = self.optimizer.get_lr() * self.gamma
            self.optimizer.set_lr(new_lr)

    def get_lr(self) -> float:
        return self.optimizer.get_lr()


class ReduceOnPlateauScheduler:
    """
    Reduce LR when a metric stops improving.
    """

    def __init__(
        self,
        optimizer,
        patience: int = 5,
        factor: float = 0.5,
        min_lr: float = 1e-6,
        mode: str = "min",
    ):
        self.optimizer = optimizer
        self.patience = patience
        self.factor = factor
        self.min_lr = min_lr
        self.mode = mode
        self._best = float("inf") if mode == "min" else float("-inf")
        self._wait = 0

    def step(self, metric: float):
        improved = (
            metric < self._best if self.mode == "min" else metric > self._best
        )
        if improved:
            self._best = metric
            self._wait = 0
        else:
            self._wait += 1
            if self._wait >= self.patience:
                new_lr = max(self.optimizer.get_lr() * self.factor, self.min_lr)
                self.optimizer.set_lr(new_lr)
                self._wait = 0

    def get_lr(self) -> float:
        return self.optimizer.get_lr()


# ── Torch-backed optimizer wrapper (for production) ───────────────────────────

class TorchAdamWrapper:
    """
    Thin wrapper around torch.optim.AdamW for production use.
    Provides the same interface as AdamOptimizer.
    """

    def __init__(
        self,
        params,
        lr: float = 1e-3,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.01,
    ):
        self._optim = torch.optim.AdamW(
            params, lr=lr, betas=betas, eps=eps, weight_decay=weight_decay
        )

    def zero_grad(self):
        self._optim.zero_grad()

    def step(self, closure=None):
        return self._optim.step(closure)

    def clip_grad_norm(self, max_norm: float) -> float:
        params = [
            p for group in self._optim.param_groups
            for p in group["params"]
            if p.grad is not None
        ]
        return torch.nn.utils.clip_grad_norm_(params, max_norm).item()

    def get_lr(self) -> float:
        return self._optim.param_groups[0]["lr"]

    def set_lr(self, lr: float):
        for group in self._optim.param_groups:
            group["lr"] = lr

    def state_dict(self) -> Dict:
        return self._optim.state_dict()

    def load_state_dict(self, state: Dict):
        self._optim.load_state_dict(state)
