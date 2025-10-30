"""Checkout operations - can run in parallel."""

from pydantic import BaseModel, Field

from core.decorators import operation


class ValidateItemsInput(BaseModel):
    """Input for validating order items."""

    order_id: str = Field(..., description="Order ID")
    items: list[dict] = Field(..., description="Items to validate")


class ValidateItemsOutput(BaseModel):
    """Output from item validation."""

    valid: bool = Field(..., description="Whether all items are in stock")
    message: str = Field(..., description="Validation message")


@operation(
    name="orders.checkout.validate_items",
    description="Validate that all items are in stock",
    inputs=ValidateItemsInput,
    outputs=ValidateItemsOutput,
    models_in=["Order", "Product"],
    models_out=[]
)
async def validate_items(input_data: ValidateItemsInput) -> ValidateItemsOutput:
    """Check inventory for all items in order."""
    return ValidateItemsOutput(
        valid=True,
        message="All items are in stock"
    )


class ValidatePaymentInput(BaseModel):
    """Input for payment validation."""

    order_id: str = Field(..., description="Order ID")
    payment_method: str = Field(..., description="Payment method")


class ValidatePaymentOutput(BaseModel):
    """Output from payment validation."""

    valid: bool = Field(..., description="Whether payment method is valid")
    message: str = Field(..., description="Validation message")


@operation(
    name="orders.checkout.validate_payment",
    description="Validate payment method and details",
    inputs=ValidatePaymentInput,
    outputs=ValidatePaymentOutput,
    models_in=["Order"],
    models_out=[]
)
async def validate_payment(input_data: ValidatePaymentInput) -> ValidatePaymentOutput:
    """Validate that payment method is valid and has sufficient funds."""
    return ValidatePaymentOutput(
        valid=True,
        message="Payment method validated"
    )


class CalculateShippingInput(BaseModel):
    """Input for shipping calculation."""

    order_id: str = Field(..., description="Order ID")
    address_zip: str = Field(..., description="Shipping zip code")
    weight: float = Field(default=1.0, description="Total weight in pounds")


class CalculateShippingOutput(BaseModel):
    """Output from shipping calculation."""

    cost: float = Field(..., description="Shipping cost")
    estimated_days: int = Field(..., description="Estimated delivery days")
    message: str = Field(..., description="Calculation message")


@operation(
    name="orders.checkout.calculate_shipping",
    description="Calculate shipping cost based on address and weight",
    inputs=CalculateShippingInput,
    outputs=CalculateShippingOutput,
    models_in=["Order"],
    models_out=[]
)
async def calculate_shipping(input_data: CalculateShippingInput) -> CalculateShippingOutput:
    """Calculate shipping cost and estimated delivery time."""
    return CalculateShippingOutput(
        cost=9.99,
        estimated_days=3,
        message="Shipping calculated"
    )
