"""
View Aggregation Service

Background job service for aggregating view data into summary tables.
This improves analytics query performance by pre-calculating daily statistics.

NOTE: This service is designed to run as a cron job or scheduled task.
For production deployment, configure a cron job or use a task scheduler like Celery.

Usage:
    python -m app.services.view_aggregation_service --date YYYY-MM-DD
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.views import FileView, ProfileView, ViewSummary
import logging

logger = logging.getLogger(__name__)


class ViewAggregationService:
    """Service for aggregating view data into summary tables."""

    @staticmethod
    def aggregate_file_views(db: Session, target_date: datetime) -> int:
        """
        Aggregate file view data for a specific date.

        Args:
            db: Database session
            target_date: Date to aggregate (will be truncated to day)

        Returns:
            Number of summary records created/updated
        """
        # Truncate to start of day
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Query aggregated data
        results = db.query(
            FileView.upload_id,
            func.count(FileView.id).label('view_count'),
            func.count(func.distinct(FileView.viewer_ip)).label('unique_viewers')
        ).filter(
            FileView.viewed_at >= start_of_day,
            FileView.viewed_at < end_of_day
        ).group_by(
            FileView.upload_id
        ).all()

        count = 0
        for result in results:
            # Check if summary already exists
            existing = db.query(ViewSummary).filter(
                ViewSummary.content_type == 'file',
                ViewSummary.content_id == result.upload_id,
                ViewSummary.date == start_of_day
            ).first()

            if existing:
                # Update existing summary
                existing.view_count = result.view_count
                existing.unique_viewers = result.unique_viewers
            else:
                # Create new summary
                summary = ViewSummary(
                    content_type='file',
                    content_id=result.upload_id,
                    date=start_of_day,
                    view_count=result.view_count,
                    unique_viewers=result.unique_viewers
                )
                db.add(summary)
            count += 1

        db.commit()
        logger.info(f"Aggregated {count} file view summaries for {start_of_day.date()}")
        return count

    @staticmethod
    def aggregate_profile_views(db: Session, target_date: datetime) -> int:
        """
        Aggregate profile view data for a specific date.

        Args:
            db: Database session
            target_date: Date to aggregate (will be truncated to day)

        Returns:
            Number of summary records created/updated
        """
        # Truncate to start of day
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Query aggregated data
        results = db.query(
            ProfileView.profile_user_id,
            func.count(ProfileView.id).label('view_count'),
            func.count(func.distinct(ProfileView.viewer_ip)).label('unique_viewers')
        ).filter(
            ProfileView.viewed_at >= start_of_day,
            ProfileView.viewed_at < end_of_day
        ).group_by(
            ProfileView.profile_user_id
        ).all()

        count = 0
        for result in results:
            # Check if summary already exists
            existing = db.query(ViewSummary).filter(
                ViewSummary.content_type == 'profile',
                ViewSummary.content_id == result.profile_user_id,
                ViewSummary.date == start_of_day
            ).first()

            if existing:
                # Update existing summary
                existing.view_count = result.view_count
                existing.unique_viewers = result.unique_viewers
            else:
                # Create new summary
                summary = ViewSummary(
                    content_type='profile',
                    content_id=result.profile_user_id,
                    date=start_of_day,
                    view_count=result.view_count,
                    unique_viewers=result.unique_viewers
                )
                db.add(summary)
            count += 1

        db.commit()
        logger.info(f"Aggregated {count} profile view summaries for {start_of_day.date()}")
        return count

    @staticmethod
    def run_daily_aggregation(target_date: datetime = None):
        """
        Run daily aggregation for both file and profile views.

        Args:
            target_date: Date to aggregate. Defaults to yesterday.
        """
        if target_date is None:
            # Default to yesterday (allow time for all views to be recorded)
            target_date = datetime.utcnow() - timedelta(days=1)

        logger.info(f"Starting view aggregation for {target_date.date()}")

        db = SessionLocal()
        try:
            file_count = ViewAggregationService.aggregate_file_views(db, target_date)
            profile_count = ViewAggregationService.aggregate_profile_views(db, target_date)

            logger.info(
                f"Aggregation complete: {file_count} file summaries, "
                f"{profile_count} profile summaries"
            )
        except Exception as e:
            logger.error(f"Error during view aggregation: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()


# CLI interface for running as a cron job
if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='Aggregate view statistics')
    parser.add_argument(
        '--date',
        type=str,
        help='Date to aggregate (YYYY-MM-DD format). Defaults to yesterday.'
    )

    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    try:
        ViewAggregationService.run_daily_aggregation(target_date)
        print(f"✅ View aggregation completed successfully")
    except Exception as e:
        print(f"❌ View aggregation failed: {str(e)}", file=sys.stderr)
        sys.exit(1)
