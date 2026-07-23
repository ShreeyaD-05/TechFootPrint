"""add chat messages table

Revision ID: 009_add_chat_messages
Revises: 008_add_suggestion_feedback
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = '009_add_chat_messages'
down_revision = '008_add_suggestion_feedback'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('recipient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False, server_default='false'),
        sa.Column('deleted_by_sender', sa.Boolean(), default=False, nullable=False, server_default='false'),
        sa.Column('deleted_by_recipient', sa.Boolean(), default=False, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
    )


def downgrade():
    op.drop_table('chat_messages')
