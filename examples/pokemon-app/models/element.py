"""Element datamodel for Pokemon types."""

from beanie import Document
from pydantic import Field

from core.decorators import datamodel


@datamodel(
    name="Element",
    description="Element/Type for Pokemon attacks and resistances. Examples: Fire, Water, Grass, Electric, etc.",
    tags=["pokemon", "element"]
)
class Element(Document):
    """Element/Type for Pokemon attacks and resistances.

    Examples: Fire, Water, Grass, Electric, etc.
    """

    name: str = Field(..., description="Element name (Fire, Water, Grass, etc.)")
    description: str = Field(..., description="Element description")
    strong_against: list[str] = Field(
        default_factory=list,
        description="List of element names this is strong against"
    )
    weak_against: list[str] = Field(
        default_factory=list,
        description="List of element names this is weak against"
    )

    class Settings:
        name = "elements"
