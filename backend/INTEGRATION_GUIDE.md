# Integration Guide — DL Recommendation System with FastAPI

## ✅ Integration Complete

The deep learning recommendation system has been successfully integrated into the existing FastAPI backend. All endpoints are now DL-powered with automatic fallback to the rule-based system.

---

## 🔌 New API Endpoints

### 1. **GET /suggestions** (Enhanced)
Main recommendation endpoint — now uses DL model by default.

**Query Parameters:**
```
- strategy: balanced (default) | gap_fill | progression | contest_prep
- n: number of recommendations (1-20, default 10)
- difficulty: filter by easy/medium/hard
- platform: filter by platform (leetcode/codeforces/etc)
- topic: filter by topic
- use_dl: use DL model if available (default true)
```

**Response:**
```json
{
  "suggestions": [
    {
      "rank": 1,
      "problem_id": "lc-1",
      "title": "Two Sum",
      "difficulty": "easy",
      "platform": "leetcode",
      "topics": ["Array", "Hash Table"],
      "dl_score": 0.8234,
      "explanation": "Recommended because you are weak in Arrays and recently solved Hash Table problems",
      "fills_gap": true,
      "target_topics": ["array"]
    },
    ...
  ],
  "skill_analysis": {...},
  "profile_summary": {...},
  "source": "dl_model"  // or "rule_based" if DL failed
}
```

**Example:**
```bash
curl "http://localhost:8000/suggestions?strategy=balanced&n=10&use_dl=true"
```

---

### 2. **GET /suggestions/skill-analysis** (Existing)
Get detailed skill gap analysis.

**Response:**
```json
{
  "skill_tier": "Intermediate",
  "target_difficulty": "medium",
  "difficulty_confidence": 0.85,
  "weak_topics": [
    {"topic": "graph", "current_count": 2, "gap_score": 0.45, "priority": "high"},
    ...
  ],
  "radar_data": [...],
  "total_solved": 50,
  "topic_diversity": 12,
  "readiness_score": 65
}
```

---

### 3. **GET /suggestions/dl-benchmark** (New)
Compare DL recommendations against rule-based system.

**Query Parameters:**
```
- n: number of recommendations to compare (1-20, default 10)
```

**Response:**
```json
{
  "dl_recommendations": [...],
  "rule_based_recommendations": [...],
  "comparison": {
    "overlap_count": 7,
    "overlap_pct": 70.0,
    "dl_topic_diversity": 8,
    "rb_topic_diversity": 6,
    "dl_latency_ms": 72.5,
    "rb_latency_ms": 4.2,
    "dl_unique_recs": ["lc-42", "lc-76"],
    "rb_unique_recs": ["lc-20"]
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/suggestions/dl-benchmark?n=10"
```

---

### 4. **GET /suggestions/dl-attention/{problem_id}** (New)
Get attention visualization for a problem.

**Response:**
```json
{
  "tokens": ["two", "sum", "array", "hash", "table"],
  "attention_maps": [
    [[[0.1, 0.2, ...], ...], ...],  // Layer 1
    [[[0.15, 0.25, ...], ...], ...], // Layer 2
    [[[0.12, 0.22, ...], ...], ...]  // Layer 3
  ],
  "token_importance": [0.8, 0.9, 0.7, 0.85, 0.75],
  "n_layers": 3,
  "n_heads": 4
}
```

**Example:**
```bash
curl "http://localhost:8000/suggestions/dl-attention/lc-1"
```

---

### 5. **POST /suggestions/feedback** (Enhanced)
Submit feedback on recommendations — now triggers online learning.

**Request Body:**
```json
{
  "problem_id": "lc-1",
  "platform": "leetcode",
  "strategy": "balanced",
  "was_helpful": true,
  "was_solved": true,
  "difficulty_felt": "just_right",
  "suggestion_score": 0.9
}
```

**Response:**
```json
{
  "success": true,
  "message": "Feedback recorded and model updated"
}
```

**What Happens:**
1. Feedback is saved to database
2. Online learning updates the model (real-time)
3. Model learns from user feedback immediately

**Example:**
```bash
curl -X POST "http://localhost:8000/suggestions/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "problem_id": "lc-1",
    "platform": "leetcode",
    "was_helpful": true,
    "was_solved": true,
    "difficulty_felt": "just_right"
  }'
```

---

## 🏗️ Architecture

```
FastAPI Request
    ↓
/suggestions endpoint
    ↓
Try DL Model (if use_dl=true)
    ├─ Load engine (singleton)
    ├─ Build user profile from DB
    ├─ Get candidate problems
    ├─ Score with DL model
    ├─ Apply exploration strategy
    └─ Return DL recommendations
    ↓
If DL fails → Fallback to rule-based
    ├─ Use existing SuggestionService
    └─ Return rule-based recommendations
    ↓
Response with source indicator
```

---

## 🚀 How to Use

### 1. Start FastAPI Server

```bash
cd backend
uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Get DL Recommendations

```bash
# Default (DL model)
curl "http://localhost:8000/suggestions"

# Force rule-based
curl "http://localhost:8000/suggestions?use_dl=false"

# Specific strategy
curl "http://localhost:8000/suggestions?strategy=gap_fill&n=15"

