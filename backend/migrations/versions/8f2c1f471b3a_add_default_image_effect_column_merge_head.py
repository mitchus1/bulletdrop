"""
Add default_image_effect column to users (merge path)

Revision ID: 8f2c1f471b3a
Revises: 7adbe9ebf11d
Create Date: 2025-09-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8f2c1f471b3a'
down_revision = '7adbe9ebf11d'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add column only if it doesn't exist to be safe across diverged heads
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'default_image_effect' not in columns:
        op.add_column('users', sa.Column('default_image_effect', sa.String(length=20), nullable=True))


def downgrade() -> None:
    # Drop column only if it exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'default_image_effect' in columns:
        op.drop_column('users', 'default_image_effect')
