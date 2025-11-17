"""
Configuration management using Pydantic Settings.

This module provides centralized configuration management using a clean,
object-oriented design with proper encapsulation and validation.

Example:
    >>> from core.utils.config import get_settings
    >>>
    >>> settings = get_settings()
    >>> print(settings.mongodb_uri)
    >>> print(settings.default_llm_model)
"""

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ==============================================================================
# Validators
# ==============================================================================


class EnvironmentValidator:
    """Validates environment configuration values."""

    ALLOWED_ENVIRONMENTS = {"development", "staging", "production"}

    @classmethod
    def validate(cls, environment: str) -> str:
        """Validate environment value.

        Args:
            environment: Environment name to validate

        Returns:
            Lowercase environment name

        Raises:
            ValueError: If environment is not allowed
        """
        env_lower = environment.lower()
        if env_lower not in cls.ALLOWED_ENVIRONMENTS:
            raise ValueError(
                f"Environment must be one of {cls.ALLOWED_ENVIRONMENTS}, got: {environment}"
            )
        return env_lower


class LogLevelValidator:
    """Validates logging level configuration values."""

    ALLOWED_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    @classmethod
    def validate(cls, log_level: str) -> str:
        """Validate log level value.

        Args:
            log_level: Log level to validate

        Returns:
            Uppercase log level

        Raises:
            ValueError: If log level is not allowed
        """
        level_upper = log_level.upper()
        if level_upper not in cls.ALLOWED_LEVELS:
            raise ValueError(f"Log level must be one of {cls.ALLOWED_LEVELS}, got: {log_level}")
        return level_upper


class ProductionValidator:
    """Validates production-specific configuration requirements."""

    @classmethod
    def validate_secret_key(cls, secret_key: str, environment: str) -> None:
        """Validate secret key for production environment.

        Args:
            secret_key: Secret key to validate
            environment: Current environment

        Raises:
            ValueError: If using default secret key in production
        """
        if environment == "production" and secret_key == "changeme":
            raise ValueError(
                "Secret key must be changed from default value in production environment"
            )


# ==============================================================================
# Settings
# ==============================================================================


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables or .env file.
    Environment variables are case-insensitive.

    Configuration Groups:
        - Database: MongoDB configuration
        - LLM: Language model API keys and defaults
        - Scraping: Rate limits and concurrency
        - Application: Environment, debug, security
        - Logging: Log level and format
    """

    # ==========================================================================
    # Database Configuration
    # ==========================================================================

    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI",
    )
    mongodb_database: str = Field(
        default="pulpo",
        description="MongoDB database name",
    )

    # ==========================================================================
    # LLM Configuration (Auth Settings)
    # ==========================================================================

    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for GPT models",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key for Claude models",
    )
    cohere_api_key: str | None = Field(
        default=None,
        description="Cohere API key for Command models",
    )
    together_api_key: str | None = Field(
        default=None,
        description="Together AI API key",
    )
    replicate_api_key: str | None = Field(
        default=None,
        description="Replicate API key",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL for local LLM inference",
    )

    # ==========================================================================
    # LLM Default Settings
    # ==========================================================================

    default_llm_model: str = Field(
        default="gpt-4o-mini",
        description="Default LLM model to use",
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for LLM generation",
    )
    llm_max_tokens: int = Field(
        default=1000,
        ge=1,
        le=8000,
        description="Default max tokens for LLM generation",
    )

    # ==========================================================================
    # Scraping Configuration
    # ==========================================================================

    scraping_rate_limit: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Maximum requests per minute for scraping",
    )
    scraping_concurrency: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent scraping tasks",
    )

    # ==========================================================================
    # Application Configuration
    # ==========================================================================

    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)",
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode",
    )
    secret_key: str = Field(
        default="changeme",
        description="Secret key for encryption/signing (MUST be changed in production)",
    )
    dry_run: bool = Field(
        default=False,
        description="Dry run mode - don't actually submit applications",
    )
    max_applications_per_day: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum job applications to submit per day",
    )

    # ==========================================================================
    # Logging Configuration
    # ==========================================================================

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_json: bool = Field(
        default=False,
        description="Output logs in JSON format",
    )

    # ==========================================================================
    # Pydantic Settings Configuration
    # ==========================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Validators
    # ==========================================================================

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment using EnvironmentValidator."""
        return EnvironmentValidator.validate(v)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level using LogLevelValidator."""
        return LogLevelValidator.validate(v)

    @model_validator(mode="after")
    def validate_production_requirements(self) -> "Settings":
        """Validate production-specific requirements."""
        ProductionValidator.validate_secret_key(self.secret_key, self.environment)
        return self

    # ==========================================================================
    # Convenience Properties
    # ==========================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production environment.

        Returns:
            True if environment is production
        """
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment.

        Returns:
            True if environment is development
        """
        return self.environment == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment.

        Returns:
            True if environment is staging
        """
        return self.environment == "staging"

    @property
    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is configured.

        Returns:
            True if OpenAI API key is set
        """
        return self.openai_api_key is not None

    @property
    def has_anthropic_key(self) -> bool:
        """Check if Anthropic API key is configured.

        Returns:
            True if Anthropic API key is set
        """
        return self.anthropic_api_key is not None


# ==============================================================================
# Settings Loader (Singleton Pattern)
# ==============================================================================


class SettingsLoader:
    """Manages the global settings instance using singleton pattern.

    This class ensures only one Settings instance is created and provides
    methods for accessing and resetting the configuration.
    """

    _instance: Settings | None = None

    @classmethod
    def get(cls) -> Settings:
        """Get the global settings instance.

        Creates a new instance if one doesn't exist. This implements
        lazy initialization with the singleton pattern.

        Returns:
            The global Settings instance
        """
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the global settings instance.

        This is primarily used for testing to ensure a clean state
        between test runs.
        """
        cls._instance = None

    @classmethod
    def is_loaded(cls) -> bool:
        """Check if settings have been loaded.

        Returns:
            True if settings instance exists, False otherwise
        """
        return cls._instance is not None

    @classmethod
    def reload(cls) -> Settings:
        """Reload settings from environment.

        Forces recreation of the settings instance, useful when
        environment variables have changed.

        Returns:
            New Settings instance
        """
        cls._instance = None
        return cls.get()


