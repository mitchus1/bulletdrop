"""merge_migration_heads

Revision ID: 185e626244aa
Revises: 3b1a2c4e8f21, 9b0dcf0a1a2b
Create Date: 2025-09-21 15:23:16.494685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '185e626244aa'
down_revision: Union[str, Sequence[str], None] = ('3b1a2c4e8f21', '9b0dcf0a1a2b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
