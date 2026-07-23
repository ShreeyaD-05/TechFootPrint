"""Add suggestion feedback table for DL model improvement

Revision ID: 008
Revises: 007
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'suggestion_feedback',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('problem_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('strategy', sa.String()),
        sa.Column('was_helpful', sa.Boolean()),          # thumbs up/down
        sa.Column('was_solved', sa.Boolean()),           # did user solve it?
        sa.Column('difficulty_felt', sa.String()),       # too_easy / just_right / too_hard
        sa.Column('suggestion_score', sa.Float()),       # model's score at time of suggestion
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_suggestion_feedback_user_id', 'suggestion_feedback', ['user_id'])
    op.create_index('ix_suggestion_feedback_problem_id', 'suggestion_feedback', ['problem_id'])


def downgrade():
    op.drop_index('ix_suggestion_feedback_problem_id', 'suggestion_feedback')
    op.drop_index('ix_suggestion_feedback_user_id', 'suggestion_feedback')
    op.drop_table('suggestion_feedback')
