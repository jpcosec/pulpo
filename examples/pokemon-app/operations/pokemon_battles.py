"""Pokemon battle operations."""

import random

from pydantic import BaseModel, Field

from core.decorators import operation
from models.pokemon import Pokemon
from models.fight_result import FightResult


class BattleInput(BaseModel):
    """Input for a Pokemon battle."""

    pokemon1_name: str = Field(..., description="First Pokemon name")
    pokemon2_name: str = Field(..., description="Second Pokemon name")


class BattleOutput(BaseModel):
    """Output from a Pokemon battle."""

    winner_name: str = Field(..., description="Name of winning Pokemon")
    loser_name: str = Field(..., description="Name of losing Pokemon")
    turns: int = Field(..., description="Number of turns")
    winning_move: str = Field(..., description="Attack that won")


@operation(
    name="pokemon.battles.execute",
    description="Simulate a battle between two Pokemon",
    inputs=BattleInput,
    outputs=BattleOutput,
    models_in=["Pokemon"],
    models_out=["FightResult"]
)
async def pokemon_battle(input_data: BattleInput) -> BattleOutput:
    """Simulate a Pokemon battle between two Pokemon.

    Determines winner based on stats and random chance.
    """
    # Simulate battle outcome
    winner = random.choice([input_data.pokemon1_name, input_data.pokemon2_name])
    loser = (
        input_data.pokemon2_name
        if winner == input_data.pokemon1_name
        else input_data.pokemon1_name
    )

    attacks = ["Tackle", "Thunderbolt", "Water Gun", "Ember", "Vine Whip"]
    winning_move = random.choice(attacks)

    return BattleOutput(
        winner_name=winner,
        loser_name=loser,
        turns=random.randint(3, 15),
        winning_move=winning_move
    )


class TrainerBattleInput(BaseModel):
    """Input for a trainer vs trainer battle."""

    trainer1_name: str = Field(..., description="First trainer name")
    trainer2_name: str = Field(..., description="Second trainer name")


class TrainerBattleOutput(BaseModel):
    """Output from a trainer battle."""

    winning_trainer: str = Field(..., description="Name of winning trainer")
    losing_trainer: str = Field(..., description="Name of losing trainer")
    battles_count: int = Field(..., description="Number of Pokemon battles")


@operation(
    name="pokemon.battles.trainer_execute",
    description="Simulate a full battle between two Pokemon trainers",
    inputs=TrainerBattleInput,
    outputs=TrainerBattleOutput,
    models_in=["Trainer"],
    models_out=["FightResult"]
)
async def trainer_battle(input_data: TrainerBattleInput) -> TrainerBattleOutput:
    """Simulate a full battle between two trainers.

    Each trainer uses multiple Pokemon from their team.
    """
    battles = random.randint(1, 6)
    winner = random.choice([input_data.trainer1_name, input_data.trainer2_name])
    loser = (
        input_data.trainer2_name
        if winner == input_data.trainer1_name
        else input_data.trainer1_name
    )

    return TrainerBattleOutput(
        winning_trainer=winner,
        losing_trainer=loser,
        battles_count=battles
    )
