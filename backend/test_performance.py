#!/usr/bin/env python3
"""
Performance Test Script for Redis Optimizations

This script tests the performance improvements from Redis caching
implementation in BulletDrop.
"""

import time
import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to path
sys.path.insert(0, '/home/bulletdrop/bulletdrop/backend')

from app.services.redis_service import redis_service
from app.services.analytics_service import AnalyticsService
from app.core.database import get_db

def measure_time(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        return result, execution_time
    return wrapper

class PerformanceTest:
    """Performance testing class for Redis optimizations."""

    def __init__(self):
        self.results = {}

    def test_redis_connection(self):
        """Test Redis connection and basic operations."""
        print("🔍 Testing Redis Connection...")

        if not redis_service.is_connected():
            print("❌ Redis is not connected!")
            return False

        # Test basic operations
        test_key = "perf_test:connection"
        redis_service._safe_operation(
            redis_service.redis_client.set, test_key, "test_value"
        )

        retrieved = redis_service._safe_operation(
            redis_service.redis_client.get, test_key
        )

        redis_service._safe_operation(
            redis_service.redis_client.delete, test_key
        )

        success = retrieved == "test_value"
        print(f"✅ Redis connection test: {'PASSED' if success else 'FAILED'}")
        return success

    @measure_time
    def test_view_count_caching(self):
        """Test view count caching performance."""
        upload_id = 63  # Use existing upload from Redis

        # First call (should use cache)
        view_data = redis_service.get_file_view_count(upload_id)
        return view_data is not None

    @measure_time
    def test_analytics_caching(self):
        """Test analytics caching performance."""
        # Test data
        test_analytics = {
            "content_id": 999,
            "content_type": "file",
            "total_views": 100,
            "unique_viewers": 50,
            "views_today": 10
        }

        # Cache the data
        redis_service.cache_analytics("file", 999, test_analytics)

        # Retrieve from cache
        cached_data = redis_service.get_cached_analytics("file", 999)
        return cached_data is not None

    @measure_time
    def test_user_cache_lookup(self):
        """Test user caching for JWT lookups."""
        test_user_data = {
            "id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "is_active": True,
            "is_admin": False,
            "is_premium": False
        }

        # Cache user data
        redis_service.cache_jwt_user("test_user", test_user_data)

        # Retrieve from cache
        cached_user = redis_service.get_cached_jwt_user("test_user")
        return cached_user is not None

    def test_cache_hit_ratio(self):
        """Test cache hit ratio."""
        print("📊 Testing Cache Hit Ratio...")

        stats = redis_service.get_cache_stats()
        if stats.get("status") == "connected":
            hits = stats.get("keyspace_hits", 0)
            misses = stats.get("keyspace_misses", 0)
            total = hits + misses

            if total > 0:
                hit_ratio = (hits / total) * 100
                print(f"📈 Cache Hit Ratio: {hit_ratio:.2f}% ({hits} hits, {misses} misses)")
                self.results["cache_hit_ratio"] = hit_ratio
            else:
                print("📊 No cache statistics available yet")
                self.results["cache_hit_ratio"] = 0
        else:
            print("❌ Could not retrieve cache statistics")
            self.results["cache_hit_ratio"] = 0

    def test_memory_usage(self):
        """Test Redis memory usage."""
        print("💾 Testing Memory Usage...")

        stats = redis_service.get_cache_stats()
        if stats.get("status") == "connected":
            memory_used = stats.get("memory_used", "unknown")
            print(f"🔋 Redis Memory Usage: {memory_used}")
            self.results["memory_usage"] = memory_used
        else:
            print("❌ Could not retrieve memory statistics")

    def run_performance_tests(self):
        """Run all performance tests."""
        print("🚀 Starting BulletDrop Redis Performance Tests")
        print("=" * 50)

        # Test Redis connection
        if not self.test_redis_connection():
            print("❌ Redis connection failed, aborting tests")
            return

        print("\n📊 Running Performance Benchmarks...")

        # Test view count caching
        result, exec_time = self.test_view_count_caching()
        print(f"⚡ View Count Cache: {exec_time:.2f}ms - {'✅ SUCCESS' if result else '❌ FAILED'}")
        self.results["view_count_cache_time"] = exec_time

        # Test analytics caching
        result, exec_time = self.test_analytics_caching()
        print(f"⚡ Analytics Cache: {exec_time:.2f}ms - {'✅ SUCCESS' if result else '❌ FAILED'}")
        self.results["analytics_cache_time"] = exec_time

        # Test user caching
        result, exec_time = self.test_user_cache_lookup()
        print(f"⚡ User Cache Lookup: {exec_time:.2f}ms - {'✅ SUCCESS' if result else '❌ FAILED'}")
        self.results["user_cache_time"] = exec_time

        # Test cache statistics
        self.test_cache_hit_ratio()
        self.test_memory_usage()

        self.print_summary()

    def print_summary(self):
        """Print performance test summary."""
        print("\n" + "=" * 50)
        print("📋 PERFORMANCE TEST SUMMARY")
        print("=" * 50)

        print(f"⚡ View Count Cache: {self.results.get('view_count_cache_time', 0):.2f}ms")
        print(f"⚡ Analytics Cache: {self.results.get('analytics_cache_time', 0):.2f}ms")
        print(f"⚡ User Cache Lookup: {self.results.get('user_cache_time', 0):.2f}ms")
        print(f"📈 Cache Hit Ratio: {self.results.get('cache_hit_ratio', 0):.2f}%")
        print(f"💾 Memory Usage: {self.results.get('memory_usage', 'unknown')}")

        # Calculate average response time
        times = [
            self.results.get('view_count_cache_time', 0),
            self.results.get('analytics_cache_time', 0),
            self.results.get('user_cache_time', 0)
        ]
        avg_time = sum(times) / len(times) if times else 0
        print(f"📊 Average Cache Response: {avg_time:.2f}ms")

        print("\n🎯 PERFORMANCE ANALYSIS:")
        if avg_time < 10:
            print("🏆 EXCELLENT: Sub-10ms cache response times!")
        elif avg_time < 50:
            print("✅ GOOD: Cache response times under 50ms")
        else:
            print("⚠️  SLOW: Cache response times over 50ms")

        hit_ratio = self.results.get('cache_hit_ratio', 0)
        if hit_ratio > 80:
            print("🎯 EXCELLENT: Cache hit ratio above 80%")
        elif hit_ratio > 60:
            print("✅ GOOD: Cache hit ratio above 60%")
        else:
            print("⚠️  LOW: Cache hit ratio needs improvement")

if __name__ == "__main__":
    test_runner = PerformanceTest()
    test_runner.run_performance_tests()