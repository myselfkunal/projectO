"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('profile_picture', sa.String(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='f'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='t'),
        sa.Column('is_online', sa.Boolean(), nullable=False, server_default='f'),
        sa.Column('role', sa.String(), nullable=False, server_default='student'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Calls table
    op.create_table(
        'calls',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('initiator_id', sa.String(), nullable=False),
        sa.Column('receiver_id', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(), nullable=False, server_default='ongoing'),
        sa.Column('call_token', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['initiator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('call_token'),
    )

    # Blocked users table
    op.create_table(
        'blocked_users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('blocker_id', sa.String(), nullable=False),
        sa.Column('blocked_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['blocked_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['blocker_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('reporter_id', sa.String(), nullable=False),
        sa.Column('reported_id', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='f'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reported_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Verification tokens table
    op.create_table(
        'verification_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='f'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )


def downgrade() -> None:
    op.drop_table('verification_tokens')
    op.drop_table('reports')
    op.drop_table('blocked_users')
    op.drop_table('calls')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
