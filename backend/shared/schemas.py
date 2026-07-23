from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Profile Schemas
class ProfileBase(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_public: bool = True

class ProfileCreate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    portfolio_slug: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Platform Account Schemas
class PlatformAccountBase(BaseModel):
    platform_name: str
    platform_username: str

class PlatformAccountCreate(PlatformAccountBase):
    pass

class PlatformAccountResponse(PlatformAccountBase):
    id: int
    user_id: int
    is_verified: bool
    last_synced_at: Optional[datetime]
    sync_enabled: bool
    
    class Config:
        from_attributes = True

# Problem Stats Schemas
class ProblemStatsResponse(BaseModel):
    id: int
    problem_id: str
    problem_title: Optional[str]
    difficulty: Optional[str]
    topics: Optional[List[str]]
    solved_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Analytics Schemas
class AnalyticsResponse(BaseModel):
    total_problems_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    current_streak: int
    longest_streak: int
    topic_distribution: Optional[Dict]
    platform_distribution: Optional[Dict]
    last_calculated_at: datetime
    
    class Config:
        from_attributes = True


# Role-based Schemas
class UserRole:
    STUDENT = "student"
    FACULTY = "faculty"
    DEPT_ADMIN = "dept_admin"
    MANAGEMENT = "management"
    SUPER_ADMIN = "super_admin"

# College Schemas
class CollegeBase(BaseModel):
    name: str
    code: str
    location: Optional[str] = None
    admin_notes: Optional[str] = None
    max_students: Optional[int] = None
    subscription_tier: str = "free"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    established_year: Optional[int] = None

class CollegeCreate(CollegeBase):
    pass

class CollegeUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    admin_notes: Optional[str] = None
    max_students: Optional[int] = None
    subscription_tier: Optional[str] = None
    is_active: Optional[bool] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    established_year: Optional[int] = None

class CollegeResponse(CollegeBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class CollegeWithStats(CollegeResponse):
    total_users: int = 0
    total_students: int = 0
    total_faculty: int = 0

# Extended User Schemas
class UserWithRoleResponse(UserResponse):
    role: str
    college_id: Optional[int]
    department: Optional[str]
    batch_year: Optional[int]
    enrollment_number: Optional[str]
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None   # ISO date string
    specialization: Optional[str] = None
    is_first_login: Optional[bool] = None
    
    class Config:
        from_attributes = True

# Mentor Assignment Schemas
class MentorAssignmentCreate(BaseModel):
    mentor_id: int
    student_id: int
    notes: Optional[str] = None

class MentorAssignmentResponse(BaseModel):
    id: int
    mentor_id: int
    student_id: int
    assigned_at: datetime
    is_active: bool
    notes: Optional[str] = None
    unassigned_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Mentor Feedback Schemas
class MentorFeedbackCreate(BaseModel):
    student_id: int
    feedback_type: str
    title: Optional[str] = None
    content: str
    priority: str = "normal"

class MentorFeedbackResponse(BaseModel):
    id: int
    mentor_id: int
    student_id: int
    feedback_type: str
    title: Optional[str]
    content: str
    priority: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Coding Goal Schemas
class CodingGoalCreate(BaseModel):
    target_type: str
    target_id: Optional[int] = None
    batch_year: Optional[int] = None
    department: Optional[str] = None
    goal_type: str
    target_value: int
    deadline: Optional[datetime] = None
    description: Optional[str] = None

class CodingGoalResponse(BaseModel):
    id: int
    created_by: int
    target_type: str
    goal_type: str
    target_value: int
    deadline: Optional[datetime]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Problem Note Schemas
class ProblemNoteCreate(BaseModel):
    problem_stat_id: int
    note_content: str
    tags: Optional[List[str]] = None

class ProblemNoteResponse(BaseModel):
    id: int
    user_id: int
    problem_stat_id: int
    note_content: str
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Student Progress Summary
class StudentProgressSummary(BaseModel):
    user_id: int
    username: str
    full_name: Optional[str]
    batch_year: Optional[int]
    department: Optional[str]
    total_problems: int
    current_streak: int
    last_active: Optional[datetime]
    mentor_feedback_count: int

# Batch Analytics
class BatchAnalytics(BaseModel):
    batch_year: int
    total_students: int
    active_students: int
    total_problems_solved: int
    avg_problems_per_student: float
    top_performers: List[Dict]

# Department Analytics
class DepartmentAnalytics(BaseModel):
    department: str
    total_students: int
    total_problems_solved: int
    avg_streak: float
    platform_distribution: Dict


# User Management Schemas
class UserCreateByAdmin(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "student"
    college_id: Optional[int] = None
    department: Optional[str] = None
    batch_year: Optional[int] = None
    enrollment_number: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None   # ISO date string YYYY-MM-DD
    specialization: Optional[str] = None

class UserUpdateByAdmin(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    college_id: Optional[int] = None
    department: Optional[str] = None
    batch_year: Optional[int] = None
    enrollment_number: Optional[str] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None
    specialization: Optional[str] = None

# System Stats Schemas
class SystemStatsResponse(BaseModel):
    total_users: int
    total_colleges: int
    total_problems_solved: int
    total_platform_connections: int
    active_users_today: int
    active_users_week: int
    active_users_month: int
    calculated_at: datetime
    
    class Config:
        from_attributes = True

# Admin Dashboard Schemas
class AdminDashboardStats(BaseModel):
    total_users: int
    total_colleges: int
    total_students: int
    total_faculty: int
    total_problems_solved: int
    active_users_week: int
    colleges_list: List[CollegeWithStats]
    recent_users: List[UserWithRoleResponse]


# Peer Discussion Schemas
class DiscussionCreate(BaseModel):
    title: str
    content: str
    problem_stat_id: Optional[int] = None
    tags: Optional[List[str]] = []

class DiscussionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_solved: Optional[bool] = None

class DiscussionReplyCreate(BaseModel):
    content: str
    is_solution: bool = False

class DiscussionVoteCreate(BaseModel):
    vote_type: str  # 'upvote' or 'downvote'

class DiscussionReplyResponse(BaseModel):
    id: int
    discussion_id: int
    user_id: int
    username: str
    full_name: Optional[str]
    content: str
    upvotes: int
    is_solution: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DiscussionResponse(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: Optional[str]
    problem_stat_id: Optional[int]
    problem_title: Optional[str]
    title: str
    content: str
    tags: Optional[List[str]]
    upvotes: int
    is_solved: bool
    reply_count: int
    created_at: datetime
    updated_at: datetime
    user_voted: Optional[str] = None  # 'upvote', 'downvote', or None
    
    class Config:
        from_attributes = True

class DiscussionDetailResponse(DiscussionResponse):
    replies: List[DiscussionReplyResponse] = []

# Submission View Schemas
class SubmissionFilterParams(BaseModel):
    platform: Optional[str] = None
    difficulty: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    page: int = 1
    limit: int = 20

class SubmissionResponse(BaseModel):
    id: int
    problem_id: str
    problem_title: Optional[str]
    platform: str
    difficulty: Optional[str]
    status: str
    language: Optional[str]
    submission_time: Optional[datetime]
    runtime: Optional[str]
    memory: Optional[str]
    submission_url: Optional[str]
    
    class Config:
        from_attributes = True

class SubmissionStatsResponse(BaseModel):
    total_submissions: int
    accepted: int
    wrong_answer: int
    time_limit_exceeded: int
    runtime_error: int
    by_platform: Dict[str, int]
    by_difficulty: Dict[str, int]
    by_language: Dict[str, int]
    recent_submissions: List[SubmissionResponse]

# Suggestion Feedback Schema
class SuggestionFeedbackCreate(BaseModel):
    problem_id: str
    platform: str
    strategy: Optional[str] = None
    was_helpful: Optional[bool] = None
    was_solved: Optional[bool] = None
    difficulty_felt: Optional[str] = None  # too_easy | just_right | too_hard
    suggestion_score: Optional[float] = None


# ── Faculty Management Schemas (used by super_admin) ─────────────────────────

class FacultyCreate(BaseModel):
    """Admin creates a faculty member — password is auto-generated and emailed."""
    email: EmailStr
    username: str
    full_name: str
    college_id: int
    department: Optional[str] = None
    role: str = "faculty"  # faculty | dept_admin | management
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None   # ISO date YYYY-MM-DD
    specialization: Optional[str] = None


class FacultyUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None
    specialization: Optional[str] = None


class FacultyResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    college_id: Optional[int]
    college_name: Optional[str] = None
    department: Optional[str]
    is_active: bool
    created_at: datetime
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None
    specialization: Optional[str] = None

    class Config:
        from_attributes = True


# ── Student Management Schemas (used by faculty) ─────────────────────────────

class StudentCreate(BaseModel):
    """Faculty creates a student — password is auto-generated and emailed."""
    email: EmailStr
    username: str
    full_name: str
    department: Optional[str] = None
    batch_year: Optional[int] = None
    enrollment_number: Optional[str] = None


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    batch_year: Optional[int] = None
    enrollment_number: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    college_id: Optional[int]
    department: Optional[str]
    batch_year: Optional[int]
    enrollment_number: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BulkStudentResult(BaseModel):
    """Result of a bulk student creation operation."""
    created: int
    failed: int
    errors: List[Dict]  # [{row, email, reason}]
    students: List[StudentResponse]


class ResetPasswordResponse(BaseModel):
    message: str
    email_sent: bool

class FeedbackResponseEnhanced(MentorFeedbackResponse):
    mentor_name: str
    problem_title: Optional[str] = None
    action_items: Optional[List[str]] = []
    
    class Config:
        from_attributes = True

class FeedbackStatsResponse(BaseModel):
    total_feedback: int
    unread_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    recent_feedback: List[FeedbackResponseEnhanced]


# ── Chat Schemas ──────────────────────────────────────────────────────────────

class ChatMessageCreate(BaseModel):
    recipient_id: int
    content: str


class ChatMessageResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    sender_name: Optional[str] = None
    sender_username: Optional[str] = None
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChatConversationSummary(BaseModel):
    """One entry in the conversations list sidebar."""
    partner_id: int
    partner_name: Optional[str]
    partner_username: str
    partner_role: str
    last_message: Optional[str]
    last_message_at: Optional[datetime]
    unread_count: int
