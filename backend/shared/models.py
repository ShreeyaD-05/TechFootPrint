from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, JSON, Float, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="student")  # student, faculty, dept_admin, management, super_admin
    college_id = Column(Integer, ForeignKey("colleges.id"))
    department = Column(String)
    batch_year = Column(Integer)
    enrollment_number = Column(String)

    # Faculty-specific fields
    phone = Column(String(20))
    employee_id = Column(String(50))          # staff/employee ID issued by the college
    joining_date = Column(Date)               # date faculty joined the institution
    specialization = Column(String(200))      # subject / area of expertise

    # Auth helpers
    is_active = Column(Boolean, default=True)
    is_first_login = Column(Boolean, default=True)  # force password change on first login

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    college = relationship("College", back_populates="users")
    profile = relationship("Profile", back_populates="user", uselist=False)
    platform_accounts = relationship("PlatformAccount", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")
    mentor_assignments_as_mentor = relationship("MentorAssignment", foreign_keys="MentorAssignment.mentor_id", back_populates="mentor")
    mentor_assignments_as_student = relationship("MentorAssignment", foreign_keys="MentorAssignment.student_id", back_populates="student")
    feedback_given = relationship("MentorFeedback", foreign_keys="MentorFeedback.mentor_id", back_populates="mentor")
    feedback_received = relationship("MentorFeedback", foreign_keys="MentorFeedback.student_id", back_populates="student")
    problem_notes = relationship("ProblemNote", back_populates="user")
    discussions = relationship("PeerDiscussion", back_populates="user")
    sent_messages = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id", back_populates="sender")
    received_messages = relationship("ChatMessage", foreign_keys="ChatMessage.recipient_id", back_populates="recipient")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bio = Column(Text)
    avatar_url = Column(String)
    location = Column(String)
    website = Column(String)
    github_username = Column(String)
    linkedin_url = Column(String)
    is_public = Column(Boolean, default=True)
    portfolio_slug = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="profile")

class PlatformAccount(Base):
    __tablename__ = "platform_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform_name = Column(String, nullable=False)  # leetcode, codeforces, etc.
    platform_username = Column(String, nullable=False)
    platform_user_id = Column(String)
    is_verified = Column(Boolean, default=False)
    last_synced_at = Column(DateTime)
    sync_enabled = Column(Boolean, default=True)
    credentials = Column(JSON)  # encrypted credentials if needed
    profile_stats = Column(JSON)  # Store profile-level stats (total_solved, easy, medium, hard)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="platform_accounts")
    problem_stats = relationship("ProblemStats", back_populates="platform_account")
    contest_stats = relationship("ContestStats", back_populates="platform_account")

class ProblemStats(Base):
    __tablename__ = "problem_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"))
    problem_id = Column(String, nullable=False)
    problem_title = Column(String)
    difficulty = Column(String)  # easy, medium, hard
    topics = Column(JSON)  # array of topics
    solved_at = Column(DateTime)
    submission_count = Column(Integer, default=1)
    is_solved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    platform_account = relationship("PlatformAccount", back_populates="problem_stats")
    submissions = relationship("Submission", back_populates="problem_stat", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_stat_id = Column(Integer, ForeignKey("problem_stats.id"))
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"))
    submission_id = Column(String)  # Platform-specific submission ID
    status = Column(String)  # accepted, wrong_answer, time_limit_exceeded, etc.
    language = Column(String)
    runtime = Column(String)
    memory = Column(String)
    submitted_at = Column(DateTime)
    code = Column(Text)  # Optional: store submission code
    created_at = Column(DateTime, default=datetime.utcnow)
    
    problem_stat = relationship("ProblemStats", back_populates="submissions")
    platform_account = relationship("PlatformAccount")

class ContestStats(Base):
    __tablename__ = "contest_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"))
    contest_id = Column(String, nullable=False)
    contest_name = Column(String)
    rating = Column(Integer)
    rank = Column(Integer)
    problems_solved = Column(Integer)
    contest_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    platform_account = relationship("PlatformAccount", back_populates="contest_stats")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String)  # problem_solved, contest_participated, etc.
    platform = Column(String)
    activity_data = Column(JSON)
    activity_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="activity_logs")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_problems_solved = Column(Integer, default=0)
    easy_solved = Column(Integer, default=0)
    medium_solved = Column(Integer, default=0)
    hard_solved = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    topic_distribution = Column(JSON)
    platform_distribution = Column(JSON)
    last_calculated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PortfolioData(Base):
    __tablename__ = "portfolio_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    portfolio_json = Column(JSON)
    view_count = Column(Integer, default=0)
    last_generated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PlatformProfileStats(Base):
    __tablename__ = "platform_profile_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"), nullable=False)
    total_solved = Column(Integer, default=0)
    easy_solved = Column(Integer, default=0)
    medium_solved = Column(Integer, default=0)
    hard_solved = Column(Integer, default=0)
    rating = Column(Integer)
    rank = Column(String)
    contests_attended = Column(Integer, default=0)
    fetched_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class College(Base):
    __tablename__ = "colleges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    location = Column(String)
    admin_notes = Column(Text)
    max_students = Column(Integer)
    subscription_tier = Column(String, default="free")
    is_active = Column(Boolean, default=True, index=True)

    # Contact & metadata
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    website = Column(String(500))
    established_year = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="college")

