"""
Security Utilities

This module provides security-related utility functions for input sanitization,
validation, and security checks.
"""

import html
import re
from typing import Optional, List
from urllib.parse import urlparse


def sanitize_html_input(text: str) -> str:
    """
    Sanitize HTML input to prevent XSS attacks.

    Args:
        text: Raw text input that might contain HTML

    Returns:
        HTML-escaped text safe for output
    """
    if not text:
        return ""

    # HTML escape the input
    sanitized = html.escape(text, quote=True)

    # Remove any remaining potentially dangerous patterns
    dangerous_patterns = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'onclick=',
        r'onmouseover=',
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    return sanitized


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem use
    """
    if not filename:
        return "unnamed_file"

    # Remove any directory traversal attempts
    filename = filename.replace('/', '_').replace('\\', '_')
    filename = filename.replace('..', '_')

    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*\x00-\x1f]', '_', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename or "unnamed_file"


def validate_url(url: str, allowed_schemes: List[str] = None) -> bool:
    """
    Validate URL format and scheme.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: http, https)

    Returns:
        True if URL is valid and safe
    """
    if not url:
        return False

    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in allowed_schemes and
            parsed.netloc and
            not parsed.netloc.startswith('localhost') and
            not re.match(r'^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)', parsed.netloc)
        )
    except Exception:
        return False


def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize general user input for safe storage and display.

    Args:
        text: User input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # HTML escape
    text = html.escape(text, quote=True)

    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')

    return text


def validate_upload_filename(filename: str) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file filename.

    Args:
        filename: Uploaded filename

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"

    if len(filename) > 255:
        return False, "Filename too long (max 255 characters)"

    # Check for dangerous extensions
    dangerous_extensions = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
    ]

    filename_lower = filename.lower()
    for ext in dangerous_extensions:
        if filename_lower.endswith(ext):
            return False, f"File type {ext} not allowed"

    # Check for hidden files or relative paths
    if filename.startswith('.') or '/' in filename or '\\' in filename:
        return False, "Invalid filename format"

    return True, None


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Token length in bytes

    Returns:
        Hex-encoded random token
    """
    import secrets
    return secrets.token_hex(length)


def is_safe_redirect_url(url: str, allowed_hosts: List[str]) -> bool:
    """
    Check if a redirect URL is safe (prevents open redirect attacks).

    Args:
        url: URL to validate
        allowed_hosts: List of allowed hostnames

    Returns:
        True if redirect is safe
    """
    if not url:
        return False

    # Relative URLs are generally safe
    if url.startswith('/') and not url.startswith('//'):
        return True

    try:
        parsed = urlparse(url)
        if parsed.netloc in allowed_hosts:
            return True
    except Exception:
        pass

    return False