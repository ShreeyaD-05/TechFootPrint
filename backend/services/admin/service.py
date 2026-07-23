from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import secrets
import string
from shared.models import User, College, SystemStats, Analytics, PlatformAccount, ActivityLog
from shared.schemas import CollegeCreate, CollegeUpdate, UserCreateByAdmin, UserUpdateByAdmin, FacultyCreate, FacultyUpdate
from services.auth.service import AuthService

class AdminService:
    @staticmethod
    def get_system_stats(db: Session) -> dict:
        """Get overall system statistics"""
        total_users = db.query(func.count(User.id)).scalar()
        total_colleges = db.query(func.count(College.id)).scalar()
        
        # Total problems solved across all users
        total_problems = db.query(func.sum(Analytics.total_problems_solved)).scalar() or 0
        
        # Total platform connections
        total_connections = db.query(func.count(PlatformAccount.id)).scalar()
        
        # Active users
        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        active_today = db.query(func.count(func.distinct(ActivityLog.user_id))).filter(
            func.date(ActivityLog.activity_date) == today
        ).scalar()
        
        active_week = db.query(func.count(func.distinct(ActivityLog.user_id))).filter(
            ActivityLog.activity_date >= week_ago
        ).scalar()
        
        active_month = db.query(func.count(func.distinct(ActivityLog.user_id))).filter(
            ActivityLog.activity_date >= month_ago
        ).scalar()
        
        return {
            "total_users": total_users,
            "total_colleges": total_colleges,
            "total_problems_solved": total_problems,
            "total_platform_connections": total_connections,
            "active_users_today": active_today,
            "active_users_week": active_week,
            "active_users_month": active_month,
            "calculated_at": datetime.utcnow()
        }
    
    @staticmethod
    def get_all_colleges(db: Session, include_stats: bool = False) -> List[dict]:
        """Get all colleges with optional statistics"""
        colleges = db.query(College).all()

        if not include_stats:
            return colleges

        # Single query: count users per college grouped by role
        from sqlalchemy import case
        role_counts = db.query(
            User.college_id,
            func.count(User.id).label("total_users"),
            func.sum(case((User.role == "student", 1), else_=0)).label("total_students"),
            func.sum(case((User.role.in_(["faculty", "dept_admin", "management"]), 1), else_=0)).label("total_faculty"),
        ).group_by(User.college_id).all()

        counts_by_college = {
            row.college_id: {
                "total_users": row.total_users,
                "total_students": int(row.total_students or 0),
                "total_faculty": int(row.total_faculty or 0),
            }
            for row in role_counts
        }

        result = []
        for college in colleges:
            counts = counts_by_college.get(college.id, {"total_users": 0, "total_students": 0, "total_faculty": 0})
            result.append({
                "id": college.id,
                "name": college.name,
                "code": college.code,
                "location": college.location,
                "admin_notes": college.admin_notes,
                "max_students": college.max_students,
                "subscription_tier": college.subscription_tier,
                "is_active": college.is_active,
                "created_at": college.created_at,
                **counts,
            })

        return result
    
    @staticmethod
    def create_college(db: Session, college: CollegeCreate) -> College:
        """Create a new college"""
        db_college = College(**college.dict())
        db.add(db_college)
        db.commit()
        db.refresh(db_college)
        return db_college
    
    @staticmethod
    def update_college(db: Session, college_id: int, college_update: CollegeUpdate) -> College:
        """Update college information"""
        db_college = db.query(College).filter(College.id == college_id).first()
        if not db_college:
            return None
        
        for key, value in college_update.dict(exclude_unset=True).items():
            setattr(db_college, key, value)
        
        db.commit()
        db.refresh(db_college)
        return db_college
    
    @staticmethod
    def delete_college(db: Session, college_id: int) -> bool:
        """Soft delete a college"""
        db_college = db.query(College).filter(College.id == college_id).first()
        if not db_college:
            return False
        
        db_college.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def get_all_users(db: Session, college_id: Optional[int] = None, role: Optional[str] = None) -> List[User]:
        """Get all users with optional filters"""
        query = db.query(User)
        
        if college_id:
            query = query.filter(User.college_id == college_id)
        
        if role:
            query = query.filter(User.role == role)
        
        return query.order_by(User.created_at.desc()).all()
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreateByAdmin) -> User:
        """Create a new user (admin function)"""
        # Check if user exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise ValueError("Email already registered")
        if db.query(User).filter(User.username == user_data.username).first():
            raise ValueError("Username already taken")
        
        hashed_password = AuthService.get_password_hash(user_data.password)

        # Parse joining_date if provided
        joining_date = None
        if getattr(user_data, 'joining_date', None):
            from datetime import date
            try:
                joining_date = date.fromisoformat(user_data.joining_date)
            except ValueError:
                pass
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
            college_id=user_data.college_id,
            department=user_data.department,
            batch_year=user_data.batch_year,
            enrollment_number=user_data.enrollment_number,
            phone=getattr(user_data, 'phone', None),
            employee_id=getattr(user_data, 'employee_id', None),
            joining_date=joining_date,
            specialization=getattr(user_data, 'specialization', None),
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create profile
        from shared.models import Profile
        profile = Profile(
            user_id=db_user.id,
            portfolio_slug=db_user.username,
            is_public=True
        )
        db.add(profile)
        db.commit()
        
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdateByAdmin) -> User:
        """Update user information (admin function)"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Soft delete a user"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        
        db_user.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def get_recent_users(db: Session, limit: int = 10) -> List[User]:
        """Get recently created users"""
        return db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def search_users(db: Session, query: str) -> List[User]:
        """Search users by username, email, or full name"""
        search_pattern = f"%{query}%"
        return db.query(User).filter(
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern))
        ).limit(50).all()

    # ── Faculty Management ────────────────────────────────────────────────────

    @staticmethod
    def _generate_temp_password(length: int = 12) -> str:
        """Generate a secure temporary password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def get_all_faculty(db: Session, college_id: Optional[int] = None) -> List[User]:
        """Get all faculty/dept_admin/management users."""
        query = db.query(User).filter(
            User.role.in_(["faculty", "dept_admin", "management"])
        )
        if college_id:
            query = query.filter(User.college_id == college_id)
        return query.order_by(User.created_at.desc()).all()

    @staticmethod
    def create_faculty(db: Session, faculty_data: FacultyCreate) -> Tuple[User, str]:
        """
        Create a faculty account.
        Returns (user, temp_password) — caller is responsible for sending the email.
        """
        if db.query(User).filter(User.email == faculty_data.email).first():
            raise ValueError("Email already registered")
        if db.query(User).filter(User.username == faculty_data.username).first():
            raise ValueError("Username already taken")

        temp_password = AdminService._generate_temp_password()
        hashed = AuthService.get_password_hash(temp_password)

        # Parse joining_date if provided
        joining_date = None
        if getattr(faculty_data, 'joining_date', None):
            from datetime import date
            try:
                joining_date = date.fromisoformat(faculty_data.joining_date)
            except ValueError:
                pass

        db_user = User(
            username=faculty_data.username,
            email=faculty_data.email,
            hashed_password=hashed,
            full_name=faculty_data.full_name,
            role=faculty_data.role,
            college_id=faculty_data.college_id,
            department=faculty_data.department,
            phone=getattr(faculty_data, 'phone', None),
            employee_id=getattr(faculty_data, 'employee_id', None),
            joining_date=joining_date,
            specialization=getattr(faculty_data, 'specialization', None),
            is_first_login=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Auto-create profile
        from shared.models import Profile
        db.add(Profile(user_id=db_user.id, portfolio_slug=db_user.username, is_public=True))
        db.commit()

        return db_user, temp_password

    @staticmethod
    def update_faculty(db: Session, user_id: int, update_data: FacultyUpdate) -> Optional[User]:
        """Update a faculty member's details."""
        db_user = db.query(User).filter(
            User.id == user_id,
            User.role.in_(["faculty", "dept_admin", "management"])
        ).first()
        if not db_user:
            return None

        # Handle joining_date conversion
        data = update_data.dict(exclude_unset=True)
        if 'joining_date' in data and data['joining_date']:
            from datetime import date
            try:
                data['joining_date'] = date.fromisoformat(data['joining_date'])
            except ValueError:
                data.pop('joining_date')

        for key, value in data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_faculty(db: Session, user_id: int) -> bool:
        """Soft-delete a faculty member and deactivate their student assignments."""
        db_user = db.query(User).filter(
            User.id == user_id,
            User.role.in_(["faculty", "dept_admin", "management"])
        ).first()
        if not db_user:
            return False
        db_user.is_active = False

        # Deactivate all active mentor assignments for this faculty
        from shared.models import MentorAssignment
        db.query(MentorAssignment).filter(
            MentorAssignment.mentor_id == user_id,
            MentorAssignment.is_active == True,
        ).update({"is_active": False, "unassigned_at": datetime.utcnow()})

        db.commit()
        return True

    @staticmethod
    def reset_user_password(db: Session, user_id: int) -> Tuple[Optional[User], str]:
        """Reset a user's password to a new temp password. Returns (user, temp_password)."""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None, ""
        temp_password = AdminService._generate_temp_password()
        db_user.hashed_password = AuthService.get_password_hash(temp_password)
        db.commit()
        db.refresh(db_user)
        return db_user, temp_password
