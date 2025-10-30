"""Pokemon datamodel."""

from beanie import Document
from pydantic import Field

from core.decorators import datamodel


@datamodel(
    name="Pokemon",
    description="A Pokemon with stats, type, and attacks. Can evolve into other Pokemon and participate in battles.",
    tags=["pokemon", "creature"]
)
class Pokemon(Document):
    """A Pokemon with stats, type, and attacks.

    Can evolve into other Pokemon and participate in battles.
    """

    name: str = Field(..., description="Pokemon name")
    element: str = Field(..., description="Primary element type")
    level: int = Field(default=1, description="Current level (1-100)")
    experience: int = Field(default=0, description="Total experience points")

    # Stats
    health: int = Field(default=20, description="Hit Points (HP)")
    attack: int = Field(default=10, description="Attack stat")
    defense: int = Field(default=10, description="Defense stat")
    sp_attack: int = Field(default=10, description="Special Attack stat")
    sp_defense: int = Field(default=10, description="Special Defense stat")
    speed: int = Field(default=10, description="Speed stat")

    # Moves/Attacks
    attacks: list[str] = Field(
        default_factory=lambda: ["Tackle"],
        description="List of attack/move names this Pokemon knows"
    )

    # Evolution
    evolves_into: str | None = Field(
        default=None,
        description="Name of Pokemon this evolves into (if any)"
    )
    evolution_level: int | None = Field(
        default=None,
        description="Level required to evolve"
    )

    class Settings:
        name = "pokemons"
