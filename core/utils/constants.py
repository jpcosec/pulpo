"""
Shared constants for the JobHunter AI application.

This module contains constant values organized into logical groups using
enums and dataclasses for better type safety and organization.

Example:
    >>> from core.utils.constants import ApplicationStatus, Timeouts
    >>>
    >>> status = ApplicationStatus.SUBMITTED
    >>> timeout = Timeouts.REQUEST
"""

from dataclasses import dataclass
from enum import Enum
from typing import Final

# ==============================================================================
# Enums
# ==============================================================================


class Language(str, Enum):
    """Supported languages for job listings and applications."""

    GERMAN = "de"
    ENGLISH = "en"
    SPANISH = "es"

    @classmethod
    def default(cls) -> "Language":
        """Get default language.

        Returns:
            Default language (German)
        """
        return cls.GERMAN


class JobSource(str, Enum):
    """Supported job board platforms for scraping."""

    INDEED = "indeed"
    STEPSTONE = "stepstone"
    LINKEDIN = "linkedin"

    @property
    def display_name(self) -> str:
        """Get display name for job source.

        Returns:
            Human-readable name
        """
        return {
            self.INDEED: "Indeed",
            self.STEPSTONE: "StepStone",
            self.LINKEDIN: "LinkedIn",
        }[self]


class ApplicationStatus(str, Enum):
    """Possible states of a job application."""

    DRAFT = "draft"  # Application created but not finalized
    SUBMITTED = "submitted"  # Application has been submitted
    PENDING = "pending"  # Application is under review
    ACCEPTED = "accepted"  # Application was accepted (interview/offer)
    REJECTED = "rejected"  # Application was rejected
    WITHDRAWN = "withdrawn"  # Application was withdrawn by user

    @property
    def display_name(self) -> str:
        """Get display name for status.

        Returns:
            Human-readable name
        """
        return {
            self.DRAFT: "Draft",
            self.SUBMITTED: "Submitted",
            self.PENDING: "Pending Review",
            self.ACCEPTED: "Accepted",
            self.REJECTED: "Rejected",
            self.WITHDRAWN: "Withdrawn",
        }[self]


class DocumentFormat(str, Enum):
    """Supported document formats for CV and cover letters."""

    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"

    @classmethod
    def default(cls) -> "DocumentFormat":
        """Get default document format.

        Returns:
            Default format (PDF)
        """
        return cls.PDF


