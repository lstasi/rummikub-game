"""Game state models: Player, Rack, Pool, Board, and GameState."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
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
    
    def validate_tile_ownership(self, tile_instances: Dict[str, "TileInstance"]) -> bool:
        """Validate that all tiles are properly allocated and no duplicates exist.
        
        Args:
            tile_instances: Dictionary mapping tile IDs to tile instances
            
        Returns:
            True if tile ownership is valid
            
        Raises:
            GameStateError: If tile ownership is invalid
        """
        from .tiles import TileInstance
        
        # Collect all tile IDs from all sources
        all_tile_ids = set()
        
        # Tiles in player racks
        for player in self.players:
            for tile_id in player.rack.tile_ids:
                if tile_id in all_tile_ids:
                    raise GameStateError(f"Duplicate tile {tile_id} found in player racks")
                all_tile_ids.add(tile_id)
        
        # Tiles in pool
        for tile_id in self.pool.tile_ids:
            if tile_id in all_tile_ids:
                raise GameStateError(f"Duplicate tile {tile_id} found in pool")
            all_tile_ids.add(tile_id)
        
        # Tiles on board
        for meld in self.board.melds:
            for tile_id in meld.tiles:
                if tile_id in all_tile_ids:
                    raise GameStateError(f"Duplicate tile {tile_id} found on board")
                all_tile_ids.add(tile_id)
        
        # Verify all tiles in tile_instances are accounted for
        expected_tile_ids = set(str(tid) for tid in tile_instances.keys())
        actual_tile_ids = set(str(tid) for tid in all_tile_ids)
        
        if expected_tile_ids != actual_tile_ids:
            missing = expected_tile_ids - actual_tile_ids
            extra = actual_tile_ids - expected_tile_ids
            if missing:
                raise GameStateError(f"Tiles missing from game state: {missing}")
            if extra:
                raise GameStateError(f"Extra tiles in game state: {extra}")
        
        return True
    
    def calculate_initial_meld_total(self, melds: List[Meld], tile_instances: Dict[str, "TileInstance"]) -> int:
        """Calculate total value of melds for initial meld requirement.
        
        Args:
            melds: List of melds to calculate total for
            tile_instances: Dictionary mapping tile IDs to tile instances
            
        Returns:
            Sum of all meld values
        """
        return sum(meld.get_value(tile_instances) for meld in melds)