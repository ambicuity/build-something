#!/usr/bin/env python3
"""
Production-level exception hierarchy for build-something projects.

Provides comprehensive error handling with clear categorization and 
proper error messages for debugging and user feedback.
"""

from typing import Optional, Any


class BuildSomethingError(Exception):
    """Base exception for all build-something projects."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# Database-specific exceptions
class DatabaseError(BuildSomethingError):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraints are violated."""
    pass


class DatabaseQueryError(DatabaseError):
    """Raised when SQL query parsing or execution fails."""
    pass


class DatabaseStorageError(DatabaseError):
    """Raised when storage engine operations fail."""
    pass


class DatabaseTransactionError(DatabaseError):
    """Raised when transaction operations fail."""
    pass


# Git-specific exceptions
class GitError(BuildSomethingError):
    """Base exception for Git-related errors."""
    pass


class GitRepositoryError(GitError):
    """Raised when Git repository operations fail."""
    pass


class GitObjectError(GitError):
    """Raised when Git object operations fail."""
    pass


class GitIndexError(GitError):
    """Raised when Git index operations fail."""
    pass


class GitCommitError(GitError):
    """Raised when Git commit operations fail."""
    pass


class GitBranchError(GitError):
    """Raised when Git branch operations fail."""
    pass


# HTTP Server-specific exceptions
class HTTPError(BuildSomethingError):
    """Base exception for HTTP server-related errors."""
    
    def __init__(self, message: str, status_code: int = 500, 
                 error_code: Optional[str] = None, context: Optional[dict] = None):
        super().__init__(message, error_code, context)
        self.status_code = status_code


class HTTPParsingError(HTTPError):
    """Raised when HTTP request parsing fails."""
    
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message, 400, "HTTP_PARSE_ERROR", context)


class HTTPRoutingError(HTTPError):
    """Raised when HTTP routing fails."""
    
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message, 404, "HTTP_ROUTING_ERROR", context)


class HTTPServerError(HTTPError):
    """Raised when HTTP server internal errors occur."""
    
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message, 500, "HTTP_SERVER_ERROR", context)


# Shell-specific exceptions
class ShellError(BuildSomethingError):
    """Base exception for shell-related errors."""
    pass


class ShellParsingError(ShellError):
    """Raised when shell command parsing fails."""
    pass


class ShellExecutionError(ShellError):
    """Raised when shell command execution fails."""
    pass


class ShellJobError(ShellError):
    """Raised when shell job control operations fail."""
    pass


# Text Editor-specific exceptions
class EditorError(BuildSomethingError):
    """Base exception for text editor-related errors."""
    pass


class EditorBufferError(EditorError):
    """Raised when text buffer operations fail."""
    pass


class EditorFileError(EditorError):
    """Raised when file operations fail."""
    pass


class EditorSyntaxError(EditorError):
    """Raised when syntax highlighting fails."""
    pass


# Template Engine-specific exceptions
class TemplateError(BuildSomethingError):
    """Base exception for template engine-related errors."""
    pass


class TemplateParsingError(TemplateError):
    """Raised when template parsing fails."""
    pass


class TemplateRenderingError(TemplateError):
    """Raised when template rendering fails."""
    pass


class TemplateContextError(TemplateError):
    """Raised when template context operations fail."""
    pass


# Regex Engine-specific exceptions
class RegexError(BuildSomethingError):
    """Base exception for regex engine-related errors."""
    pass


class RegexParsingError(RegexError):
    """Raised when regex pattern parsing fails."""
    pass


class RegexExecutionError(RegexError):
    """Raised when regex pattern execution fails."""
    pass


# CLI Tools-specific exceptions
class CLIError(BuildSomethingError):
    """Base exception for CLI tools-related errors."""
    pass


class CLIArgumentError(CLIError):
    """Raised when CLI argument parsing fails."""
    pass


class CLIExecutionError(CLIError):
    """Raised when CLI tool execution fails."""
    pass


# Validation exceptions
class ValidationError(BuildSomethingError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, context: Optional[dict] = None):
        super().__init__(message, "VALIDATION_ERROR", context)
        self.field = field
        self.value = value


class SecurityError(BuildSomethingError):
    """Raised when security violations are detected."""
    
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message, "SECURITY_ERROR", context)


class ConfigurationError(BuildSomethingError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 context: Optional[dict] = None):
        super().__init__(message, "CONFIG_ERROR", context)
        self.config_key = config_key