class JobType(str, Enum):
    """Supported job types."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class RemoteOption(str, Enum):
    """Remote work options."""

    ON_SITE = "on_site"  # No remote work
    HYBRID = "hybrid"  # Mix of remote and on-site
    REMOTE = "remote"  # Fully remote


class ExperienceLevel(str, Enum):
    """Experience levels for job positions."""

    ENTRY = "entry"  # Entry level / Junior
    MID = "mid"  # Mid-level / Experienced
    SENIOR = "senior"  # Senior level
    LEAD = "lead"  # Lead / Principal
    EXECUTIVE = "executive"  # Executive / C-level


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

    @property
    def default_model(self) -> str:
        """Get default model for provider.

        Returns:
            Default model name
        """
        return {
            self.OPENAI: "gpt-4-turbo-preview",
            self.ANTHROPIC: "claude-3-sonnet-20240229",
            self.OLLAMA: "llama2",
        }[self]


# ==============================================================================
# Dataclasses for Grouped Constants
# ==============================================================================


@dataclass(frozen=True)
class MatchScores:
    """Thresholds for job-candidate matching scores (0.0 - 1.0 scale)."""

    EXCELLENT: float = 0.8
    GOOD: float = 0.6
    ACCEPTABLE: float = 0.4
    MIN: float = 0.0
    MAX: float = 1.0


@dataclass(frozen=True)
class RateLimits:
    """Default rate limits for various operations (per minute)."""

    SCRAPING: int = 15
    API: int = 60
    APPLICATION: int = 5
    MAX_RETRIES: int = 3


@dataclass(frozen=True)
class Timeouts:
    """Timeout values in seconds."""

    REQUEST: int = 30
    BROWSER: int = 60
    PROCESSING: int = 300


@dataclass(frozen=True)
class Directories:
    """Default paths for various files and directories."""

    DATA: str = "data"
    LOGS: str = "logs"
    CACHE: str = "cache"
    TEMPLATES: str = "templates"


@dataclass(frozen=True)
class Collections:
    """MongoDB collection names."""

    JOBS: str = "jobs"
    APPLICATIONS: str = "applications"
    PROFILES: str = "profiles"
    DOCUMENTS: str = "documents"
    COMPANIES: str = "companies"
    SCRAPING_JOBS: str = "scraping_jobs"


@dataclass(frozen=True)
class DateFormats:
    """Standard date/time format strings."""

    DATE: str = "%Y-%m-%d"
    DATETIME: str = "%Y-%m-%d %H:%M:%S"
    DATETIME_ISO: str = "%Y-%m-%dT%H:%M:%S"


@dataclass(frozen=True)
class ValidationLimits:
    """Maximum and minimum lengths for various fields."""

    # Job title
    MAX_JOB_TITLE: int = 200
    MIN_JOB_TITLE: int = 2

    # Company name
    MAX_COMPANY_NAME: int = 200
    MIN_COMPANY_NAME: int = 2

    # Description
    MAX_DESCRIPTION: int = 50000
    MIN_DESCRIPTION: int = 10

    # Cover letter
    MAX_COVER_LETTER: int = 5000
    MIN_COVER_LETTER: int = 100

    # Email and URL
    MAX_EMAIL: int = 254  # RFC 5321
    MAX_URL: int = 2048


@dataclass(frozen=True)
class LLMTemperatures:
    """LLM temperature settings for different use cases."""

    CREATIVE: float = 0.8
    BALANCED: float = 0.5
    PRECISE: float = 0.2


@dataclass(frozen=True)
class HTTPDefaults:
    """Common HTTP headers for scraping."""

    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    ACCEPT_LANGUAGE: str = "en-US,en;q=0.9,de;q=0.8"


@dataclass(frozen=True)
class CacheTTL:
    """Cache TTL values in seconds."""

    SHORT: int = 300  # 5 minutes
    MEDIUM: int = 3600  # 1 hour
    LONG: int = 86400  # 24 hours
    VERY_LONG: int = 604800  # 7 days


# ==============================================================================
# Singleton Instances (for easy access)
# ==============================================================================


# Instantiate dataclasses as singletons
MATCH_SCORES = MatchScores()
RATE_LIMITS = RateLimits()
TIMEOUTS = Timeouts()
DIRECTORIES = Directories()
COLLECTIONS = Collections()
DATE_FORMATS = DateFormats()
VALIDATION_LIMITS = ValidationLimits()
LLM_TEMPERATURES = LLMTemperatures()
HTTP_DEFAULTS = HTTPDefaults()
CACHE_TTL = CacheTTL()


# ==============================================================================
# Legacy Constants (For Backward Compatibility)
# ==============================================================================


# Languages
SUPPORTED_LANGUAGES: Final[list[str]] = [lang.value for lang in Language]
DEFAULT_LANGUAGE: Final[str] = Language.default().value

# Job Sources
JOB_SOURCES: Final[list[str]] = [source.value for source in JobSource]
JOB_SOURCE_NAMES: Final[dict[str, str]] = {
    source.value: source.display_name for source in JobSource
}

# Application Statuses
APPLICATION_STATUSES: Final[list[str]] = [status.value for status in ApplicationStatus]
APPLICATION_STATUS_NAMES: Final[dict[str, str]] = {
    status.value: status.display_name for status in ApplicationStatus
}

# Document Formats
DOCUMENT_FORMATS: Final[list[str]] = [fmt.value for fmt in DocumentFormat]
DEFAULT_DOCUMENT_FORMAT: Final[str] = DocumentFormat.default().value

# Job Types
JOB_TYPES: Final[list[str]] = [jt.value for jt in JobType]

# Remote Options
REMOTE_OPTIONS: Final[list[str]] = [opt.value for opt in RemoteOption]

# Experience Levels
EXPERIENCE_LEVELS: Final[list[str]] = [level.value for level in ExperienceLevel]

# LLM Providers
LLM_PROVIDERS: Final[list[str]] = [provider.value for provider in LLMProvider]
DEFAULT_LLM_MODEL: Final[dict[str, str]] = {
    provider.value: provider.default_model for provider in LLMProvider
}


# ==============================================================================
# Utility Functions
# ==============================================================================


def get_job_source_display_name(source: str) -> str:
    """Get display name for job source.

    Args:
        source: Job source value

    Returns:
        Display name or original value if not found
    """
    try:
        return JobSource(source).display_name
    except ValueError:
        return source


def get_application_status_display_name(status: str) -> str:
    """Get display name for application status.

    Args:
        status: Application status value

    Returns:
        Display name or original value if not found
    """
    try:
        return ApplicationStatus(status).display_name
    except ValueError:
        return status
