"""
User configuration management for CLI.

This module manages the active user context with clean separation of
concerns using file handlers and proper encapsulation.

Example:
    >>> from core.utils.user_config import get_user_config
    >>>
    >>> config = get_user_config()
    >>> if config.has_active_user():
    ...     user_id = config.get_active_user_id()
    ...     print(f"Active user: {user_id}")
"""

import json
from pathlib import Path
from typing import Any

# Conditional import to handle case where logging is not yet set up
try:
    from core.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


# ==============================================================================
# File Handler
# ==============================================================================


class ConfigFileHandler:
    """Handles reading and writing configuration files.

    This class encapsulates all file I/O operations for user configuration,
    providing a clean interface and proper error handling.
    """

    def __init__(self, config_file: Path):
        """Initialize file handler.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file

    def load(self) -> dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary (empty if file doesn't exist or on error)
        """
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file: {e}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}", exc_info=True)
            return {}

    def save(self, config: dict[str, Any]) -> bool:
        """Save configuration to file.

        Args:
            config: Configuration dictionary to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Write with proper formatting
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}", exc_info=True)
            return False


# ==============================================================================
# User Config Manager
# ==============================================================================


class UserConfig:
    """Manages user configuration and active user context.

    This class provides a clean interface for managing user configuration
    with proper encapsulation and separation of file I/O concerns.

    Example:
        >>> config = UserConfig()
        >>> config.set_active_user("user-123", "user@example.com")
        >>> user_id = config.get_active_user_id()
        >>> config.clear_active_user()
    """

    # Configuration keys
    KEY_ACTIVE_USER_ID = "active_user_id"
    KEY_ACTIVE_USER_EMAIL = "active_user_email"

    def __init__(self, config_dir: Path | None = None):
        """Initialize user configuration.

        Args:
            config_dir: Optional custom config directory (default: ~/.pulpo)
        """
        self.config_dir = config_dir or Path.home() / ".pulpo"
        self.config_file = self.config_dir / "config.json"

        # Initialize file handler
        self._file_handler = ConfigFileHandler(self.config_file)

        # Ensure config directory exists
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary
        """
        return self._file_handler.load()

    def _save_config(self, config: dict[str, Any]) -> bool:
        """Save configuration to file.

        Args:
            config: Configuration dictionary

        Returns:
            True if successful, False otherwise
        """
        return self._file_handler.save(config)

    # ==========================================================================
    # Active User Management
    # ==========================================================================

    def get_active_user_id(self) -> str | None:
        """Get the active user ID.

        Returns:
            Active user ID or None if not set
        """
        config = self._load_config()
        return config.get(self.KEY_ACTIVE_USER_ID)

    def get_active_user_email(self) -> str | None:
        """Get the active user email.

        Returns:
            Active user email or None if not set
        """
        config = self._load_config()
        return config.get(self.KEY_ACTIVE_USER_EMAIL)

    def set_active_user(self, user_id: str, email: str) -> bool:
        """Set the active user.

        Args:
            user_id: User ID
            email: User email

        Returns:
            True if successful, False otherwise
        """
        config = self._load_config()
        config[self.KEY_ACTIVE_USER_ID] = user_id
        config[self.KEY_ACTIVE_USER_EMAIL] = email

        success = self._save_config(config)
        if success:
            logger.info(f"Set active user: {email} ({user_id})")
        return success

    def clear_active_user(self) -> bool:
        """Clear the active user.

        Returns:
            True if successful, False otherwise
        """
        config = self._load_config()
        config.pop(self.KEY_ACTIVE_USER_ID, None)
        config.pop(self.KEY_ACTIVE_USER_EMAIL, None)

        success = self._save_config(config)
        if success:
            logger.info("Cleared active user")
        return success

    def has_active_user(self) -> bool:
        """Check if there is an active user.

        Returns:
            True if active user is set, False otherwise
        """
        return self.get_active_user_id() is not None

    # ==========================================================================
    # Generic Configuration Management
    # ==========================================================================

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        config = self._load_config()
        return config.get(key, default)

    def set_value(self, key: str, value: Any) -> bool:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        config = self._load_config()
        config[key] = value
        return self._save_config(config)

    def delete_value(self, key: str) -> bool:
        """Delete a configuration value.

        Args:
            key: Configuration key

        Returns:
            True if successful, False otherwise
        """
        config = self._load_config()
        if key in config:
            del config[key]
            return self._save_config(config)
        return True  # Key doesn't exist, consider it a success

    def get_all(self) -> dict[str, Any]:
        """Get all configuration values.

        Returns:
            Complete configuration dictionary
        """
        return self._load_config()

    def clear_all(self) -> bool:
        """Clear all configuration values.

        Returns:
            True if successful, False otherwise
        """
        return self._save_config({})


# ==============================================================================
# Singleton Instance
# ==============================================================================


_user_config: UserConfig | None = None


def get_user_config() -> UserConfig:
    """Get the global user configuration instance.

    This function implements a singleton pattern to ensure only one
    UserConfig instance is created.

    Returns:
        Global UserConfig instance

    Example:
        >>> config = get_user_config()
        >>> user_id = config.get_active_user_id()
    """
    global _user_config
    if _user_config is None:
        _user_config = UserConfig()
    return _user_config


def reset_user_config() -> None:
    """Reset the global user configuration instance.

    This is primarily used for testing to ensure a clean state
    between test runs.
    """
    global _user_config
    _user_config = None


# ==============================================================================
# Convenience Functions
# ==============================================================================


def get_active_user_id() -> str | None:
    """Get the active user ID (convenience function).

    Returns:
        Active user ID or None

    Example:
        >>> user_id = get_active_user_id()
        >>> if user_id:
        ...     print(f"Current user: {user_id}")
    """
    return get_user_config().get_active_user_id()


def get_active_user_email() -> str | None:
    """Get the active user email (convenience function).

    Returns:
        Active user email or None

    Example:
        >>> email = get_active_user_email()
        >>> if email:
        ...     print(f"Current user: {email}")
    """
    return get_user_config().get_active_user_email()


def require_active_user() -> str:
    """Require an active user to be set.

    Returns:
        Active user ID

    Raises:
        ValueError: If no active user is set

    Example:
        >>> try:
        ...     user_id = require_active_user()
        ...     print(f"User ID: {user_id}")
        ... except ValueError as e:
        ...     print(f"Error: {e}")
    """
    user_id = get_active_user_id()
    if user_id is None:
        raise ValueError(
            "No active user set. Please create a profile with 'pulpo profile create' "
            "or switch to an existing user with 'pulpo profile use <email>'"
        )
    return user_id


def has_active_user() -> bool:
    """Check if there is an active user (convenience function).

    Returns:
        True if active user is set, False otherwise

    Example:
        >>> if has_active_user():
        ...     print("User is logged in")
        ... else:
        ...     print("No active user")
    """
    return get_user_config().has_active_user()
