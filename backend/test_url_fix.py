#!/usr/bin/env python
"""
Test that URLs are correctly returned in suggestion API responses.
"""

import sys
sys.path.insert(0, '.')

import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models import Base, User, Profile
from services.suggestions.service import SuggestionService, PROBLEM_BANK
from services.suggestions.model import UserProfile as UserProfileModel
from services.inference.predict import get_engine

# ── Setup test database ────────────────────────────────────────────────────────

DATABASE_URL = "sqlite:///./test_url.db"
engine_db = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine_db)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)

db = SessionLocal()

# Clean up old test user
old_user = db.query(User).filter(User.email == "test_url@example.com").first()
if old_user:
    db.query(Profile).filter(Profile.user_id == old_user.id).delete()
    db.delete(old_user)
    db.commit()

# Create test user
test_user = User(
    email="test_url@example.com",
    username="test_url_user",
    hashed_password="dummy_hash",
    role="student",
    batch_year=2024,
    department="CSE"
)
db.add(test_user)
db.commit()
db.refresh(test_user)

print(f"✅ Created test user: {test_user.id}")

# ── Test 1: Rule-based system URLs ─────────────────────────────────────────────

print("\n" + "="*70)
print("TESTING RULE-BASED SYSTEM URLs")
print("="*70)

try:
    rb_result = SuggestionService.get_suggestions(
        db, test_user.id,
        strategy="balanced", n=5
    )
    
    suggestions = rb_result.get("suggestions", [])
    print(f"✅ Rule-based returned {len(suggestions)} suggestions")
    
    for i, s in enumerate(suggestions[:3], 1):
        url = s.get("url", "NO URL")
        print(f"\n   Suggestion {i}:")
        print(f"   - Title: {s.get('title', 'NO TITLE')}")
        print(f"   - Platform: {s.get('platform', 'NO PLATFORM')}")
        print(f"   - URL: {url}")
        
        if url == "NO URL" or url == "#":
            print(f"   ❌ Missing URL!")
        elif url.startswith("https://"):
            print(f"   ✅ Valid URL")
        else:
            print(f"   ❌ Invalid URL format")
            
except Exception as e:
    print(f"❌ Rule-based test failed: {e}")
    import traceback
    traceback.print_exc()

# ── Test 2: DL system URLs ─────────────────────────────────────────────────────

print("\n" + "="*70)
print("TESTING DL SYSTEM URLs")
print("="*70)

try:
    engine_dl = get_engine(device_str="cpu")
    if engine_dl is None:
        print("❌ DL model not loaded!")
    else:
        # Build user profile for DL model
        user_profile_dl = UserProfileModel(
            user_id=test_user.id,
            total_solved=10,
            easy_solved=8,
            medium_solved=2,
            hard_solved=0,
            topics={"array": 5, "string": 3},
            platforms=["leetcode"],
            recent_topics=["array", "string"],
            streak=3
        )
        
        # Get candidate problems (first 20 from PROBLEM_BANK)
        candidates = PROBLEM_BANK[:20]
        
        dl_recs = engine_dl.recommend(
            user_profile=user_profile_dl,
            candidate_problems=candidates,
            n=5,
            strategy="balanced",
            use_exploration=True
        )
        
        print(f"✅ DL model returned {len(dl_recs)} recommendations")
        
        for i, rec in enumerate(dl_recs[:3], 1):
            url = rec.get("url", "NO URL")
            print(f"\n   Recommendation {i}:")
            print(f"   - Title: {rec.get('title', 'NO TITLE')}")
            print(f"   - Platform: {rec.get('platform', 'NO PLATFORM')}")
            print(f"   - URL: {url}")
            
            if url == "NO URL" or url == "#":
                print(f"   ❌ Missing URL!")
            elif url.startswith("https://"):
                print(f"   ✅ Valid URL")
            else:
                print(f"   ❌ Invalid URL format")
                
except Exception as e:
    print(f"❌ DL test failed: {e}")
    import traceback
    traceback.print_exc()

# ── Test 3: Verify specific URLs ───────────────────────────────────────────────

print("\n" + "="*70)
print("TESTING SPECIFIC URLs")
print("="*70)

test_problems = [
    ("lc-1", "Two Sum", "https://leetcode.com/problems/two-sum/"),
    ("lc-121", "Best Time to Buy and Sell Stock", "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/"),
    ("cf-1A", "Theatre Square", "https://codeforces.com/problemset/problem/1/A"),
]

for pid, title, expected_url in test_problems:
    problem = next((p for p in PROBLEM_BANK if p["id"] == pid), None)
    if problem:
        actual_url = problem.get("url", "NO URL")
        if actual_url == expected_url:
            print(f"✅ {title}: URL correct")
        else:
            print(f"❌ {title}: Expected {expected_url}, got {actual_url}")
    else:
        print(f"❌ {title}: Problem not found in PROBLEM_BANK")

# ── Cleanup ────────────────────────────────────────────────────────────────────

db.close()

print("\n" + "="*70)
print("✅ URL TESTS COMPLETED!")
print("="*70)
print("\nThe LeetCode and Codeforces links should now work correctly.")
print("Users can click the external link icon to open problems in new tabs.")