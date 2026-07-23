"""add submissions table

Revision ID: 002
Revises: 001
Create Date: 2024-03-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_stat_id', sa.Integer(), nullable=True),
        sa.Column('platform_account_id', sa.Integer(), nullable=True),
        sa.Column('submission_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('runtime', sa.String(), nullable=True),
        sa.Column('memory', sa.String(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('code', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['problem_stat_id'], ['problem_stats.id'], ),
        sa.ForeignKeyConstraint(['platform_account_id'], ['platform_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_submissions_id'), 'submissions', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_submissions_id'), table_name='submissions')
    op.drop_table('submissions')
