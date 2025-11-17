"""Structured logging configuration for Pulpo AI.

This module provides centralized logging configuration with:
- JSON structured logging for production
- Console logging for development
- File rotation
- Log levels per environment
"""

import logging
import sys
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """Structured logging with JSON format and file rotation."""

    def __init__(
        self,
        name: str = "pulpo",
        log_dir: str = "logs",
        level: str = "INFO",
        enable_json: bool = True,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            log_dir: Directory for log files
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            enable_json: Enable JSON formatted logs
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.level = level
        self.enable_json = enable_json

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))

        # Remove existing handlers
        self.logger.handlers = []

        # Add handlers
        self._add_console_handler()
        self._add_file_handler()

    def _add_console_handler(self):
        """Add console handler with color formatting."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.level))

        if self.enable_json:
            # JSON format for production
            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s",
                timestamp=True,
            )
        else:
            # Human-readable format for development
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _add_file_handler(self):
        """Add rotating file handler."""
        from logging.handlers import RotatingFileHandler

        # Application log (all levels)
        app_log = self.log_dir / "application.log"
        app_handler = RotatingFileHandler(
            app_log,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        app_handler.setLevel(logging.DEBUG)

        # Error log (errors only)
        error_log = self.log_dir / "errors.log"
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        error_handler.setLevel(logging.ERROR)

        # JSON formatter for files
        if self.enable_json:
            file_formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
                timestamp=True,
            )
        else:
            file_formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        app_handler.setFormatter(file_formatter)
        error_handler.setFormatter(file_formatter)

        self.logger.addHandler(app_handler)
        self.logger.addHandler(error_handler)

    def get_logger(self) -> logging.Logger:
        """Get configured logger."""
        return self.logger


def setup_logging(
    level: str = "INFO",
    enable_json: bool = False,
    log_dir: str = "logs",
) -> logging.Logger:
    """Setup application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        enable_json: Enable JSON formatted logs
        log_dir: Directory for log files

    Returns:
        Configured logger instance

    Example:
        logger = setup_logging(level="DEBUG", enable_json=True)
        logger.info("Application started", extra={"version": "1.0.0"})
    """
    structured_logger = StructuredLogger(
        name="pulpo",
        log_dir=log_dir,
        level=level,
        enable_json=enable_json,
    )

    return structured_logger.get_logger()


def get_logger(name: str) -> logging.Logger:
    """Get a child logger.

    Args:
        name: Logger name (e.g., "pulpo.scraping")

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Scraping started")
    """
    return logging.getLogger(f"pulpo.{name}")


# Structured logging helpers


def log_operation_start(logger: logging.Logger, operation: str, **kwargs: Any):
    """Log operation start with structured data.

    Args:
        logger: Logger instance
        operation: Operation name
        **kwargs: Additional context
    """
    logger.info(
        f"Operation started: {operation}",
        extra={
            "event": "operation_start",
            "operation": operation,
            **kwargs,
        },
    )


def log_operation_complete(
    logger: logging.Logger,
    operation: str,
    duration: float,
    success: bool = True,
    **kwargs: Any,
):
    """Log operation completion with structured data.

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Execution duration in seconds
        success: Whether operation succeeded
        **kwargs: Additional context
    """
    level = logging.INFO if success else logging.ERROR

    logger.log(
        level,
        f"Operation {'completed' if success else 'failed'}: {operation}",
        extra={
            "event": "operation_complete",
            "operation": operation,
            "duration_seconds": duration,
            "success": success,
            **kwargs,
        },
    )


def log_error(logger: logging.Logger, error: Exception, context: dict[str, Any] | None = None):
    """Log error with structured data and traceback.

    Args:
        logger: Logger instance
        error: Exception instance
        context: Additional context
    """
    import traceback

    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            **(context or {}),
        },
    )
