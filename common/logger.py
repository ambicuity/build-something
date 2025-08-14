#!/usr/bin/env python3
"""
Production-level logging system for build-something projects.

Provides structured logging with proper configuration, formatting,
and context management for debugging and monitoring.
"""

import logging
import logging.handlers
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured logs with context."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }
        
        # Add extra context if present
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        # Add process/thread info for debugging
        log_entry['process_id'] = record.process
        log_entry['thread_id'] = record.thread
        
        return json.dumps(log_entry, default=str, indent=2 if self.is_pretty else None)
    
    def __init__(self, pretty: bool = False):
        super().__init__()
        self.is_pretty = pretty


class ProductionLogger:
    """Production-ready logger with structured output and context management."""
    
    def __init__(self, name: str, level: str = "INFO", 
                 log_file: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 structured: bool = True,
                 pretty_console: bool = False):
        """
        Initialize production logger.
        
        Args:
            name: Logger name (typically module name)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for log output
            max_file_size: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            structured: Whether to use structured JSON logging
            pretty_console: Whether to pretty-print console logs
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if structured:
            console_formatter = StructuredFormatter(pretty=pretty_console)
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_file_size, backupCount=backup_count
            )
            
            if structured:
                file_formatter = StructuredFormatter(pretty=False)
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message with optional context."""
        self._log(logging.DEBUG, message, context)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message with optional context."""
        self._log(logging.INFO, message, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message with optional context."""
        self._log(logging.WARNING, message, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, 
              exception: Optional[Exception] = None):
        """Log error message with optional context and exception."""
        self._log(logging.ERROR, message, context, exception)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None,
                 exception: Optional[Exception] = None):
        """Log critical message with optional context and exception."""
        self._log(logging.CRITICAL, message, context, exception)
    
    def _log(self, level: int, message: str, context: Optional[Dict[str, Any]] = None,
             exception: Optional[Exception] = None):
        """Internal logging method with context support."""
        extra = {}
        if context:
            extra['context'] = context
        
        if exception:
            self.logger.log(level, message, exc_info=exception, extra=extra)
        else:
            self.logger.log(level, message, extra=extra)
    
    @contextmanager
    def operation_context(self, operation: str, **kwargs):
        """Context manager for logging operation start/end with timing."""
        start_time = datetime.now()
        context = {
            'operation': operation,
            'start_time': start_time.isoformat(),
            **kwargs
        }
        
        self.info(f"Starting {operation}", context)
        
        try:
            yield self
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            success_context = {
                **context,
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'status': 'success'
            }
            self.info(f"Completed {operation}", success_context)
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            error_context = {
                **context,
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'status': 'error',
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            self.error(f"Failed {operation}", error_context, e)
            raise


def get_logger(name: str, **kwargs) -> ProductionLogger:
    """
    Get a production logger instance.
    
    Args:
        name: Logger name (typically __name__)
        **kwargs: Additional arguments passed to ProductionLogger
        
    Returns:
        Configured ProductionLogger instance
    """
    return ProductionLogger(name, **kwargs)


def configure_global_logging(level: str = "INFO", 
                           log_dir: Optional[str] = None,
                           structured: bool = True):
    """
    Configure global logging settings for the application.
    
    Args:
        level: Global logging level
        log_dir: Directory for log files
        structured: Whether to use structured logging
    """
    # Set root logger level
    logging.getLogger().setLevel(getattr(logging, level.upper()))
    
    # Configure uncaught exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        root_logger = get_logger('uncaught')
        root_logger.critical(
            "Uncaught exception",
            context={'exception_type': exc_type.__name__},
            exception=exc_value
        )
    
    sys.excepthook = handle_exception
    
    # Store global configuration
    global _global_config
    _global_config = {
        'level': level,
        'log_dir': log_dir,
        'structured': structured
    }


# Global configuration storage
_global_config = {}


def get_global_config():
    """Get global logging configuration."""
    return _global_config.copy()


# Performance logging decorator
def log_performance(logger: Optional[ProductionLogger] = None, 
                   operation: Optional[str] = None):
    """
    Decorator to log function performance.
    
    Args:
        logger: Logger instance (uses function's module logger if None)
        operation: Operation name (uses function name if None)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger, operation
            
            if logger is None:
                logger = get_logger(func.__module__)
            
            if operation is None:
                operation = func.__name__
            
            with logger.operation_context(operation):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator