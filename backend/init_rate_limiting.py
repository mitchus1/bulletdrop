#!/usr/bin/env python3
"""
Rate Limiting Startup Script

This script initializes the rate limiting system by adding common
development and local IPs to the whitelist automatically.
"""

import sys
import os
sys.path.append('/home/bulletdrop/bulletdrop/backend')

from app.services.redis_service import redis_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def initialize_rate_limiting():
    """Initialize rate limiting with default whitelisted IPs."""
    try:
        if not redis_service.is_connected():
            print("⚠️  Redis not available, skipping rate limiting initialization")
            return
        
        # Common development and local IPs to whitelist
        default_whitelist = [
            "127.0.0.1",        # localhost
            "::1",              # localhost IPv6
            "192.168.1.1",      # common router IP
            "10.0.0.1",         # common private network
            "172.16.0.1",       # common private network
            "165.22.80.177",    # Current production IP
        ]
        
        client = redis_service.client
        whitelist_key = "rate_limit:whitelist"
        
        # Get current whitelist
        current_whitelist = set(client.smembers(whitelist_key))
        
        # Add missing IPs to whitelist
        added_ips = []
        for ip in default_whitelist:
            if ip not in current_whitelist:
                client.sadd(whitelist_key, ip)
                added_ips.append(ip)
        
        if added_ips:
            print(f"✅ Added {len(added_ips)} IPs to whitelist: {', '.join(added_ips)}")
        else:
            print("ℹ️  All default IPs already whitelisted")
            
        # Show current whitelist
        final_whitelist = list(client.smembers(whitelist_key))
        print(f"📋 Current whitelist ({len(final_whitelist)} IPs):")
        for ip in sorted(final_whitelist):
            print(f"   {ip}")
            
    except Exception as e:
        print(f"❌ Error initializing rate limiting: {e}")

if __name__ == "__main__":
    initialize_rate_limiting()