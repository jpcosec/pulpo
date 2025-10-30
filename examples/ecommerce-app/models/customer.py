"""Customer model for e-commerce."""

from datetime import datetime
from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field

from core.decorators import datamodel


class Address(BaseModel):
    """Customer address."""

    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    zip_code: str = Field(..., description="Postal code")
    country: str = Field(default="US", description="Country")


@datamodel(
    name="Customer",
    description="A customer who can place orders",
    tags=["customer", "account"]
)
class Customer(Document):
    """Customer account for e-commerce platform."""

    email: str = Field(..., description="Customer email address")
    name: str = Field(..., description="Customer full name")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    addresses: list[Address] = Field(
        default_factory=list,
        description="Shipping and billing addresses"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    class Settings:
        name = "customers"
