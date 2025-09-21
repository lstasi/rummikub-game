"""Tile-related models: Color, TileKind, and TileInstance."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Union
from uuid import UUID

from .base import generate_uuid
from .exceptions import InvalidNumberError


class Color(str, Enum):
    """Tile colors in Rummikub."""
    BLACK = "black"
    RED = "red"  
    BLUE = "blue"
    ORANGE = "orange"


@dataclass(frozen=True)
class NumberedTile:
    """A numbered tile with a specific color and number (1-13)."""
    
    number: int
    color: Color
    type: str = "numbered"
    
    def __post_init__(self):
        """Validate tile number after initialization."""
        if not (1 <= self.number <= 13):
            raise InvalidNumberError(f"Tile number must be 1-13, got {self.number}")
    
    def __str__(self) -> str:
        return f"{self.color.value.title()} {self.number}"


@dataclass(frozen=True)
class JokerTile:
    """A joker tile that can represent any numbered tile contextually."""
    
    type: str = "joker"
    
    def __str__(self) -> str:
        return "Joker"


# Union type for tile kinds
TileKind = Union[NumberedTile, JokerTile]


@dataclass
class TileInstance:
    """A physical tile instance with a unique ID and kind.
    
    This represents an actual tile in the game, distinguishing between
    the two copies of each numbered tile and the two jokers.
    """
    
    kind: TileKind
    id: UUID = field(default_factory=generate_uuid)
    
    def __str__(self) -> str:
        return str(self.kind)
    
    @property
    def is_joker(self) -> bool:
        """Returns True if this tile is a joker."""
        return isinstance(self.kind, JokerTile)
    
    @property 
    def is_numbered(self) -> bool:
        """Returns True if this tile is a numbered tile."""
        return isinstance(self.kind, NumberedTile)