"""Fight result datamodel."""

from beanie import Document
from pydantic import Field

from core.decorators import datamodel


@datamodel(
    name="FightResult",
    description="Result of a battle between two Pokemon.",
    tags=["pokemon", "battle"]
)
class FightResult(Document):
    """Result of a battle between two Pokemon."""

    pokemon1_name: str = Field(..., description="First Pokemon name")
    pokemon2_name: str = Field(..., description="Second Pokemon name")
    winner: str = Field(..., description="Name of winning Pokemon")
    loser: str = Field(..., description="Name of losing Pokemon")

    pokemon1_hp_left: int = Field(default=0, description="HP remaining for Pokemon 1")
    pokemon2_hp_left: int = Field(default=0, description="HP remaining for Pokemon 2")

    winning_move: str | None = Field(
        default=None,
        description="Attack that caused victory"
    )
    turns: int = Field(default=1, description="Number of turns the battle lasted")
    experience_gained: int = Field(default=0, description="Experience gained by winner")

    class Settings:
        name = "fight_results"
