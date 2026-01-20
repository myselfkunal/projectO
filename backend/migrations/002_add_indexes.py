"""Add database indexes for performance optimization

Revision ID: 002
Revises: 001
Create Date: 2026-01-20 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create indexes on frequently queried columns"""
    # Index on users.email for faster lookups during login and registration
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    
    # Index on users.username for profile lookups
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    
    # Index on verification_tokens.token for faster token lookups during email verification
    op.create_index('idx_verification_tokens_token', 'verification_tokens', ['token'], unique=True)
    
    # Index on calls.caller_id for call history queries
    op.create_index('idx_calls_caller_id', 'calls', ['caller_id'])
    
    # Index on calls.receiver_id for call history queries
    op.create_index('idx_calls_receiver_id', 'calls', ['receiver_id'])
    
    # Index on calls.created_at for chronological sorting
    op.create_index('idx_calls_created_at', 'calls', ['created_at'])
    
    # Index on blocked_users for permission checks
    op.create_index('idx_blocked_users_blocker_id', 'blocked_users', ['blocker_id'])
    op.create_index('idx_blocked_users_blocked_id', 'blocked_users', ['blocked_id'])


def downgrade() -> None:
    """Remove all indexes"""
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    op.drop_index('idx_verification_tokens_token', table_name='verification_tokens')
    op.drop_index('idx_calls_caller_id', table_name='calls')
    op.drop_index('idx_calls_receiver_id', table_name='calls')
    op.drop_index('idx_calls_created_at', table_name='calls')
    op.drop_index('idx_blocked_users_blocker_id', table_name='blocked_users')
    op.drop_index('idx_blocked_users_blocked_id', table_name='blocked_users')
