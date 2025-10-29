"""
Validation system for the JobHunter AI application.

This module provides a clean, object-oriented validation system with
validator classes, fluent chains, and detailed validation results.

Example:
    >>> from core.utils.validators import EmailValidator, ValidationChain
    >>>
    >>> # Class-based validation
    >>> validator = EmailValidator()
    >>> result = validator.validate("user@example.com")
    >>> print(result.is_valid)  # True
    >>>
    >>> # Functional API (backward compatible)
    >>> from core.utils.validators import validate_email
    >>> is_valid = validate_email("user@example.com")  # True
    >>>
    >>> # Fluent chain
    >>> chain = ValidationChain()
    >>> result = (chain
    ...     .add(EmailValidator())
    ...     .add(UrlValidator())
    ...     .validate_all({"email": "user@example.com", "url": "https://example.com"}))
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

# ==============================================================================
# Validation Result
# ==============================================================================


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed
        value: The validated value (may be transformed)
        errors: List of error messages
        field_name: Optional field name that was validated
    """

    is_valid: bool
    value: Any
    errors: list[str] = field(default_factory=list)
    field_name: str | None = None

    def add_error(self, error: str) -> None:
        """Add an error message.

        Args:
            error: Error message to add
        """
        self.errors.append(error)
        self.is_valid = False

    @property
    def error_message(self) -> str:
        """Get combined error message.

        Returns:
            Combined error messages
        """
        return "; ".join(self.errors)

    @classmethod
    def success(cls, value: Any, field_name: str | None = None) -> "ValidationResult":
        """Create successful validation result.

        Args:
            value: Validated value
            field_name: Optional field name

        Returns:
            ValidationResult indicating success
        """
        return cls(is_valid=True, value=value, field_name=field_name)

    @classmethod
    def failure(
        cls, value: Any, errors: list[str], field_name: str | None = None
    ) -> "ValidationResult":
        """Create failed validation result.

        Args:
            value: Invalid value
            errors: List of error messages
            field_name: Optional field name

        Returns:
            ValidationResult indicating failure
        """
        return cls(is_valid=False, value=value, errors=errors, field_name=field_name)


# ==============================================================================
# Base Validator
# ==============================================================================


class Validator(ABC):
    """Abstract base class for validators.

    All validators must implement the validate() method which returns
    a ValidationResult.
    """

    def __init__(self, field_name: str | None = None):
        """Initialize validator.

        Args:
            field_name: Optional field name for error messages
        """
        self.field_name = field_name

    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """Validate a value.

        Args:
            value: Value to validate

        Returns:
            ValidationResult indicating success or failure
        """
        pass

    def is_valid(self, value: Any) -> bool:
        """Check if value is valid (simple boolean).

        Args:
            value: Value to validate

        Returns:
            True if valid, False otherwise
        """
        return self.validate(value).is_valid


# ==============================================================================
# Email Validator
# ==============================================================================


class EmailValidator(Validator):
    """Validates email addresses using RFC 5322 compliant regex.

    Example:
        >>> validator = EmailValidator()
        >>> result = validator.validate("user@example.com")
        >>> print(result.is_valid)  # True
    """

    # RFC 5322 compliant email regex (simplified)
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    MAX_EMAIL_LENGTH = 254  # RFC 5321

    def validate(self, value: Any) -> ValidationResult:
        """Validate email address.

        Args:
            value: Email address to validate

        Returns:
            ValidationResult
        """
        errors = []

        # Type check
        if not value or not isinstance(value, str):
            errors.append("Email must be a non-empty string")
            return ValidationResult.failure(value, errors, self.field_name)

        # Length check
        if len(value) > self.MAX_EMAIL_LENGTH:
            errors.append(f"Email exceeds maximum length of {self.MAX_EMAIL_LENGTH}")

        # Consecutive dots check
        if ".." in value:
            errors.append("Email cannot contain consecutive dots")

        # Pattern check
        if not self.EMAIL_PATTERN.match(value):
            errors.append("Email format is invalid")

        if errors:
            return ValidationResult.failure(value, errors, self.field_name)

        return ValidationResult.success(value, self.field_name)


# ==============================================================================
# URL Validator
# ==============================================================================