class SystemStats(Base):
    __tablename__ = "system_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    total_users = Column(Integer, default=0)
    total_colleges = Column(Integer, default=0)
    total_problems_solved = Column(Integer, default=0)
    total_platform_connections = Column(Integer, default=0)
    active_users_today = Column(Integer, default=0)
    active_users_week = Column(Integer, default=0)
    active_users_month = Column(Integer, default=0)
    calculated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MentorAssignment(Base):
    __tablename__ = "mentor_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)                          # reason / context for assignment
    unassigned_at = Column(DateTime)              # when deactivated
    created_at = Column(DateTime, default=datetime.utcnow)
    
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="mentor_assignments_as_mentor")
    student = relationship("User", foreign_keys=[student_id], back_populates="mentor_assignments_as_student")

class MentorFeedback(Base):
    __tablename__ = "mentor_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String, nullable=False)  # comment, task, recommendation
    title = Column(String)
    content = Column(Text, nullable=False)
    priority = Column(String, default="normal")  # low, normal, high
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="feedback_given")
    student = relationship("User", foreign_keys=[student_id], back_populates="feedback_received")

class CodingGoal(Base):
    __tablename__ = "coding_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_type = Column(String, nullable=False)  # student, batch, department
    target_id = Column(Integer, ForeignKey("users.id"))
    batch_year = Column(Integer)
    department = Column(String)
    goal_type = Column(String, nullable=False)  # problems_count, streak, contest
    target_value = Column(Integer, nullable=False)
    deadline = Column(DateTime)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProblemNote(Base):
    __tablename__ = "problem_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_stat_id = Column(Integer, ForeignKey("problem_stats.id"), nullable=False)
    note_content = Column(Text, nullable=False)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="problem_notes")
    problem_stat = relationship("ProblemStats")


class PeerDiscussion(Base):
    __tablename__ = "peer_discussions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_stat_id = Column(Integer, ForeignKey("problem_stats.id"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=[])
    upvotes = Column(Integer, default=0)
    is_solved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="discussions")
    problem_stat = relationship("ProblemStats")
    replies = relationship("DiscussionReply", back_populates="discussion", cascade="all, delete-orphan")
    votes = relationship("DiscussionVote", back_populates="discussion", cascade="all, delete-orphan")


class DiscussionReply(Base):
    __tablename__ = "discussion_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    discussion_id = Column(Integer, ForeignKey("peer_discussions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    upvotes = Column(Integer, default=0)
    is_solution = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    discussion = relationship("PeerDiscussion", back_populates="replies")
    user = relationship("User")
    votes = relationship("DiscussionVote", back_populates="reply", cascade="all, delete-orphan")


class DiscussionVote(Base):
    __tablename__ = "discussion_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    discussion_id = Column(Integer, ForeignKey("peer_discussions.id", ondelete="CASCADE"), nullable=True)
    reply_id = Column(Integer, ForeignKey("discussion_replies.id", ondelete="CASCADE"), nullable=True)
    vote_type = Column(String(10), nullable=False)  # 'upvote' or 'downvote'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    discussion = relationship("PeerDiscussion", back_populates="votes")
    reply = relationship("DiscussionReply", back_populates="votes")


class SuggestionFeedback(Base):
    """Stores user feedback on AI suggestions — used to improve the DL model"""
    __tablename__ = "suggestion_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False)
    strategy = Column(String)
    was_helpful = Column(Boolean)
    was_solved = Column(Boolean)
    difficulty_felt = Column(String)  # too_easy | just_right | too_hard
    suggestion_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class ChatMessage(Base):
    """
    Direct messages between two users (faculty ↔ student).
    A conversation is identified by the sorted pair (sender_id, recipient_id).
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    # Soft-delete: hide from one side without losing history
    deleted_by_sender = Column(Boolean, default=False)
    deleted_by_recipient = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
