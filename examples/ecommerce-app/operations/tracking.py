"""Tracking operations - post-fulfillment."""

from pydantic import BaseModel, Field

from core.decorators import operation


class UpdateCustomerInput(BaseModel):
    """Input for customer update."""

    order_id: str = Field(..., description="Order ID")
    customer_id: str = Field(..., description="Customer ID")


class UpdateCustomerOutput(BaseModel):
    """Output from customer update."""

    success: bool = Field(..., description="Whether update succeeded")
    message: str = Field(..., description="Update message")


@operation(
    name="orders.tracking.update_customer",
    category="tracking",
    description="Send shipping notification to customer (depends on shipment)",
    inputs=UpdateCustomerInput,
    outputs=UpdateCustomerOutput,
    models_in=["Order", "Customer"],
    models_out=[]
)
async def update_customer(input_data: UpdateCustomerInput) -> UpdateCustomerOutput:
    """Notify customer that order has shipped."""
    return UpdateCustomerOutput(
        success=True,
        message="Customer notified of shipment"
    )
