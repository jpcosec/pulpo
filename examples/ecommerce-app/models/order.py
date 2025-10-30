"""Order model for e-commerce transactions."""

from datetime import datetime
from enum import Enum

from beanie import Document
from pydantic import BaseModel, Field

from core.decorators import datamodel


class OrderStatus(str, Enum):
    """Order status values."""

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    """Item within an order."""

    product_id: str = Field(..., description="ID of ordered product")
    product_name: str = Field(..., description="Name of product")
    quantity: int = Field(..., description="Quantity ordered")
    unit_price: float = Field(..., description="Price per unit")
    total_price: float = Field(..., description="Total price for this item")


@datamodel(
    name="Order",
    description="A customer order",
    tags=["order", "transaction"]
)
class Order(Document):
    """Customer order with items and fulfillment tracking."""

    order_number: str = Field(..., description="Unique order number")
    customer_id: str = Field(..., description="ID of customer who placed order")
    items: list[OrderItem] = Field(..., description="Items in the order")
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        description="Current order status"
    )
    subtotal: float = Field(..., description="Subtotal before shipping/tax")
    shipping_cost: float = Field(default=0.0, description="Shipping cost")
    tax: float = Field(default=0.0, description="Sales tax")
    total: float = Field(..., description="Total order amount")
    shipping_address_id: str = Field(..., description="ID of shipping address")
    payment_method: str = Field(..., description="Payment method used")
    tracking_number: str = Field(default="", description="Shipping tracking number")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Order creation time")
    shipped_at: datetime = Field(default=None, description="When order was shipped")
    delivered_at: datetime = Field(default=None, description="When order was delivered")

    class Settings:
        name = "orders"
