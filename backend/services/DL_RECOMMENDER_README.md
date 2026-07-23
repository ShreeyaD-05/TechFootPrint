# Deep Learning Recommendation System

A self-implemented Transformer-based recommendation system for coding practice problems, built from scratch without high-level training frameworks.

## 🎯 Overview

This system replaces the rule-based recommendation engine with a deep learning approach that:
- **Understands problem content** using a mini Transformer encoder
- **Learns user skill representations** from interaction history
- **Predicts multiple signals** (solve probability, helpfulness, difficulty match)
- **Explores intelligently** using epsilon-greedy and UCB strategies
- **Explains recommendations** with human-readable reasoning

## 📦 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PROBLEM ENCODER                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Input: title + description + tags                    │  │
│  │   ↓                                                   │  │
│  │ BPE Tokenizer → Token Embeddings                     │  │
│  │   ↓                                                   │  │
│  │ Positional Encoding + Tag Embeddings                 │  │
│  │   ↓                                                   │  │
│  │ 3× Transformer Encoder Layers                        │  │
│  │   (Multi-Head Self-Attention + FFN)                  │  │
│  │   ↓                                                   │  │
│  │ [CLS] Token → Problem Embedding (64-dim)             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     USER ENCODER                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Sequential Encoder (Transformer over history)        │  │
│  │   [USER] + solved problem embeddings                 │  │
│  │   ↓                                                   │  │
│  │   2× Transformer Layers                              │  │
│  │   ↓                                                   │  │
│  │   [USER] token → sequence embedding                  │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Skill Profile Encoder (MLP)                          │  │
│  │   topic counts + difficulty distribution             │  │
│  │   ↓                                                   │  │
│  │   skill embedding                                    │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Gated Fusion                                         │  │
│  │   gate = σ(W [seq_emb; skill_emb])                  │  │
│  │   user_emb = gate * seq + (1-gate) * skill          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  RECOMMENDATION MODEL                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Interaction Layer                                    │  │
│  │   [user_emb; problem_emb; user⊙problem; |user-prob|]│  │
│  │   ↓                                                   │  │
│  │ 3× Residual MLP Blocks                               │  │
│  │   ↓                                                   │  │
│  │ Multi-Task Heads:                                    │  │
│  │   • p_solve      (binary)                            │  │
│  │   • p_helpful    (binary)                            │  │
│  │   • p_difficulty (3-class: too_easy/just_right/hard) │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🧠 Self-Implemented Components

### Transformer Internals
- **Tokenizer** (`tokenizer.py`): BPE-inspired subword tokenizer from scratch
- **Embeddings** (`embeddings.py`): Token, positional (sinusoidal + learnable), tag embeddings
- **Attention** (`attention.py`): Scaled dot-product attention, multi-head attention, FFN
- **Encoder** (`encoder.py`): Full Transformer encoder stack with layer norm

### Training Pipeline
- **Optimizer** (`optimizer.py`): Adam from scratch with gradient clipping
- **Loss** (`loss.py`): Multi-task loss (BCE + CE), contrastive loss (InfoNCE)
- **Scheduler** (`optimizer.py`): Warmup + cosine annealing, step decay, reduce-on-plateau
- **Curriculum** (`loss.py`): Difficulty-based curriculum learning

### Recommendation Logic
- **User Encoder** (`user_encoder.py`): Sequential + skill profile fusion
- **Problem Encoder** (`problem_encoder.py`): Caching layer for fast lookup
- **Recommender** (`recommender_model.py`): Multi-task prediction + exploration
- **Exploration** (`recommender_model.py`): Epsilon-greedy, UCB1

## 📂 File Structure

```
backend/services/
├── transformer/
│   ├── tokenizer.py          # BPE tokenizer (self-implemented)
│   ├── embeddings.py          # Token, positional, tag embeddings
│   ├── attention.py           # Multi-head attention + FFN
│   ├── encoder.py             # Transformer encoder
│   └── model.py               # Public API
├── recommender/
│   ├── user_encoder.py        # User representation learning
│   ├── problem_encoder.py     # Problem bank caching
│   ├── recommender_model.py   # Multi-task recommendation model
│   └── loss.py                # Multi-task + contrastive loss
├── training/
│   ├── dataset.py             # Data loaders (Excel + DB)
│   ├── optimizer.py           # Adam optimizer + schedulers
│   └── train.py               # Full training pipeline
└── inference/
    └── predict.py             # Production inference engine
```

## 🚀 Training

### 1. Install Dependencies

