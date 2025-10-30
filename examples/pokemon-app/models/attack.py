"""Attack datamodel for Pokemon moves."""

from beanie import Document
from pydantic import Field

from core.decorators import datamodel


@datamodel(
    name="Attack",
    description="Attack/Move that a Pokemon can learn. Examples: Tackle, Thunderbolt, Water Gun, etc.",
    tags=["pokemon", "attack"]
)
class Attack(Document):
    """Attack/Move that a Pokemon can learn.

    Examples: Tackle, Thunderbolt, Water Gun, etc.
    """

    name: str = Field(..., description="Attack name")
    description: str = Field(..., description="Attack description")
    power: int = Field(default=0, description="Attack power (0-150)")
    accuracy: float = Field(default=1.0, description="Attack accuracy (0-1)")
    element: str = Field(..., description="Element type of this attack")
    pp: int = Field(default=15, description="Power Points (uses per battle)")

    class Settings:
        name = "attacks"
