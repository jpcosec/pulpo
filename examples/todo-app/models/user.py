"""User model for todo list application."""

from datetime import datetime

from beanie import Document
from pydantic import Field

from core.decorators import datamodel


@datamodel(
    name="User",
    description="A user who can manage todo tasks",
    tags=["user", "account"]
)
class User(Document):
    """User account for todo list application."""

    username: str = Field(..., description="Unique username")
    email: str = Field(..., description="User email address")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "users"
