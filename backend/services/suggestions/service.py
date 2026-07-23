"""
Suggestion Service — bridges DB data with the DL recommendation engine
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from shared.models import (
    User, PlatformAccount, ProblemStats, Analytics,
    PlatformProfileStats, ContestStats
)
from services.suggestions.model import (
    ProblemSuggestionEngine, UserProfile, ProblemFeature,
    suggestion_engine
)

# Curated problem bank (in production: pull from DB or external API)
PROBLEM_BANK: List[Dict] = [
    # Easy
    {"id": "lc-1", "title": "Two Sum", "difficulty": "easy", "topics": ["Array", "Hash Table"], "platform": "leetcode", "url": "https://leetcode.com/problems/two-sum/"},
    {"id": "lc-121", "title": "Best Time to Buy and Sell Stock", "difficulty": "easy", "topics": ["Array", "Dynamic Programming"], "platform": "leetcode", "url": "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/"},
    {"id": "lc-20", "title": "Valid Parentheses", "difficulty": "easy", "topics": ["String", "Stack"], "platform": "leetcode", "url": "https://leetcode.com/problems/valid-parentheses/"},
    {"id": "lc-206", "title": "Reverse Linked List", "difficulty": "easy", "topics": ["Linked List", "Recursion"], "platform": "leetcode", "url": "https://leetcode.com/problems/reverse-linked-list/"},
    {"id": "lc-104", "title": "Maximum Depth of Binary Tree", "difficulty": "easy", "topics": ["Tree", "Depth First Search"], "platform": "leetcode", "url": "https://leetcode.com/problems/maximum-depth-of-binary-tree/"},
    {"id": "lc-217", "title": "Contains Duplicate", "difficulty": "easy", "topics": ["Array", "Hash Table", "Sorting"], "platform": "leetcode", "url": "https://leetcode.com/problems/contains-duplicate/"},
    {"id": "lc-242", "title": "Valid Anagram", "difficulty": "easy", "topics": ["Hash Table", "String", "Sorting"], "platform": "leetcode", "url": "https://leetcode.com/problems/valid-anagram/"},
    {"id": "lc-704", "title": "Binary Search", "difficulty": "easy", "topics": ["Array", "Binary Search"], "platform": "leetcode", "url": "https://leetcode.com/problems/binary-search/"},
    {"id": "lc-226", "title": "Invert Binary Tree", "difficulty": "easy", "topics": ["Tree", "Depth First Search"], "platform": "leetcode", "url": "https://leetcode.com/problems/invert-binary-tree/"},
    {"id": "lc-125", "title": "Valid Palindrome", "difficulty": "easy", "topics": ["Two Pointers", "String"], "platform": "leetcode", "url": "https://leetcode.com/problems/valid-palindrome/"},
    {"id": "lc-383", "title": "Ransom Note", "difficulty": "easy", "topics": ["Hash Table", "String", "Counting"], "platform": "leetcode", "url": "https://leetcode.com/problems/ransom-note/"},
    {"id": "lc-412", "title": "Fizz Buzz", "difficulty": "easy", "topics": ["Math", "String", "Simulation"], "platform": "leetcode", "url": "https://leetcode.com/problems/fizz-buzz/"},
    # Medium
    {"id": "lc-3", "title": "Longest Substring Without Repeating Characters", "difficulty": "medium", "topics": ["Hash Table", "String", "Sliding Window"], "platform": "leetcode", "url": "https://leetcode.com/problems/longest-substring-without-repeating-characters/"},
    {"id": "lc-15", "title": "3Sum", "difficulty": "medium", "topics": ["Array", "Two Pointers", "Sorting"], "platform": "leetcode", "url": "https://leetcode.com/problems/3sum/"},
    {"id": "lc-11", "title": "Container With Most Water", "difficulty": "medium", "topics": ["Array", "Two Pointers", "Greedy"], "platform": "leetcode", "url": "https://leetcode.com/problems/container-with-most-water/"},
    {"id": "lc-49", "title": "Group Anagrams", "difficulty": "medium", "topics": ["Array", "Hash Table", "String", "Sorting"], "platform": "leetcode", "url": "https://leetcode.com/problems/group-anagrams/"},
    {"id": "lc-153", "title": "Find Minimum in Rotated Sorted Array", "difficulty": "medium", "topics": ["Array", "Binary Search"], "platform": "leetcode", "url": "https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/"},
    {"id": "lc-33", "title": "Search in Rotated Sorted Array", "difficulty": "medium", "topics": ["Array", "Binary Search"], "platform": "leetcode", "url": "https://leetcode.com/problems/search-in-rotated-sorted-array/"},
    {"id": "lc-102", "title": "Binary Tree Level Order Traversal", "difficulty": "medium", "topics": ["Tree", "Breadth First Search"], "platform": "leetcode", "url": "https://leetcode.com/problems/binary-tree-level-order-traversal/"},
    {"id": "lc-200", "title": "Number of Islands", "difficulty": "medium", "topics": ["Array", "Depth First Search", "Breadth First Search", "Graph"], "platform": "leetcode", "url": "https://leetcode.com/problems/number-of-islands/"},
    {"id": "lc-322", "title": "Coin Change", "difficulty": "medium", "topics": ["Array", "Dynamic Programming"], "platform": "leetcode", "url": "https://leetcode.com/problems/coin-change/"},
    {"id": "lc-198", "title": "House Robber", "difficulty": "medium", "topics": ["Array", "Dynamic Programming"], "platform": "leetcode", "url": "https://leetcode.com/problems/house-robber/"},
    {"id": "lc-213", "title": "House Robber II", "difficulty": "medium", "topics": ["Array", "Dynamic Programming"], "platform": "leetcode", "url": "https://leetcode.com/problems/house-robber-ii/"},
    {"id": "lc-91", "title": "Decode Ways", "difficulty": "medium", "topics": ["String", "Dynamic Programming"], "platform": "leetcode", "url": "https://leetcode.com/problems/decode-ways/"},
    {"id": "lc-139", "title": "Word Break", "difficulty": "medium", "topics": ["Hash Table", "String", "Dynamic Programming", "Trie"], "platform": "leetcode", "url": "https://leetcode.com/problems/word-break/"},
    {"id": "lc-300", "title": "Longest Increasing Subsequence", "difficulty": "medium", "topics": ["Array", "Binary Search", "Dynamic Programming"], "platform": "leetcode", "url": "https://leetcode.com/problems/longest-increasing-subsequence/"},
    {"id": "lc-207", "title": "Course Schedule", "difficulty": "medium", "topics": ["Depth First Search", "Breadth First Search", "Graph", "Topological Sort"], "platform": "leetcode", "url": "https://leetcode.com/problems/course-schedule/"},
    {"id": "lc-417", "title": "Pacific Atlantic Water Flow", "difficulty": "medium", "topics": ["Array", "Depth First Search", "Breadth First Search", "Graph"], "platform": "leetcode", "url": "https://leetcode.com/problems/pacific-atlantic-water-flow/"},
    {"id": "lc-238", "title": "Product of Array Except Self", "difficulty": "medium", "topics": ["Array", "Prefix Sum"], "platform": "leetcode", "url": "https://leetcode.com/problems/product-of-array-except-self/"},
    {"id": "lc-347", "title": "Top K Frequent Elements", "difficulty": "medium", "topics": ["Array", "Hash Table", "Sorting", "Heap"], "platform": "leetcode", "url": "https://leetcode.com/problems/top-k-frequent-elements/"},
    # Hard
    {"id": "lc-4", "title": "Median of Two Sorted Arrays", "difficulty": "hard", "topics": ["Array", "Binary Search", "Divide and Conquer"], "platform": "leetcode", "url": "https://leetcode.com/problems/median-of-two-sorted-arrays/"},
    {"id": "lc-23", "title": "Merge K Sorted Lists", "difficulty": "hard", "topics": ["Linked List", "Divide and Conquer", "Heap", "Merge Sort"], "platform": "leetcode", "url": "https://leetcode.com/problems/merge-k-sorted-lists/"},
    {"id": "lc-76", "title": "Minimum Window Substring", "difficulty": "hard", "topics": ["Hash Table", "String", "Sliding Window"], "platform": "leetcode", "url": "https://leetcode.com/problems/minimum-window-substring/"},
    {"id": "lc-42", "title": "Trapping Rain Water", "difficulty": "hard", "topics": ["Array", "Two Pointers", "Dynamic Programming", "Stack"], "platform": "leetcode", "url": "https://leetcode.com/problems/trapping-rain-water/"},
    {"id": "lc-84", "title": "Largest Rectangle in Histogram", "difficulty": "hard", "topics": ["Array", "Stack", "Monotonic Stack"], "platform": "leetcode", "url": "https://leetcode.com/problems/largest-rectangle-in-histogram/"},
    {"id": "lc-124", "title": "Binary Tree Maximum Path Sum", "difficulty": "hard", "topics": ["Dynamic Programming", "Tree", "Depth First Search"], "platform": "leetcode", "url": "https://leetcode.com/problems/binary-tree-maximum-path-sum/"},
    {"id": "lc-297", "title": "Serialize and Deserialize Binary Tree", "difficulty": "hard", "topics": ["String", "Tree", "Depth First Search", "Design"], "platform": "leetcode", "url": "https://leetcode.com/problems/serialize-and-deserialize-binary-tree/"},
    {"id": "lc-295", "title": "Find Median from Data Stream", "difficulty": "hard", "topics": ["Two Pointers", "Design", "Sorting", "Heap"], "platform": "leetcode", "url": "https://leetcode.com/problems/find-median-from-data-stream/"},
    {"id": "lc-51", "title": "N-Queens", "difficulty": "hard", "topics": ["Array", "Backtracking"], "platform": "leetcode", "url": "https://leetcode.com/problems/n-queens/"},
    {"id": "lc-10", "title": "Regular Expression Matching", "difficulty": "hard", "topics": ["String", "Dynamic Programming", "Recursion"], "platform": "leetcode", "url": "https://leetcode.com/problems/regular-expression-matching/"},
    # Codeforces
    {"id": "cf-1A", "title": "Theatre Square", "difficulty": "easy", "topics": ["Math"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/1/A"},
    {"id": "cf-71A", "title": "Way Too Long Words", "difficulty": "easy", "topics": ["String"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/71/A"},
    {"id": "cf-158A", "title": "Next Round", "difficulty": "easy", "topics": ["Greedy", "Sorting"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/158/A"},
    {"id": "cf-231A", "title": "Team", "difficulty": "easy", "topics": ["Greedy"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/231/A"},
    {"id": "cf-4A", "title": "Watermelon", "difficulty": "easy", "topics": ["Math", "Greedy"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/4/A"},
    {"id": "cf-1B", "title": "Spreadsheets", "difficulty": "medium", "topics": ["Math", "String", "Implementation"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/1/B"},
    {"id": "cf-2A", "title": "Winner", "difficulty": "medium", "topics": ["Hash Table", "Sorting"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/2/A"},
    {"id": "cf-580C", "title": "Kefa and Park", "difficulty": "medium", "topics": ["Tree", "Depth First Search"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/580/C"},
    {"id": "cf-1352C", "title": "K-th Not Divisible by n", "difficulty": "medium", "topics": ["Math"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/1352/C"},
    {"id": "cf-1C", "title": "Ancient Berland Circus", "difficulty": "hard", "topics": ["Math", "Number Theory"], "platform": "codeforces", "url": "https://codeforces.com/problemset/problem/1/C"},
]


class SuggestionService:

    @staticmethod
    def _build_user_profile(db: Session, user_id: int) -> Optional[UserProfile]:
        """Build UserProfile from database records"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        analytics = db.query(Analytics).filter(Analytics.user_id == user_id).first()

        # Get platform accounts
        accounts = db.query(PlatformAccount).filter(
            PlatformAccount.user_id == user_id
        ).all()
        platforms = [a.platform_name for a in accounts]

        # Aggregate topic counts from problem stats
        account_ids = [a.id for a in accounts]
        problems = db.query(ProblemStats).filter(
            ProblemStats.platform_account_id.in_(account_ids),
            ProblemStats.is_solved == True
        ).all()

        topic_counts: Dict[str, int] = {}
        for p in problems:
            if p.topics:
                for t in p.topics:
                    key = t.lower().replace(" ", "-")
                    topic_counts[key] = topic_counts.get(key, 0) + 1

        # Get streak from analytics
        streak = 0
        if analytics and analytics.current_streak:
            streak = analytics.current_streak

        # Recent topics (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        recent_problems = db.query(ProblemStats).filter(
            ProblemStats.platform_account_id.in_(account_ids),
            ProblemStats.is_solved == True,
            ProblemStats.solved_at >= cutoff
        ).all()

        recent_topics = []
        for p in recent_problems:
            if p.topics:
                recent_topics.extend([t.lower().replace(" ", "-") for t in p.topics])

        return UserProfile(
            user_id=user_id,
            total_solved=analytics.total_problems_solved if analytics else 0,
            easy_solved=analytics.easy_solved if analytics else 0,
            medium_solved=analytics.medium_solved if analytics else 0,
            hard_solved=analytics.hard_solved if analytics else 0,
            topics=topic_counts,
            platforms=platforms,
            streak=streak,
            recent_topics=list(set(recent_topics))[:20]
        )

    @staticmethod
    def _get_solved_ids(db: Session, user_id: int) -> set:
        """Get set of already-solved problem IDs"""
        accounts = db.query(PlatformAccount).filter(
            PlatformAccount.user_id == user_id
        ).all()
        account_ids = [a.id for a in accounts]

        solved = db.query(ProblemStats.problem_id).filter(
            ProblemStats.platform_account_id.in_(account_ids),
            ProblemStats.is_solved == True
        ).all()

        return {s.problem_id for s in solved}

    @staticmethod
    def get_suggestions(
        db: Session,
        user_id: int,
        strategy: str = "balanced",
        n: int = 10,
        difficulty_filter: Optional[str] = None,
        platform_filter: Optional[str] = None,
        topic_filter: Optional[str] = None
    ) -> Dict:
        """Get personalized problem suggestions"""
        profile = SuggestionService._build_user_profile(db, user_id)
        if not profile:
            return {"suggestions": [], "skill_analysis": {}, "error": "User not found"}

        solved_ids = SuggestionService._get_solved_ids(db, user_id)

        # Create a map of problem IDs to full problem data
        problem_map = {p["id"]: p for p in PROBLEM_BANK}

        # Filter candidate problems
        candidates = []
        for p in PROBLEM_BANK:
            if p["id"] in solved_ids:
                continue
            if difficulty_filter and p["difficulty"].lower() != difficulty_filter.lower():
                continue
            if platform_filter and p["platform"].lower() != platform_filter.lower():
                continue
            if topic_filter:
                topic_lower = topic_filter.lower()
                if not any(topic_lower in t.lower() for t in p["topics"]):
                    continue

            candidates.append(ProblemFeature(
                problem_id=p["id"],
                title=p["title"],
                difficulty=p["difficulty"],
                topics=p["topics"],
                platform=p["platform"]
            ))

        suggestions = suggestion_engine.generate_suggestions(
            profile, candidates, n_suggestions=n, strategy=strategy
        )
        
        # Add URLs from problem_map
        for s in suggestions:
            problem_data = problem_map.get(s["problem_id"], {})
            s["url"] = problem_data.get("url", "#")
        
        skill_analysis = suggestion_engine.get_skill_analysis(profile)

        return {
            "suggestions": suggestions,
            "skill_analysis": skill_analysis,
            "profile_summary": {
                "total_solved": profile.total_solved,
                "easy": profile.easy_solved,
                "medium": profile.medium_solved,
                "hard": profile.hard_solved,
                "platforms": profile.platforms,
                "streak": profile.streak,
            }
        }

    @staticmethod
    def get_skill_analysis(db: Session, user_id: int) -> Dict:
        """Get detailed skill analysis without suggestions"""
        profile = SuggestionService._build_user_profile(db, user_id)
        if not profile:
            return {}
        return suggestion_engine.get_skill_analysis(profile)

    @staticmethod
    def get_batch_readiness(db: Session, user_ids: List[int]) -> List[Dict]:
        """Get placement readiness scores for a batch of students"""
        results = []
        for uid in user_ids:
            profile = SuggestionService._build_user_profile(db, uid)
            if profile:
                analysis = suggestion_engine.get_skill_analysis(profile)
                results.append({
                    "user_id": uid,
                    "readiness_score": analysis.get("readiness_score", 0),
                    "skill_tier": analysis.get("skill_tier", "Beginner"),
                    "total_solved": profile.total_solved,
                })
        return results
