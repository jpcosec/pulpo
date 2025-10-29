"""
Utilities package for JobHunter AI.

This package provides common utilities including logging, configuration,
validation, exceptions, and constants.

Example:
    >>> from core.utils import get_logger, get_settings, validate_email
    >>>
    >>> # Setup logging
    >>> from core.utils.logging import setup_logging
    >>> setup_logging(level="INFO")
    >>>
    >>> # Get logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Application started")
    >>>
    >>> # Get settings
    >>> settings = get_settings()
    >>> print(settings.mongodb_uri)
    >>>
    >>> # Validate data
    >>> is_valid = validate_email("user@example.com")
"""

# ==============================================================================
# Logging
# ==============================================================================

# ==============================================================================
# Configuration
# ==============================================================================
from core.utils.config import (
    EnvironmentValidator,
    LogLevelValidator,
    ProductionValidator,
    Settings,
    SettingsBuilder,
    SettingsLoader,
    get_settings,
    reload_settings,
    reset_settings,
)

# ==============================================================================
# Constants
# ==============================================================================
from core.utils.constants import (
    CACHE_TTL,
    COLLECTIONS,
    DATE_FORMATS,
    DIRECTORIES,
    HTTP_DEFAULTS,
    LLM_TEMPERATURES,
    # Dataclass instances
    MATCH_SCORES,
    RATE_LIMITS,
    TIMEOUTS,
    VALIDATION_LIMITS,
    ApplicationStatus,
    DocumentFormat,
    ExperienceLevel,
    JobSource,
    JobType,
    # Enums
    Language,
    LLMProvider,
    RemoteOption,
    get_application_status_display_name,
    # Utility functions
    get_job_source_display_name,
)

# ==============================================================================
# Exceptions
# ==============================================================================
from core.utils.exceptions import (
    ApplicationError,
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    # Factory and utilities
    ExceptionFactory,
    ExternalServiceError,
    InternalError,
    # Base exceptions
    JobHunterException,
    OperationalError,
    ProcessingError,
    RateLimitError,
    RetryableError,
    # Specific exceptions
    ScrapingError,
    TimeoutError,
    UserInputError,
    ValidationError,
    get_error_category,
    handle_errors,
    is_retryable,
    retry_on_error,
)
from core.utils.logging import (
    BoundLogger,
    LogContext,
    LoggerConfig,
    LoggerFactory,
    bind_context,
    clear_context,
    get_logger,
    setup_logging,
)

# ==============================================================================
# User Configuration
# ==============================================================================
from core.utils.user_config import (
    ConfigFileHandler,
    UserConfig,
    get_active_user_email,
    get_active_user_id,
    get_user_config,
    has_active_user,
    require_active_user,
    reset_user_config,
)

# ==============================================================================
# Validators
# ==============================================================================
from core.utils.validators import (
    EmailValidator,
    LengthValidator,
    PhoneValidator,
    PostalCodeValidator,
    UrlValidator,
    ValidationChain,
    # Classes
    ValidationResult,
    Validator,
    # Functional API
    validate_email,
    validate_german_postal_code,
    validate_job_title,
    validate_phone,
    validate_url,
)

# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    # Logging
    "LoggerConfig",
    "LoggerFactory",
    "LogContext",
    "setup_logging",
    "get_logger",
    "bind_context",
    "clear_context",
    "BoundLogger",
    # Configuration
    "Settings",
    "SettingsLoader",
    "SettingsBuilder",
    "EnvironmentValidator",
    "LogLevelValidator",
    "ProductionValidator",
    "get_settings",
    "reset_settings",
    "reload_settings",
    # Exceptions
    "JobHunterException",
    "ExternalServiceError",
    "InternalError",
    "UserInputError",
    "OperationalError",
    "ScrapingError",
    "DatabaseError",
    "ProcessingError",
    "ApplicationError",
    "ValidationError",
    "ConfigurationError",
    "RateLimitError",
    "AuthenticationError",
    "TimeoutError",
    "RetryableError",
    "ExceptionFactory",
    "handle_errors",
    "retry_on_error",
    "is_retryable",
    "get_error_category",
    # Validators
    "ValidationResult",
    "Validator",
    "EmailValidator",
    "UrlValidator",
    "PhoneValidator",
    "PostalCodeValidator",
    "LengthValidator",
    "ValidationChain",
    "validate_email",
    "validate_url",
    "validate_phone",
    "validate_german_postal_code",
    "validate_job_title",
    # Constants
    "Language",
    "JobSource",
    "ApplicationStatus",
    "DocumentFormat",
    "JobType",
    "RemoteOption",
    "ExperienceLevel",
    "LLMProvider",
    "MATCH_SCORES",
    "RATE_LIMITS",
    "TIMEOUTS",
    "DIRECTORIES",
    "COLLECTIONS",
    "DATE_FORMATS",
    "VALIDATION_LIMITS",
    "LLM_TEMPERATURES",
    "HTTP_DEFAULTS",
    "CACHE_TTL",
    "get_job_source_display_name",
    "get_application_status_display_name",
    # User Configuration
    "UserConfig",
    "ConfigFileHandler",
    "get_user_config",
    "reset_user_config",
    "get_active_user_id",
    "get_active_user_email",
    "require_active_user",
    "has_active_user",
]
