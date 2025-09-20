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
    
    def validate_initial_rack_size(self) -> bool:
        """Validate that rack contains exactly 14 tiles for initial game setup.
        
        According to Rummikub rules, each player starts with exactly 14 tiles.
        
        Returns:
            True if validation passes
            
        Raises:
            GameStateError: If rack doesn't contain exactly 14 tiles
        """
        if len(self.tile_ids) != 14:
            raise GameStateError(f"Initial rack must contain exactly 14 tiles, got {len(self.tile_ids)}")
        return True


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
    
    @classmethod
    def create_full_pool(cls) -> tuple["Pool", Dict[str, "TileInstance"]]:
        """Create a complete pool with all 106 tiles according to Rummikub rules.
        
        Creates:
        - 104 numbered tiles: 2 copies of each number (1-13) in each color (4 colors)
        - 2 joker tiles
        
        Returns:
            Tuple of (Pool instance, dictionary mapping tile IDs to TileInstance objects)
            
        Raises:
            GameStateError: If pool creation fails validation
        """
        from .tiles import TileInstance, NumberedTile, JokerTile, Color
        
        tile_instances = {}
        tile_ids = []
        
        # Create 104 numbered tiles (2 of each number 1-13 in each of 4 colors)
        for color in Color:
            for number in range(1, 14):  # 1-13 inclusive
                for copy in range(2):  # 2 copies of each
                    tile = TileInstance(kind=NumberedTile(number=number, color=color))
                    tile_instances[str(tile.id)] = tile
                    tile_ids.append(tile.id)
        
        # Create 2 joker tiles
        for _ in range(2):
            joker = TileInstance(kind=JokerTile())
            tile_instances[str(joker.id)] = joker
            tile_ids.append(joker.id)
        
        # Create pool and validate
        pool = cls(tile_ids=tile_ids)
        pool.validate_complete_pool(tile_instances)
        
        return pool, tile_instances
    
    def validate_complete_pool(self, tile_instances: Dict[str, "TileInstance"]) -> bool:
        """Validate that pool contains exactly the correct set of tiles.
        
        Validates:
        - No duplicate tile instances
        - Total of 106 tiles
        - Exactly 2 copies of each numbered tile (1-13 in each of 4 colors = 104 tiles)
        - Exactly 2 joker tiles
        
        Args:
            tile_instances: Dictionary mapping tile IDs to TileInstance objects
            
        Returns:
            True if validation passes
            
        Raises:
            GameStateError: If validation fails
        """
        from .tiles import NumberedTile, JokerTile, Color
        
        # Check for duplicate tile IDs first
        if len(set(self.tile_ids)) != len(self.tile_ids):
            raise GameStateError("Pool contains duplicate tile IDs")
        
        if len(self.tile_ids) != 106:
            raise GameStateError(f"Pool must contain exactly 106 tiles, got {len(self.tile_ids)}")
        
        # Count tiles by type
        numbered_tile_counts = {}  # (number, color) -> count
        joker_count = 0
        
        for tile_id in self.tile_ids:
            tile_id_str = str(tile_id)
            if tile_id_str not in tile_instances:
                raise GameStateError(f"Tile {tile_id} not found in tile_instances")
                
            tile = tile_instances[tile_id_str]
            
            if isinstance(tile.kind, NumberedTile):
                key = (tile.kind.number, tile.kind.color)
                numbered_tile_counts[key] = numbered_tile_counts.get(key, 0) + 1
            elif isinstance(tile.kind, JokerTile):
                joker_count += 1
            else:
                raise GameStateError(f"Unknown tile kind: {type(tile.kind)}")
        
        # Validate jokers first: should have exactly 2
        if joker_count != 2:
            raise GameStateError(f"Expected exactly 2 joker tiles, got {joker_count}")
        
        # Validate numbered tiles: should have exactly 2 of each (number, color) combination
        expected_numbered_count = 4 * 13  # 4 colors * 13 numbers = 52 unique combinations
        if len(numbered_tile_counts) != expected_numbered_count:
            raise GameStateError(f"Expected {expected_numbered_count} unique numbered tile types, got {len(numbered_tile_counts)}")
        
        for color in Color:
            for number in range(1, 14):
                key = (number, color)
                count = numbered_tile_counts.get(key, 0)
                if count != 2:
                    raise GameStateError(f"Expected exactly 2 copies of {color.value} {number}, got {count}")
        
        # Validate jokers: should have exactly 2
        if joker_count != 2:
            raise GameStateError(f"Expected exactly 2 joker tiles, got {joker_count}")
        
        return True


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
    
    @classmethod
    def create_new_game(cls, game_id: UUID, num_players: int) -> "GameState":
        """Create a new game state with specified number of players.
        
        Args:
            game_id: Unique identifier for the game
            num_players: Number of players (must be 2-4 according to Rummikub rules)
            
        Returns:
            New GameState instance
            
        Raises:
            GameStateError: If num_players is not within valid range (2-4)
        """
        if not (2 <= num_players <= 4):
            raise GameStateError(f"Number of players must be between 2 and 4, got {num_players}")
        
        return cls(game_id=game_id)
    
    def validate_player_count(self) -> bool:
        """Validate that the number of players is within the valid range.
        
        According to Rummikub rules, games support 2-4 players.
        
        Returns:
            True if validation passes
            
        Raises:
            GameStateError: If player count is not within valid range
        """
        num_players = len(self.players)
        if not (2 <= num_players <= 4):
            raise GameStateError(f"Number of players must be between 2 and 4, got {num_players}")
        return True
    
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