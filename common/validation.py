#!/usr/bin/env python3
"""
Input validation and security utilities for build-something projects.

Provides comprehensive input validation, sanitization, and security 
measures to protect against common vulnerabilities.
"""

import re
import html
import urllib.parse
import hashlib
import secrets
import string
from typing import Any, List, Dict, Union, Optional, Callable
from pathlib import Path
from exceptions import ValidationError, SecurityError


class InputValidator:
    """Comprehensive input validation with security checks."""
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#[^\s]*)?$')
    IPV4_PATTERN = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
    
    # Dangerous patterns that should be rejected
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"].*['\"])",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
    ]
    
    def __init__(self):
        self.compiled_sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.compiled_xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
        self.compiled_path_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
    
    def validate_string(self, value: Any, field_name: str, 
                       min_length: int = 0, max_length: int = None,
                       pattern: Optional[re.Pattern] = None,
                       allowed_chars: Optional[str] = None) -> str:
        """
        Validate and return a string value.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            pattern: Optional regex pattern to match
            allowed_chars: Optional string of allowed characters
            
        Returns:
            Validated string value
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"{field_name} must be a string", 
                field=field_name, 
                value=value
            )
        
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters long",
                field=field_name,
                value=value
            )
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must not exceed {max_length} characters",
                field=field_name,
                value=value
            )
        
        if pattern and not pattern.match(value):
            raise ValidationError(
                f"{field_name} format is invalid",
                field=field_name,
                value=value
            )
        
        if allowed_chars:
            if not all(c in allowed_chars for c in value):
                raise ValidationError(
                    f"{field_name} contains invalid characters",
                    field=field_name,
                    value=value
                )
        
        return value
    
    def validate_integer(self, value: Any, field_name: str,
                        min_value: Optional[int] = None,
                        max_value: Optional[int] = None) -> int:
        """Validate and return an integer value."""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a valid integer",
                field=field_name,
                value=value
            )
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                field=field_name,
                value=value
            )
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} must not exceed {max_value}",
                field=field_name,
                value=value
            )
        
        return int_value
    
    def validate_float(self, value: Any, field_name: str,
                      min_value: Optional[float] = None,
                      max_value: Optional[float] = None) -> float:
        """Validate and return a float value."""
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a valid number",
                field=field_name,
                value=value
            )
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                field=field_name,
                value=value
            )
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(
                f"{field_name} must not exceed {max_value}",
                field=field_name,
                value=value
            )
        
        return float_value
    
    def validate_email(self, value: Any, field_name: str) -> str:
        """Validate and return an email address."""
        email_str = self.validate_string(value, field_name, max_length=254)
        
        if not self.EMAIL_PATTERN.match(email_str):
            raise ValidationError(
                f"{field_name} must be a valid email address",
                field=field_name,
                value=value
            )
        
        return email_str
    
    def validate_url(self, value: Any, field_name: str) -> str:
        """Validate and return a URL."""
        url_str = self.validate_string(value, field_name, max_length=2048)
        
        if not self.URL_PATTERN.match(url_str):
            raise ValidationError(
                f"{field_name} must be a valid URL",
                field=field_name,
                value=value
            )
        
        return url_str
    
    def validate_filename(self, value: Any, field_name: str) -> str:
        """Validate and return a safe filename."""
        filename_str = self.validate_string(value, field_name, max_length=255)
        
        if not self.FILENAME_PATTERN.match(filename_str):
            raise ValidationError(
                f"{field_name} contains invalid characters for a filename",
                field=field_name,
                value=value
            )
        
        # Check for reserved names
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        if filename_str.upper() in reserved_names:
            raise ValidationError(
                f"{field_name} is a reserved filename",
                field=field_name,
                value=value
            )
        
        return filename_str
    
    def validate_path(self, value: Any, field_name: str, 
                     allow_absolute: bool = False) -> str:
        """Validate and return a safe file path."""
        path_str = self.validate_string(value, field_name, max_length=4096)
        
        # Check for path traversal attempts
        for pattern in self.compiled_path_patterns:
            if pattern.search(path_str):
                raise SecurityError(
                    f"{field_name} contains path traversal attempt",
                    context={'field': field_name, 'value': value}
                )
        
        if not allow_absolute and Path(path_str).is_absolute():
            raise ValidationError(
                f"{field_name} must be a relative path",
                field=field_name,
                value=value
            )
        
        return path_str
    
    def check_sql_injection(self, value: str, field_name: str) -> str:
        """Check for SQL injection patterns (excluding legitimate SQL keywords)."""
        # Create a more permissive check that allows legitimate SQL but blocks malicious patterns
        suspicious_patterns = [
            r"(--|#)",  # SQL comments
            r"(/\*|\*/)",  # Block comments
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",  # Boolean always-true conditions
            r"(\b(OR|AND)\s+['\"].*['\"])",  # String-based injection attempts
            r"(\bUNION\s+(?:ALL\s+)?SELECT\b)",  # UNION injection attempts
            r"(\bEXEC\b|\bEXECUTE\b)",  # Execute statements
            r"(;\s*(DROP|DELETE|UPDATE|INSERT))",  # Multiple statements
        ]
        
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in suspicious_patterns]
        
        for pattern in compiled_patterns:
            if pattern.search(value):
                raise SecurityError(
                    f"{field_name} contains potential SQL injection",
                    context={'field': field_name, 'pattern_matched': pattern.pattern}
                )
        return value
    
    def check_xss(self, value: str, field_name: str) -> str:
        """Check for XSS patterns."""
        for pattern in self.compiled_xss_patterns:
            if pattern.search(value):
                raise SecurityError(
                    f"{field_name} contains potential XSS content",
                    context={'field': field_name, 'pattern_matched': pattern.pattern}
                )
        return value
    
    def sanitize_html(self, value: str) -> str:
        """Sanitize HTML content by escaping special characters."""
        return html.escape(value, quote=True)
    
    def sanitize_url(self, value: str) -> str:
        """Sanitize URL by encoding special characters."""
        return urllib.parse.quote(value, safe='/:?#[]@!$&\'()*+,;=')
    
    def sanitize_sql(self, value: str) -> str:
        """Sanitize SQL input by escaping quotes."""
        return value.replace("'", "''").replace('"', '""')


class SecurityUtils:
    """Security utilities for authentication, encryption, etc."""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash a password with salt.
        
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """Verify a password against its hash."""
        computed_hash, _ = SecurityUtils.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, hashed_password)
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a CSRF token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Compare two strings in constant time to prevent timing attacks."""
        return secrets.compare_digest(a, b)


# Global validator instance
validator = InputValidator()
security = SecurityUtils()


def validate_input(validator_func: Callable, *args, **kwargs):
    """Decorator to validate function inputs."""
    def decorator(func):
        def wrapper(*func_args, **func_kwargs):
            # Apply validation
            validator_func(*func_args, **func_kwargs)
            return func(*func_args, **func_kwargs)
        return wrapper
    return decorator