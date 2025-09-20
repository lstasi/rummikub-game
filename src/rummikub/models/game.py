"""Game state models: Player, Rack, Pool, Board, and GameState."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from .base import generate_uuid
from .exceptions import GameStateError
from .melds import Meld


@dataclass
class Rack:
    """A player's rack containing their tiles (hidden from other players)."""
    
    tile_ids: List[UUID] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Return the number of tiles in the rack."""
        return len(self.tile_ids)
    
    def is_empty(self) -> bool:
        """Return True if the rack has no tiles."""
        return len(self.tile_ids) == 0


@dataclass
class Pool:
    """The pool of face-down tiles available to draw from."""
    
    tile_ids: List[UUID] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Return the number of tiles in the pool."""
        return len(self.tile_ids)
    
    def is_empty(self) -> bool:
        """Return True if the pool has no tiles."""
        return len(self.tile_ids) == 0


@dataclass
class Board:
    """The game board containing all visible melds."""
    
    melds: List[Meld] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Return the number of melds on the board."""
        return len(self.melds)
    
    def is_empty(self) -> bool:
        """Return True if the board has no melds."""
        return len(self.melds) == 0


@dataclass
class Player:
    """A player in the game."""
    
    id: str
    name: Optional[str] = None
    initial_meld_met: bool = False
    rack: Rack = field(default_factory=Rack)


class GameStatus(str, Enum):
    """Game status enumeration."""
    WAITING_FOR_PLAYERS = "waiting_for_players"
    IN_PROGRESS = "in_progress"  
    COMPLETED = "completed"


@dataclass
class GameState:
    """Complete state of a Rummikub game."""
    
    game_id: UUID
    players: List[Player] = field(default_factory=list)
    current_player_index: int = 0
    pool: Pool = field(default_factory=Pool)
    board: Board = field(default_factory=Board)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: GameStatus = GameStatus.WAITING_FOR_PLAYERS
    winner_player_id: Optional[str] = None
    id: UUID = field(default_factory=generate_uuid)