# ==============================================================================
# Settings Builder (For Testing)
# ==============================================================================


class SettingsBuilder:
    """Builder for creating Settings instances with custom values.

    This class provides a fluent interface for building Settings objects
    with specific configurations, useful for testing.

    Example:
        >>> builder = SettingsBuilder()
        >>> settings = (builder
        ...     .with_environment("testing")
        ...     .with_debug(True)
        ...     .build())
    """

    def __init__(self) -> None:
        """Initialize builder with default values."""
        self._values: dict = {}

    def with_environment(self, environment: str) -> "SettingsBuilder":
        """Set environment."""
        self._values["environment"] = environment
        return self

    def with_debug(self, debug: bool) -> "SettingsBuilder":
        """Set debug flag."""
        self._values["debug"] = debug
        return self

    def with_log_level(self, log_level: str) -> "SettingsBuilder":
        """Set log level."""
        self._values["log_level"] = log_level
        return self

    def with_llm_model(self, model: str) -> "SettingsBuilder":
        """Set default LLM model."""
        self._values["default_llm_model"] = model
        return self

    def with_secret_key(self, secret_key: str) -> "SettingsBuilder":
        """Set secret key."""
        self._values["secret_key"] = secret_key
        return self

    def build(self) -> Settings:
        """Build Settings instance with configured values.

        Returns:
            Settings instance with custom values
        """
        return Settings(**self._values)


# ==============================================================================
# Public API
# ==============================================================================


def get_settings() -> Settings:
    """Get the global settings instance.

    This function implements a singleton pattern to ensure only one
    Settings instance is created and reused throughout the application.

    Returns:
        The global Settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.mongodb_uri)
        >>> print(settings.environment)
    """
    return SettingsLoader.get()


def reset_settings() -> None:
    """Reset the global settings instance.

    This is primarily used for testing to ensure a clean state
    between test runs.

    Example:
        >>> reset_settings()
        >>> settings = get_settings()  # Creates new instance
    """
    SettingsLoader.reset()


def reload_settings() -> Settings:
    """Reload settings from environment.

    Forces recreation of the settings instance. Useful when environment
    variables have changed during runtime.

    Returns:
        New Settings instance

    Example:
        >>> import os
        >>> os.environ["LOG_LEVEL"] = "DEBUG"
        >>> settings = reload_settings()
        >>> assert settings.log_level == "DEBUG"
    """
    return SettingsLoader.reload()
