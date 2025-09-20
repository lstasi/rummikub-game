"""Meld models with validation logic."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List
from uuid import UUID

from .base import generate_uuid
from .exceptions import InvalidMeldError


class MeldKind(str, Enum):
    """Types of melds in Rummikub."""
    GROUP = "group"
    RUN = "run"


@dataclass
class Meld:
    """A meld (group or run) containing tiles.
    
    This represents a valid combination of tiles on the board.
    The tiles list maintains order for runs; for groups, order
    doesn't affect validity but is preserved for deterministic serialization.
    """
    
    kind: MeldKind
    tiles: List[UUID]
    id: UUID = field(default_factory=generate_uuid)
    
    def __post_init__(self):
        """Validate that meld is not empty."""
        if not self.tiles:
            raise InvalidMeldError("Meld cannot be empty")
    
    def __str__(self) -> str:
        return f"{self.kind.value.title()} meld with {len(self.tiles)} tiles"