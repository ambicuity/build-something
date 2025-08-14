#!/usr/bin/env python3
"""
Configuration management system for build-something projects.

Provides centralized, type-safe configuration management with environment
variable support, validation, and hierarchical configuration loading.
"""

import os
import json
import yaml
from typing import Any, Dict, Optional, Union, Type, TypeVar, Generic
from pathlib import Path
from dataclasses import dataclass, field, fields, is_dataclass
from exceptions import ConfigurationError
from validation import InputValidator

T = TypeVar('T')


class ConfigValue(Generic[T]):
    """A configuration value with validation and default handling."""
    
    def __init__(self, 
                 default: Optional[T] = None,
                 env_var: Optional[str] = None,
                 description: Optional[str] = None,
                 validator: Optional[callable] = None,
                 required: bool = False):
        self.default = default
        self.env_var = env_var
        self.description = description
        self.validator = validator
        self.required = required
        self._value = None
        self._resolved = False
    
    def resolve(self, config_data: Dict[str, Any], key: str) -> T:
        """Resolve the configuration value from various sources."""
        if self._resolved:
            return self._value
        
        value = None
        
        # Priority order: env var > config data > default
        if self.env_var and self.env_var in os.environ:
            value = os.environ[self.env_var]
        elif key in config_data:
            value = config_data[key]
        elif self.default is not None:
            value = self.default
        elif self.required:
            raise ConfigurationError(
                f"Required configuration '{key}' is missing",
                config_key=key
            )
        
        # Apply validation if present
        if value is not None and self.validator:
            try:
                value = self.validator(value)
            except Exception as e:
                raise ConfigurationError(
                    f"Configuration validation failed for '{key}': {e}",
                    config_key=key
                )
        
        self._value = value
        self._resolved = True
        return value


@dataclass
class DatabaseConfig:
    """Database configuration."""
    filename: str = field(default="database.db")
    page_size: int = field(default=4096)
    cache_size: int = field(default=1000)
    max_connections: int = field(default=10)
    enable_wal: bool = field(default=True)
    backup_interval: int = field(default=3600)  # seconds
    
    def __post_init__(self):
        validator = InputValidator()
        self.filename = validator.validate_string(self.filename, "filename", min_length=1)
        self.page_size = validator.validate_integer(self.page_size, "page_size", min_value=512, max_value=65536)
        self.cache_size = validator.validate_integer(self.cache_size, "cache_size", min_value=1, max_value=100000)
        self.max_connections = validator.validate_integer(self.max_connections, "max_connections", min_value=1, max_value=1000)
        self.backup_interval = validator.validate_integer(self.backup_interval, "backup_interval", min_value=60)


@dataclass
class HTTPServerConfig:
    """HTTP server configuration."""
    host: str = field(default="localhost")
    port: int = field(default=8080)
    max_connections: int = field(default=100)
    request_timeout: int = field(default=30)
    static_dir: str = field(default="static")
    upload_dir: str = field(default="uploads")
    max_upload_size: int = field(default=10 * 1024 * 1024)  # 10MB
    enable_compression: bool = field(default=True)
    enable_caching: bool = field(default=True)
    cors_enabled: bool = field(default=False)
    
    def __post_init__(self):
        validator = InputValidator()
        self.host = validator.validate_string(self.host, "host", min_length=1)
        self.port = validator.validate_integer(self.port, "port", min_value=1, max_value=65535)
        self.max_connections = validator.validate_integer(self.max_connections, "max_connections", min_value=1, max_value=10000)
        self.request_timeout = validator.validate_integer(self.request_timeout, "request_timeout", min_value=1, max_value=300)
        self.static_dir = validator.validate_string(self.static_dir, "static_dir", min_length=1)
        self.upload_dir = validator.validate_string(self.upload_dir, "upload_dir", min_length=1)
        self.max_upload_size = validator.validate_integer(self.max_upload_size, "max_upload_size", min_value=1024)


@dataclass
class GitConfig:
    """Git configuration."""
    repository_dir: str = field(default=".mygit")
    default_branch: str = field(default="main")
    author_name: str = field(default="")
    author_email: str = field(default="")
    editor: str = field(default="nano")
    merge_tool: str = field(default="")
    ignore_file: str = field(default=".gitignore")
    
    def __post_init__(self):
        validator = InputValidator()
        self.repository_dir = validator.validate_string(self.repository_dir, "repository_dir", min_length=1)
        self.default_branch = validator.validate_string(self.default_branch, "default_branch", min_length=1)
        self.ignore_file = validator.validate_string(self.ignore_file, "ignore_file", min_length=1)
        if self.author_email:
            self.author_email = validator.validate_email(self.author_email, "author_email")


@dataclass
class ShellConfig:
    """Shell configuration."""
    prompt: str = field(default="$ ")
    history_file: str = field(default=".myshell_history")
    history_size: int = field(default=1000)
    max_jobs: int = field(default=100)
    timeout: int = field(default=30)
    
    def __post_init__(self):
        validator = InputValidator()
        self.prompt = validator.validate_string(self.prompt, "prompt", min_length=1)
        self.history_file = validator.validate_string(self.history_file, "history_file", min_length=1)
        self.history_size = validator.validate_integer(self.history_size, "history_size", min_value=1, max_value=100000)
        self.max_jobs = validator.validate_integer(self.max_jobs, "max_jobs", min_value=1, max_value=1000)
        self.timeout = validator.validate_integer(self.timeout, "timeout", min_value=1, max_value=3600)