```bash
cd backend
pip install torch numpy openpyxl
```

### 2. Run Training

```bash
python -m services.training.train
```

This will:
1. Load problems from `dataset/LeetCode Questions.xlsx`
2. Build a BPE tokenizer (vocab size 4096)
3. Pre-train the problem encoder with contrastive learning (10 epochs)
4. Generate synthetic interaction data (300 users × 40 interactions)
5. Train the full recommendation model (30 epochs)
6. Save checkpoints to `checkpoints/dl_recommender/`

### 3. Training Configuration

Edit `DEFAULT_CONFIG` in `services/training/train.py`:

```python
DEFAULT_CONFIG = {
    # Model architecture
    "vocab_size": 4096,
    "d_model": 128,           # Transformer hidden size
    "embed_dim": 64,          # Final embedding dimension
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
}
```

### 4. Training with Real Data

To train on real user feedback from the database:

```python
from shared.database import SessionLocal
from services.training.train import run_full_training

db = SessionLocal()
results = run_full_training(
    excel_path="../dataset/LeetCode Questions.xlsx",
    db=db,
    device_str="cuda",  # or "cpu"
)
db.close()
```

## 🔮 Inference

### Load the Trained Model

```python
from services.inference.predict import DeepRecommenderEngine

engine = DeepRecommenderEngine.load(
    checkpoint_dir="checkpoints/dl_recommender",
    excel_path="../dataset/LeetCode Questions.xlsx",
    device_str="cpu",
)
```

### Generate Recommendations

```python
from services.suggestions.model import UserProfile

# Build user profile
user_profile = UserProfile(
    user_id=1,
    total_solved=50,
    easy_solved=20,
    medium_solved=25,
    hard_solved=5,
    topics={"array": 15, "dynamic-programming": 10, "graph": 5},
    platforms=["leetcode"],
    streak=7,
    recent_topics=["array", "hash-table"],
)

# Get candidate problems (unsolved)
candidate_problems = [
    {"id": "lc-200", "title": "Number of Islands", "difficulty": "medium", "topics": ["Graph", "DFS"]},
    {"id": "lc-322", "title": "Coin Change", "difficulty": "medium", "topics": ["Dynamic Programming"]},
    # ... more problems
]

# Recommend
recommendations = engine.recommend(
    user_profile=user_profile,
    candidate_problems=candidate_problems,
    n=10,
    strategy="balanced",  # balanced | gap_fill | progression | contest_prep
)

for rec in recommendations:
    print(f"{rec['rank']}. {rec['title']} ({rec['difficulty']})")
    print(f"   Score: {rec['dl_score']:.4f}")
    print(f"   Explanation: {rec['explanation']}")
```

### Integrate with Existing Service

Update `services/suggestions/service.py`:

```python
from services.inference.predict import get_engine

class SuggestionService:
    @staticmethod
    def get_suggestions(db, user_id, strategy="balanced", n=10, **filters):
        profile = SuggestionService._build_user_profile(db, user_id)
        
        # Try DL engine first
        dl_engine = get_engine(
            checkpoint_dir="checkpoints/dl_recommender",
            excel_path="../dataset/LeetCode Questions.xlsx",
        )
        
        if dl_engine is not None:
            # Use deep learning recommendations
            candidates = _get_candidate_problems(db, user_id, filters)
            suggestions = dl_engine.recommend(profile, candidates, n, strategy)
            skill_analysis = dl_engine.get_skill_analysis(profile)
            return {
                "suggestions": suggestions,
                "skill_analysis": skill_analysis,
                "engine": "deep_learning",
            }
        else:
            # Fallback to rule-based
            return _rule_based_suggestions(db, user_id, strategy, n, filters)
```

## 📊 Evaluation

### Benchmark vs Rule-Based

```python
comparison = engine.benchmark_vs_rule_based(
    user_profile=user_profile,
    candidate_problems=candidate_problems,
    n=10,
)

print(f"Overlap: {comparison['comparison']['overlap_pct']}%")
print(f"DL latency: {comparison['comparison']['dl_latency_ms']} ms")
print(f"Rule-based latency: {comparison['comparison']['rb_latency_ms']} ms")
```

### Attention Visualization

```python
problem = {"id": "lc-200", "title": "Number of Islands", "difficulty": "medium", "topics": ["Graph", "DFS"]}
attn_data = engine.visualize_attention(problem)

print("Tokens:", attn_data["tokens"])
print("Token importance:", attn_data["token_importance"])
# Use attention_maps for heatmap visualization
```

