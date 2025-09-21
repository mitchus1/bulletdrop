#!/usr/bin/env python3
"""
Rate Limiting Configuration Checker

This script checks the rate limiting configuration and ensures all
dependencies are properly set up.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_redis_connection():
    """Check if Redis is available and accessible."""
    try:
        from app.services.redis_service import redis_service
        if redis_service.is_connected():
            print("✅ Redis connection: OK")
            return True
        else:
            print("❌ Redis connection: FAILED")
            print("   Make sure Redis is running and accessible")
            return False
    except Exception as e:
        print(f"❌ Redis connection: ERROR - {e}")
        return False

def check_rate_limit_config():
    """Check rate limiting configuration."""
    try:
        from app.core.config import settings
        
        print("📊 Rate Limiting Configuration:")
        print(f"   Enabled: {settings.RATE_LIMIT_ENABLED}")
        print(f"   Auth limits: {settings.RATE_LIMIT_AUTH_PER_MINUTE}/min, {settings.RATE_LIMIT_AUTH_PER_HOUR}/hour")
        print(f"   API limits: {settings.RATE_LIMIT_API_PER_MINUTE}/min, {settings.RATE_LIMIT_API_PER_HOUR}/hour")
        print(f"   Upload limits: {settings.RATE_LIMIT_UPLOAD_PER_MINUTE}/min, {settings.RATE_LIMIT_UPLOAD_PER_HOUR}/hour")
        print(f"   Block duration: {settings.RATE_LIMIT_BLOCK_DURATION} seconds")
        
        if not settings.RATE_LIMIT_ENABLED:
            print("⚠️  Rate limiting is DISABLED")
        
        return True
    except Exception as e:
        print(f"❌ Configuration check: ERROR - {e}")
        return False

def check_middleware_import():
    """Check if rate limiting middleware can be imported."""
    try:
        from app.middleware.rate_limit import RateLimitMiddleware, RateLimiter
        print("✅ Rate limiting middleware: OK")
        return True
    except Exception as e:
        print(f"❌ Middleware import: ERROR - {e}")
        return False

def main():
    print("🔍 BulletDrop Rate Limiting Configuration Check")
    print("=" * 50)
    
    all_good = True
    
    # Check middleware import
    if not check_middleware_import():
        all_good = False
    
    # Check configuration
    if not check_rate_limit_config():
        all_good = False
    
    # Check Redis connection
    if not check_redis_connection():
        all_good = False
        print("   💡 To install Redis:")
        print("      Ubuntu/Debian: sudo apt install redis-server")
        print("      macOS: brew install redis")
        print("      Docker: docker run -d -p 6379:6379 redis:alpine")
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All checks passed! Rate limiting is ready to use.")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()