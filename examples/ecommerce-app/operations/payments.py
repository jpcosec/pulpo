"""Payment processing operations - can run parallel to fulfillment."""

from pydantic import BaseModel, Field

from core.decorators import operation


class ChargePaymentInput(BaseModel):
    """Input for charging payment."""

    order_id: str = Field(..., description="Order ID")
    amount: float = Field(..., description="Amount to charge")
    payment_method: str = Field(..., description="Payment method")


class ChargePaymentOutput(BaseModel):
    """Output from payment charge."""

    success: bool = Field(..., description="Whether charge succeeded")
    transaction_id: str = Field(..., description="Transaction ID")
    message: str = Field(..., description="Charge message")


@operation(
    name="payments.processing.charge",
    description="Charge customer payment (parallel to fulfillment)",
    inputs=ChargePaymentInput,
    outputs=ChargePaymentOutput,
    models_in=["Order", "Payment"],
    models_out=["Payment"]
)
async def charge_payment(input_data: ChargePaymentInput) -> ChargePaymentOutput:
    """Charge the customer's payment method."""
    return ChargePaymentOutput(
        success=True,
        transaction_id="txn_1234567890",
        message=f"Charged ${input_data.amount} to payment method"
    )


class ConfirmPaymentInput(BaseModel):
    """Input for confirming payment."""

    order_id: str = Field(..., description="Order ID")
    transaction_id: str = Field(..., description="Transaction ID from charge")


class ConfirmPaymentOutput(BaseModel):
    """Output from payment confirmation."""

    confirmed: bool = Field(..., description="Whether payment is confirmed")
    message: str = Field(..., description="Confirmation message")


@operation(
    name="payments.processing.confirm",
    description="Confirm payment was processed (depends on charge)",
    inputs=ConfirmPaymentInput,
    outputs=ConfirmPaymentOutput,
    models_in=["Payment"],
    models_out=["Payment"]
)
async def confirm_payment(input_data: ConfirmPaymentInput) -> ConfirmPaymentOutput:
    """Confirm that payment has been successfully processed."""
    return ConfirmPaymentOutput(
        confirmed=True,
        message="Payment confirmed and settled"
    )


class VerifyPaymentInput(BaseModel):
    """Input for verifying payment."""

    order_id: str = Field(..., description="Order ID")
    transaction_id: str = Field(..., description="Transaction ID")


class VerifyPaymentOutput(BaseModel):
    """Output from payment verification."""

    verified: bool = Field(..., description="Whether payment is verified")
    settlement_status: str = Field(..., description="Settlement status")
    message: str = Field(..., description="Verification message")


@operation(
    name="payments.reconciliation.verify",
    description="Verify payment in reconciliation system (depends on confirmation)",
    inputs=VerifyPaymentInput,
    outputs=VerifyPaymentOutput,
    models_in=["Payment"],
    models_out=["Payment"]
)
async def verify_payment(input_data: VerifyPaymentInput) -> VerifyPaymentOutput:
    """Verify payment in accounting/reconciliation system."""
    return VerifyPaymentOutput(
        verified=True,
        settlement_status="settled",
        message="Payment verified in reconciliation system"
    )