class UrlValidator(Validator):
    """Validates URL format and structure.

    Example:
        >>> validator = UrlValidator(require_https=True)
        >>> result = validator.validate("https://example.com")
        >>> print(result.is_valid)  # True
    """

    def __init__(self, require_https: bool = False, field_name: str | None = None):
        """Initialize URL validator.

        Args:
            require_https: If True, only accept HTTPS URLs
            field_name: Optional field name
        """
        super().__init__(field_name)
        self.require_https = require_https

    def validate(self, value: Any) -> ValidationResult:
        """Validate URL.

        Args:
            value: URL to validate

        Returns:
            ValidationResult
        """
        errors = []

        # Type check
        if not value or not isinstance(value, str):
            errors.append("URL must be a non-empty string")
            return ValidationResult.failure(value, errors, self.field_name)

        try:
            result = urlparse(value)

            # Check required components
            if not result.scheme:
                errors.append("URL must have a scheme (http:// or https://)")
            if not result.netloc:
                errors.append("URL must have a domain")

            # Check scheme
            if self.require_https:
                if result.scheme != "https":
                    errors.append("URL must use HTTPS")
            else:
                if result.scheme not in ["http", "https"]:
                    errors.append("URL scheme must be http or https")

            # Basic domain validation
            if result.netloc and "." not in result.netloc:
                errors.append("URL domain must contain at least one dot")

        except (ValueError, AttributeError) as e:
            errors.append(f"Invalid URL format: {str(e)}")

        if errors:
            return ValidationResult.failure(value, errors, self.field_name)

        return ValidationResult.success(value, self.field_name)


# ==============================================================================
# Phone Validator
# ==============================================================================


class PhoneValidator(Validator):
    """Validates phone numbers for specific countries.

    Example:
        >>> validator = PhoneValidator(country="DE")
        >>> result = validator.validate("+49 151 12345678")
        >>> print(result.is_valid)  # True
    """

    def __init__(self, country: str = "DE", field_name: str | None = None):
        """Initialize phone validator.

        Args:
            country: Country code (default: DE for Germany)
            field_name: Optional field name
        """
        super().__init__(field_name)
        self.country = country.upper()

    def validate(self, value: Any) -> ValidationResult:
        """Validate phone number.

        Args:
            value: Phone number to validate

        Returns:
            ValidationResult
        """
        errors = []

        # Type check
        if not value or not isinstance(value, str):
            errors.append("Phone number must be a non-empty string")
            return ValidationResult.failure(value, errors, self.field_name)

        # Remove common separators
        cleaned = re.sub(r"[\s\-\(\)\.]", "", value)

        # Validate based on country
        if self.country == "DE":
            if not self._validate_german_phone(cleaned):
                errors.append("Invalid German phone number format")
        else:
            # Generic validation for other countries
            pattern = r"^[\+0]\d{6,14}$"
            if not re.match(pattern, cleaned):
                errors.append(f"Invalid phone number format for country {self.country}")

        if errors:
            return ValidationResult.failure(value, errors, self.field_name)

        return ValidationResult.success(cleaned, self.field_name)

    @staticmethod
    def _validate_german_phone(phone: str) -> bool:
        """Validate German phone number.

        Args:
            phone: Cleaned phone number

        Returns:
            True if valid
        """
        # International format: +49 followed by 9-12 digits
        if phone.startswith("+49"):
            digits = phone[3:]
            return 9 <= len(digits) <= 12 and digits.isdigit()

        # National format: 0 followed by 9-12 digits
        if phone.startswith("0"):
            digits = phone[1:]
            return 9 <= len(digits) <= 12 and digits.isdigit()

        return False


# ==============================================================================
# Postal Code Validator
# ==============================================================================


class PostalCodeValidator(Validator):
    """Validates postal codes for specific countries.

    Example:
        >>> validator = PostalCodeValidator(country="DE")
        >>> result = validator.validate("10115")
        >>> print(result.is_valid)  # True
    """

    def __init__(self, country: str = "DE", field_name: str | None = None):
        """Initialize postal code validator.

        Args:
            country: Country code (default: DE for Germany)
            field_name: Optional field name
        """
        super().__init__(field_name)
        self.country = country.upper()

    def validate(self, value: Any) -> ValidationResult:
        """Validate postal code.

        Args:
            value: Postal code to validate

        Returns:
            ValidationResult
        """
        errors = []

        # Type check
        if not value or not isinstance(value, str):
            errors.append("Postal code must be a non-empty string")
            return ValidationResult.failure(value, errors, self.field_name)

        # Validate based on country
        if self.country == "DE":
            # German postal codes are exactly 5 digits
            if not re.match(r"^\d{5}$", value):
                errors.append("German postal code must be exactly 5 digits")
        else:
            errors.append(f"Postal code validation not implemented for country {self.country}")

        if errors:
            return ValidationResult.failure(value, errors, self.field_name)

        return ValidationResult.success(value, self.field_name)


