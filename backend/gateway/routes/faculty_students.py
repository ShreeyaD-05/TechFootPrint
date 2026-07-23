"""
Faculty Student Management Routes.

Role access:
  - faculty / dept_admin / management  → manage students in their own college
  - super_admin                        → manage students in any college
                                         (pass ?college_id=X to target a specific college)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from shared.database import get_db
from shared.schemas import (
    StudentCreate, StudentUpdate, StudentResponse,
    ResetPasswordResponse,
)
from services.faculty.service import FacultyStudentService
from services.email.service import EmailService
from gateway.routes.auth import get_current_user
from shared.models import User, College

router = APIRouter()

# Roles that can manage students
FACULTY_ROLES = {"faculty", "dept_admin", "management", "super_admin"}


def require_faculty(current_user: User) -> User:
    if current_user.role not in FACULTY_ROLES:
        raise HTTPException(status_code=403, detail="Faculty access required")
    return current_user


def _resolve_college(db: Session, user: User, college_id_param: Optional[int] = None) -> College:
    """
    Determine which college to operate on.
    - super_admin: must supply ?college_id or defaults to first college (raises if none)
    - others: always use their own college_id
    """
    if user.role == "super_admin":
        cid = college_id_param or user.college_id
        if not cid:
            raise HTTPException(
                status_code=400,
                detail="super_admin must supply ?college_id to manage students",
            )
    else:
        if not user.college_id:
            raise HTTPException(status_code=400, detail="You are not associated with a college")
        cid = user.college_id

    college = db.query(College).filter(College.id == cid).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    return college


# ── Static sub-routes FIRST (must precede /{student_id}) ─────────────────────

@router.get("/students/bulk-upload/template")
def download_bulk_template(
    current_user: User = Depends(get_current_user),
):
    """Return expected Excel column headers so the frontend can build a template."""
    require_faculty(current_user)
    return {
        "columns": [
            {"name": "email",             "required": True,  "example": "student@college.edu"},
            {"name": "username",          "required": True,  "example": "john_doe"},
            {"name": "full_name",         "required": True,  "example": "John Doe"},
            {"name": "department",        "required": False, "example": "Computer Science"},
            {"name": "batch_year",        "required": False, "example": 2025},
            {"name": "enrollment_number", "required": False, "example": "CS2025001"},
            {"name": "faculty_username",  "required": False, "example": "prof_sharma",
             "note": "Auto-assigns student to this faculty mentor"},
        ],
        "instructions": (
            "Fill in one student per row. "
            "email, username, and full_name are required. "
            "faculty_username (optional) auto-assigns the student to that faculty. "
            "Save as .xlsx before uploading."
        ),
    }


@router.post("/students/bulk-upload")
async def bulk_upload_students(
    file: UploadFile = File(...),
    send_emails: bool = Query(True, description="Send welcome emails to created students"),
    college_id: Optional[int] = Query(None, description="Target college (super_admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk-create students from an Excel (.xlsx / .xls) file.

    Required columns: email, username, full_name
    Optional columns: department, batch_year, enrollment_number
    """
    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    try:
        result = FacultyStudentService.bulk_create_from_excel(db, file_bytes, college.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    emails_sent = 0
    if send_emails and result["credentials"]:
        for cred in result["credentials"]:
            ok = EmailService.send_welcome_student(
                to_email=cred["email"],
                full_name=cred["username"],
                username=cred["username"],
                temp_password=cred["temp_password"],
                college_name=college.name,
                faculty_name=current_user.full_name or current_user.username,
            )
            if ok:
                emails_sent += 1

    return {
        "created": result["created"],
        "failed": result["failed"],
        "errors": result["errors"],
        "emails_sent": emails_sent,
        "students": [
            {
                "id": s.id,
                "email": s.email,
                "username": s.username,
                "full_name": s.full_name,
                "department": s.department,
                "batch_year": s.batch_year,
            }
            for s in result["students"]
        ],
    }


# ── Student CRUD ──────────────────────────────────────────────────────────────

@router.get("/students", response_model=List[StudentResponse])
def list_students(
    department: Optional[str] = None,
    batch_year: Optional[int] = None,
    search: Optional[str] = None,
    college_id: Optional[int] = Query(None, description="Target college (super_admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List students. Faculty see their own college; super_admin can pass ?college_id."""
    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)
    return FacultyStudentService.get_students(
        db, college.id, department=department, batch_year=batch_year, search=search
    )


@router.post("/students", response_model=StudentResponse, status_code=201)
def create_student(
    student_data: StudentCreate,
    college_id: Optional[int] = Query(None, description="Target college (super_admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a single student and send a welcome email with credentials."""
    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)

    try:
        student, temp_password = FacultyStudentService.create_student(db, student_data, college.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    EmailService.send_welcome_student(
        to_email=student.email,
        full_name=student.full_name or student.username,
        username=student.username,
        temp_password=temp_password,
        college_name=college.name,
        faculty_name=current_user.full_name or current_user.username,
    )
    return student


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific student by ID."""
    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)
    student = FacultyStudentService.get_student_by_id(db, student_id, college.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    update_data: StudentUpdate,
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a student's details."""
    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)
    student = FacultyStudentService.update_student(db, student_id, college.id, update_data)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate a student account."""
    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)
    success = FacultyStudentService.delete_student(db, student_id, college.id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deactivated successfully"}


@router.post("/students/{student_id}/reset-password", response_model=ResetPasswordResponse)
def reset_student_password(
    student_id: int,
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset a student's password and email new credentials."""
    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)
    student, temp_password = FacultyStudentService.reset_student_password(db, student_id, college.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    email_sent = EmailService.send_password_reset(
        to_email=student.email,
        full_name=student.full_name or student.username,
        new_password=temp_password,
    )
    return {"message": "Password reset successfully", "email_sent": email_sent}


# ── Faculty Assignment (assign students to a faculty mentor) ──────────────────

@router.get("/faculty-list")
def get_college_faculty(
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return faculty members in the same college.
    Used to populate the 'Assign to Faculty' dropdown.
    """
    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)

    faculty = db.query(User).filter(
        User.college_id == college.id,
        User.role.in_(["faculty", "dept_admin", "management"]),
        User.is_active == True,
    ).order_by(User.full_name).all()

    return [
        {
            "id": f.id,
            "username": f.username,
            "full_name": f.full_name,
            "role": f.role,
            "department": f.department,
        }
        for f in faculty
    ]


@router.post("/students/{student_id}/assign-faculty")
def assign_student_to_faculty(
    student_id: int,
    faculty_id: int = Query(..., description="Faculty user ID to assign as mentor"),
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign a student to a faculty mentor.
    Deactivates any existing active assignment first (one mentor per student).
    """
    from shared.models import MentorAssignment

    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)

    # Verify student belongs to this college
    student = FacultyStudentService.get_student_by_id(db, student_id, college.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Verify faculty belongs to this college
    faculty = db.query(User).filter(
        User.id == faculty_id,
        User.college_id == college.id,
        User.role.in_(["faculty", "dept_admin", "management"]),
        User.is_active == True,
    ).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found in this college")

    # Deactivate existing assignment for this student
    db.query(MentorAssignment).filter(
        MentorAssignment.student_id == student_id,
        MentorAssignment.is_active == True,
    ).update({"is_active": False, "unassigned_at": datetime.utcnow()})

    # Create new assignment
    assignment = MentorAssignment(
        mentor_id=faculty_id,
        student_id=student_id,
        assigned_by=current_user.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "message": f"Student assigned to {faculty.full_name or faculty.username}",
        "assignment_id": assignment.id,
        "mentor_id": faculty_id,
        "mentor_name": faculty.full_name or faculty.username,
        "student_id": student_id,
    }


@router.delete("/students/{student_id}/assign-faculty")
def unassign_student_faculty(
    student_id: int,
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove the current faculty assignment from a student."""
    from shared.models import MentorAssignment

    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)

    student = FacultyStudentService.get_student_by_id(db, student_id, college.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    updated = db.query(MentorAssignment).filter(
        MentorAssignment.student_id == student_id,
        MentorAssignment.is_active == True,
    ).update({"is_active": False, "unassigned_at": datetime.utcnow()})

    db.commit()
    return {"message": "Assignment removed", "rows_updated": updated}


@router.get("/students/{student_id}/assigned-faculty")
def get_student_assigned_faculty(
    student_id: int,
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the faculty currently assigned to a student."""
    from shared.models import MentorAssignment

    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)

    student = FacultyStudentService.get_student_by_id(db, student_id, college.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    assignment = db.query(MentorAssignment).filter(
        MentorAssignment.student_id == student_id,
        MentorAssignment.is_active == True,
    ).first()

    if not assignment:
        return {"assigned": False, "mentor": None}

    mentor = db.query(User).filter(User.id == assignment.mentor_id).first()
    return {
        "assigned": True,
        "mentor": {
            "id": mentor.id,
            "username": mentor.username,
            "full_name": mentor.full_name,
            "role": mentor.role,
        } if mentor else None,
    }


# ── Bulk assign: assign all students in a batch/dept to a faculty ─────────────

@router.post("/students/bulk-assign-faculty")
def bulk_assign_faculty(
    faculty_id: int = Query(...),
    batch_year: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    college_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk-assign all students in a batch/department to a faculty mentor.
    At least one of batch_year or department must be provided.
    """
    from shared.models import MentorAssignment
    from sqlalchemy import and_

    require_faculty(current_user)
    college = _resolve_college(db, current_user, college_id)

    if not batch_year and not department:
        raise HTTPException(status_code=400, detail="Provide batch_year or department")

    # Verify faculty
    faculty = db.query(User).filter(
        User.id == faculty_id,
        User.college_id == college.id,
        User.role.in_(["faculty", "dept_admin", "management"]),
        User.is_active == True,
    ).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found in this college")

    # Find matching students
    filters = [User.college_id == college.id, User.role == "student", User.is_active == True]
    if batch_year:
        filters.append(User.batch_year == batch_year)
    if department:
        filters.append(User.department == department)

    students = db.query(User).filter(and_(*filters)).all()
    if not students:
        return {"message": "No matching students found", "assigned": 0}

    student_ids = [s.id for s in students]

    # Deactivate existing assignments
    db.query(MentorAssignment).filter(
        MentorAssignment.student_id.in_(student_ids),
        MentorAssignment.is_active == True,
    ).update({"is_active": False, "unassigned_at": datetime.utcnow()}, synchronize_session=False)

    # Create new assignments
    for sid in student_ids:
        db.add(MentorAssignment(
            mentor_id=faculty_id,
            student_id=sid,
            assigned_by=current_user.id,
        ))

    db.commit()
    return {
        "message": f"Assigned {len(student_ids)} student(s) to {faculty.full_name or faculty.username}",
        "assigned": len(student_ids),
        "faculty_id": faculty_id,
        "faculty_name": faculty.full_name or faculty.username,
    }
