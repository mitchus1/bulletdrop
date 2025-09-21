#!/usr/bin/env python3
"""
Whitelist Test Script

This script tests that whitelisted IPs can bypass rate limiting.
"""

import sys
import os
sys.path.append('/home/bulletdrop/bulletdrop/backend')

import asyncio
from app.middleware.rate_limit import RateLimiter

async def test_whitelist():
    """Test that whitelisted IPs bypass rate limiting."""
    rate_limiter = RateLimiter()
    
    # Test IP (your current IP should be whitelisted)
    test_ip = "165.22.80.177"
    
    print(f"🧪 Testing whitelist functionality for IP: {test_ip}")
    print("=" * 50)
    
    # Check if IP is whitelisted
    is_whitelisted = await rate_limiter.is_ip_whitelisted(test_ip)
    print(f"Is whitelisted: {is_whitelisted}")
    
    if not is_whitelisted:
        print("❌ IP is not whitelisted! Adding it now...")
        await rate_limiter.add_to_whitelist(test_ip)
        is_whitelisted = await rate_limiter.is_ip_whitelisted(test_ip)
        print(f"Is whitelisted now: {is_whitelisted}")
    
    # Test that rate limiting is bypassed for whitelisted IP
    print("\\n🔄 Testing rate limiting bypass...")
    
    # Simulate multiple rapid requests (would normally trigger rate limiting)
    for i in range(10):
        key = f"auth:ip:{test_ip}:1m"
        is_limited, rate_info = await rate_limiter.is_rate_limited(key, 5, 60)
        print(f"Request {i+1}: Limited={is_limited}, Current={rate_info['current']}")
        
        if is_limited:
            print("❌ Rate limiting should not apply to whitelisted IPs!")
            break
    else:
        print("✅ Rate limiting properly bypassed for whitelisted IP")
    
    # Show current whitelist
    whitelist = await rate_limiter.get_whitelist()
    print(f"\\n📋 Current whitelist ({len(whitelist)} IPs):")
    for ip in sorted(whitelist):
        print(f"   {ip}")

if __name__ == "__main__":
    asyncio.run(test_whitelist())