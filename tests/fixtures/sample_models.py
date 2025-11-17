"""Sample data models extracted from todo-app for testing.

These are fixtures for testing Pulpo framework functionality.
They mirror the structure of real models without importing the actual project.
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from beanie import Document, Link, BackLink
from pydantic import Field, BaseModel, computed_field

from core.decorators import datamodel


# Simple model - minimal fields
@datamodel(
    name="Category",
    description="Task category for organization",
    tags=["category", "test"]
)
class Category(Document):
    """Simple model for testing basic discovery."""

    name: str = Field(..., description="Category name")
    color: str = Field(default="#0066CC", description="Hex color")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "categories"


# Embedded model - used within other models
class DateRange(BaseModel):
    """Embedded date range model."""

    start: Optional[datetime] = Field(default=None, description="Start date")
    finish: Optional[datetime] = Field(default=None, description="Finish date")

    def is_overdue(self) -> bool:
        """Check if finish date has passed."""
        if self.finish is None:
            return False
        return datetime.utcnow() > self.finish


# Enum for status
class TaskStatusEnum(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Complex model - with relationships and computed fields
@datamodel(
    name="Task",
    description="Task with dependencies and computed fields",
    tags=["task", "test"]
)
class Task(Document):
    """Complex model for testing graph relationships and computed fields."""

    # Basic fields
    title: str = Field(..., description="Task title")
    description: str = Field(default="", description="Task description")

    # Status and priority
    status: TaskStatusEnum = Field(
        default=TaskStatusEnum.PENDING,
        description="Current status"
    )
    importance_rate: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Importance 0-5"
    )

    # Reference to category
    category_id: Optional[str] = Field(
        default=None,
        description="Category ID"
    )

    # Embedded model
    date: DateRange = Field(
        default_factory=DateRange,
        description="Task dates"
    )

    # Graph relationships
    dependencies: list[Link["Task"]] = Field(
        default_factory=list,
        description="Task dependencies"
    )
    subtasks: list[BackLink["Task"]] = Field(
        default=[],
        description="Subtasks"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def urgency(self) -> float:
        """Computed urgency score 0-10."""
        if self.date.finish is None:
            return 0.5
        if self.date.is_overdue():
            return 10.0
        return 5.0

    class Settings:
        name = "tasks"


# Model with enum
@datamodel(
    name="Alarm",
    description="Task reminder with recurrence",
    tags=["alarm", "test"]
)
class Alarm(Document):
    """Model for testing enum handling."""

    class RecurrencePattern(str, Enum):
        """Recurrence patterns."""
        ONCE = "once"
        DAILY = "daily"
        WEEKLY = "weekly"

    task_id: str = Field(..., description="Task ID")
    alarm_time: datetime = Field(..., description="Trigger time")
    recurrence: RecurrencePattern = Field(
        default=RecurrencePattern.ONCE,
        description="Recurrence pattern"
    )
    enabled: bool = Field(default=True, description="Is active")

    class Settings:
        name = "alarms"
