#!/usr/bin/env python3
"""
Rate Limiting Summary

Shows the current status of the rate limiting system.
"""

import sys
import os
sys.path.append('/home/bulletdrop/bulletdrop/backend')

from app.services.redis_service import redis_service
from app.core.config import settings

def show_rate_limiting_status():
    """Show comprehensive rate limiting status."""
    print("🛡️  BulletDrop Rate Limiting Status")
    print("=" * 50)
    
    # Configuration
    print("⚙️  Configuration:")
    print(f"   Enabled: {settings.RATE_LIMIT_ENABLED}")
    print(f"   Auth limits: {settings.RATE_LIMIT_AUTH_PER_MINUTE}/min, {settings.RATE_LIMIT_AUTH_PER_HOUR}/hour")
    print(f"   API limits: {settings.RATE_LIMIT_API_PER_MINUTE}/min, {settings.RATE_LIMIT_API_PER_HOUR}/hour")
    print(f"   Upload limits: {settings.RATE_LIMIT_UPLOAD_PER_MINUTE}/min, {settings.RATE_LIMIT_UPLOAD_PER_HOUR}/hour")
    print(f"   Block duration: {settings.RATE_LIMIT_BLOCK_DURATION} seconds")
    
    # Redis connection
    print(f"\\n🔗 Redis Connection:")
    print(f"   URL: {settings.REDIS_URL}")
    print(f"   Connected: {redis_service.is_connected()}")
    
    if not redis_service.is_connected():
        print("❌ Redis not available - rate limiting will be disabled")
        return
    
    client = redis_service.client
    
    # Blocked IPs
    print("\\n🚫 Blocked IPs:")
    blocked_keys = client.keys('rate_limit:blocked:*')
    if blocked_keys:
        for key in blocked_keys:
            ip = key.replace('rate_limit:blocked:', '')
            ttl = client.ttl(key)
            print(f"   {ip} (expires in {ttl}s)")
    else:
        print("   None")
    
    # Whitelisted IPs
    print("\\n✅ Whitelisted IPs:")
    whitelist = list(client.smembers('rate_limit:whitelist'))
    if whitelist:
        for ip in sorted(whitelist):
            print(f"   {ip}")
    else:
        print("   None")
    
    # Active rate limits
    print("\\n📊 Active Rate Limit Counters:")
    rate_keys = client.keys('rate_limit:*')
    rate_keys = [k for k in rate_keys if not k.startswith('rate_limit:whitelist') and not k.startswith('rate_limit:blocked')]
    
    if rate_keys:
        for key in rate_keys[:10]:  # Show first 10
            count = client.zcard(key)
            ttl = client.ttl(key)
            print(f"   {key}: {count} requests (TTL: {ttl}s)")
        if len(rate_keys) > 10:
            print(f"   ... and {len(rate_keys) - 10} more")
    else:
        print("   None")
    
    print("\\n🎯 Summary:")
    print(f"   ✅ Rate limiting is {'enabled' if settings.RATE_LIMIT_ENABLED else 'disabled'}")
    print(f"   ✅ Redis connection is {'working' if redis_service.is_connected() else 'failed'}")
    print(f"   ✅ {len(whitelist)} IP(s) whitelisted")
    print(f"   ✅ {len(blocked_keys)} IP(s) currently blocked")
    print(f"   ✅ Your IP (165.22.80.177) is {'whitelisted' if '165.22.80.177' in whitelist else 'not whitelisted'}")

if __name__ == "__main__":
    show_rate_limiting_status()