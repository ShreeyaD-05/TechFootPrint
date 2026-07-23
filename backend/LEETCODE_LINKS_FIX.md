# LeetCode Links Fix

## Problem
The LeetCode problem links in the Suggestions page were not working because:
1. The backend was not providing URLs for problems
2. The frontend was trying to construct URLs from problem IDs, but LeetCode URLs require problem slugs (e.g., "two-sum"), not just numbers

## Solution

### Backend Changes
**File: `backend/services/suggestions/service.py`**

Added a `url` field to each problem in the `PROBLEM_BANK`:
- LeetCode problems: `https://leetcode.com/problems/{slug}/`
- Codeforces problems: `https://codeforces.com/problemset/problem/{contest}/{problem}/`

Example:
```python
{
    "id": "lc-1",
    "title": "Two Sum",
    "difficulty": "easy",
    "topics": ["Array", "Hash Table"],
    "platform": "leetcode",
    "url": "https://leetcode.com/problems/two-sum/"  # ← NEW
}
```

### Frontend Changes
**File: `frontend/src/pages/Suggestions.jsx`**

Changed from constructing URLs to using the `url` field from the API response:

**Before:**
```javascript
const platformUrl = {
  leetcode: `https://leetcode.com/problems/${s.problem_id?.replace('lc-', '')}`,
  codeforces: `https://codeforces.com/problemset/problem/${s.problem_id?.replace('cf-', '').replace(/([A-Z])$/, '/$1')}`,
}[s.platform] || '#'
```

**After:**
```javascript
const platformUrl = s.url || '#'
```

## Benefits
1. ✅ All LeetCode links now work correctly
2. ✅ All Codeforces links now work correctly
3. ✅ Cleaner frontend code (no URL construction logic)
4. ✅ More maintainable (URLs are centralized in the backend)
5. ✅ Easier to add new platforms in the future

## Testing
- Verified all 45 problems in PROBLEM_BANK have correct URLs
- Tested LeetCode URLs: `https://leetcode.com/problems/two-sum/` ✅
- Tested Codeforces URLs: `https://codeforces.com/problemset/problem/1/A` ✅
- Integration test passes with new URL field ✅

## Deployment
No additional steps needed. The changes are backward compatible:
- If a problem doesn't have a `url` field, it defaults to `#`
- Existing API responses will include the new `url` field automatically
