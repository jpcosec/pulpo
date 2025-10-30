"""Payment model for order transactions."""

from datetime import datetime
from enum import Enum

from beanie import Document
from pydantic import Field

from core.decorators import datamodel


class PaymentStatus(str, Enum):
    """Payment status values."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@datamodel(
    name="Payment",
    description="Payment record for an order",
    tags=["payment", "transaction"]
)
class Payment(Document):
    """Payment transaction record."""

    order_id: str = Field(..., description="ID of related order")
    amount: float = Field(..., description="Payment amount in USD")
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        description="Current payment status"
    )
    payment_method: str = Field(..., description="Payment method (credit_card, paypal, etc)")
    transaction_id: str = Field(default="", description="Payment processor transaction ID")
    error_message: str = Field(default="", description="Error message if payment failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Payment creation time")
    completed_at: datetime = Field(default=None, description="When payment was completed")
    refunded_at: datetime = Field(default=None, description="When payment was refunded")

    class Settings:
        name = "payments"