@dataclass
class EditorConfig:
    """Text editor configuration."""
    tab_size: int = field(default=4)
    auto_indent: bool = field(default=True)
    syntax_highlighting: bool = field(default=True)
    line_numbers: bool = field(default=True)
    word_wrap: bool = field(default=False)
    backup_files: bool = field(default=True)
    backup_dir: str = field(default=".backups")
    
    def __post_init__(self):
        validator = InputValidator()
        self.tab_size = validator.validate_integer(self.tab_size, "tab_size", min_value=1, max_value=16)
        self.backup_dir = validator.validate_string(self.backup_dir, "backup_dir", min_length=1)


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = field(default="INFO")
    format: str = field(default="structured")
    file: Optional[str] = field(default=None)
    max_file_size: int = field(default=10 * 1024 * 1024)  # 10MB
    backup_count: int = field(default=5)
    console_pretty: bool = field(default=False)
    
    def __post_init__(self):
        validator = InputValidator()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ConfigurationError(f"Invalid log level: {self.level}")
        self.level = self.level.upper()
        
        valid_formats = ["structured", "simple"]
        if self.format not in valid_formats:
            raise ConfigurationError(f"Invalid log format: {self.format}")
        
        self.max_file_size = validator.validate_integer(self.max_file_size, "max_file_size", min_value=1024)
        self.backup_count = validator.validate_integer(self.backup_count, "backup_count", min_value=0, max_value=100)


@dataclass
class ApplicationConfig:
    """Main application configuration containing all sub-configurations."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    http_server: HTTPServerConfig = field(default_factory=HTTPServerConfig)
    git: GitConfig = field(default_factory=GitConfig)
    shell: ShellConfig = field(default_factory=ShellConfig)
    editor: EditorConfig = field(default_factory=EditorConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, config_paths: Optional[list] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_paths: List of configuration file paths to load
        """
        self.config_paths = config_paths or []
        self.config_data = {}
        self._config = None
        
        # Add default config paths
        self._add_default_paths()
        
    def _add_default_paths(self):
        """Add default configuration file paths."""
        default_paths = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml",
            Path.cwd() / "config.json",
            Path.home() / ".config" / "build-something" / "config.yaml",
        ]
        
        for path in default_paths:
            if path.exists() and str(path) not in self.config_paths:
                self.config_paths.append(str(path))
    
    def load_config(self) -> ApplicationConfig:
        """Load and merge configuration from all sources."""
        merged_data = {}
        
        # Load from files
        for path in self.config_paths:
            try:
                file_data = self._load_config_file(path)
                merged_data = self._merge_config(merged_data, file_data)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load config from {path}: {e}",
                    context={'config_file': path}
                )
        
        # Store merged data
        self.config_data = merged_data
        
        # Create configuration object
        try:
            self._config = self._create_config_object(merged_data)
            return self._config
        except Exception as e:
            raise ConfigurationError(f"Failed to create configuration object: {e}")
    
    def _load_config_file(self, path: str) -> dict:
        """Load configuration from a single file."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return {}
        
        with open(path_obj, 'r') as f:
            if path_obj.suffix.lower() in ['.yaml', '.yml']:
                try:
                    import yaml
                    return yaml.safe_load(f) or {}
                except ImportError:
                    raise ConfigurationError("PyYAML is required for YAML config files")
            elif path_obj.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ConfigurationError(f"Unsupported config file format: {path_obj.suffix}")
    
    def _merge_config(self, base: dict, override: dict) -> dict:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_config_object(self, data: dict) -> ApplicationConfig:
        """Create configuration object from data dictionary."""
        config = ApplicationConfig()
        
        # Update sub-configurations if present in data
        for section_name in ['database', 'http_server', 'git', 'shell', 'editor', 'logging']:
            if section_name in data:
                section_data = data[section_name]
                if hasattr(config, section_name):
                    section_config = getattr(config, section_name)
                    
                    # Update fields in the section config
                    for field_info in fields(section_config):
                        if field_info.name in section_data:
                            setattr(section_config, field_info.name, section_data[field_info.name])
                    
                    # Re-run validation
                    section_config.__post_init__()
        
        return config
    
    def get_config(self) -> ApplicationConfig:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def save_config(self, path: str, config: Optional[ApplicationConfig] = None):
        """Save configuration to file."""
        if config is None:
            config = self.get_config()
        
        # Convert to dictionary
        config_dict = self._config_to_dict(config)
        
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path_obj, 'w') as f:
            if path_obj.suffix.lower() in ['.yaml', '.yml']:
                try:
                    import yaml
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                except ImportError:
                    raise ConfigurationError("PyYAML is required for YAML config files")
            elif path_obj.suffix.lower() == '.json':
                json.dump(config_dict, f, indent=2)
            else:
                raise ConfigurationError(f"Unsupported config file format: {path_obj.suffix}")
    
    def _config_to_dict(self, config: ApplicationConfig) -> dict:
        """Convert configuration object to dictionary."""
        result = {}
        
        for field_info in fields(config):
            value = getattr(config, field_info.name)
            if is_dataclass(value):
                result[field_info.name] = {
                    f.name: getattr(value, f.name) for f in fields(value)
                }
            else:
                result[field_info.name] = value
        
        return result


# Global configuration manager
_config_manager = None


def get_config_manager(config_paths: Optional[list] = None) -> ConfigManager:
    """Get or create the global configuration manager."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_paths)
    
    return _config_manager


def get_config() -> ApplicationConfig:
    """Get the global application configuration."""
    return get_config_manager().get_config()


def reload_config():
    """Reload the global configuration."""
    global _config_manager
    if _config_manager:
        _config_manager.load_config()