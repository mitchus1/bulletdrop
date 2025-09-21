#!/usr/bin/env python3
"""
IP Management Script for BulletDrop Rate Limiting

Quick script to:
1. Check blocked IPs
2. Unblock specific IPs
3. Add IPs to whitelist
"""

import sys
import os
sys.path.append('/home/bulletdrop/bulletdrop/backend')

from app.services.redis_service import redis_service
from app.core.config import settings

def get_blocked_ips():
    """Get all currently blocked IPs"""
    try:
        client = redis_service.client
        if not client:
            print("❌ Redis not available")
            return []
        
        blocked_keys = client.keys('rate_limit:blocked:*')
        blocked_ips = []
        
        print("🚫 Currently blocked IPs:")
        for key in blocked_keys:
            ip = key.replace('rate_limit:blocked:', '')
            ttl = client.ttl(key)
            blocked_ips.append(ip)
            print(f"   {ip} (expires in {ttl} seconds)")
        
        if not blocked_ips:
            print("   No IPs currently blocked")
            
        return blocked_ips
    except Exception as e:
        print(f"❌ Error getting blocked IPs: {e}")
        return []

def unblock_ip(ip):
    """Unblock a specific IP"""
    try:
        client = redis_service.client
        if not client:
            print("❌ Redis not available")
            return False
        
        # Remove from blocked list
        key = f'rate_limit:blocked:{ip}'
        removed = client.delete(key)
        
        # Clear rate limit counters for this IP
        rate_keys = client.keys(f'rate_limit:*:{ip}:*')
        if rate_keys:
            client.delete(*rate_keys)
        
        if removed:
            print(f"✅ Unblocked IP: {ip}")
        else:
            print(f"ℹ️  IP {ip} was not blocked")
            
        return True
    except Exception as e:
        print(f"❌ Error unblocking IP {ip}: {e}")
        return False

def add_to_whitelist(ip):
    """Add IP to whitelist"""
    try:
        client = redis_service.client
        if not client:
            print("❌ Redis not available")
            return False
        
        # Add to whitelist set
        client.sadd('rate_limit:whitelist', ip)
        print(f"✅ Added {ip} to whitelist")
        return True
    except Exception as e:
        print(f"❌ Error adding IP to whitelist: {e}")
        return False

def get_whitelist():
    """Get all whitelisted IPs"""
    try:
        client = redis_service.client
        if not client:
            print("❌ Redis not available")
            return []
        
        whitelist = client.smembers('rate_limit:whitelist')
        print("✅ Whitelisted IPs:")
        for ip in whitelist:
            print(f"   {ip}")
        
        if not whitelist:
            print("   No IPs in whitelist")
            
        return list(whitelist)
    except Exception as e:
        print(f"❌ Error getting whitelist: {e}")
        return []

def get_current_ip():
    """Try to detect current IP"""
    import socket
    import requests
    
    try:
        # Try to get external IP
        response = requests.get('https://ipinfo.io/ip', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    try:
        # Fallback to local IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except:
        return "127.0.0.1"

def main():
    if len(sys.argv) == 1:
        print("🔍 BulletDrop IP Management Tool")
        print("=" * 40)
        
        # Show current status
        get_blocked_ips()
        print()
        get_whitelist()
        
        # Detect current IP
        current_ip = get_current_ip()
        print(f"\\n🌐 Your current IP appears to be: {current_ip}")
        
        print("\\n📋 Commands:")
        print(f"  python3 {sys.argv[0]} unblock <ip>     - Unblock an IP")
        print(f"  python3 {sys.argv[0]} whitelist <ip>   - Add IP to whitelist")
        print(f"  python3 {sys.argv[0]} unblock-me      - Unblock your current IP")
        print(f"  python3 {sys.argv[0]} whitelist-me    - Whitelist your current IP")
        
    elif len(sys.argv) >= 2:
        command = sys.argv[1].lower()
        
        if command == "unblock" and len(sys.argv) == 3:
            unblock_ip(sys.argv[2])
        elif command == "whitelist" and len(sys.argv) == 3:
            add_to_whitelist(sys.argv[2])
        elif command == "unblock-me":
            current_ip = get_current_ip()
            print(f"🌐 Detected IP: {current_ip}")
            unblock_ip(current_ip)
        elif command == "whitelist-me":
            current_ip = get_current_ip()
            print(f"🌐 Detected IP: {current_ip}")
            add_to_whitelist(current_ip)
        else:
            print("❌ Invalid command")

if __name__ == "__main__":
    main()