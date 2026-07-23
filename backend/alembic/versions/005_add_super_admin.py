"""add super admin role and system stats

Revision ID: 005
Revises: 004
Create Date: 2024-03-08 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create system_stats table for tracking platform-wide metrics
    op.create_table('system_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('total_users', sa.Integer(), default=0),
        sa.Column('total_colleges', sa.Integer(), default=0),
        sa.Column('total_problems_solved', sa.Integer(), default=0),
        sa.Column('total_platform_connections', sa.Integer(), default=0),
        sa.Column('active_users_today', sa.Integer(), default=0),
        sa.Column('active_users_week', sa.Integer(), default=0),
        sa.Column('active_users_month', sa.Integer(), default=0),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add admin_notes to colleges table
    op.add_column('colleges', sa.Column('admin_notes', sa.Text(), nullable=True))
    op.add_column('colleges', sa.Column('max_students', sa.Integer(), nullable=True))
    op.add_column('colleges', sa.Column('subscription_tier', sa.String(), default='free'))


def downgrade():
    op.drop_column('colleges', 'subscription_tier')
    op.drop_column('colleges', 'max_students')
    op.drop_column('colleges', 'admin_notes')
    op.drop_table('system_stats')
