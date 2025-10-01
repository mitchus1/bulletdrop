"""add_analytics_indexes

Revision ID: ef4d1a2bfa74
Revises: 50bf5a9d58c7
Create Date: 2025-10-01 11:08:12.064800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef4d1a2bfa74'
down_revision: Union[str, Sequence[str], None] = '50bf5a9d58c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for analytics tables to improve query performance."""
    # FileView indexes
    op.create_index('idx_file_views_upload_time', 'file_views', ['upload_id', 'viewed_at'])
    op.create_index('idx_file_views_ip_time', 'file_views', ['viewer_ip', 'viewed_at'])

    # ProfileView indexes
    op.create_index('idx_profile_views_user_time', 'profile_views', ['profile_user_id', 'viewed_at'])
    op.create_index('idx_profile_views_ip_time', 'profile_views', ['viewer_ip', 'viewed_at'])

    # ViewSummary indexes
    op.create_index('idx_view_summary_lookup', 'view_summaries', ['content_type', 'content_id', 'date'])
    op.create_index('idx_view_summary_date', 'view_summaries', ['date', 'view_count'])


def downgrade() -> None:
    """Remove analytics indexes."""
    # ViewSummary indexes
    op.drop_index('idx_view_summary_date', 'view_summaries')
    op.drop_index('idx_view_summary_lookup', 'view_summaries')

    # ProfileView indexes
    op.drop_index('idx_profile_views_ip_time', 'profile_views')
    op.drop_index('idx_profile_views_user_time', 'profile_views')

    # FileView indexes
    op.drop_index('idx_file_views_ip_time', 'file_views')
    op.drop_index('idx_file_views_upload_time', 'file_views')