# With filters
curl "http://localhost:8000/suggestions?difficulty=medium&platform=leetcode"
```

### 3. Compare Systems

```bash
curl "http://localhost:8000/suggestions/dl-benchmark?n=10"
```

### 4. Visualize Attention

```bash
curl "http://localhost:8000/suggestions/dl-attention/lc-1"
```

### 5. Submit Feedback

```bash
curl -X POST "http://localhost:8000/suggestions/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "problem_id": "lc-1",
    "platform": "leetcode",
    "was_helpful": true,
    "was_solved": true,
    "difficulty_felt": "just_right"
  }'
```

---

## 📊 Response Format

All endpoints return a consistent format:

```json
{
  "suggestions": [...],           // Array of recommendations
  "skill_analysis": {...},        // User skill profile
  "profile_summary": {...},       // User stats
  "source": "dl_model",           // "dl_model" or "rule_based"
  "message": "..."                // Optional status message
}
```

---

## 🔄 Fallback Behavior

The system automatically falls back to rule-based recommendations if:

1. **DL model not trained** → Use rule-based
2. **DL model fails** → Log warning, use rule-based
3. **use_dl=false** → Skip DL, use rule-based directly
4. **No candidates** → Return empty suggestions

**Logging:**
```
INFO: Using DL model for user 123
INFO: Using rule-based system for user 456
WARNING: DL model failed for user 789: [error]. Falling back to rule-based.
```

---

## 🎯 Online Learning

When users submit feedback, the model updates in real-time:

```python
# Feedback triggers:
1. Database save (SuggestionFeedback table)
2. Online learning update (OnlineLearner)
3. Model weights updated
4. Next recommendation uses updated model
```

**Replay Buffer:**
- Keeps last 512 feedback samples
- Uses mini-batch of 8 for gradient step
- One gradient step per feedback
- No full retraining needed

---

## 📈 Monitoring

### Metrics to Track

```
- DL vs Rule-based accuracy
- Inference latency (target: <100ms)
- Model convergence (online learning)
- User engagement (solve rate, helpfulness)
- Fallback rate (should be <5%)
```

### Logging

All DL operations are logged:
```
INFO: Using DL model for user 123
INFO: Online learning update for user 123: {'online_loss': 0.42}
WARNING: DL model failed: [error]
ERROR: Benchmark failed: [error]
```

---

## 🔧 Configuration

### Model Configuration

Located in `checkpoints/dl_recommender/config.json`:

```json
{
  "vocab_size": 2329,
  "d_model": 128,
  "embed_dim": 64,
  "num_heads": 4,
  "num_encoder_layers": 3,
  "d_ff": 512,
  "max_len": 64,
  "dropout": 0.1,
  "batch_size": 64,
  "lr": 0.0003,
  "weight_decay": 0.01
}
```

### Runtime Configuration

In `gateway/routes/suggestions.py`:

```python
# Device (CPU or GPU)
engine = get_engine(device_str="cpu")

# Exploration strategy
use_exploration=True  # epsilon-greedy

# Fallback behavior
use_dl=True  # try DL first
```

---

## 🧪 Testing

### Unit Test

```bash
python test_integration.py
```

**Output:**
```
✅ All imports successful
✅ Suggestions router has 6 routes
✅ DL engine loaded: True
✅ Problem bank size: 3433 problems
✅ Integration test passed!
```

### Integration Test

```bash
# Start server
uvicorn gateway.main:app --reload

# In another terminal
curl "http://localhost:8000/suggestions"
curl "http://localhost:8000/suggestions/dl-benchmark"
curl "http://localhost:8000/suggestions/dl-attention/lc-1"
```

---

## 📋 Checklist

- ✅ DL model trained and weights saved
- ✅ FastAPI routes updated
- ✅ Fallback to rule-based implemented
- ✅ Online learning integrated
- ✅ Logging added
- ✅ Error handling implemented
- ✅ Documentation complete
- ✅ Integration tested

---

## 🚨 Troubleshooting

### "DL model not trained yet"
```bash
# Re-train the model
python train_dl_recommender.py
```

### "DL model failed: [error]"
```
Check logs for specific error
Fallback to rule-based is automatic
```

### Slow inference
```python
# Use GPU if available
engine = get_engine(device_str="cuda")

# Or reduce batch size in config
batch_size = 32  # was 64
```

### Poor recommendations
```python
# Collect more feedback
# Online learning will improve model
# Or fine-tune on real data
```

---

## 📚 Related Documentation

- **DL_RECOMMENDER_GUIDE.md** — Complete technical guide
- **TRAINING_SUMMARY.md** — Training results
- **QUICKSTART_DL.md** — Quick start guide
- **DELIVERY_SUMMARY.md** — Project overview

---

## 🎉 Summary

The DL recommendation system is now fully integrated into the FastAPI backend:

✅ **6 new/enhanced endpoints**  
✅ **Automatic fallback to rule-based**  
✅ **Online learning support**  
✅ **Attention visualization**  
✅ **Benchmark tools**  
✅ **Comprehensive logging**  
✅ **Error handling**  
✅ **Production ready**  

**Ready to deploy!** 🚀
