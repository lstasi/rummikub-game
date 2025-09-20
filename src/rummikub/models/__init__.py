"""Rummikub game models package.

This package contains all domain models for the Rummikub game, including
tiles, melds, game state, and validation utilities.
"""

# Core models
from .tiles import Color, NumberedTile, JokerTile, TileKind, TileInstance
from .melds import Meld, MeldKind
from .game import Rack, Pool, Board, Player, GameState, GameStatus
from .actions import Turn, Action, PlayTilesAction, DrawAction

# Base classes and utilities
from .base import generate_uuid, to_dict, to_json

# Validation utilities
from .validators import (
    is_valid_group,
    is_valid_run,
    assign_jokers_in_group,
    assign_jokers_in_run,
    meld_value,
    initial_meld_total,
    validate_meld,
    validate_tile_ownership
)

# Exceptions
from .exceptions import (
    RummikubError,
    ValidationError,
    InvalidColorError,
    InvalidNumberError,
    InvalidMeldError,
    JokerAssignmentError,
    GameStateError
)

__all__ = [
    # Core models
    "Color",
    "NumberedTile", 
    "JokerTile",
    "TileKind",
    "TileInstance",
    "Meld",
    "MeldKind",
    "Rack",
    "Pool", 
    "Board",
    "Player",
    "GameState",
    "GameStatus",
    "Turn",
    "Action",
    "PlayTilesAction",
    "DrawAction",
    
    # Base utilities
    "generate_uuid",
    "to_dict",
    "to_json",
    
    # Validation utilities
    "is_valid_group",
    "is_valid_run",
    "assign_jokers_in_group",
    "assign_jokers_in_run",
    "meld_value",
    "initial_meld_total",
    "validate_meld",
    "validate_tile_ownership",
    
    # Exceptions
    "RummikubError",
    "ValidationError",
    "InvalidColorError",
    "InvalidNumberError",
    "InvalidMeldError",
    "JokerAssignmentError",
    "GameStateError"
]