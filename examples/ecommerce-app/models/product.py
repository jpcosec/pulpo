"""Product model for e-commerce catalog."""

from beanie import Document
from pydantic import Field

from core.decorators import datamodel


@datamodel(
    name="Product",
    description="A product in the e-commerce catalog",
    tags=["catalog", "product", "inventory"]
)
class Product(Document):
    """Product available for purchase in the catalog."""

    sku: str = Field(..., description="Stock Keeping Unit - unique product identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(default="", description="Detailed product description")
    price: float = Field(..., description="Price in USD")
    inventory: int = Field(default=0, description="Current stock count")
    category: str = Field(default="general", description="Product category")

    class Settings:
        name = "products"
