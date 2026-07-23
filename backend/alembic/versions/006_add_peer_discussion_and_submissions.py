"""add peer discussion and submissions view

Revision ID: 006
Revises: 005
Create Date: 2024-03-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create peer_discussions table
    op.create_table(
        'peer_discussions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('problem_stat_id', sa.Integer(), sa.ForeignKey('problem_stats.id'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tags', JSONB, default=[]),
        sa.Column('upvotes', sa.Integer(), default=0),
        sa.Column('is_solved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create discussion_replies table
    op.create_table(
        'discussion_replies',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('discussion_id', sa.Integer(), sa.ForeignKey('peer_discussions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('upvotes', sa.Integer(), default=0),
        sa.Column('is_solution', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create discussion_votes table
    op.create_table(
        'discussion_votes',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('discussion_id', sa.Integer(), sa.ForeignKey('peer_discussions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('reply_id', sa.Integer(), sa.ForeignKey('discussion_replies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('vote_type', sa.String(10), nullable=False),  # 'upvote' or 'downvote'
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'discussion_id', name='unique_discussion_vote'),
        sa.UniqueConstraint('user_id', 'reply_id', name='unique_reply_vote'),
    )
    
    # Add indexes
    op.create_index('idx_discussions_user', 'peer_discussions', ['user_id'])
    op.create_index('idx_discussions_problem', 'peer_discussions', ['problem_stat_id'])
    op.create_index('idx_discussions_created', 'peer_discussions', ['created_at'])
    op.create_index('idx_replies_discussion', 'discussion_replies', ['discussion_id'])
    op.create_index('idx_replies_user', 'discussion_replies', ['user_id'])


def downgrade():
    op.drop_table('discussion_votes')
    op.drop_table('discussion_replies')
    op.drop_table('peer_discussions')
