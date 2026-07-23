"""add profile stats table

Revision ID: 003
Revises: 002
Create Date: 2024-03-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create platform_profile_stats table to store aggregate stats from platform profiles
    op.create_table('platform_profile_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform_account_id', sa.Integer(), nullable=False),
        sa.Column('total_solved', sa.Integer(), default=0),
        sa.Column('easy_solved', sa.Integer(), default=0),
        sa.Column('medium_solved', sa.Integer(), default=0),
        sa.Column('hard_solved', sa.Integer(), default=0),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('rank', sa.String(), nullable=True),
        sa.Column('contests_attended', sa.Integer(), default=0),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['platform_account_id'], ['platform_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_platform_profile_stats_platform_account', 'platform_profile_stats', ['platform_account_id'])


def downgrade():
    op.drop_index('ix_platform_profile_stats_platform_account', table_name='platform_profile_stats')
    op.drop_table('platform_profile_stats')
