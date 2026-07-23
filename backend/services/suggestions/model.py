"""
Deep Learning Problem Suggestion Engine
Uses collaborative filtering + content-based filtering hybrid model
with a lightweight neural network for personalized recommendations.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import math


@dataclass
class UserProfile:
    user_id: int
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    topics: Dict[str, int]  # topic -> count
    platforms: List[str]
    streak: int
    recent_topics: List[str]  # last 30 days


@dataclass
class ProblemFeature:
    problem_id: str
    title: str
    difficulty: str
    topics: List[str]
    platform: str
    acceptance_rate: Optional[float] = None
    frequency: Optional[float] = None


class SkillVector:
    """Encodes user skill as a normalized vector across topics"""

    TOPICS = [
        "array", "string", "hash-table", "dynamic-programming", "math",
        "sorting", "greedy", "depth-first-search", "binary-search", "database",
        "breadth-first-search", "tree", "matrix", "two-pointers", "bit-manipulation",
        "stack", "design", "graph", "simulation", "backtracking",
        "prefix-sum", "counting", "sliding-window", "linked-list", "union-find",
        "ordered-set", "monotonic-stack", "number-theory", "trie", "recursion",
        "divide-and-conquer", "heap", "binary-tree", "queue", "memoization",
        "geometry", "segment-tree", "topological-sort", "game-theory", "shortest-path"
    ]

    DIFFICULTY_WEIGHTS = {"easy": 1.0, "medium": 2.5, "hard": 5.0}

    @classmethod
    def encode(cls, profile: UserProfile) -> np.ndarray:
        """Encode user profile into a skill vector"""
        vec = np.zeros(len(cls.TOPICS) + 4)  # topics + difficulty features

        total = max(profile.total_solved, 1)

        # Topic proficiency (normalized)
        for i, topic in enumerate(cls.TOPICS):
            count = profile.topics.get(topic, 0)
            # Log-scale normalization
            vec[i] = math.log1p(count) / math.log1p(total)

        # Difficulty distribution features
        vec[-4] = profile.easy_solved / total
        vec[-3] = profile.medium_solved / total
        vec[-2] = profile.hard_solved / total
        vec[-1] = min(profile.streak / 30.0, 1.0)  # streak factor

        return vec

    @classmethod
    def encode_problem(cls, problem: ProblemFeature) -> np.ndarray:
        """Encode problem into a feature vector"""
        vec = np.zeros(len(cls.TOPICS) + 3)

        for i, topic in enumerate(cls.TOPICS):
            if topic in [t.lower().replace(" ", "-") for t in problem.topics]:
                vec[i] = 1.0

        diff_map = {"easy": 0, "medium": 1, "hard": 2}
        diff_idx = diff_map.get(problem.difficulty.lower() if problem.difficulty else "medium", 1)
        vec[-3 + diff_idx] = 1.0

        return vec


class NeuralRecommender:
    """
    Lightweight 2-layer neural network for problem recommendation scoring.
    Uses cosine similarity + difficulty gap scoring as the core signal.
    In production, weights would be trained on historical solve data.
    """

    def __init__(self):
        # Simulated trained weights (in production: load from file/DB)
        np.random.seed(42)
        input_dim = len(SkillVector.TOPICS) + 4
        hidden_dim = 32

        # Xavier initialization
        self.W1 = np.random.randn(input_dim * 2, hidden_dim) * np.sqrt(2.0 / (input_dim * 2))
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, 1) * np.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros(1)

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _sigmoid(self, x: np.ndarray) -> float:
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def forward(self, user_vec: np.ndarray, problem_vec: np.ndarray) -> float:
        """Forward pass: returns recommendation score [0, 1]"""
        # Pad problem vector to match user vector size
        p_padded = np.zeros(len(user_vec))
        p_padded[:len(problem_vec)] = problem_vec

        combined = np.concatenate([user_vec, p_padded])
        h1 = self._relu(combined @ self.W1 + self.b1)
        score = self._sigmoid(h1 @ self.W2 + self.b2)[0]
        return float(score)

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class DifficultyProgressionEngine:
    """
    Determines optimal next difficulty based on user's current skill level.
    Uses a zone-of-proximal-development (ZPD) inspired approach.
    """

    @staticmethod
    def get_target_difficulty(profile: UserProfile) -> Tuple[str, float]:
        """
        Returns (target_difficulty, confidence_score)
        ZPD: slightly above current comfort zone
        """
        total = max(profile.total_solved, 1)
        easy_ratio = profile.easy_solved / total
        medium_ratio = profile.medium_solved / total
        hard_ratio = profile.hard_solved / total

        # Beginner: mostly easy
        if total < 20 or easy_ratio > 0.7:
            return ("easy", 0.9)

        # Intermediate: ready for medium
        if total < 100 or medium_ratio < 0.3:
            return ("medium", 0.85)

        # Advanced: push toward hard
        if medium_ratio > 0.5 and hard_ratio < 0.2:
            return ("hard", 0.8)

        # Expert: mix of medium/hard
        if hard_ratio > 0.3:
            return ("hard", 0.75)

        return ("medium", 0.8)


class TopicGapAnalyzer:
    """Identifies weak topics that need improvement"""

    TOPIC_PREREQUISITES = {
        "dynamic-programming": ["recursion", "memoization", "array"],
        "graph": ["depth-first-search", "breadth-first-search"],
        "segment-tree": ["tree", "array"],
        "trie": ["tree", "string"],
        "topological-sort": ["graph", "depth-first-search"],
        "shortest-path": ["graph", "breadth-first-search"],
    }

    @staticmethod
    def find_weak_topics(profile: UserProfile, top_n: int = 5) -> List[Dict]:
        """Find topics with low proficiency relative to overall skill"""
        total = max(profile.total_solved, 1)
        skill_level = min(total / 200.0, 1.0)  # 0-1 scale

        # Expected topic coverage at this skill level
        core_topics = [
            "array", "string", "hash-table", "two-pointers", "sliding-window",
            "binary-search", "sorting", "stack", "linked-list", "tree",
            "depth-first-search", "breadth-first-search", "dynamic-programming",
            "greedy", "backtracking"
        ]

        weak = []
        for topic in core_topics:
            count = profile.topics.get(topic, 0)
            proficiency = math.log1p(count) / math.log1p(max(total * 0.1, 1))
            expected = skill_level

            gap = max(0, expected - min(proficiency, 1.0))
            if gap > 0.1:
                weak.append({
                    "topic": topic,
                    "current_count": count,
                    "gap_score": round(gap, 3),
                    "priority": "high" if gap > 0.5 else "medium" if gap > 0.25 else "low"
                })

        weak.sort(key=lambda x: x["gap_score"], reverse=True)
        return weak[:top_n]


class ProblemSuggestionEngine:
    """Main recommendation engine combining all components"""

    def __init__(self):
        self.neural_net = NeuralRecommender()
        self.difficulty_engine = DifficultyProgressionEngine()
        self.gap_analyzer = TopicGapAnalyzer()

    def generate_suggestions(
        self,
        profile: UserProfile,
        candidate_problems: List[ProblemFeature],
        n_suggestions: int = 10,
        strategy: str = "balanced"  # balanced | gap_fill | progression | contest_prep
    ) -> List[Dict]:
        """
        Generate personalized problem suggestions.

        Strategies:
        - balanced: Mix of gap-filling and progression
        - gap_fill: Focus on weak topics
        - progression: Push difficulty level
        - contest_prep: Focus on speed/common contest patterns
        """
        user_vec = SkillVector.encode(profile)
        target_diff, diff_confidence = self.difficulty_engine.get_target_difficulty(profile)
        weak_topics = self.gap_analyzer.find_weak_topics(profile)
        weak_topic_names = {w["topic"] for w in weak_topics}

        scored = []
        for problem in candidate_problems:
            prob_vec = SkillVector.encode_problem(problem)

            # Neural network base score
            nn_score = self.neural_net.forward(user_vec, prob_vec)

            # Cosine similarity (topic alignment)
            topic_sim = self.neural_net.cosine_similarity(
                user_vec[:len(SkillVector.TOPICS)],
                prob_vec[:len(SkillVector.TOPICS)]
            )

            # Difficulty alignment score
            diff_score = self._difficulty_score(problem.difficulty, target_diff, strategy)

            # Gap fill bonus
            gap_bonus = 0.0
            prob_topics = [t.lower().replace(" ", "-") for t in problem.topics]
            if strategy in ("balanced", "gap_fill"):
                overlap = len(set(prob_topics) & weak_topic_names)
                gap_bonus = min(overlap * 0.15, 0.3)

            # Contest prep bonus
            contest_bonus = 0.0
            if strategy == "contest_prep":
                contest_topics = {"dynamic-programming", "greedy", "graph", "math", "binary-search"}
                if set(prob_topics) & contest_topics:
                    contest_bonus = 0.2

            # Final composite score
            final_score = (
                0.30 * nn_score +
                0.25 * topic_sim +
                0.25 * diff_score +
                0.10 * gap_bonus +
                0.10 * contest_bonus
            )

            # Reason generation
            reason = self._generate_reason(
                problem, profile, weak_topic_names, target_diff, strategy
            )

            scored.append({
                "problem": problem,
                "score": round(final_score, 4),
                "reason": reason,
                "difficulty_match": diff_score > 0.7,
                "fills_gap": gap_bonus > 0,
                "target_topics": [t for t in prob_topics if t in weak_topic_names]
            })

        # Sort by score, deduplicate by topic coverage
        scored.sort(key=lambda x: x["score"], reverse=True)
        selected = self._diversify(scored, n_suggestions)

        return [
            {
                "rank": i + 1,
                "problem_id": s["problem"].problem_id,
                "title": s["problem"].title,
                "difficulty": s["problem"].difficulty,
                "platform": s["problem"].platform,
                "topics": s["problem"].topics,
                "score": s["score"],
                "reason": s["reason"],
                "fills_gap": s["fills_gap"],
                "target_topics": s["target_topics"],
            }
            for i, s in enumerate(selected)
        ]

    def _difficulty_score(self, problem_diff: str, target_diff: str, strategy: str) -> float:
        """Score how well problem difficulty matches target"""
        if not problem_diff:
            return 0.5

        diff_order = {"easy": 0, "medium": 1, "hard": 2}
        p = diff_order.get(problem_diff.lower(), 1)
        t = diff_order.get(target_diff.lower(), 1)

        if strategy == "progression":
            # Prefer slightly harder
            if p == t:
                return 1.0
            elif p == t + 1:
                return 0.8
            else:
                return 0.3
        else:
            # Balanced: prefer exact match
            distance = abs(p - t)
            return [1.0, 0.6, 0.2][distance]

    def _generate_reason(
        self,
        problem: ProblemFeature,
        profile: UserProfile,
        weak_topics: set,
        target_diff: str,
        strategy: str
    ) -> str:
        """Generate human-readable recommendation reason"""
        prob_topics = [t.lower().replace(" ", "-") for t in problem.topics]
        gap_topics = [t for t in prob_topics if t in weak_topics]

        if gap_topics:
            return f"Strengthen your {gap_topics[0].replace('-', ' ')} skills — identified as a growth area"
        elif problem.difficulty and problem.difficulty.lower() == target_diff:
            return f"Perfect difficulty match for your current level ({target_diff})"
        elif strategy == "contest_prep":
            return "High-frequency contest pattern — great for competitive programming"
        elif profile.streak > 7:
            return f"Keep your {profile.streak}-day streak going with this {problem.difficulty} challenge"
        else:
            return f"Recommended based on your {profile.total_solved} solved problems profile"

    def _diversify(self, scored: List[Dict], n: int) -> List[Dict]:
        """Ensure topic diversity in final recommendations"""
        selected = []
        covered_topics = set()

        for item in scored:
            if len(selected) >= n:
                break
            prob_topics = set(t.lower().replace(" ", "-") for t in item["problem"].topics)
            # Allow if it covers new topics or we don't have enough yet
            if len(selected) < n // 2 or not prob_topics.issubset(covered_topics):
                selected.append(item)
                covered_topics.update(prob_topics)

        # Fill remaining slots
        for item in scored:
            if len(selected) >= n:
                break
            if item not in selected:
                selected.append(item)

        return selected[:n]

    def get_skill_analysis(self, profile: UserProfile) -> Dict:
        """Full skill analysis for the suggestions page"""
        user_vec = SkillVector.encode(profile)
        target_diff, confidence = self.difficulty_engine.get_target_difficulty(profile)
        weak_topics = self.gap_analyzer.find_weak_topics(profile, top_n=8)

        # Skill radar data
        radar_topics = ["array", "string", "dynamic-programming", "graph",
                        "tree", "math", "greedy", "binary-search"]
        radar_data = []
        total = max(profile.total_solved, 1)
        for topic in radar_topics:
            count = profile.topics.get(topic, 0)
            score = min(int(math.log1p(count) / math.log1p(max(total * 0.15, 1)) * 100), 100)
            radar_data.append({"topic": topic.replace("-", " ").title(), "score": score})

        # Overall skill tier
        tier = self._get_skill_tier(profile)

        return {
            "skill_tier": tier,
            "target_difficulty": target_diff,
            "difficulty_confidence": round(confidence, 2),
            "weak_topics": weak_topics,
            "radar_data": radar_data,
            "total_solved": profile.total_solved,
            "topic_diversity": len([t for t, c in profile.topics.items() if c > 0]),
            "readiness_score": self._placement_readiness(profile),
        }

    def _get_skill_tier(self, profile: UserProfile) -> str:
        total = profile.total_solved
        hard_ratio = profile.hard_solved / max(total, 1)

        if total < 25:
            return "Beginner"
        elif total < 75:
            return "Novice"
        elif total < 150:
            return "Intermediate"
        elif total < 300 and hard_ratio < 0.15:
            return "Advanced"
        elif total >= 300 or hard_ratio >= 0.2:
            return "Expert"
        return "Advanced"

    def _placement_readiness(self, profile: UserProfile) -> int:
        """0-100 placement readiness score"""
        score = 0
        # Total problems (max 40 pts)
        score += min(profile.total_solved / 300 * 40, 40)
        # Hard problems (max 20 pts)
        score += min(profile.hard_solved / 50 * 20, 20)
        # Topic diversity (max 20 pts)
        diverse = len([t for t, c in profile.topics.items() if c >= 3])
        score += min(diverse / 10 * 20, 20)
        # Streak (max 10 pts)
        score += min(profile.streak / 30 * 10, 10)
        # Platform diversity (max 10 pts)
        score += min(len(profile.platforms) / 3 * 10, 10)
        return int(score)


# Singleton instance
suggestion_engine = ProblemSuggestionEngine()
