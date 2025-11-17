"""
Structured logging configuration using structlog.

This module provides centralized logging setup for the Pulpo AI application
using a clean, object-oriented design pattern.

Example:
    >>> from core.utils.logging import get_logger, setup_logging
    >>>
    >>> # Setup logging once at application start
    >>> setup_logging(level="INFO", json_logs=False)
    >>>
    >>> # Get logger instances throughout the app
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing job", job_id="12345", status="active")
"""

import logging
import sys
from dataclasses import dataclass
from typing import Any

import structlog
from structlog.types import EventDict, Processor

# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(frozen=True)
class LoggerConfig:
    """Configuration for logger setup.

    Attributes:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output JSON format; if False, use console format
        logger_name: Optional specific logger name to configure
        app_name: Application name to include in logs (default: "pulpo")
        use_colors: Enable colored console output (default: True)
        show_exceptions: Include exception formatting (default: True)
    """

    level: str = "INFO"
    json_logs: bool = False
    logger_name: str | None = None
    app_name: str = "pulpo"
    use_colors: bool = True
    show_exceptions: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in allowed_levels:
            raise ValueError(f"Invalid log level: {self.level}. Must be one of {allowed_levels}")

    @property
    def numeric_level(self) -> int:
        """Get numeric logging level."""
        return getattr(logging, self.level.upper(), logging.INFO)


# ==============================================================================
# Processor Factory
# ==============================================================================


class ProcessorBuilder:
    """Builds structlog processor chains based on configuration.

    This class encapsulates the logic for creating different processor
    chains for development vs. production environments.
    """

    def __init__(self, config: LoggerConfig):
        """Initialize processor builder.

        Args:
            config: Logger configuration
        """
        self.config = config

    def build(self) -> list[Processor]:
        """Build processor chain based on configuration.

        Returns:
            List of structlog processors
        """
        processors: list[Processor] = []

        # Add core processors (always included)
        processors.extend(self._get_core_processors())

        # Add exception formatters
        if self.config.show_exceptions:
            processors.append(self._get_exception_processor())

        # Add final renderer (JSON or Console)
        processors.append(self._get_renderer())

        return processors

    def _get_core_processors(self) -> list[Processor]:
        """Get core processors (common to all configurations).

        Returns:
            List of core processors
        """
        return [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            self._create_app_context_processor(),
        ]

    def _create_app_context_processor(self) -> Processor:
        """Create processor that adds app context to logs.

        Returns:
            Processor function
        """
        app_name = self.config.app_name

        def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
            """Add application name to event dict."""
            event_dict["app"] = app_name
            return event_dict

        return add_app_context

    def _get_exception_processor(self) -> Processor:
        """Get exception formatting processor.

        Returns:
            Exception processor based on output format
        """
        if self.config.json_logs:
            return structlog.processors.format_exc_info
        else:
            return structlog.dev.set_exc_info

    def _get_renderer(self) -> Processor:
        """Get final rendering processor.

        Returns:
            Renderer based on output format
        """
        if self.config.json_logs:
            return structlog.processors.JSONRenderer()
        else:
            return structlog.dev.ConsoleRenderer(
                colors=self.config.use_colors,
                exception_formatter=structlog.dev.rich_traceback,
            )


# ==============================================================================
# Logger Factory
# ==============================================================================


