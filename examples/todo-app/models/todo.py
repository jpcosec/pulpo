"""Todo model for task management."""

from datetime import datetime
from enum import Enum

from beanie import Document
from pydantic import Field

from core.decorators import datamodel


class TodoStatus(str, Enum):
    """Todo item status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@datamodel(
    name="Todo",
    description="A task item in the todo list",
    tags=["task", "todo"]
)
class Todo(Document):
    """Todo item representing a task to be completed."""

    title: str = Field(..., description="Short task title")
    description: str = Field(default="", description="Detailed task description")
    status: TodoStatus = Field(
        default=TodoStatus.PENDING,
        description="Current status of the todo (pending, in_progress, completed)"
    )
    created_by: str = Field(..., description="Username of who created this todo")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When todo was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last time todo was updated")

    class Settings:
        name = "todos"
