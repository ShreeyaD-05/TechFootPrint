"""Faculty schema improvements

Adds columns needed to properly maintain faculty profiles and
faculty-student assignment integrity.

Changes:
  users table:
    - phone              VARCHAR  — contact number (faculty & students)
    - employee_id        VARCHAR  — faculty employee/staff ID (unique per college)
    - joining_date       DATE     — when faculty joined the institution
    - specialization     VARCHAR  — faculty area of expertise / subject
    - is_first_login     BOOLEAN  — flag to force password change on first login

  colleges table:
    - contact_email      VARCHAR  — primary contact email for the college
    - contact_phone      VARCHAR  — primary contact phone
    - website            VARCHAR  — college website URL
    - established_year   INTEGER  — year the college was established

  mentor_assignments table:
    - notes              TEXT     — reason / context for the assignment
    - unassigned_at      DATETIME — when the assignment was deactivated
    - UNIQUE constraint  (student_id) WHERE is_active = TRUE
      → enforces one active mentor per student at the DB level

  Indexes:
    - ix_users_college_role  — (college_id, role) composite for fast faculty/student lookups
    - ix_colleges_is_active  — fast filtering of active colleges
    - ix_mentor_assignments_active — (student_id, is_active) for fast active-assignment lookup

Revision ID: 010_faculty_schema_improvements
Revises: 009_add_chat_messages
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = '010_faculty_schema_improvements'
down_revision = '009_add_chat_messages'
branch_labels = None
depends_on = None


def upgrade():
    # ── users: faculty & student profile fields ───────────────────────────────
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('employee_id', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('joining_date', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('specialization', sa.String(200), nullable=True))
    op.add_column('users', sa.Column(
        'is_first_login', sa.Boolean(), nullable=False,
        server_default='true',
    ))

    # Composite index: fast lookup of all faculty/students in a college
    op.create_index(
        'ix_users_college_role',
        'users',
        ['college_id', 'role'],
    )

    # ── colleges: contact & metadata fields ──────────────────────────────────
    op.add_column('colleges', sa.Column('contact_email', sa.String(255), nullable=True))
    op.add_column('colleges', sa.Column('contact_phone', sa.String(20), nullable=True))
    op.add_column('colleges', sa.Column('website', sa.String(500), nullable=True))
    op.add_column('colleges', sa.Column('established_year', sa.Integer(), nullable=True))

    # Index for fast active-college filtering
    op.create_index('ix_colleges_is_active', 'colleges', ['is_active'])

    # ── mentor_assignments: audit & integrity ─────────────────────────────────
    op.add_column('mentor_assignments', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('mentor_assignments', sa.Column('unassigned_at', sa.DateTime(), nullable=True))

    # Composite index: fast lookup of active assignment for a student
    op.create_index(
        'ix_mentor_assignments_active',
        'mentor_assignments',
        ['student_id', 'is_active'],
    )

    # Partial unique constraint: only one ACTIVE assignment per student.
    # PostgreSQL supports WHERE clauses on unique indexes.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_mentor_assignments_one_active_per_student
        ON mentor_assignments (student_id)
        WHERE is_active = TRUE
        """
    )


def downgrade():
    # Drop partial unique index
    op.execute('DROP INDEX IF EXISTS uq_mentor_assignments_one_active_per_student')

    # Drop composite indexes
    op.drop_index('ix_mentor_assignments_active', table_name='mentor_assignments')
    op.drop_index('ix_colleges_is_active', table_name='colleges')
    op.drop_index('ix_users_college_role', table_name='users')

    # Drop mentor_assignments columns
    op.drop_column('mentor_assignments', 'unassigned_at')
    op.drop_column('mentor_assignments', 'notes')

    # Drop colleges columns
    op.drop_column('colleges', 'established_year')
    op.drop_column('colleges', 'website')
    op.drop_column('colleges', 'contact_phone')
    op.drop_column('colleges', 'contact_email')

    # Drop users columns
    op.drop_column('users', 'is_first_login')
    op.drop_column('users', 'specialization')
    op.drop_column('users', 'joining_date')
    op.drop_column('users', 'employee_id')
    op.drop_column('users', 'phone')
