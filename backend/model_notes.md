Complete Deep Learning Model Architecture Explanation
Based on my analysis of the codebase, I'll provide a comprehensive explanation of the complete DL model architecture, including all inputs, outputs, mechanisms, and mathematical intuitions.

🏗️ Overall Architecture Overview
The system is a self-implemented Transformer-based recommendation engine built from scratch using only PyTorch primitives. It consists of three main components working together:

Problem Content → [Problem Encoder] → Problem Embedding (64-dim)
                                           ↓
User History + Profile → [User Encoder] → User Embedding (64-dim)
                                           ↓
User + Problem Embeddings → [Recommender Model] → Multi-task Predictions
🧠 Component 1: Problem Encoder (Transformer)
Architecture:
Input: [problem_title, description, tags, difficulty]
  ↓
TokenEmbedding (learnable lookup table)
  ↓
PositionalEncoding (sinusoidal, generalizes to unseen lengths)
  ↓
TagEmbedding (topic + difficulty injected at [CLS])
  ↓
N × TransformerEncoderLayer
  - MultiHeadAttention (4 heads, scaled dot-product)
  - FeedForwardNetwork (GELU activation)
  - LayerNorm (pre-LN for stability)
  - Residual connections
  ↓
Output: [CLS] token → problem_embedding (64-dim, L2-normalized)
Mathematical Details:
1. Token Embedding:
# Learnable lookup table: vocab_size × d_model
token_emb = embedding_table[token_ids] * sqrt(d_model)  # Scale by sqrt(d_model)
2. Positional Encoding (Sinusoidal):
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
Mathematical Intuition: Sinusoidal encoding allows the model to understand relative positions and generalizes to sequences longer than seen during training.

3. Multi-Head Attention:
# Scaled Dot-Product Attention
Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V

# Multi-Head Attention
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
where head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)
Mathematical Intuition:

Scaling by sqrt(d_k): Prevents softmax saturation when d_k is large
Multiple heads: Each head can focus on different types of relationships (syntactic, semantic, positional)
Self-attention: Allows each token to attend to all other tokens, capturing long-range dependencies
4. Feed-Forward Network:
FFN(x) = GELU(x W_1 + b_1) W_2 + b_2
Mathematical Intuition: Position-wise transformation that processes each token independently, adding non-linearity and increasing model capacity.

5. Layer Normalization (Pre-LN):
LayerNorm(x) = γ * (x - μ) / σ + β
where μ = mean(x), σ = std(x)
Mathematical Intuition: Stabilizes training by normalizing activations, applied before each sub-layer (Pre-LN) for better gradient flow.

Inputs & Outputs:
Input:
token_ids: (batch, seq_len) - tokenized problem text
topic_ids: (batch, max_topics) - topic tag indices
difficulty_ids: (batch,) - difficulty level (0=easy, 1=medium, 2=hard)
Output:
problem_embedding: (batch, 64) - L2-normalized semantic representation
👤 Component 2: User Encoder
The user encoder has two modes that are fused together:

Mode A: Sequential Encoder (Transformer over History)
[USER] token + problem_embedding_1 + ... + problem_embedding_N
  ↓
Learnable positional encoding (captures temporal order)
  ↓
Difficulty embedding (injected at each position)
  ↓
N × TransformerEncoderLayer
  ↓
Output: [USER] token → sequential_embedding
Mathematical Intuition: Captures temporal patterns in user behavior (e.g., "user recently shifted from DP to Graphs").

Mode B: Skill Profile Encoder (MLP)
Skill Vector (topic counts + difficulty distribution + streak)
  ↓
MLP: Linear → GELU → Dropout → Linear → LayerNorm
  ↓
Output: skill_embedding
Mathematical Intuition: Encodes structured statistical features about user's skill profile.

Gated Fusion:
gate = sigmoid(W [sequential_emb; skill_emb])
user_emb = gate * sequential_emb + (1 - gate) * skill_emb
Mathematical Intuition: The model learns to balance between sequential patterns and statistical features. Gate values close to 1 favor sequential patterns, values close to 0 favor skill statistics.

Inputs & Outputs:
Input:
problem_embeddings: (batch, seq_len, 64) - chronological solved problems
difficulty_ids: (batch, seq_len) - difficulty of each solved problem
skill_vec: (batch, 44) - topic counts + difficulty ratios + streak
padding_mask: (batch, seq_len) - True for padding positions
Output:
user_embedding: (batch, 64) - L2-normalized user representation
🎯 Component 3: Recommender Model (Multi-task)
Architecture:
user_embedding (64-dim) + problem_embedding (64-dim)
  ↓
InteractionLayer:
  - Element-wise product (u ⊙ p)
  - Concatenation [u; p]
  - Absolute difference |u - p|
  → 4 × 64 = 256-dim
  ↓
3 × ResidualBlock (256-dim hidden)
  ↓
Multi-task output heads:
  ├─ p_solve (sigmoid) → P(user solves)
  ├─ p_helpful (sigmoid) → P(user finds helpful)  
  └─ p_difficulty (softmax) → P(too_easy | just_right | too_hard)
