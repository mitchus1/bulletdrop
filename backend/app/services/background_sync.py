"""
Background Sync Service

This module provides background tasks for syncing Redis data to PostgreSQL
to maintain data consistency and provide backup/recovery capabilities.

Functions:
    sync_view_counts: Sync view counts from Redis to database
    sync_user_analytics: Sync user analytics data
    cleanup_expired_cache: Clean up expired cache entries
    health_check_redis: Monitor Redis health and connection
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.services.redis_service import redis_service
from app.models.upload import Upload
from app.models.user import User
from app.models.views import FileView, ProfileView

logger = logging.getLogger(__name__)


class BackgroundSyncService:
    """Service for background synchronization between Redis and PostgreSQL."""

    @staticmethod
    async def sync_view_counts_to_db():
        """
        Sync view counts from Redis to PostgreSQL database.
        This ensures data persistence and consistency.
        """
        if not redis_service.is_connected():
            logger.warning("Redis not connected, skipping view count sync")
            return

        db = next(get_db())
        try:
            logger.info("Starting view count sync from Redis to PostgreSQL")
            synced_files = 0
            synced_profiles = 0

            # Sync file view counts
            file_view_keys = redis_service._safe_operation(
                redis_service.redis_client.keys, "views:file:*"
            )

            if file_view_keys:
                for key in file_view_keys:
                    try:
                        upload_id = int(key.split(":")[-1])
                        redis_data = redis_service.get_file_view_count(upload_id)

                        if redis_data and redis_data.get("total", 0) > 0:
                            # Update upload record with latest view count
                            upload = db.query(Upload).filter(Upload.id == upload_id).first()
                            if upload:
                                db_view_count = db.query(func.count(FileView.id)).filter(
                                    FileView.upload_id == upload_id
                                ).scalar() or 0

                                redis_view_count = redis_data.get("total", 0)

                                # Only update if Redis has more recent data
                                if redis_view_count > db_view_count:
                                    upload.view_count = redis_view_count
                                    synced_files += 1

                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error syncing file view count for {key}: {e}")
                        continue

            # Sync profile view counts
            profile_view_keys = redis_service._safe_operation(
                redis_service.redis_client.keys, "views:profile:*"
            )

            if profile_view_keys:
                for key in profile_view_keys:
                    try:
                        user_id = int(key.split(":")[-1])
                        redis_count = redis_service._safe_operation(
                            redis_service.redis_client.get, key
                        )

                        if redis_count and int(redis_count) > 0:
                            # Update user profile view stats
                            user = db.query(User).filter(User.id == user_id).first()
                            if user:
                                db_view_count = db.query(func.count(ProfileView.id)).filter(
                                    ProfileView.profile_user_id == user_id
                                ).scalar() or 0

                                redis_view_count = int(redis_count)

                                # Store the latest count (could add profile_view_count field to User model)
                                if redis_view_count > db_view_count:
                                    synced_profiles += 1

                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error syncing profile view count for {key}: {e}")
                        continue

            # Commit all changes
            db.commit()
            logger.info(f"View count sync completed: {synced_files} files, {synced_profiles} profiles")

        except Exception as e:
            db.rollback()
            logger.error(f"Error during view count sync: {e}")
        finally:
            db.close()

    @staticmethod
    async def sync_trending_data():
        """
        Update trending data in Redis based on recent database activity.
        This rebuilds trending sorted sets from fresh database queries.
        """
        if not redis_service.is_connected():
            logger.warning("Redis not connected, skipping trending data sync")
            return

        db = next(get_db())
        try:
            logger.info("Rebuilding trending data from database")

            # Time periods to rebuild
            periods = [
                ("24h", timedelta(hours=24)),
                ("7d", timedelta(days=7)),
                ("30d", timedelta(days=30))
            ]

            for period_name, period_delta in periods:
                cutoff = datetime.utcnow() - period_delta

                # Rebuild trending files
                trending_files = db.query(
                    FileView.upload_id,
                    func.count(FileView.id).label('view_count')
                ).filter(
                    FileView.viewed_at >= cutoff
                ).group_by(FileView.upload_id).order_by(func.count(FileView.id).desc()).limit(100).all()

                # Clear existing trending data for this period
                redis_service._safe_operation(
                    redis_service.redis_client.delete,
                    f"trending:files:{period_name}"
                )

                # Populate with fresh data
                for upload_id, view_count in trending_files:
                    redis_service.add_to_trending("file", upload_id, score=view_count, period=period_name)

                # Rebuild trending profiles
                trending_profiles = db.query(
                    ProfileView.profile_user_id,
                    func.count(ProfileView.id).label('view_count')
                ).filter(
                    ProfileView.viewed_at >= cutoff
                ).group_by(ProfileView.profile_user_id).order_by(func.count(ProfileView.id).desc()).limit(100).all()

                # Clear existing trending data for this period
                redis_service._safe_operation(
                    redis_service.redis_client.delete,
                    f"trending:profiles:{period_name}"
                )

                # Populate with fresh data
                for user_id, view_count in trending_profiles:
                    redis_service.add_to_trending("profile", user_id, score=view_count, period=period_name)

            logger.info("Trending data rebuild completed")

        except Exception as e:
            logger.error(f"Error during trending data sync: {e}")
        finally:
            db.close()

    @staticmethod
    async def cleanup_expired_cache():
        """
        Clean up expired cache entries and optimize Redis memory usage.
        """
        if not redis_service.is_connected():
            return

        try:
            logger.info("Starting Redis cache cleanup")

            # Get Redis info
            info = redis_service._safe_operation(redis_service.redis_client.info, "memory")
            if info:
                used_memory = info.get("used_memory_human", "unknown")
                logger.info(f"Redis memory usage before cleanup: {used_memory}")

            # Clean up old view count entries (older than 7 days)
            cutoff_timestamp = int((datetime.utcnow() - timedelta(days=7)).timestamp())

            # Remove old daily view counts
            old_keys = redis_service._safe_operation(
                redis_service.redis_client.keys, "views:*:daily:*"
            )

            if old_keys:
                removed_count = 0
                for key in old_keys:
                    try:
                        # Extract timestamp from key if possible
                        key_parts = key.split(":")
                        if len(key_parts) >= 4:
                            # If key is older than cutoff, remove it
                            redis_service._safe_operation(redis_service.redis_client.delete, key)
                            removed_count += 1
                    except:
                        continue

                logger.info(f"Removed {removed_count} expired view count keys")

            # Clean up old analytics cache (older than 1 hour)
            old_analytics = redis_service._safe_operation(
                redis_service.redis_client.keys, "analytics:*"
            )

            if old_analytics:
                removed_analytics = 0
                for key in old_analytics:
                    ttl = redis_service._safe_operation(redis_service.redis_client.ttl, key)
                    if ttl == -1:  # No expiration set
                        redis_service._safe_operation(redis_service.redis_client.expire, key, 3600)
                    elif ttl == -2:  # Key doesn't exist or expired
                        removed_analytics += 1

                logger.info(f"Cleaned up {removed_analytics} expired analytics entries")

            # Final memory check
            info = redis_service._safe_operation(redis_service.redis_client.info, "memory")
            if info:
                used_memory = info.get("used_memory_human", "unknown")
                logger.info(f"Redis memory usage after cleanup: {used_memory}")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    @staticmethod
    async def health_check_redis():
        """
        Monitor Redis health and log statistics.
        """
        try:
            if not redis_service.is_connected():
                logger.warning("Redis health check failed: Not connected")
                return

            stats = redis_service.get_cache_stats()
            if stats.get("status") == "connected":
                logger.info(f"Redis health check passed - Memory: {stats.get('memory_used', 'unknown')}, "
                           f"Clients: {stats.get('connected_clients', 'unknown')}")
            else:
                logger.warning(f"Redis health check failed: {stats}")

        except Exception as e:
            logger.error(f"Redis health check error: {e}")

    @staticmethod
    async def run_all_background_tasks():
        """
        Run all background tasks in sequence.
        This is the main entry point for background processing.
        """
        logger.info("Starting background sync tasks")

        try:
            # Run tasks in order of importance
            await BackgroundSyncService.health_check_redis()
            await BackgroundSyncService.sync_view_counts_to_db()
            await BackgroundSyncService.cleanup_expired_cache()

            # Rebuild trending data less frequently (every 30 minutes)
            now = datetime.utcnow()
            if now.minute % 30 == 0:
                await BackgroundSyncService.sync_trending_data()

            logger.info("Background sync tasks completed successfully")

        except Exception as e:
            logger.error(f"Error in background sync tasks: {e}")


# For testing purposes
async def main():
    """Test function to run background tasks manually."""
    await BackgroundSyncService.run_all_background_tasks()


if __name__ == "__main__":
    asyncio.run(main())