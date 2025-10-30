"""Fulfillment operations - sequential pipeline."""

from pydantic import BaseModel, Field

from core.decorators import operation


class ReserveItemsInput(BaseModel):
    """Input for reserving items."""

    order_id: str = Field(..., description="Order ID")


class ReserveItemsOutput(BaseModel):
    """Output from item reservation."""

    success: bool = Field(..., description="Whether items were reserved")
    message: str = Field(..., description="Reservation message")


@operation(
    name="orders.fulfillment.reserve_items",
    description="Reserve inventory for order (depends on checkout validations)",
    inputs=ReserveItemsInput,
    outputs=ReserveItemsOutput,
    models_in=["Order", "Product"],
    models_out=["Order"]
)
async def reserve_items(input_data: ReserveItemsInput) -> ReserveItemsOutput:
    """Reserve items in inventory for this order."""
    return ReserveItemsOutput(
        success=True,
        message="Items reserved in inventory"
    )


class PickItemsInput(BaseModel):
    """Input for picking items."""

    order_id: str = Field(..., description="Order ID")


class PickItemsOutput(BaseModel):
    """Output from item picking."""

    picked_count: int = Field(..., description="Number of items picked")
    message: str = Field(..., description="Picking message")


@operation(
    name="orders.fulfillment.pick_items",
    description="Pick items from warehouse (depends on reservation)",
    inputs=PickItemsInput,
    outputs=PickItemsOutput,
    models_in=["Order", "Product"],
    models_out=["Order"]
)
async def pick_items(input_data: PickItemsInput) -> PickItemsOutput:
    """Pick items from warehouse shelves."""
    return PickItemsOutput(
        picked_count=3,
        message="All items picked from warehouse"
    )


class PackItemsInput(BaseModel):
    """Input for packing items."""

    order_id: str = Field(..., description="Order ID")


class PackItemsOutput(BaseModel):
    """Output from item packing."""

    packed: bool = Field(..., description="Whether items are packed")
    weight: float = Field(..., description="Total package weight")
    message: str = Field(..., description="Packing message")


@operation(
    name="orders.fulfillment.pack_items",
    description="Pack items for shipping (depends on picking)",
    inputs=PackItemsInput,
    outputs=PackItemsOutput,
    models_in=["Order", "Product"],
    models_out=["Order"]
)
async def pack_items(input_data: PackItemsInput) -> PackItemsOutput:
    """Pack items in shipping boxes."""
    return PackItemsOutput(
        packed=True,
        weight=2.5,
        message="Items packed and ready for shipment"
    )


class ShipItemsInput(BaseModel):
    """Input for shipping items."""

    order_id: str = Field(..., description="Order ID")
    tracking_carrier: str = Field(default="UPS", description="Shipping carrier")


class ShipItemsOutput(BaseModel):
    """Output from shipping."""

    shipped: bool = Field(..., description="Whether order was shipped")
    tracking_number: str = Field(..., description="Shipping tracking number")
    estimated_delivery: str = Field(..., description="Estimated delivery date")
    message: str = Field(..., description="Shipping message")


@operation(
    name="orders.fulfillment.ship_items",
    description="Ship order to customer (depends on packing)",
    inputs=ShipItemsInput,
    outputs=ShipItemsOutput,
    models_in=["Order"],
    models_out=["Order"]
)
async def ship_items(input_data: ShipItemsInput) -> ShipItemsOutput:
    """Ship order to customer address."""
    return ShipItemsOutput(
        shipped=True,
        tracking_number="1Z999AA10123456784",
        estimated_delivery="2025-11-02",
        message="Order shipped via UPS"
    )
