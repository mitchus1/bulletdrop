"""
Make users.hashed_password nullable

Revision ID: 9b0dcf0a1a2b
Revises: 8f2c1f471b3a
Create Date: 2025-09-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9b0dcf0a1a2b'
down_revision = '8f2c1f471b3a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=255), nullable=False)
