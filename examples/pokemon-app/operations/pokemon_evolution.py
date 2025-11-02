"""Pokemon evolution operations."""

from pydantic import BaseModel, Field

from core.decorators import operation
from models.pokemon import Pokemon


class EvolutionInput(BaseModel):
    """Input for Pokemon evolution."""

    pokemon_name: str = Field(..., description="Name of Pokemon to evolve")


class EvolutionOutput(BaseModel):
    """Output from Pokemon evolution."""

    success: bool = Field(..., description="Whether evolution succeeded")
    evolved_into: str | None = Field(None, description="Name of evolved Pokemon")
    message: str = Field(..., description="Evolution result message")


@operation(
    name="pokemon.evolution.stage1",
    category="evolution",
    description="Evolve a Pokemon to its first evolution form",
    inputs=EvolutionInput,
    outputs=EvolutionOutput,
    models_in=["Pokemon"],
    models_out=["Pokemon"]
)
async def evolve_pokemon_stage1(input_data: EvolutionInput) -> EvolutionOutput:
    """Evolve a Pokemon to its first evolution.

    Example: Charmander → Charmeleon
    """
    return EvolutionOutput(
        success=True,
        evolved_into=f"{input_data.pokemon_name}->EvolutionForm1",
        message=f"Successfully evolved {input_data.pokemon_name}!"
    )


@operation(
    name="pokemon.evolution.stage2",
    category="evolution",
    description="Evolve a Pokemon to its second evolution form",
    inputs=EvolutionInput,
    outputs=EvolutionOutput,
    models_in=["Pokemon"],
    models_out=["Pokemon"]
)
async def evolve_pokemon_stage2(input_data: EvolutionInput) -> EvolutionOutput:
    """Evolve a Pokemon to its second evolution.

    Example: Charmeleon → Charizard
    """
    return EvolutionOutput(
        success=True,
        evolved_into=f"{input_data.pokemon_name}->EvolutionForm2",
        message=f"Successfully evolved {input_data.pokemon_name} to final form!"
    )