## 🔄 Online Learning

Update the model in real-time from new user feedback:

```python
from services.training.train import OnlineLearner

learner = OnlineLearner(
    user_encoder=engine.user_encoder,
    recommender=engine.recommender,
    config=engine.config,
    device=engine.device,
)

# When user provides feedback
sample = {
    "problem_embedding": problem_emb,
    "history_embeddings": hist_emb,
    "history_difficulties": hist_diff,
    "padding_mask": pad_mask,
    "skill_vec": skill_vec,
    "solve_label": torch.tensor(1.0),  # user solved it
    "helpful_label": torch.tensor(1.0),
    "helpful_mask": torch.tensor(True),
    "difficulty_label": torch.tensor(1),  # just_right
    "difficulty_mask": torch.tensor(True),
}

loss_dict = learner.partial_fit(sample)
print(f"Online update loss: {loss_dict['online_loss']:.4f}")
```

## 🎓 Key Features

### 1. Multi-Task Learning
Predicts three signals simultaneously:
- **p_solve**: Will the user solve this problem?
- **p_helpful**: Will the user find it helpful?
- **p_difficulty**: Is the difficulty appropriate? (too_easy / just_right / too_hard)

### 2. Exploration Strategies
- **Epsilon-greedy**: With probability ε, recommend a random problem
- **UCB1**: Balance exploitation and exploration using confidence bounds
- **Greedy**: Pure exploitation (highest score)

### 3. Curriculum Learning
Gradually increases difficulty during training:
- Epochs 1-3: Easy problems only
- Epochs 4-8: Easy + Medium
- Epochs 9+: All difficulties

### 4. Contrastive Learning
Pre-trains the problem encoder by pulling together embeddings of problems with similar topics and pushing apart dissimilar ones (InfoNCE loss).

### 5. Interpretability
- **Attention weights**: Visualize which tokens the model focuses on
- **Token importance**: Per-token contribution scores
- **Explanations**: Human-readable reasoning for each recommendation

## 📈 Model Size

| Component | Parameters |
|-----------|-----------|
| Problem Encoder | ~250K |
| User Encoder | ~180K |
| Recommender | ~120K |
| **Total** | **~550K** |

Lightweight enough to run on CPU in production.

## 🔧 Hyperparameter Tuning

Key hyperparameters to tune:
- `d_model`: Transformer hidden size (128–256)
- `embed_dim`: Final embedding dimension (64–128)
- `num_heads`: Attention heads (4–8)
- `num_encoder_layers`: Transformer depth (2–4)
- `lr`: Learning rate (1e-4 to 5e-4)
- `batch_size`: Batch size (16–64)
- `w_solve`, `w_helpful`, `w_difficulty`: Loss weights

## 🐛 Troubleshooting

### Out of Memory
- Reduce `batch_size` to 16 or 8
- Reduce `d_model` to 64
- Reduce `max_history` to 16

### Poor Recommendations
- Increase `pretrain_epochs` to 20
- Increase `train_epochs` to 50
- Collect more real user feedback data
- Adjust loss weights based on task importance

### Slow Training
- Use GPU: `device_str="cuda"`
- Reduce `vocab_size` to 2048
- Reduce `num_encoder_layers` to 2

## 📚 References

- Vaswani et al., "Attention Is All You Need" (2017)
- Devlin et al., "BERT: Pre-training of Deep Bidirectional Transformers" (2019)
- Kingma & Ba, "Adam: A Method for Stochastic Optimization" (2015)
- Oord et al., "Representation Learning with Contrastive Predictive Coding" (2018)

## 🤝 Integration with Existing System

The DL engine is designed as a drop-in replacement for the rule-based system:

1. **Same interface**: Uses the same `UserProfile` and `ProblemFeature` data structures
2. **Graceful fallback**: If checkpoints don't exist, falls back to rule-based
3. **Incremental adoption**: Can run both systems side-by-side for A/B testing
4. **Feedback loop**: Collects user feedback via `SuggestionFeedback` table for continuous improvement

## 🎯 Next Steps

1. **Train the model**: Run `python -m services.training.train`
2. **Collect feedback**: Enable feedback collection in the UI
3. **Fine-tune**: Retrain periodically with new feedback data
4. **Monitor**: Track recommendation quality metrics (CTR, solve rate, helpfulness)
5. **Optimize**: Profile inference latency and optimize bottlenecks

---

**Built with ❤️ using PyTorch primitives — no high-level training frameworks.**
