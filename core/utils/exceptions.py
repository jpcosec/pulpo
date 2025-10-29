"""
Custom exception hierarchy for the JobHunter AI application.

This module defines a structured exception hierarchy with proper categorization,
factory methods, and context managers for clean exception handling.

Example:
    >>> from core.utils.exceptions import ScrapingError, ExceptionFactory
    >>>
    >>> # Raise with details
    >>> raise ScrapingError(
    ...     "Failed to scrape job listings",
    ...     details={"url": "https://example.com", "status_code": 404}
    ... )
    >>>
    >>> # Use factory
    >>> error = ExceptionFactory.scraping_failed(url="https://example.com", status_code=404)
    >>> raise error
"""

from abc import ABC
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

# ==============================================================================
# Base Exception
# ==============================================================================


class JobHunterException(Exception, ABC):
    """Base exception for all JobHunter AI errors.

    All custom exceptions in the application inherit from this class.
    This allows for catching all application-specific errors with a
    single except clause.

    Attributes:
        message: Human-readable error message
        details: Optional dictionary with additional error context
        category: Exception category (auto-set by subclasses)
    """

    # Category is set by subclasses
    category: str = "general"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation of the exception."""
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"

    def with_detail(self, key: str, value: Any) -> "JobHunterException":
        """Add a detail to the exception.

        Args:
            key: Detail key
            value: Detail value

        Returns:
            Self for method chaining
        """
        self.details[key] = value
        return self


# ==============================================================================
# Exception Categories (Abstract Base Classes)
# ==============================================================================


class ExternalServiceError(JobHunterException, ABC):
    """Base for errors related to external services.

    This includes scraping errors, API errors, and network errors.
    """

    category: str = "external_service"


class InternalError(JobHunterException, ABC):
    """Base for errors related to internal operations.

    This includes database errors, processing errors, and validation errors.
    """

    category: str = "internal"


class UserInputError(JobHunterException, ABC):
    """Base for errors caused by invalid user input.

    This includes validation errors and configuration errors.
    """

    category: str = "user_input"


class OperationalError(JobHunterException, ABC):
    """Base for errors during job application operations.

    This includes application submission errors and automation errors.
    """

    category: str = "operational"


# ==============================================================================
# External Service Errors
# ==============================================================================


class ScrapingError(ExternalServiceError):
    """Exception raised for scraping-related errors.

    This includes errors during web scraping, parsing, or data extraction
    from job boards and websites.

    Example:
        >>> raise ScrapingError(
        ...     "Failed to scrape job listings",
        ...     details={"url": "https://example.com", "status_code": 404}
        ... )
    """

    pass


class TimeoutError(ExternalServiceError):
    """Exception raised when operations timeout.

    This includes network timeouts, processing timeouts, or any operation
    that exceeds its maximum allowed duration.

    Example:
        >>> raise TimeoutError(
        ...     "Scraping operation timed out",
        ...     details={"url": "https://example.com", "timeout_seconds": 30}
        ... )
    """

    pass


class RateLimitError(ExternalServiceError):
    """Exception raised when rate limits are exceeded.

    This includes API rate limits, scraping rate limits, or application
    submission limits.

    Example:
        >>> raise RateLimitError(
        ...     "Exceeded daily application limit",
        ...     details={"limit": 10, "current": 11}
        ... )
    """

    pass


class AuthenticationError(ExternalServiceError):
    """Exception raised for authentication and authorization errors.

    This includes invalid credentials, expired tokens, or insufficient
    permissions.

    Example:
        >>> raise AuthenticationError(
        ...     "Invalid API key",
        ...     details={"provider": "OpenAI"}
        ... )
    """

    pass


# ==============================================================================
# Internal Errors
# ==============================================================================


class DatabaseError(InternalError):
    """Exception raised for database-related errors.

    This includes connection errors, query failures, and data integrity issues.

    Example:
        >>> raise DatabaseError(
        ...     "Failed to connect to MongoDB",
        ...     details={"uri": "mongodb://localhost:27017"}
        ... )
    """

    pass


class ProcessingError(InternalError):
    """Exception raised for data processing errors.

    This includes errors during job matching, document generation,
    or any data transformation operations.

    Example:
        >>> raise ProcessingError(
        ...     "Failed to generate cover letter",
        ...     details={"job_id": "12345", "template": "default"}
        ... )
    """

    pass


# ==============================================================================
# User Input Errors
# ==============================================================================


class ValidationError(UserInputError):
    """Exception raised for validation errors.

    This includes errors during data validation, such as invalid email
    addresses, malformed URLs, or missing required fields.

    Example:
        >>> raise ValidationError(
        ...     "Invalid email address",
        ...     details={"field": "email", "value": "not-an-email"}
        ... )
    """

    pass


class ConfigurationError(UserInputError):
    """Exception raised for configuration errors.

    This includes missing required configuration values, invalid settings,
    or environment setup issues.

    Example:
        >>> raise ConfigurationError(
        ...     "Missing required API key",
        ...     details={"key": "OPENAI_API_KEY"}
        ... )
    """

    pass


# ==============================================================================
# Operational Errors
# ==============================================================================


class ApplicationError(OperationalError):
    """Exception raised for job application errors.

    This includes errors during application submission, form filling,
    or communication with job application portals.

    Example:
        >>> raise ApplicationError(
        ...     "Failed to submit application",
        ...     details={"job_id": "12345", "company": "Example Corp"}
        ... )
    """

    pass


# ==============================================================================
# Special Errors
# ==============================================================================


class RetryableError(JobHunterException):
    """Exception raised for errors that can be retried.

    This is a marker exception that indicates an operation failed but
    can potentially succeed if retried.

    Example:
        >>> raise RetryableError(
        ...     "Temporary network error",
        ...     details={"attempt": 1, "max_retries": 3}
        ... )
    """

    category: str = "retryable"


# ==============================================================================
# Exception Factory
# ==============================================================================


class ExceptionFactory:
    """Factory for creating common exceptions with standardized messages.

    This class provides factory methods for creating exceptions with
    consistent error messages and details.
    """

    @staticmethod
    def scraping_failed(url: str, reason: str, **details: Any) -> ScrapingError:
        """Create ScrapingError for failed scraping operation.

        Args:
            url: URL that failed to scrape
            reason: Reason for failure
            **details: Additional details

        Returns:
            ScrapingError instance
        """
        return ScrapingError(
            f"Failed to scrape {url}: {reason}",
            details={"url": url, "reason": reason, **details},
        )

    @staticmethod
    def database_connection_failed(uri: str, error: str) -> DatabaseError:
        """Create DatabaseError for connection failure.

        Args:
            uri: Database URI
            error: Error message

        Returns:
            DatabaseError instance
        """
        return DatabaseError(
            f"Failed to connect to database: {error}",
            details={"uri": uri, "error": error},
        )

    @staticmethod
    def validation_failed(field: str, value: Any, reason: str) -> ValidationError:
        """Create ValidationError for field validation failure.

        Args:
            field: Field name
            value: Invalid value
            reason: Reason for validation failure

        Returns:
            ValidationError instance
        """
        return ValidationError(
            f"Validation failed for field '{field}': {reason}",
            details={"field": field, "value": value, "reason": reason},
        )

    @staticmethod
    def rate_limit_exceeded(
        limit: int, current: int, reset_time: str | None = None
    ) -> RateLimitError:
        """Create RateLimitError for exceeded rate limit.

        Args:
            limit: Rate limit
            current: Current count
            reset_time: Optional reset time

        Returns:
            RateLimitError instance
        """
        details = {"limit": limit, "current": current}
        if reset_time:
            details["reset_time"] = reset_time

        return RateLimitError(
            f"Rate limit exceeded: {current}/{limit}",
            details=details,
        )

    @staticmethod
    def timeout_exceeded(operation: str, timeout_seconds: int) -> TimeoutError:
        """Create TimeoutError for timeout.

        Args:
            operation: Operation that timed out
            timeout_seconds: Timeout in seconds

        Returns:
            TimeoutError instance
        """
        return TimeoutError(
            f"Operation timed out: {operation}",
            details={"operation": operation, "timeout_seconds": timeout_seconds},
        )

    @staticmethod
    def configuration_missing(key: str, environment: str) -> ConfigurationError:
        """Create ConfigurationError for missing config.

        Args:
            key: Missing configuration key
            environment: Current environment

        Returns:
            ConfigurationError instance
        """
        return ConfigurationError(
            f"Missing required configuration: {key}",
            details={"key": key, "environment": environment},
        )


# ==============================================================================
# Exception Context Managers
# ==============================================================================


E = TypeVar("E", bound=JobHunterException)


@contextmanager
def handle_errors(
    *exception_types: type[Exception],
    reraise_as: type[E] | None = None,
    message: str | None = None,
    **details: Any,
) -> Iterator[None]:
    """Context manager for handling and converting exceptions.

    Args:
        *exception_types: Exception types to catch
        reraise_as: Exception type to reraise as
        message: Custom error message
        **details: Additional details for the exception

    Example:
        >>> with handle_errors(ValueError, KeyError, reraise_as=ValidationError, message="Invalid data"):
        ...     # Code that might raise ValueError or KeyError
        ...     int("not a number")
    """
    try:
        yield
    except exception_types as e:
        if reraise_as:
            error_message = message or str(e)
            raise reraise_as(error_message, details={"original_error": str(e), **details}) from e
        raise


@contextmanager
def retry_on_error(
    *exception_types: type[Exception],
    max_retries: int = 3,
    on_retry: Callable[[int], None] | None = None,
) -> Iterator[None]:
    """Context manager for retrying operations on specific errors.

    Args:
        *exception_types: Exception types that should trigger retry
        max_retries: Maximum number of retry attempts
        on_retry: Optional callback called before each retry

    Example:
        >>> def log_retry(attempt: int):
        ...     print(f"Retry attempt {attempt}")
        >>>
        >>> with retry_on_error(ConnectionError, max_retries=3, on_retry=log_retry):
        ...     # Code that might raise ConnectionError
        ...     fetch_data()
    """
    attempts = 0
    while attempts < max_retries:
        try:
            yield
            return  # Success, exit
        except exception_types as e:
            attempts += 1
            if attempts >= max_retries:
                # Max retries reached, raise as RetryableError
                raise RetryableError(
                    f"Operation failed after {attempts} attempts",
                    details={"attempts": attempts, "max_retries": max_retries, "error": str(e)},
                ) from e
            if on_retry:
                on_retry(attempts)


# ==============================================================================
# Utility Functions
# ==============================================================================


def is_retryable(error: Exception) -> bool:
    """Check if an exception is retryable.

    Args:
        error: Exception to check

    Returns:
        True if error is retryable
    """
    return isinstance(error, RetryableError | ExternalServiceError)


def get_error_category(error: Exception) -> str:
    """Get the category of an exception.

    Args:
        error: Exception to categorize

    Returns:
        Error category string
    """
    if isinstance(error, JobHunterException):
        return error.category
    return "unknown"
