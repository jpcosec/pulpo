"""Trainer datamodel."""

from __future__ import annotations

from beanie import Document
from pydantic import Field

from core.decorators import datamodel
from models.pokemon import Pokemon


@datamodel(
    name="Trainer",
    description="A Pokemon Trainer with a team of Pokemons.",
    tags=["pokemon", "trainer"]
)
class Trainer(Document):
    """A Pokemon Trainer with a team of Pokemons."""

    name: str = Field(..., description="Trainer name")
    region: str = Field(default="Kanto", description="Home region")
    badge_count: int = Field(default=0, description="Number of badges earned (0-8)")
    level: int = Field(default=1, description="Trainer level")

    # Team
    pokemon_team: list[Pokemon] = Field(
        default_factory=list,
        description="List of Pokemon in this trainer's team (max 6)"
    )
    pokemon_count: int = Field(default=0, description="Total Pokemon caught")

    # Battle stats
    wins: int = Field(default=0, description="Battle wins")
    losses: int = Field(default=0, description="Battle losses")

    class Settings:
        name = "trainers"
