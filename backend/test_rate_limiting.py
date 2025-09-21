#!/usr/bin/env python3
"""
Rate Limiting Test Script

This script tests the rate limiting functionality by making multiple requests
to authentication endpoints and verifying that rate limits are enforced.
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, Any

class RateLimitTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, method: str = "POST", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request and return response data and headers."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "POST":
                async with self.session.post(url, json=data) as response:
                    response_data = await response.json()
                    return {
                        "status": response.status,
                        "data": response_data,
                        "headers": dict(response.headers)
                    }
            else:
                async with self.session.get(url) as response:
                    response_data = await response.json()
                    return {
                        "status": response.status,
                        "data": response_data,
                        "headers": dict(response.headers)
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "headers": {}
            }
    
    async def test_auth_rate_limit(self):
        """Test authentication endpoint rate limiting."""
        print("🔒 Testing Authentication Rate Limiting...")
        print("=" * 50)
        
        # Test data for login attempts
        test_login = {
            "username": "nonexistent_user",
            "password": "wrong_password"
        }
        
        # Make multiple requests to trigger rate limiting
        for i in range(8):  # Exceed the 5 requests per minute limit
            print(f"Request {i + 1}: ", end="")
            
            response = await self.make_request("/login/json", "POST", test_login)
            
            if response["status"] == 429:
                print(f"⛔ RATE LIMITED (429)")
                print(f"   Rate Limit Headers:")
                for header, value in response["headers"].items():
                    if "ratelimit" in header.lower() or "retry" in header.lower():
                        print(f"   {header}: {value}")
                break
            elif response["status"] == 401:
                print(f"✅ Normal auth failure (401)")
            else:
                print(f"❓ Unexpected status: {response['status']}")
            
            # Add rate limit info if available
            if "X-RateLimit-Remaining" in response["headers"]:
                remaining = response["headers"]["X-RateLimit-Remaining"]
                limit = response["headers"].get("X-RateLimit-Limit", "unknown")
                print(f"   Rate Limit: {remaining}/{limit} remaining")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    async def test_api_rate_limit(self):
        """Test general API endpoint rate limiting."""
        print("\n🔍 Testing API Rate Limiting...")
        print("=" * 50)
        
        # Test with health endpoint (should have higher limits)
        for i in range(5):
            print(f"Request {i + 1}: ", end="")
            
            response = await self.make_request("/health", "GET")
            
            if response["status"] == 429:
                print(f"⛔ RATE LIMITED (429)")
                break
            elif response["status"] == 200:
                print(f"✅ Success (200)")
            else:
                print(f"❓ Status: {response['status']}")
            
            # Add rate limit info if available
            if "X-RateLimit-Remaining" in response["headers"]:
                remaining = response["headers"]["X-RateLimit-Remaining"]
                limit = response["headers"].get("X-RateLimit-Limit", "unknown")
                print(f"   Rate Limit: {remaining}/{limit} remaining")
            
            await asyncio.sleep(0.2)
    
    async def test_rate_limit_headers(self):
        """Test that rate limit headers are present in responses."""
        print("\n📊 Testing Rate Limit Headers...")
        print("=" * 50)
        
        response = await self.make_request("/health", "GET")
        
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        
        print("Rate limit headers in response:")
        for header in rate_limit_headers:
            value = response["headers"].get(header, "❌ Missing")
            print(f"  {header}: {value}")
    
    async def check_server_status(self):
        """Check if the server is running and accessible."""
        print("🏥 Checking server status...")
        response = await self.make_request("/health", "GET")
        
        if response["status"] == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server is not accessible (status: {response['status']})")
            return False

async def main():
    print("🚀 BulletDrop Rate Limiting Test")
    print("=" * 50)
    
    async with RateLimitTester() as tester:
        # Check server status first
        if not await tester.check_server_status():
            print("\n❌ Cannot proceed - server is not accessible")
            print("Make sure the BulletDrop backend is running on http://localhost:8000")
            return
        
        # Test rate limiting
        await tester.test_rate_limit_headers()
        await tester.test_api_rate_limit()
        await tester.test_auth_rate_limit()
        
        print("\n🎉 Rate limiting tests completed!")
        print("\nWhat to expect:")
        print("- Authentication endpoints should be rate limited after 5 requests/minute")
        print("- API endpoints should have higher limits (60 requests/minute)")
        print("- Rate limit headers should be present in responses")
        print("- Blocked IPs should receive 429 status codes")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")