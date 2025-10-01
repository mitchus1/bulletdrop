"""
Utility Functions

Common utility functions used across the application for IP extraction,
input validation, and other shared functionality.
"""

from fastapi import Request
from typing import Optional
import re


def extract_client_ip(request: Request) -> str:
    """
    Extract client IP address from request with proper proxy handling.

    Handles X-Forwarded-For and X-Real-IP headers commonly used by
    reverse proxies and load balancers.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address as string
    """
    # Check X-Forwarded-For header (most common with proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # Take the first one (leftmost) as the original client IP
        ip = forwarded_for.split(",")[0].strip()
        if validate_ip_address(ip):
            return ip

    # Check X-Real-IP header (used by nginx and others)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        ip = real_ip.strip()
        if validate_ip_address(ip):
            return ip

    # Fallback to direct client IP
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def validate_ip_address(ip: str) -> bool:
    """
    Validate if a string is a valid IPv4 or IPv6 address.

    Args:
        ip: IP address string to validate

    Returns:
        True if valid IP address, False otherwise
    """
    # IPv4 regex pattern
    ipv4_pattern = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )

    # IPv6 regex pattern (simplified)
    ipv6_pattern = re.compile(
        r'^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,7}:|'
        r'([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|'
        r'([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|'
        r'([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|'
        r'[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|'
        r':((:[0-9a-fA-F]{1,4}){1,7}|:))$'
    )

    return bool(ipv4_pattern.match(ip) or ipv6_pattern.match(ip))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem use
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    # Remove parent directory references
    filename = filename.replace('..', '')
    # Remove null bytes
    filename = filename.replace('\x00', '')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]

    return filename


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable string.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string like "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


# Constants for file sizes (avoiding magic numbers)
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024

# Constants for time durations (avoiding magic numbers)
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800