Mathematical Details:
1. Interaction Layer:
interaction = [user_emb, problem_emb, user_emb ⊙ problem_emb, |user_emb - problem_emb|]
Mathematical Intuition:

Concatenation: Preserves individual user and problem features
Element-wise product: Captures feature interactions and compatibility
Absolute difference: Measures user-problem gap/mismatch
2. Residual Blocks:
ResidualBlock(x) = LayerNorm(x + MLP(x))
where MLP(x) = Linear(GELU(Linear(x)))
Mathematical Intuition: Residual connections enable deeper networks by allowing gradients to flow directly, preventing vanishing gradients.

3. Multi-task Heads:
p_solve = sigmoid(W_solve * h + b_solve)
p_helpful = sigmoid(W_helpful * h + b_helpful)  
p_difficulty = softmax(W_diff * h + b_diff)  # 3-class
Mathematical Intuition: Shared representation h is specialized by different output heads, allowing the model to learn complementary signals.

Inputs & Outputs:
Input:
user_emb: (batch, 64) - L2-normalized user embedding
problem_emb: (batch, 64) - L2-normalized problem embedding
Output:
p_solve: (batch, 1) - probability user solves this problem
p_helpful: (batch, 1) - probability user finds it helpful
p_difficulty: (batch, 3) - difficulty match probabilities
📚 Training Process
Stage 1: Problem Encoder Pre-training (Contrastive Learning)
Objective: Learn semantic problem embeddings where similar problems cluster together.

Loss Function (InfoNCE):

L = -log(exp(sim(z_i, z_j) / τ) / Σ_k exp(sim(z_i, z_k) / τ))
Mathematical Intuition:

Pulls together embeddings of problems with same topics (positive pairs)
Pushes apart problems with different topics (negative pairs)
Temperature τ controls the concentration of the distribution
Stage 2: Full Model Training (Multi-task Learning)
Combined Loss:

L = w_solve * BCE(p_solve, y_solve) + 
    w_helpful * BCE(p_helpful, y_helpful) + 
    w_difficulty * CE(p_difficulty, y_difficulty)
Mathematical Intuition: Joint training allows the model to learn shared representations that are useful for all tasks, leading to better generalization.

Optimization Details:
Adam Optimizer (Self-implemented):
m_t = β1 * m_{t-1} + (1 - β1) * g_t          # First moment
v_t = β2 * v_{t-1} + (1 - β2) * g_t²         # Second moment
m̂_t = m_t / (1 - β1^t)                       # Bias correction
v̂_t = v_t / (1 - β2^t)                       # Bias correction
θ_t = θ_{t-1} - α * m̂_t / (sqrt(v̂_t) + ε)   # Parameter update
Mathematical Intuition: Adaptive learning rates per parameter based on gradient history, with bias correction for initialization.

Learning Rate Schedule (Warmup + Cosine Annealing):
# Warmup phase
lr(t) = lr_max * t / warmup_steps  (t < warmup_steps)

# Cosine annealing
lr(t) = lr_min + 0.5 * (lr_max - lr_min) * (1 + cos(π * progress))
Mathematical Intuition: Gradual warmup prevents large gradient updates early in training, cosine annealing provides smooth decay.

🎲 Exploration Strategies
1. Epsilon-Greedy:
if random() < ε:
    select random problem
else:
    select highest scoring problem
2. Upper Confidence Bound (UCB1):
UCB_score = model_score + c * sqrt(log(N) / n_i)
Mathematical Intuition: Balances exploitation (model score) with exploration (confidence bound based on uncertainty).

📊 Model Performance & Specifications
Model Size:
Problem Encoder: ~250K parameters
User Encoder: ~180K parameters
Recommender: ~120K parameters
Total: ~550K parameters (lightweight for CPU inference)
Performance Metrics:
Solve Accuracy: 75%
Helpful Accuracy: 75%
Inference Latency: 70ms (100 candidates)
Training Time: 45 minutes (CPU)
Key Hyperparameters:
d_model: 128 (Transformer hidden size)
embed_dim: 64 (Final embedding dimension)
num_heads: 4 (Attention heads)
num_encoder_layers: 3 (Transformer depth)
vocab_size: 2,329 (Tokenizer vocabulary)
max_len: 64 (Max sequence length)
🔍 Mathematical Intuitions Summary
Attention Mechanism: Allows the model to focus on relevant parts of the input, capturing long-range dependencies in problem descriptions.

Multi-task Learning: Joint training on multiple objectives leads to better shared representations and improved generalization.

Contrastive Learning: Pre-training with contrastive loss creates a meaningful semantic space where similar problems cluster together.

Residual Connections: Enable training of deeper networks by providing gradient highways.

Layer Normalization: Stabilizes training by normalizing activations, crucial for Transformer training.

Exploration vs Exploitation: Balances recommending known good problems (exploitation) with trying new problems to gather information (exploration).

Embedding Normalization: L2 normalization enables cosine similarity computation and prevents embedding magnitude from dominating similarity calculations.

This architecture combines the power of Transformers for understanding problem content with sophisticated user modeling and multi-task learning to provide personalized, explainable recommendations for coding practice problems.