# ==============================================================================
# String Length Validator
# ==============================================================================


class LengthValidator(Validator):
    """Validates string length constraints.

    Example:
        >>> validator = LengthValidator(min_length=2, max_length=100)
        >>> result = validator.validate("Software Engineer")
        >>> print(result.is_valid)  # True
    """

    def __init__(
        self,
        min_length: int | None = None,
        max_length: int | None = None,
        field_name: str | None = None,
    ):
        """Initialize length validator.

        Args:
            min_length: Minimum length (inclusive)
            max_length: Maximum length (inclusive)
            field_name: Optional field name
        """
        super().__init__(field_name)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: Any) -> ValidationResult:
        """Validate string length.

        Args:
            value: String to validate

        Returns:
            ValidationResult
        """
        errors = []

        # Type check
        if not isinstance(value, str):
            errors.append("Value must be a string")
            return ValidationResult.failure(value, errors, self.field_name)

        value_stripped = value.strip()
        length = len(value_stripped)

        # Min length check
        if self.min_length is not None and length < self.min_length:
            errors.append(f"Length must be at least {self.min_length} characters")

        # Max length check
        if self.max_length is not None and length > self.max_length:
            errors.append(f"Length must not exceed {self.max_length} characters")

        if errors:
            return ValidationResult.failure(value, errors, self.field_name)

        return ValidationResult.success(value_stripped, self.field_name)


# ==============================================================================
# Validation Chain
# ==============================================================================


class ValidationChain:
    """Chain multiple validators together for complex validation.

    Example:
        >>> chain = ValidationChain()
        >>> chain.add(EmailValidator(), "email")
        >>> chain.add(UrlValidator(), "website")
        >>> results = chain.validate_all({
        ...     "email": "user@example.com",
        ...     "website": "https://example.com"
        ... })
    """

    def __init__(self):
        """Initialize validation chain."""
        self.validators: dict[str, Validator] = {}

    def add(self, validator: Validator, field_name: str | None = None) -> "ValidationChain":
        """Add a validator to the chain.

        Args:
            validator: Validator to add
            field_name: Optional field name (uses validator's field_name if not provided)

        Returns:
            Self for method chaining
        """
        name = field_name or validator.field_name or f"validator_{len(self.validators)}"
        self.validators[name] = validator
        return self

    def validate_all(self, values: dict[str, Any]) -> dict[str, ValidationResult]:
        """Validate all values.

        Args:
            values: Dictionary of field names to values

        Returns:
            Dictionary of field names to ValidationResults
        """
        results = {}
        for field_name, validator in self.validators.items():
            value = values.get(field_name)
            results[field_name] = validator.validate(value)
        return results

    def is_valid(self, values: dict[str, Any]) -> bool:
        """Check if all values are valid.

        Args:
            values: Dictionary of field names to values

        Returns:
            True if all validations pass
        """
        results = self.validate_all(values)
        return all(result.is_valid for result in results.values())


# ==============================================================================
# Functional API (Backward Compatibility)
# ==============================================================================


def validate_email(email: str) -> bool:
    """Validate email address format (functional API).

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    return EmailValidator().is_valid(email)


def validate_url(url: str, require_https: bool = False) -> bool:
    """Validate URL format (functional API).

    Args:
        url: URL to validate
        require_https: If True, only accept HTTPS URLs

    Returns:
        True if valid, False otherwise
    """
    return UrlValidator(require_https=require_https).is_valid(url)


def validate_phone(phone: str, country: str = "DE") -> bool:
    """Validate phone number format (functional API).

    Args:
        phone: Phone number to validate
        country: Country code (default: DE)

    Returns:
        True if valid, False otherwise
    """
    return PhoneValidator(country=country).is_valid(phone)


def validate_german_postal_code(postal_code: str) -> bool:
    """Validate German postal code format (functional API).

    Args:
        postal_code: Postal code to validate

    Returns:
        True if valid, False otherwise
    """
    return PostalCodeValidator(country="DE").is_valid(postal_code)


def validate_job_title(title: str, min_length: int = 2, max_length: int = 200) -> bool:
    """Validate job title format (functional API).

    Args:
        title: Job title to validate
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        True if valid, False otherwise
    """
    # First check length
    length_validator = LengthValidator(min_length=min_length, max_length=max_length)
    if not length_validator.is_valid(title):
        return False

    # Check for at least one letter
    if not any(c.isalpha() for c in title):
        return False

    return True


# Note: IBAN validation from legacy is not included as it's complex
# and better suited for a dedicated library like schwifty
