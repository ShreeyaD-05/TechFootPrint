# API Documentation

Base URL: `http://localhost:8000`

## Authentication

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepass123",
  "full_name": "John Doe"
}
```

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=securepass123
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer {token}
```

## User Profile

### Create Profile
```http
POST /users/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "bio": "Software Engineer",
  "location": "San Francisco",
  "website": "https://example.com",
  "github_username": "johndoe",
  "is_public": true
}
```

### Get Profile
```http
GET /users/profile
Authorization: Bearer {token}
```

### Update Profile
```http
PUT /users/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "bio": "Updated bio"
}
```

## Platforms

### List Available Platforms
```http
GET /platforms/available
```

Response:
```json
{
  "platforms": ["leetcode", "codeforces", "codechef"]
}
```

### Connect Platform
```http
POST /platforms/connect
Authorization: Bearer {token}
Content-Type: application/json

{
  "platform_name": "leetcode",
  "platform_username": "johndoe"
}
```

### List Connected Platforms
```http
GET /platforms/connected
Authorization: Bearer {token}
```

### Sync Platform
```http
POST /platforms/sync/{platform_id}
Authorization: Bearer {token}
```

### Disconnect Platform
```http
DELETE /platforms/{platform_id}
Authorization: Bearer {token}
```

## Analytics

### Get Analytics
```http
GET /analytics/
Authorization: Bearer {token}
```

Response:
```json
{
  "total_problems_solved": 150,
  "easy_solved": 50,
  "medium_solved": 75,
  "hard_solved": 25,
  "current_streak": 7,
  "longest_streak": 30,
  "topic_distribution": {
    "arrays": 40,
    "dynamic-programming": 25
  },
  "platform_distribution": {
    "leetcode": 100,
    "codeforces": 50
  }
}
```

### Recalculate Analytics
```http
POST /analytics/recalculate
Authorization: Bearer {token}
```

### Get Activity Heatmap
```http
GET /analytics/heatmap?days=365
Authorization: Bearer {token}
```

## Portfolio

### Generate Portfolio
```http
POST /portfolio/generate
Authorization: Bearer {token}
```

### Get Public Portfolio
```http
GET /portfolio/{portfolio_slug}
```

Response:
```json
{
  "profile": {
    "username": "johndoe",
    "full_name": "John Doe",
    "bio": "Software Engineer",
    "avatar_url": "https://...",
    "location": "San Francisco"
  },
  "analytics": {
    "total_problems_solved": 150,
    "easy_solved": 50,
    "medium_solved": 75,
    "hard_solved": 25
  },
  "platforms": [
    {
      "name": "leetcode",
      "username": "johndoe"
    }
  ]
}
```

## Error Responses

All endpoints may return these error codes:

- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error format:
```json
{
  "detail": "Error message"
}
```


## Platform Management

### List Available Platforms
```http
GET /platforms/available
Authorization: Bearer {token}
```

Response:
```json
{
  "platforms": ["leetcode", "codeforces", "github", "codechef", "hackerrank", "geeksforgeeks"]
}
```

### Connect Platform
```http
POST /platforms/connect
Authorization: Bearer {token}
Content-Type: application/json

{
  "platform_name": "leetcode",
  "platform_username": "your_username"
}
```

### List Connected Platforms
```http
GET /platforms/connected
Authorization: Bearer {token}
```

### Get Platform Problems
```http
GET /platforms/{platform_id}/problems
Authorization: Bearer {token}
```

Response:
```json
[
  {
    "id": 1,
    "platform_account_id": 1,
    "problem_id": "two-sum",
    "problem_title": "Two Sum",
    "difficulty": "Easy",
    "topics": ["Array", "Hash Table"],
    "solved_at": "2024-03-07T10:30:00",
    "submission_count": 3,
    "is_solved": true
  }
]
```

### Get Problem Submissions
```http
GET /platforms/{platform_id}/problems/{problem_id}/submissions
Authorization: Bearer {token}
```

Response:
```json
{
  "problem": {
    "id": 1,
    "title": "Two Sum",
    "difficulty": "Easy",
    "topics": ["Array", "Hash Table"],
    "solved_at": "2024-03-07T10:30:00"
  },
  "submissions": [
    {
      "id": 1,
      "submission_id": "12345",
      "status": "accepted",
      "language": "Python3",
      "runtime": "52 ms",
      "memory": "14.2 MB",
      "submitted_at": "2024-03-07T10:30:00",
      "code": "class Solution:\n    def twoSum(self, nums, target):\n        ..."
    }
  ]
}
```

### Sync Platform
```http
POST /platforms/sync/{platform_id}
Authorization: Bearer {token}
```

### Disconnect Platform
```http
DELETE /platforms/{platform_id}
Authorization: Bearer {token}
```

## Supported Platforms

### LeetCode
- Profile stats (total solved, easy/medium/hard breakdown)
- Recent submissions (up to 500)
- Contest history
- Activity tracking

### Codeforces
- Profile stats with rating
- Problem submissions
- Contest participation
- Rating history

### GitHub
- Repository count
- Public activity
- Contribution tracking

### CodeChef
- Profile stats with rating
- Solved problems
- Contest history
- Rating data

### HackerRank
- Profile stats
- Recent challenges
- Contest participation
- Domain-wise scores

### GeeksforGeeks
- Profile stats
- Problem count by difficulty
- Basic activity tracking
