"""add profile_stats column to platform_accounts

Revision ID: 007
Revises: 006
Create Date: 2024-04-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'platform_accounts',
        sa.Column('profile_stats', JSONB, nullable=True)
    )


def downgrade():
    op.drop_column('platform_accounts', 'profile_stats')