class LoggerFactory:
    """Factory for creating and configuring structured loggers.

    This class encapsulates all logger setup logic and provides a clean
    interface for configuring the logging system.

    Example:
        >>> config = LoggerConfig(level="DEBUG", json_logs=False)
        >>> factory = LoggerFactory(config)
        >>> factory.configure()
        >>> logger = factory.get_logger(__name__)
        >>> logger.info("Application started")
    """

    _configured: bool = False
    _config: LoggerConfig | None = None

    def __init__(self, config: LoggerConfig):
        """Initialize logger factory.

        Args:
            config: Logger configuration
        """
        self.config = config

    def configure(self) -> None:
        """Configure the logging system.

        This method sets up both standard library logging and structlog
        with the appropriate processors and formatters.
        """
        # Configure standard library logging
        self._configure_stdlib_logging()

        # Build processor chain
        processor_builder = ProcessorBuilder(self.config)
        processors = processor_builder.build()

        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Configure specific logger if provided
        if self.config.logger_name:
            logger = logging.getLogger(self.config.logger_name)
            logger.setLevel(self.config.numeric_level)

        # Mark as configured
        LoggerFactory._configured = True
        LoggerFactory._config = self.config

    def _configure_stdlib_logging(self) -> None:
        """Configure standard library logging."""
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=self.config.numeric_level,
        )

    @staticmethod
    def get_logger(name: str) -> structlog.stdlib.BoundLogger:
        """Get a logger instance.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured structlog logger

        Raises:
            RuntimeError: If logging has not been configured
        """
        if not LoggerFactory._configured:
            # Auto-configure with defaults if not configured
            default_config = LoggerConfig()
            factory = LoggerFactory(default_config)
            factory.configure()

        return structlog.get_logger(name)

    @staticmethod
    def is_configured() -> bool:
        """Check if logging has been configured.

        Returns:
            True if configured, False otherwise
        """
        return LoggerFactory._configured

    @staticmethod
    def get_config() -> LoggerConfig | None:
        """Get current logger configuration.

        Returns:
            Current configuration or None if not configured
        """
        return LoggerFactory._config


# ==============================================================================
# Context Management
# ==============================================================================


class LogContext:
    """Context manager for binding logging context variables.

    This class provides a clean way to add contextual information to logs
    within a specific scope.

    Example:
        >>> with LogContext(request_id="abc-123", user_id="user-456"):
        ...     logger.info("Processing request")  # Includes context
        >>> logger.info("After context")  # No context
    """

    def __init__(self, **kwargs: Any):
        """Initialize log context.

        Args:
            **kwargs: Key-value pairs to bind to logging context
        """
        self.context = kwargs

    def __enter__(self) -> "LogContext":
        """Enter context - bind variables."""
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context - clear variables."""
        structlog.contextvars.clear_contextvars()


# ==============================================================================
# Public API (Functional Interface)
# ==============================================================================


def setup_logging(
    level: str = "INFO",
    json_logs: bool = False,
    logger_name: str | None = None,
    app_name: str = "pulpo",
) -> None:
    """Configure structured logging for the application.

    This is a convenience function that creates a LoggerConfig and
    LoggerFactory to set up logging. For more control, use LoggerFactory
    directly.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output logs in JSON format
        logger_name: Optional specific logger name to configure
        app_name: Application name to include in logs

    Example:
        >>> setup_logging(level="DEBUG", json_logs=False)
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started", version="0.5.0")
    """
    config = LoggerConfig(
        level=level,
        json_logs=json_logs,
        logger_name=logger_name,
        app_name=app_name,
    )
    factory = LoggerFactory(config)
    factory.configure()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger instance for the given name.

    This function returns a structlog logger that supports structured
    logging with key-value pairs.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing job", job_id="12345", status="active")
        >>> logger.error("Failed to connect", error="Connection refused")
    """
    return LoggerFactory.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind context variables for all subsequent log entries.

    Context variables will be included in all logs until cleared.
    Consider using LogContext context manager instead for automatic cleanup.

    Args:
        **kwargs: Key-value pairs to bind to logging context

    Example:
        >>> bind_context(request_id="abc-123", user_id="user-456")
        >>> logger.info("Processing")  # Includes context
        >>> clear_context()
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables.

    This should be called to prevent context from leaking between
    different operations. Consider using LogContext context manager
    for automatic cleanup.

    Example:
        >>> bind_context(request_id="abc-123")
        >>> # ... process request ...
        >>> clear_context()
    """
    structlog.contextvars.clear_contextvars()


# ==============================================================================
# Type Aliases
# ==============================================================================


# Export BoundLogger for type hints
BoundLogger = structlog.stdlib.BoundLogger
