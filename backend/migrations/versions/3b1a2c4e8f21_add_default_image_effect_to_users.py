"""
Add default_image_effect to users

Revision ID: 3b1a2c4e8f21
Revises: e0ba0815ce33
Create Date: 2025-09-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3b1a2c4e8f21'
down_revision = 'e0ba0815ce33'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('default_image_effect', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'default_image_effect')
