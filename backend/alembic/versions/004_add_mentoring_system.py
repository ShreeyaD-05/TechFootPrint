"""add mentoring and college management system

Revision ID: 004
Revises: 003
Create Date: 2024-03-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add role and college info to users table
    op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='student'))
    op.add_column('users', sa.Column('college_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('department', sa.String(), nullable=True))
    op.add_column('users', sa.Column('batch_year', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('enrollment_number', sa.String(), nullable=True))
    
    # Create colleges table
    op.create_table('colleges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), unique=True, nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_colleges_code', 'colleges', ['code'])
    
    # Create mentor_assignments table
    op.create_table('mentor_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mentor_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['mentor_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mentor_assignments_mentor', 'mentor_assignments', ['mentor_id'])
    op.create_index('ix_mentor_assignments_student', 'mentor_assignments', ['student_id'])
    
    # Create mentor_feedback table
    op.create_table('mentor_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mentor_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.String(), nullable=False),  # comment, task, recommendation
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(), default='normal'),  # low, normal, high
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['mentor_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mentor_feedback_student', 'mentor_feedback', ['student_id'])
    
    # Create coding_goals table
    op.create_table('coding_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),  # student, batch, department
        sa.Column('target_id', sa.Integer(), nullable=True),  # user_id for student, null for batch/dept
        sa.Column('batch_year', sa.Integer(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('goal_type', sa.String(), nullable=False),  # problems_count, streak, contest
        sa.Column('target_value', sa.Integer(), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create problem_notes table
    op.create_table('problem_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('problem_stat_id', sa.Integer(), nullable=False),
        sa.Column('note_content', sa.Text(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_stat_id'], ['problem_stats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key for college_id
    op.create_foreign_key('fk_users_college', 'users', 'colleges', ['college_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint('fk_users_college', 'users', type_='foreignkey')
    op.drop_table('problem_notes')
    op.drop_table('coding_goals')
    op.drop_index('ix_mentor_feedback_student', table_name='mentor_feedback')
    op.drop_table('mentor_feedback')
    op.drop_index('ix_mentor_assignments_student', table_name='mentor_assignments')
    op.drop_index('ix_mentor_assignments_mentor', table_name='mentor_assignments')
    op.drop_table('mentor_assignments')
    op.drop_index('ix_colleges_code', table_name='colleges')
    op.drop_table('colleges')
    op.drop_column('users', 'enrollment_number')
    op.drop_column('users', 'batch_year')
    op.drop_column('users', 'department')
    op.drop_column('users', 'college_id')
    op.drop_column('users', 'role')
