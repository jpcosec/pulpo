"""Pokemon and Trainer management operations."""

from pydantic import BaseModel, Field

from core.decorators import operation
from models.pokemon import Pokemon
from models.trainer import Trainer


class CatchPokemonInput(BaseModel):
    """Input for catching a Pokemon."""

    trainer_name: str = Field(..., description="Trainer name")
    pokemon_name: str = Field(..., description="Pokemon name to catch")
    element: str = Field(..., description="Pokemon element type")


class CatchPokemonOutput(BaseModel):
    """Output from catching a Pokemon."""

    success: bool = Field(..., description="Whether catch was successful")
    message: str = Field(..., description="Catch result message")
    team_size: int = Field(..., description="Current team size")


@operation(
    name="pokemon.management.catch",
    description="Trainer catches a new Pokemon",
    inputs=CatchPokemonInput,
    outputs=CatchPokemonOutput,
    models_in=["Trainer"],
    models_out=["Pokemon"]
)
async def catch_pokemon(input_data: CatchPokemonInput) -> CatchPokemonOutput:
    """Trainer catches a new Pokemon and adds to team."""
    # 70% catch rate
    success = True  # Simplified - always succeeds in this demo

    return CatchPokemonOutput(
        success=success,
        message=f"Trainer {input_data.trainer_name} caught {input_data.pokemon_name}!",
        team_size=6  # Demo value
    )


class TrainPokemonInput(BaseModel):
    """Input for training a Pokemon."""

    pokemon_name: str = Field(..., description="Pokemon to train")
    training_hours: int = Field(..., description="Hours of training")


class TrainPokemonOutput(BaseModel):
    """Output from training."""

    pokemon_name: str = Field(..., description="Pokemon trained")
    level_gained: int = Field(..., description="Levels gained")
    new_level: int = Field(..., description="New level")
    stats_increase: dict = Field(..., description="Stat increases")


@operation(
    name="pokemon.management.train",
    description="Train a Pokemon to increase stats and level",
    inputs=TrainPokemonInput,
    outputs=TrainPokemonOutput,
    models_in=["Pokemon"],
    models_out=["Pokemon"]
)
async def train_pokemon(input_data: TrainPokemonInput) -> TrainPokemonOutput:
    """Train a Pokemon, increasing its level and stats."""
    levels_gained = (input_data.training_hours // 10) + 1

    return TrainPokemonOutput(
        pokemon_name=input_data.pokemon_name,
        level_gained=levels_gained,
        new_level=5 + levels_gained,  # Demo value
        stats_increase={
            "attack": 5 * levels_gained,
            "defense": 3 * levels_gained,
            "speed": 4 * levels_gained
        }
    )


class CreateTrainerInput(BaseModel):
    """Input for creating a new trainer."""

    trainer_name: str = Field(..., description="Trainer name")
    region: str = Field(default="Kanto", description="Starting region")


class CreateTrainerOutput(BaseModel):
    """Output from trainer creation."""

    trainer_name: str = Field(..., description="Trainer name")
    starter_pokemon: str = Field(..., description="Starting Pokemon")
    message: str = Field(..., description="Welcome message")


@operation(
    name="pokemon.management.trainer_create",
    description="Create a new Pokemon trainer",
    inputs=CreateTrainerInput,
    outputs=CreateTrainerOutput,
    models_in=["Trainer"],
    models_out=["Pokemon"]
)
async def create_trainer(input_data: CreateTrainerInput) -> CreateTrainerOutput:
    """Create a new trainer and assign starter Pokemon."""
    starters = ["Charmander", "Squirtle", "Bulbasaur"]
    starter = starters[hash(input_data.trainer_name) % 3]

    return CreateTrainerOutput(
        trainer_name=input_data.trainer_name,
        starter_pokemon=starter,
        message=f"Welcome trainer {input_data.trainer_name}! You received {starter} as your starter Pokemon!"
    )
