"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create profiles table
    op.create_table('profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('github_username', sa.String(), nullable=True),
        sa.Column('linkedin_url', sa.String(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('portfolio_slug', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_profiles_id'), 'profiles', ['id'], unique=False)
    op.create_index(op.f('ix_profiles_portfolio_slug'), 'profiles', ['portfolio_slug'], unique=True)

    # Create platform_accounts table
    op.create_table('platform_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('platform_name', sa.String(), nullable=False),
        sa.Column('platform_username', sa.String(), nullable=False),
        sa.Column('platform_user_id', sa.String(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=True),
        sa.Column('credentials', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_platform_accounts_id'), 'platform_accounts', ['id'], unique=False)

    # Create problem_stats table
    op.create_table('problem_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform_account_id', sa.Integer(), nullable=True),
        sa.Column('problem_id', sa.String(), nullable=False),
        sa.Column('problem_title', sa.String(), nullable=True),
        sa.Column('difficulty', sa.String(), nullable=True),
        sa.Column('topics', sa.JSON(), nullable=True),
        sa.Column('solved_at', sa.DateTime(), nullable=True),
        sa.Column('submission_count', sa.Integer(), nullable=True),
        sa.Column('is_solved', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['platform_account_id'], ['platform_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_problem_stats_id'), 'problem_stats', ['id'], unique=False)

    # Create contest_stats table
    op.create_table('contest_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform_account_id', sa.Integer(), nullable=True),
        sa.Column('contest_id', sa.String(), nullable=False),
        sa.Column('contest_name', sa.String(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('problems_solved', sa.Integer(), nullable=True),
        sa.Column('contest_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['platform_account_id'], ['platform_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contest_stats_id'), 'contest_stats', ['id'], unique=False)

    # Create activity_logs table
    op.create_table('activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('activity_type', sa.String(), nullable=True),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('activity_data', sa.JSON(), nullable=True),
        sa.Column('activity_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_logs_id'), 'activity_logs', ['id'], unique=False)

    # Create analytics table
    op.create_table('analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('total_problems_solved', sa.Integer(), nullable=True),
        sa.Column('easy_solved', sa.Integer(), nullable=True),
        sa.Column('medium_solved', sa.Integer(), nullable=True),
        sa.Column('hard_solved', sa.Integer(), nullable=True),
        sa.Column('current_streak', sa.Integer(), nullable=True),
        sa.Column('longest_streak', sa.Integer(), nullable=True),
        sa.Column('topic_distribution', sa.JSON(), nullable=True),
        sa.Column('platform_distribution', sa.JSON(), nullable=True),
        sa.Column('last_calculated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_id'), 'analytics', ['id'], unique=False)

    # Create portfolio_data table
    op.create_table('portfolio_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('portfolio_json', sa.JSON(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('last_generated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolio_data_id'), 'portfolio_data', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_portfolio_data_id'), table_name='portfolio_data')
    op.drop_table('portfolio_data')
    op.drop_index(op.f('ix_analytics_id'), table_name='analytics')
    op.drop_table('analytics')
    op.drop_index(op.f('ix_activity_logs_id'), table_name='activity_logs')
    op.drop_table('activity_logs')
    op.drop_index(op.f('ix_contest_stats_id'), table_name='contest_stats')
    op.drop_table('contest_stats')
    op.drop_index(op.f('ix_problem_stats_id'), table_name='problem_stats')
    op.drop_table('problem_stats')
    op.drop_index(op.f('ix_platform_accounts_id'), table_name='platform_accounts')
    op.drop_table('platform_accounts')
    op.drop_index(op.f('ix_profiles_portfolio_slug'), table_name='profiles')
    op.drop_index(op.f('ix_profiles_id'), table_name='profiles')
    op.drop_table('profiles')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
