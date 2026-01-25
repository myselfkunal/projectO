"""Add login OTPs table

Revision ID: 003
Revises: 002
Create Date: 2026-01-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'login_otps',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='f'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('idx_login_otps_user_id', 'login_otps', ['user_id'])
    op.create_index('idx_login_otps_code', 'login_otps', ['code'])


def downgrade() -> None:
    op.drop_index('idx_login_otps_code', table_name='login_otps')
    op.drop_index('idx_login_otps_user_id', table_name='login_otps')
    op.drop_table('login_otps')
