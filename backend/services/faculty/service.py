"""
Faculty Student Management Service.
Faculty members can create, update, deactivate, and bulk-import students
for their own college.
"""
import io
import secrets
import string
import logging
from typing import List, Optional, Tuple, Dict

from sqlalchemy.orm import Session
from sqlalchemy import and_

from shared.models import User, College, Profile
from shared.schemas import StudentCreate, StudentUpdate
from services.auth.service import AuthService

logger = logging.getLogger(__name__)


class FacultyStudentService:

    @staticmethod
    def _generate_temp_password(length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def _create_student_record(
        db: Session,
        student_data: StudentCreate,
        college_id: int,
    ) -> Tuple[User, str]:
        """
        Core helper: create a single student user + profile.
        Returns (user, temp_password).
        Raises ValueError on duplicate email/username.
        """
        if db.query(User).filter(User.email == student_data.email).first():
            raise ValueError(f"Email already registered: {student_data.email}")
        if db.query(User).filter(User.username == student_data.username).first():
            raise ValueError(f"Username already taken: {student_data.username}")

        temp_password = FacultyStudentService._generate_temp_password()
        hashed = AuthService.get_password_hash(temp_password)

        db_user = User(
            username=student_data.username,
            email=student_data.email,
            hashed_password=hashed,
            full_name=student_data.full_name,
            role="student",
            college_id=college_id,
            department=student_data.department,
            batch_year=student_data.batch_year,
            enrollment_number=student_data.enrollment_number,
        )
        db.add(db_user)
        db.flush()  # get id without committing

        db.add(Profile(user_id=db_user.id, portfolio_slug=db_user.username, is_public=True))
        return db_user, temp_password

    # ── Single student ────────────────────────────────────────────────────────

    @staticmethod
    def create_student(
        db: Session,
        student_data: StudentCreate,
        college_id: int,
    ) -> Tuple[User, str]:
        """Create a single student. Returns (user, temp_password)."""
        user, temp_password = FacultyStudentService._create_student_record(db, student_data, college_id)
        db.commit()
        db.refresh(user)
        return user, temp_password

    @staticmethod
    def get_students(
        db: Session,
        college_id: int,
        department: Optional[str] = None,
        batch_year: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[User]:
        """Get students for a college with optional filters."""
        query = db.query(User).filter(
            and_(User.college_id == college_id, User.role == "student")
        )
        if department:
            query = query.filter(User.department == department)
        if batch_year:
            query = query.filter(User.batch_year == batch_year)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                User.username.ilike(pattern)
                | User.email.ilike(pattern)
                | User.full_name.ilike(pattern)
                | User.enrollment_number.ilike(pattern)
            )
        return query.order_by(User.created_at.desc()).all()

    @staticmethod
    def get_student_by_id(db: Session, student_id: int, college_id: int) -> Optional[User]:
        return db.query(User).filter(
            User.id == student_id,
            User.college_id == college_id,
            User.role == "student",
        ).first()

    @staticmethod
    def update_student(
        db: Session,
        student_id: int,
        college_id: int,
        update_data: StudentUpdate,
    ) -> Optional[User]:
        db_user = FacultyStudentService.get_student_by_id(db, student_id, college_id)
        if not db_user:
            return None
        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_student(db: Session, student_id: int, college_id: int) -> bool:
        db_user = FacultyStudentService.get_student_by_id(db, student_id, college_id)
        if not db_user:
            return False
        db_user.is_active = False
        db.commit()
        return True

    @staticmethod
    def reset_student_password(db: Session, student_id: int, college_id: int) -> Tuple[Optional[User], str]:
        db_user = FacultyStudentService.get_student_by_id(db, student_id, college_id)
        if not db_user:
            return None, ""
        temp_password = FacultyStudentService._generate_temp_password()
        db_user.hashed_password = AuthService.get_password_hash(temp_password)
        db.commit()
        db.refresh(db_user)
        return db_user, temp_password

    # ── Bulk import from Excel ────────────────────────────────────────────────

    @staticmethod
    def bulk_create_from_excel(
        db: Session,
        file_bytes: bytes,
        college_id: int,
    ) -> Dict:
        """
        Parse an Excel file and create students in bulk.

        Expected columns (case-insensitive):
          email, username, full_name, department, batch_year,
          enrollment_number, faculty_username (optional — auto-assigns mentor)

        Returns:
          {created, failed, errors: [{row, email, reason}], students: [...], credentials: [...]}
        """
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError("openpyxl is required for Excel import. Run: pip install openpyxl")

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {"created": 0, "failed": 0, "errors": [], "students": [], "credentials": []}

        # Normalise header row
        header = [str(h).strip().lower() if h else "" for h in rows[0]]
        required = {"email", "username", "full_name"}
        missing = required - set(header)
        if missing:
            raise ValueError(f"Excel is missing required columns: {', '.join(missing)}")

        def col(row_vals, name):
            idx = header.index(name) if name in header else -1
            if idx == -1:
                return None
            val = row_vals[idx]
            return str(val).strip() if val is not None else None

        # Pre-build faculty username → id map for this college (avoid per-row queries)
        faculty_rows = db.query(User).filter(
            User.college_id == college_id,
            User.role.in_(["faculty", "dept_admin", "management"]),
            User.is_active == True,
        ).all()
        faculty_by_username = {f.username.lower(): f.id for f in faculty_rows}

        created_users = []
        credentials = []
        errors = []
        # Track (student_id, faculty_id) pairs for post-commit assignment
        pending_assignments: list = []

        for row_num, row_vals in enumerate(rows[1:], start=2):
            email = col(row_vals, "email")
            username = col(row_vals, "username")
            full_name = col(row_vals, "full_name")

            if not email or not username or not full_name:
                errors.append({"row": row_num, "email": email or "", "reason": "Missing required field(s)"})
                continue

            batch_raw = col(row_vals, "batch_year")
            try:
                batch_year = int(batch_raw) if batch_raw else None
            except ValueError:
                batch_year = None

            faculty_username_raw = col(row_vals, "faculty_username")
            faculty_id = None
            if faculty_username_raw:
                faculty_id = faculty_by_username.get(faculty_username_raw.lower())
                if not faculty_id:
                    errors.append({
                        "row": row_num,
                        "email": email,
                        "reason": f"Faculty '{faculty_username_raw}' not found in this college (student still created)",
                    })
                    # Don't skip — still create the student, just skip assignment

            student_data = StudentCreate(
                email=email,
                username=username,
                full_name=full_name,
                department=col(row_vals, "department"),
                batch_year=batch_year,
                enrollment_number=col(row_vals, "enrollment_number"),
            )

            try:
                user, temp_password = FacultyStudentService._create_student_record(
                    db, student_data, college_id
                )
                created_users.append(user)
                credentials.append({"email": email, "username": username, "temp_password": temp_password})
                if faculty_id:
                    pending_assignments.append((user, faculty_id))
            except ValueError as exc:
                db.rollback()
                errors.append({"row": row_num, "email": email, "reason": str(exc)})
                continue

        if created_users:
            try:
                db.commit()
                for u in created_users:
                    db.refresh(u)
            except Exception as exc:
                db.rollback()
                logger.error("Bulk commit failed: %s", exc)
                raise

        # Create mentor assignments after commit so student IDs are stable
        if pending_assignments:
            from shared.models import MentorAssignment
            for student_user, fac_id in pending_assignments:
                # Deactivate any existing assignment
                db.query(MentorAssignment).filter(
                    MentorAssignment.student_id == student_user.id,
                    MentorAssignment.is_active == True,
                ).update({"is_active": False})
                db.add(MentorAssignment(
                    mentor_id=fac_id,
                    student_id=student_user.id,
                    assigned_by=None,
                ))
            db.commit()

        return {
            "created": len(created_users),
            "failed": len(errors),
            "errors": errors,
            "students": created_users,
            "credentials": credentials,
        }
